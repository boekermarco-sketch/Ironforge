"""
Blutbild-PDF-Parser für deutsche Labor-PDFs.
Erkennt Markernamen + Werte automatisch via Regex und Biomarker-Alias-Matching.
"""
import re
import pdfplumber
from pathlib import Path
from datetime import date, datetime
from typing import Optional
from sqlalchemy.orm import Session

from app.models import Biomarker, BloodPanel, BloodValue, Stack


# Regex für deutsche Zahlenwerte (Komma als Dezimaltrenner)
_NUMBER_RE = re.compile(r"[-+]?\d{1,4}(?:[,\.]\d{1,4})?")
# Datum-Pattern: 01.04.2026 oder 01/04/2026 oder 2026-04-01
_DATE_RE = re.compile(r"(\d{2})[.\-/](\d{2})[.\-/](\d{4})|(\d{4})[.\-/](\d{2})[.\-/](\d{2})")


def _parse_german_float(value_str: str) -> Optional[float]:
    """Konvertiert deutschen Zahlstring (1.234,56 oder 1234,56) zu float."""
    if not value_str:
        return None
    cleaned = value_str.strip().replace(" ", "")
    # 1.234,56 → 1234.56
    if "," in cleaned and "." in cleaned:
        cleaned = cleaned.replace(".", "").replace(",", ".")
    else:
        cleaned = cleaned.replace(",", ".")
    try:
        return float(cleaned)
    except ValueError:
        return None


def _extract_date_from_text(text: str) -> Optional[date]:
    """Versucht das Abnahmedatum aus dem PDF-Text zu extrahieren."""
    for match in _DATE_RE.finditer(text):
        groups = match.groups()
        if groups[0]:  # DD.MM.YYYY
            try:
                return date(int(groups[2]), int(groups[1]), int(groups[0]))
            except ValueError:
                continue
        elif groups[3]:  # YYYY-MM-DD
            try:
                return date(int(groups[3]), int(groups[4]), int(groups[5]))
            except ValueError:
                continue
    return None


def _build_alias_map(db: Session) -> dict[str, int]:
    """
    Baut eine Map: alias_lower → biomarker_id
    Enthält name + alle Aliases jedes Biomarkers.
    """
    alias_map = {}
    for bm in db.query(Biomarker).all():
        alias_map[bm.name.lower()] = bm.id
        if bm.aliases:
            for alias in bm.aliases.split(","):
                alias_map[alias.strip().lower()] = bm.id
    return alias_map


def _find_biomarker_in_line(line: str, alias_map: dict) -> Optional[int]:
    """Sucht in einer Zeile nach einem bekannten Biomarker-Alias."""
    line_lower = line.lower()
    # Längste Übereinstimmung bevorzugen (z.B. "GPT (ALAT)" vor "GPT")
    best_match = None
    best_len = 0
    for alias, bm_id in alias_map.items():
        if alias in line_lower and len(alias) > best_len:
            best_match = bm_id
            best_len = len(alias)
    return best_match


def _extract_value_and_range(line: str) -> tuple[Optional[float], Optional[float], Optional[float], Optional[str]]:
    """
    Extrahiert Wert, Referenz-Min, Referenz-Max und Einheit aus einer Zeile.
    Typische Formate:
      - "Hämoglobin       17,7   g/dL    13,5 - 17,8"
      - "GPT (ALAT)   51   U/L   <50"
      - "Testosteron   >15,00   µg/L   2,49 - 8,36"
    """
    numbers = _NUMBER_RE.findall(line)
    floats = []
    for n in numbers:
        f = _parse_german_float(n)
        if f is not None:
            floats.append(f)

    value = floats[0] if floats else None
    ref_min = None
    ref_max = None

    # Referenzbereich: "13,5 - 17,8" oder "< 50" oder "> 60"
    range_match = re.search(r"(\d+[,.]?\d*)\s*[-–]\s*(\d+[,.]?\d*)", line)
    if range_match:
        ref_min = _parse_german_float(range_match.group(1))
        ref_max = _parse_german_float(range_match.group(2))

    less_match = re.search(r"<\s*(\d+[,.]?\d*)", line)
    if less_match and not range_match:
        ref_max = _parse_german_float(less_match.group(1))

    greater_match = re.search(r">\s*(\d+[,.]?\d*)", line)
    if greater_match and not range_match:
        ref_min = _parse_german_float(greater_match.group(1))

    # Einheit erkennen
    unit_match = re.search(
        r"\b(µg/L|ng/L|ng/dL|µg/dL|g/dL|mg/dL|mg/L|mmol/L|nmol/L|µmol/L|U/L|mU/L|µU/mL|IU/L|pmol/L|%|T/L|G/L|ml/min|ms|bpm|brpm|FU)\b",
        line
    )
    unit = unit_match.group(1) if unit_match else None

    return value, ref_min, ref_max, unit


def parse_pdf(pdf_path: Path, db: Session, lab_name: Optional[str] = None) -> Optional[BloodPanel]:
    """
    Hauptfunktion: Parsed eine Labor-PDF und speichert die Werte in der DB.
    Gibt das erstellte BloodPanel zurück oder None bei Fehler.
    """
    if not pdf_path.exists():
        print(f"FEHLER: PDF nicht gefunden: {pdf_path}")
        return None

    alias_map = _build_alias_map(db)
    extracted_values: dict[int, tuple[float, Optional[float], Optional[float], Optional[str]]] = {}
    panel_date = None
    full_text = ""

    try:
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                text = page.extract_text() or ""
                full_text += text + "\n"

                if not panel_date:
                    panel_date = _extract_date_from_text(text)

                for line in text.splitlines():
                    line = line.strip()
                    if len(line) < 3:
                        continue

                    bm_id = _find_biomarker_in_line(line, alias_map)
                    if bm_id and bm_id not in extracted_values:
                        value, ref_min, ref_max, unit = _extract_value_and_range(line)
                        if value is not None:
                            extracted_values[bm_id] = (value, ref_min, ref_max, unit)

    except Exception as e:
        print(f"FEHLER: PDF-Parsing: {e}")
        return None

    if not extracted_values:
        print(f"WARNUNG: Keine Biomarker erkannt in: {pdf_path.name}")
        return None

    if not panel_date:
        panel_date = date.today()
        print(f"WARNUNG: Kein Datum im PDF gefunden, verwende heute: {panel_date}")

    # Aktiven Stack zum Datum ermitteln
    active_stack = (
        db.query(Stack)
        .filter(Stack.start_date <= panel_date)
        .filter((Stack.end_date == None) | (Stack.end_date >= panel_date))
        .filter(Stack.status == "aktiv")
        .first()
    )

    panel = BloodPanel(
        date=panel_date,
        lab=lab_name or pdf_path.stem,
        notes=f"Automatisch geparst aus: {pdf_path.name}",
        active_stack_id=active_stack.id if active_stack else None,
        source_file=pdf_path.name
    )
    db.add(panel)
    db.flush()

    for bm_id, (value, ref_min, ref_max, unit) in extracted_values.items():
        bm = db.query(Biomarker).filter(Biomarker.id == bm_id).first()
        db.add(BloodValue(
            panel_id=panel.id,
            biomarker_id=bm_id,
            value=value,
            unit=unit or (bm.unit if bm else None),
            ref_min=ref_min,
            ref_max=ref_max,
        ))

    db.commit()
    print(f"OK: {len(extracted_values)} Marker aus '{pdf_path.name}' geparst (Datum: {panel_date})")
    return panel


def scan_folder_for_new_pdfs(db: Session) -> list[BloodPanel]:
    """
    Scannt den Ordner data/Blutbilder/ nach PDFs die noch nicht in der DB sind.
    Gibt Liste der neu erstellten Panels zurück.
    """
    base_dir = Path(__file__).resolve().parent.parent.parent
    blutbilder_dir = base_dir / "data" / "Blutbilder"

    if not blutbilder_dir.exists():
        return []

    existing_files = {
        p.source_file for p in db.query(BloodPanel).all()
        if p.source_file
    }

    new_panels = []
    for pdf_file in blutbilder_dir.glob("*.pdf"):
        if pdf_file.name not in existing_files:
            print(f"Neue PDF gefunden: {pdf_file.name}")
            panel = parse_pdf(pdf_file, db)
            if panel:
                new_panels.append(panel)

    return new_panels

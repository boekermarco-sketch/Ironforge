"""
MyFitnessPal CSV-Export → DailyLog (calories, protein, carbs, fat).

Export in MFP: myfitnesspal.com → Einstellungen → Daten exportieren
→ "Nutrition Summary" CSV per E-Mail → Datei in Imports/MyFitnessPal/ ablegen.

Typisches MFP-CSV-Format (Premium-Export):
  Date,Meal,Calories,Carbohydrates (g),Fat (g),Protein (g),Sodium (mg),Sugar (g)
  2026-04-14,Breakfast,370,45.2,8.1,32.4,890,12.3
  2026-04-14,Lunch,650,78.3,21.5,43.2,1240,8.7
  ...

Eine Zeile pro Mahlzeit/Lebensmittel – wird zu Tagesgesamtwerten aggregiert.
"""
import csv
from datetime import date, datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.models import DailyLog

MFP_CSV_DIR = Path(__file__).resolve().parent.parent.parent / "Imports" / "MyFitnessPal"


# ─── Hilfsfunktionen ──────────────────────────────────────────────────────────

def _parse_date(raw: str) -> date | None:
    """Parst MFP-Datumsformate: ISO, US, deutsch, englisch-ausgeschrieben."""
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%d.%m.%Y", "%d/%m/%Y",
                "%B %d, %Y", "%b %d, %Y"):
        try:
            return datetime.strptime(raw, fmt).date()
        except ValueError:
            continue
    return None


def _find_col(headers: list[str], *candidates: str) -> int | None:
    """Gibt den Index der ersten passenden Spalte zurück (case-insensitiv)."""
    lower = [h.lower().strip() for h in headers]
    for c in candidates:
        for i, h in enumerate(lower):
            if c.lower() in h:
                return i
    return None


def _safe_float(row: list[str], idx: int | None) -> float:
    if idx is None or idx >= len(row):
        return 0.0
    try:
        val = row[idx].strip().replace(",", ".")
        return float(val) if val else 0.0
    except ValueError:
        return 0.0


def _is_totals_row(row: list[str], ci_meal: int | None) -> bool:
    """Filtert MFP-'Totals'-Zusammenfassungszeilen heraus."""
    if ci_meal is not None and ci_meal < len(row):
        meal = row[ci_meal].strip().lower()
        if meal in ("totals", "gesamt", "daily totals", "tagesgesamt"):
            return True
    return False


# ─── Import-Logik ─────────────────────────────────────────────────────────────

def import_mfp_csv(filepath: Path, db: Session) -> dict:
    """Importiert eine MFP-CSV-Datei in DailyLog."""
    try:
        with open(filepath, encoding="utf-8-sig") as f:
            reader = csv.reader(f)
            headers = next(reader, None)
            if not headers:
                return {"error": "CSV leer oder kein Header"}

            ci_date = _find_col(headers, "date", "datum")
            ci_cal  = _find_col(headers, "calories", "kcal", "energie", "kalorien")
            ci_fat  = _find_col(headers, "fat (g)", "total fat", "fat", "fett")
            ci_carb = _find_col(headers, "carbohydrates", "carbs", "kohlenhydrate", "carbohydrate (g)")
            ci_prot = _find_col(headers, "protein")
            ci_meal = _find_col(headers, "meal", "mahlzeit")

            if ci_date is None or ci_cal is None:
                return {"skipped": True, "reason": f"Keine Ernährungsspalten – kein Nutrition-Export (Spalten: {', '.join(headers[:6])})"}

            by_date: dict[date, dict] = {}
            for row in reader:
                if not row:
                    continue
                if _is_totals_row(row, ci_meal):
                    continue
                d = _parse_date(row[ci_date]) if ci_date < len(row) else None
                if not d:
                    continue
                if d not in by_date:
                    by_date[d] = {"cal": 0.0, "fat": 0.0, "carb": 0.0, "prot": 0.0}
                by_date[d]["cal"]  += _safe_float(row, ci_cal)
                by_date[d]["fat"]  += _safe_float(row, ci_fat)
                by_date[d]["carb"] += _safe_float(row, ci_carb)
                by_date[d]["prot"] += _safe_float(row, ci_prot)

    except Exception as exc:
        return {"error": str(exc)}

    imported = updated = 0
    for d, n in by_date.items():
        if n["cal"] == 0:
            continue
        log = db.query(DailyLog).filter(DailyLog.date == d).first()
        is_new = log is None
        if is_new:
            log = DailyLog(date=d, source="myfitnesspal")
            db.add(log)
            db.flush()
        else:
            if log.source not in ("myfitnesspal", "gemischt"):
                log.source = "gemischt"

        log.calories = round(n["cal"])
        if n["prot"] > 0: log.protein = round(n["prot"], 1)
        if n["carb"] > 0: log.carbs   = round(n["carb"], 1)
        if n["fat"]  > 0: log.fat     = round(n["fat"],  1)

        if is_new:
            imported += 1
        else:
            updated += 1

    db.commit()
    return {
        "imported": imported,
        "updated":  updated,
        "total":    imported + updated,
        "dates":    len(by_date),
    }


def scan_mfp_folder(db: Session) -> dict:
    """Scannt Imports/MyFitnessPal/ und importiert alle CSV-Dateien."""
    if not MFP_CSV_DIR.exists():
        return {"error": f"Ordner nicht gefunden: {MFP_CSV_DIR}"}

    csvs = list(MFP_CSV_DIR.glob("*.csv"))
    if not csvs:
        return {"error": "Keine CSV-Dateien in Imports/MyFitnessPal/ gefunden"}

    total_imp = total_upd = 0
    errors = []
    skipped_files = []
    for f in csvs:
        result = import_mfp_csv(f, db)
        if result.get("skipped"):
            skipped_files.append(f"{f.name} ({result.get('reason', 'übersprungen')})")
        elif result.get("error"):
            errors.append(f"{f.name}: {result['error']}")
        else:
            total_imp += result.get("imported", 0)
            total_upd += result.get("updated",  0)

    return {
        "files":    len(csvs),
        "imported": total_imp,
        "updated":  total_upd,
        "errors":   errors,
        "skipped_files": skipped_files,
    }

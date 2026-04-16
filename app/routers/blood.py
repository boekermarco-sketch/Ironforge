from fastapi import APIRouter, Request, Depends, Form, UploadFile, File, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import date
from pathlib import Path
import shutil

from app.database import get_db
from app.models import BloodPanel, BloodValue, Biomarker, Stack, DoseEvent, Substance
from app.services.blood_pdf_parser import scan_folder_for_new_pdfs, parse_pdf

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
BLUTBILDER_DIR = BASE_DIR / "data" / "Blutbilder"


def _status(value, ref_min, ref_max, optimal_min=None, optimal_max=None):
    """Gibt Ampel-Status zurück: kritisch / warnung / optimal / normal"""
    if value is None:
        return "unbekannt"
    if ref_min is not None and value < ref_min:
        return "kritisch"
    if ref_max is not None and value > ref_max:
        return "kritisch"
    if optimal_min is not None and value < optimal_min:
        return "warnung"
    if optimal_max is not None and value > optimal_max:
        return "warnung"
    if optimal_min is not None and optimal_max is not None:
        return "optimal"
    return "normal"


@router.get("/", include_in_schema=False)
async def blood_overview(request: Request, db: Session = Depends(get_db)):
    panels = db.query(BloodPanel).order_by(BloodPanel.date.desc()).all()
    biomarkers = db.query(Biomarker).order_by(Biomarker.category, Biomarker.name).all()
    stacks = db.query(Stack).order_by(Stack.start_date.desc()).all()

    return templates.TemplateResponse("blood.html", {
        "request": request,
        "panels": panels,
        "biomarkers": biomarkers,
        "stacks": stacks,
        "today": date.today(),
    })


@router.get("/{panel_id}", include_in_schema=False)
async def blood_panel_detail(panel_id: int, request: Request, db: Session = Depends(get_db)):
    panel = db.query(BloodPanel).filter(BloodPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Blutbild nicht gefunden")

    rows = (
        db.query(BloodValue, Biomarker)
        .join(Biomarker, BloodValue.biomarker_id == Biomarker.id)
        .filter(BloodValue.panel_id == panel_id)
        .order_by(Biomarker.category, Biomarker.name)
        .all()
    )

    # Kategorie-Gruppen + Ampel-Status
    grouped: dict[str, list] = {}
    for bv, bm in rows:
        st = _status(bv.value, bv.ref_min or bm.ref_min, bv.ref_max or bm.ref_max, bm.optimal_min, bm.optimal_max)
        grouped.setdefault(bm.category or "Sonstiges", []).append({
            "bv": bv, "bm": bm, "status": st
        })

    # Vergleich mit vorherigem Panel
    prev_panel = (
        db.query(BloodPanel)
        .filter(BloodPanel.date < panel.date)
        .order_by(BloodPanel.date.desc())
        .first()
    )
    prev_values: dict[int, float] = {}
    if prev_panel:
        for pv in db.query(BloodValue).filter(BloodValue.panel_id == prev_panel.id).all():
            prev_values[pv.biomarker_id] = pv.value

    all_biomarkers = db.query(Biomarker).order_by(Biomarker.category, Biomarker.name).all()
    tagesplan = _get_tagesplan(panel.date, db)

    return templates.TemplateResponse("blood_panel.html", {
        "request": request,
        "panel": panel,
        "grouped": grouped,
        "prev_panel": prev_panel,
        "prev_values": prev_values,
        "all_biomarkers": all_biomarkers,
        "tagesplan": tagesplan,
        "today": date.today(),
    })


@router.post("/pdf-scan", include_in_schema=False)
async def scan_pdfs(request: Request, db: Session = Depends(get_db)):
    new_panels = scan_folder_for_new_pdfs(db)
    return RedirectResponse(f"/blutbilder/", status_code=303)


@router.post("/pdf-upload", include_in_schema=False)
async def upload_pdf(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    if not file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Nur PDF-Dateien erlaubt")

    dest = BLUTBILDER_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)

    panel = parse_pdf(dest, db)
    if panel:
        return RedirectResponse(f"/blutbilder/{panel.id}", status_code=303)
    return RedirectResponse("/blutbilder/", status_code=303)


@router.post("/manuell", include_in_schema=False)
async def add_manual_panel(
    panel_date: str = Form(...),
    lab: str = Form(""),
    notes: str = Form(""),
    active_stack_id: str = Form(""),
    db: Session = Depends(get_db)
):
    panel = BloodPanel(
        date=date.fromisoformat(panel_date),
        lab=lab or None,
        notes=notes or None,
        active_stack_id=int(active_stack_id) if active_stack_id else None,
    )
    db.add(panel)
    db.commit()
    db.refresh(panel)
    return RedirectResponse(f"/blutbilder/{panel.id}", status_code=303)


@router.post("/{panel_id}/wert", include_in_schema=False)
async def add_blood_value(
    panel_id: int,
    biomarker_id: int = Form(...),
    value: float = Form(...),
    unit: str = Form(""),
    ref_min: str = Form(""),
    ref_max: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    db.add(BloodValue(
        panel_id=panel_id,
        biomarker_id=biomarker_id,
        value=value,
        unit=unit or None,
        ref_min=float(ref_min) if ref_min else None,
        ref_max=float(ref_max) if ref_max else None,
        notes=notes or None,
    ))
    db.commit()
    return RedirectResponse(f"/blutbilder/{panel_id}", status_code=303)


@router.post("/{panel_id}/loeschen", include_in_schema=False)
async def delete_blood_panel(panel_id: int, db: Session = Depends(get_db)):
    panel = db.query(BloodPanel).filter(BloodPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Blutbild nicht gefunden")
    db.delete(panel)
    db.commit()
    return RedirectResponse("/blutbilder/", status_code=303)


@router.post("/{panel_id}/notizen", include_in_schema=False)
async def update_panel_notes(
    panel_id: int,
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    panel = db.query(BloodPanel).filter(BloodPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Blutbild nicht gefunden")
    panel.notes = notes or None
    db.commit()
    return RedirectResponse(f"/blutbilder/{panel_id}", status_code=303)


def _get_tagesplan(panel_date: date, db: Session) -> dict:
    """
    Gibt aktuelle DoseEvents gruppiert nach Tageszeit zurück.
    Zeitfenster: morgens, mittag, abend, nacht + injektionen
    """
    stack = (
        db.query(Stack)
        .filter(Stack.start_date <= panel_date)
        .filter((Stack.end_date == None) | (Stack.end_date >= panel_date))
        .filter(Stack.status == "aktiv")
        .first()
    )
    if not stack:
        return {}

    rows = (
        db.query(DoseEvent, Substance)
        .join(Substance, DoseEvent.substance_id == Substance.id)
        .filter(DoseEvent.stack_id == stack.id)
        .filter(DoseEvent.start_date <= panel_date)
        .filter((DoseEvent.end_date == None) | (DoseEvent.end_date >= panel_date))
        .order_by(Substance.name)
        .all()
    )

    SLOT_ORDER = ["07:00", "10-11", "17-18", "21-22", "Injektionen"]
    plan: dict[str, list] = {s: [] for s in SLOT_ORDER}
    plan["Sonstiges"] = []

    def _slot(timing: str) -> str:
        t = (timing or "").lower()
        # Injektionen zuerst prüfen (Subkutan/IM schlägt Zeitangaben)
        if any(k in t for k in ["intramuskulär", "intramuskulaer", "subkutan", "i.m.", "pin-tag",
                                 "mi abend", "so morgen", "donnerstag morgen", "mittwoch abend",
                                 "sonntag morgen"]):
            return "Injektionen"
        if "07" in t or ("nüchtern" in t and "abend" not in t):
            return "07:00"
        if "10" in t or "11" in t or "erst" in t:
            return "10-11"
        if "17" in t or "18" in t:
            return "17-18"
        if "21" in t or "22" in t or "schlaf" in t or "nacht" in t:
            return "21-22"
        return "Sonstiges"

    for de, sub in rows:
        slot = _slot(de.timing or "")
        plan[slot].append({
            "name": sub.name,
            "dose": f"{de.dose_amount:g} {de.dose_unit}",
            "timing": de.timing or "",
            "notes": de.notes or "",
        })

    # Injektionen extra behandeln (Steroide sind meist 2x/Woche)
    inj_rows = (
        db.query(DoseEvent, Substance)
        .join(Substance, DoseEvent.substance_id == Substance.id)
        .filter(DoseEvent.stack_id == stack.id)
        .filter(DoseEvent.start_date <= panel_date)
        .filter((DoseEvent.end_date == None) | (DoseEvent.end_date >= panel_date))
        .filter(Substance.route.in_(["intramuskulaer", "subkutan"]))
        .order_by(Substance.name)
        .all()
    )
    if inj_rows:
        plan["Injektionen"] = [
            {"name": sub.name, "dose": f"{de.dose_amount:g} {de.dose_unit}",
             "timing": de.timing or "", "notes": de.notes or ""}
            for de, sub in inj_rows
        ]

    return {k: v for k, v in plan.items() if v}


@router.get("/api/verlauf/{biomarker_id}")
async def biomarker_trend(biomarker_id: int, db: Session = Depends(get_db)):
    """API-Endpoint für Chart.js: Verlauf eines Markers über alle Blutbilder."""
    rows = (
        db.query(BloodValue, BloodPanel)
        .join(BloodPanel, BloodValue.panel_id == BloodPanel.id)
        .filter(BloodValue.biomarker_id == biomarker_id)
        .order_by(BloodPanel.date.asc())
        .all()
    )
    bm = db.query(Biomarker).filter(Biomarker.id == biomarker_id).first()
    return {
        "marker": bm.name if bm else str(biomarker_id),
        "unit": bm.unit if bm else "",
        "ref_min": bm.ref_min if bm else None,
        "ref_max": bm.ref_max if bm else None,
        "data": [
            {"date": str(bp.date), "value": bv.value}
            for bv, bp in rows
        ]
    }

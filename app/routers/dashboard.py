from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date, timedelta
from pathlib import Path

from app.database import get_db
from app.models import Stack, DoseEvent, Substance, DailyLog, BloodPanel, BloodValue, Biomarker, MedicalEvent, JournalEntry

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", include_in_schema=False)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    today = date.today()

    # Aktiver Stack
    active_stack = (
        db.query(Stack)
        .filter(Stack.start_date <= today)
        .filter((Stack.end_date == None) | (Stack.end_date >= today))
        .filter(Stack.status == "aktiv")
        .first()
    )

    # Aktive Dosierungen im Stack
    active_doses = []
    if active_stack:
        active_doses = (
            db.query(DoseEvent, Substance)
            .join(Substance, DoseEvent.substance_id == Substance.id)
            .filter(DoseEvent.stack_id == active_stack.id)
            .filter(DoseEvent.start_date <= today)
            .filter((DoseEvent.end_date == None) | (DoseEvent.end_date >= today))
            .order_by(Substance.category, Substance.name)
            .all()
        )

    # Letzter Tageslog
    last_log = db.query(DailyLog).order_by(DailyLog.date.desc()).first()

    # Letztes Blutbild
    last_panel = db.query(BloodPanel).order_by(BloodPanel.date.desc()).first()
    critical_values = []
    if last_panel:
        bvs = (
            db.query(BloodValue, Biomarker)
            .join(Biomarker, BloodValue.biomarker_id == Biomarker.id)
            .filter(BloodValue.panel_id == last_panel.id)
            .all()
        )
        for bv, bm in bvs:
            status = _value_status(bv.value, bv.ref_min, bv.ref_max)
            if status == "kritisch":
                critical_values.append({"name": bm.name, "value": bv.value, "unit": bv.unit or bm.unit})

    # Letztes medizinisches Ereignis
    last_event = db.query(MedicalEvent).order_by(MedicalEvent.date.desc()).first()

    # Letzte 7 Tage HRV + Gewicht für Mini-Chart
    week_ago = today - timedelta(days=7)
    recent_logs = (
        db.query(DailyLog)
        .filter(DailyLog.date >= week_ago)
        .order_by(DailyLog.date.asc())
        .all()
    )

    # Stack-Fortschritt
    stack_progress = None
    stack_days_total = None
    stack_days_done = None
    if active_stack and active_stack.end_date:
        stack_days_total = (active_stack.end_date - active_stack.start_date).days
        stack_days_done = (today - active_stack.start_date).days
        stack_progress = min(100, int((stack_days_done / stack_days_total) * 100))

    # Nächstes Blutbild aus Journal oder hartcodiert
    next_blood_date = date(2026, 5, 10)  # zweites geplantes Blutbild

    # Letzte Journal-Einträge
    recent_journal = (
        db.query(JournalEntry)
        .order_by(JournalEntry.date.desc(), JournalEntry.id.desc())
        .limit(3)
        .all()
    )

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "today": today,
        "active_stack": active_stack,
        "active_doses": active_doses,
        "last_log": last_log,
        "last_panel": last_panel,
        "critical_values": critical_values,
        "last_event": last_event,
        "recent_logs": recent_logs,
        "stack_progress": stack_progress,
        "stack_days_total": stack_days_total,
        "stack_days_done": stack_days_done,
        "next_blood_date": next_blood_date,
        "recent_journal": recent_journal,
    })


def _value_status(value, ref_min, ref_max) -> str:
    if value is None:
        return "unbekannt"
    if ref_min is not None and value < ref_min:
        return "kritisch"
    if ref_max is not None and value > ref_max:
        return "kritisch"
    return "normal"

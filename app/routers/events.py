from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from pathlib import Path

from app.database import get_db
from app.models import MedicalEvent, DoseEvent, Substance, Stack

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

EVENT_TYPES = ["Aderlass", "Blutspende", "Arzttermin", "Impfung", "Sonstiges"]


@router.get("/", include_in_schema=False)
async def events_overview(request: Request, db: Session = Depends(get_db)):
    events = db.query(MedicalEvent).order_by(MedicalEvent.date.desc()).all()

    # Stack-Timeline: alle DoseEvents mit Substanz + Stack
    dose_rows = (
        db.query(DoseEvent, Substance, Stack)
        .join(Substance, DoseEvent.substance_id == Substance.id)
        .outerjoin(Stack, DoseEvent.stack_id == Stack.id)
        .order_by(DoseEvent.start_date.desc())
        .limit(200)
        .all()
    )

    return templates.TemplateResponse("events.html", {
        "request": request,
        "events": events,
        "event_types": EVENT_TYPES,
        "today": date.today(),
        "dose_rows": dose_rows,
    })


@router.post("/neu", include_in_schema=False)
async def add_event(
    event_date: str = Form(...),
    event_type: str = Form(...),
    amount_ml: str = Form(default=""),
    location: str = Form(default=""),
    notes: str = Form(default=""),
    db: Session = Depends(get_db)
):
    db.add(MedicalEvent(
        date=date.fromisoformat(event_date),
        event_type=event_type,
        amount_ml=int(amount_ml) if amount_ml.strip() else None,
        location=location or None,
        notes=notes or None,
    ))
    db.commit()
    return RedirectResponse("/ereignisse/", status_code=303)


@router.post("/{event_id}/loeschen", include_in_schema=False)
async def delete_event(event_id: int, db: Session = Depends(get_db)):
    event = db.query(MedicalEvent).filter(MedicalEvent.id == event_id).first()
    if event:
        db.delete(event)
        db.commit()
    return RedirectResponse("/ereignisse/", status_code=303)

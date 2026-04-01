from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date
from pathlib import Path

from app.database import get_db
from app.models import Stack, Substance, DoseEvent

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", include_in_schema=False)
async def stack_overview(request: Request, db: Session = Depends(get_db)):
    today = date.today()
    stacks = db.query(Stack).order_by(Stack.start_date.desc()).all()

    active_stack = next((s for s in stacks if s.status == "aktiv"), None)
    active_doses = []
    if active_stack:
        rows = (
            db.query(DoseEvent, Substance)
            .join(Substance, DoseEvent.substance_id == Substance.id)
            .filter(DoseEvent.stack_id == active_stack.id)
            .filter(DoseEvent.start_date <= today)
            .filter((DoseEvent.end_date == None) | (DoseEvent.end_date >= today))
            .order_by(Substance.category, Substance.name)
            .all()
        )
        # Gruppiert nach Kategorie
        grouped: dict[str, list] = {}
        for de, sub in rows:
            grouped.setdefault(sub.category, []).append({"dose": de, "substance": sub})
        active_doses = grouped

    substances = db.query(Substance).filter(Substance.active == True).order_by(Substance.category, Substance.name).all()

    return templates.TemplateResponse("stack.html", {
        "request": request,
        "stacks": stacks,
        "active_stack": active_stack,
        "active_doses": active_doses,
        "substances": substances,
        "today": today,
    })


@router.post("/substanz/neu", include_in_schema=False)
async def add_substance(
    request: Request,
    name: str = Form(...),
    category: str = Form(...),
    route: str = Form("oral"),
    default_unit: str = Form("mg"),
    description: str = Form(""),
    db: Session = Depends(get_db)
):
    existing = db.query(Substance).filter(Substance.name == name).first()
    if existing:
        raise HTTPException(status_code=400, detail="Substanz existiert bereits")
    db.add(Substance(name=name, category=category, route=route, default_unit=default_unit, description=description))
    db.commit()
    return RedirectResponse("/stack/", status_code=303)


@router.post("/dosis/neu", include_in_schema=False)
async def add_dose_event(
    substance_id: int = Form(...),
    stack_id: int = Form(...),
    dose_amount: float = Form(...),
    dose_unit: str = Form("mg"),
    frequency: str = Form(""),
    timing: str = Form(""),
    start_date: str = Form(...),
    change_reason: str = Form(""),
    notes: str = Form(""),
    db: Session = Depends(get_db)
):
    db.add(DoseEvent(
        substance_id=substance_id,
        stack_id=stack_id,
        dose_amount=dose_amount,
        dose_unit=dose_unit,
        frequency=frequency,
        timing=timing,
        start_date=date.fromisoformat(start_date),
        change_reason=change_reason or None,
        notes=notes or None,
    ))
    db.commit()
    return RedirectResponse("/stack/", status_code=303)


@router.post("/dosis/{dose_id}/abschliessen", include_in_schema=False)
async def end_dose_event(
    dose_id: int,
    end_date: str = Form(default=None),
    db: Session = Depends(get_db)
):
    de = db.query(DoseEvent).filter(DoseEvent.id == dose_id).first()
    if de:
        de.end_date = date.fromisoformat(end_date) if end_date else date.today()
        db.commit()
    return RedirectResponse("/stack/", status_code=303)

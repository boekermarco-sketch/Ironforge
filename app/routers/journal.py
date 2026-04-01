from fastapi import APIRouter, Request, Depends, Form, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, datetime
from pathlib import Path
import shutil
import uuid

from app.database import get_db
from app.models import JournalEntry, DailyLog

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
FOTOS_DIR = BASE_DIR / "data" / "Fortschritt_Fotos"

ENTRY_TYPES = ["Fortschrittsfoto", "Blutbild", "Garmin", "Check-in", "Allgemein"]
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp", ".pdf"}


@router.get("/", include_in_schema=False)
async def journal_overview(
    request: Request,
    entry_type: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(JournalEntry)
    if entry_type:
        query = query.filter(JournalEntry.entry_type == entry_type)
    entries = query.order_by(JournalEntry.date.desc(), JournalEntry.id.desc()).all()

    return templates.TemplateResponse("journal.html", {
        "request": request,
        "entries": entries,
        "entry_types": ENTRY_TYPES,
        "active_filter": entry_type,
        "today": date.today(),
    })


@router.post("/neu", include_in_schema=False)
async def add_journal_entry(
    request: Request,
    entry_date: str = Form(default=None),
    entry_time: str = Form(default=""),
    title: str = Form(...),
    entry_type: str = Form(default="Allgemein"),
    analysis_text: str = Form(default=""),
    tags: str = Form(default=""),
    weight_at_time: str = Form(default=""),
    body_fat_at_time: str = Form(default=""),
    notes: str = Form(default=""),
    image: UploadFile = File(default=None),
    db: Session = Depends(get_db)
):
    entry_date_obj = date.fromisoformat(entry_date) if entry_date else date.today()
    image_path = None

    # Bild speichern
    if image and image.filename:
        ext = Path(image.filename).suffix.lower()
        if ext in ALLOWED_EXTENSIONS:
            unique_name = f"{entry_date_obj}_{uuid.uuid4().hex[:8]}{ext}"
            dest = FOTOS_DIR / unique_name
            with open(dest, "wb") as f:
                shutil.copyfileobj(image.file, f)
            image_path = f"Fortschritt_Fotos/{unique_name}"

    # Gewicht aus Tageslog holen wenn nicht angegeben
    weight_val = float(weight_at_time) if weight_at_time.strip() else None
    fat_val = float(body_fat_at_time) if body_fat_at_time.strip() else None
    if not weight_val:
        log = db.query(DailyLog).filter(DailyLog.date == entry_date_obj).first()
        if log:
            weight_val = log.weight
            fat_val = fat_val or log.body_fat

    entry = JournalEntry(
        date=entry_date_obj,
        time=entry_time or None,
        title=title,
        entry_type=entry_type,
        image_path=image_path,
        analysis_text=analysis_text or None,
        tags=tags or None,
        weight_at_time=weight_val,
        body_fat_at_time=fat_val,
        notes=notes or None,
    )
    db.add(entry)
    db.commit()
    return RedirectResponse("/journal/", status_code=303)


@router.post("/{entry_id}/loeschen", include_in_schema=False)
async def delete_entry(entry_id: int, db: Session = Depends(get_db)):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if entry:
        # Bild löschen wenn vorhanden
        if entry.image_path:
            img = BASE_DIR / "data" / entry.image_path
            if img.exists():
                img.unlink()
        db.delete(entry)
        db.commit()
    return RedirectResponse("/journal/", status_code=303)

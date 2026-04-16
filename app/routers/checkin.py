from fastapi import APIRouter, Request, Depends, Form, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from pathlib import Path

from app.database import get_db
from app.models import JournalEntry, DailyLog, BloodPanel
from app.services.checkin_scanner import get_all_checkins, scan_checkin_folder

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", include_in_schema=False)
async def checkin_overview(request: Request, db: Session = Depends(get_db)):
    grouped = get_all_checkins(db)

    # Tageslog-Daten für jeden Check-in-Tag
    logs: dict[date, DailyLog] = {}
    for d in grouped:
        log = db.query(DailyLog).filter(DailyLog.date == d).first()
        if log:
            logs[d] = log

    # Zu diesem Datum gehöriges Blutbild (±3 Tage)
    panels: dict[date, BloodPanel] = {}
    for d in grouped:
        panel = (
            db.query(BloodPanel)
            .filter(BloodPanel.date >= d - timedelta(days=3))
            .filter(BloodPanel.date <= d + timedelta(days=3))
            .order_by(BloodPanel.date.asc())
            .first()
        )
        if panel:
            panels[d] = panel

    # Sortierte Datumsliste (neueste zuerst) als Liste für JS
    date_list = [str(d) for d in sorted(grouped.keys(), reverse=True)]

    verlauf_entry = (
        db.query(JournalEntry)
        .filter(JournalEntry.entry_type == "CheckIn-Verlauf")
        .first()
    )

    return templates.TemplateResponse("checkin.html", {
        "request": request,
        "grouped": grouped,
        "logs": logs,
        "panels": panels,
        "date_list": date_list,
        "blast_start": date(2026, 2, 23),
        "verlauf": verlauf_entry.analysis_text if verlauf_entry else "",
        "today": date.today(),
    })


@router.post("/scan", include_in_schema=False)
async def trigger_scan(db: Session = Depends(get_db)):
    new = scan_checkin_folder(db)
    return RedirectResponse(f"/checkin/?msg={len(new)} neue Fotos importiert", status_code=303)


@router.post("/{entry_id}/analyse", include_in_schema=False)
async def save_analysis(
    entry_id: int,
    analysis_text: str = Form(""),
    db: Session = Depends(get_db)
):
    entry = db.query(JournalEntry).filter(JournalEntry.id == entry_id).first()
    if not entry:
        raise HTTPException(status_code=404)
    entry.analysis_text = analysis_text
    db.commit()
    return RedirectResponse("/checkin/", status_code=303)


@router.post("/verlauf", include_in_schema=False)
async def save_verlauf(
    verlauf_text: str = Form(""),
    db: Session = Depends(get_db)
):
    entry = db.query(JournalEntry).filter(JournalEntry.entry_type == "CheckIn-Verlauf").first()
    if entry:
        entry.analysis_text = verlauf_text
    else:
        db.add(JournalEntry(
            date=date.today(),
            title="Fortlaufender Verlauf",
            entry_type="CheckIn-Verlauf",
            analysis_text=verlauf_text,
        ))
    db.commit()
    return RedirectResponse("/checkin/", status_code=303)


@router.get("/api/entries")
async def api_entries(db: Session = Depends(get_db)):
    """Alle Check-in Einträge als JSON für den JS-Client."""
    grouped = get_all_checkins(db)
    result = []
    for d, entries in sorted(grouped.items(), reverse=True):
        log = db.query(DailyLog).filter(DailyLog.date == d).first()
        result.append({
            "date": str(d),
            "date_fmt": d.strftime("%d.%m.%Y"),
            "entries": [
                {
                    "id": e.id,
                    "image_url": f"/imports/{e.image_path}",
                    "analysis": e.analysis_text or "",
                    "title": e.title,
                }
                for e in entries
            ],
            "weight": log.weight if log else None,
            "body_fat": log.body_fat if log else None,
        })
    return result

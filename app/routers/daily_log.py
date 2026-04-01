from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from pathlib import Path

from app.database import get_db
from app.models import DailyLog

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@router.get("/", include_in_schema=False)
async def log_overview(request: Request, db: Session = Depends(get_db)):
    logs = db.query(DailyLog).order_by(DailyLog.date.desc()).limit(30).all()
    today = date.today()
    today_log = db.query(DailyLog).filter(DailyLog.date == today).first()

    # Chart-Daten: letzte 30 Tage
    days_30 = today - timedelta(days=30)
    chart_logs = db.query(DailyLog).filter(DailyLog.date >= days_30).order_by(DailyLog.date.asc()).all()

    return templates.TemplateResponse("daily_log.html", {
        "request": request,
        "logs": logs,
        "today_log": today_log,
        "today": today,
        "chart_logs": chart_logs,
    })


@router.post("/eintragen", include_in_schema=False)
async def save_log(
    log_date: str = Form(default=None),
    hrv: str = Form(default=""),
    heart_rate_night: str = Form(default=""),
    sleep_score: str = Form(default=""),
    deep_sleep_min: str = Form(default=""),
    rem_sleep_min: str = Form(default=""),
    total_sleep_min: str = Form(default=""),
    body_battery: str = Form(default=""),
    breath_rate: str = Form(default=""),
    steps: str = Form(default=""),
    weight: str = Form(default=""),
    body_fat: str = Form(default=""),
    calories: str = Form(default=""),
    protein: str = Form(default=""),
    carbs: str = Form(default=""),
    fat: str = Form(default=""),
    energy_level: str = Form(default=""),
    libido: str = Form(default=""),
    mood: str = Form(default=""),
    training_feel: str = Form(default=""),
    water_retention: str = Form(default=""),
    acne: str = Form(default=""),
    night_sweat: str = Form(default=""),
    training_sessions: str = Form(default=""),
    notes: str = Form(default=""),
    db: Session = Depends(get_db)
):
    entry_date = date.fromisoformat(log_date) if log_date else date.today()

    existing = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
    if not existing:
        existing = DailyLog(date=entry_date, source="manuell")
        db.add(existing)

    def _f(s): return float(s) if s.strip() else None
    def _i(s): return int(float(s)) if s.strip() else None

    existing.hrv = _f(hrv)
    existing.heart_rate_night = _f(heart_rate_night)
    existing.sleep_score = _i(sleep_score)
    existing.deep_sleep_min = _i(deep_sleep_min)
    existing.rem_sleep_min = _i(rem_sleep_min)
    existing.total_sleep_min = _i(total_sleep_min)
    existing.body_battery = _i(body_battery)
    existing.breath_rate = _f(breath_rate)
    existing.steps = _i(steps)
    existing.weight = _f(weight)
    existing.body_fat = _f(body_fat)
    existing.calories = _i(calories)
    existing.protein = _f(protein)
    existing.carbs = _f(carbs)
    existing.fat = _f(fat)
    existing.energy_level = _i(energy_level)
    existing.libido = _i(libido)
    existing.mood = _i(mood)
    existing.training_feel = _i(training_feel)
    existing.water_retention = _i(water_retention)
    existing.acne = _i(acne)
    existing.night_sweat = night_sweat or None
    existing.training_sessions = _i(training_sessions)
    existing.notes = notes or None

    db.commit()
    return RedirectResponse("/tageslog/", status_code=303)


@router.get("/api/chart")
async def chart_data(days: int = 30, db: Session = Depends(get_db)):
    """Chart-Daten als JSON für Chart.js."""
    since = date.today() - timedelta(days=days)
    logs = db.query(DailyLog).filter(DailyLog.date >= since).order_by(DailyLog.date.asc()).all()
    return {
        "dates": [str(l.date) for l in logs],
        "hrv": [l.hrv for l in logs],
        "weight": [l.weight for l in logs],
        "sleep_score": [l.sleep_score for l in logs],
        "heart_rate_night": [l.heart_rate_night for l in logs],
        "body_battery": [l.body_battery for l in logs],
    }

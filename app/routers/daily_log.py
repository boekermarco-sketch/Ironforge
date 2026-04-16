from fastapi import APIRouter, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from app.database import get_db
from app.models import DailyLog

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")

WOCHENTAGE = ["Mo", "Di", "Mi", "Do", "Fr", "Sa", "So"]

# Felder für per-Feld-Fallback-Suche (90 Tage rückwärts)
_GARMIN_FIELDS = [
    "hrv", "heart_rate_night", "body_battery", "sleep_score",
    "total_sleep_min", "deep_sleep_min", "rem_sleep_min", "light_sleep_min",
    "breath_rate", "steps", "stress_avg", "training_readiness",
    "training_status",
]
_WITHINGS_FIELDS = [
    "weight", "body_fat", "fat_mass_kg", "muscle_mass", "water_percent",
    "bmi", "resting_pulse", "bp_systolic", "bp_diastolic",
    "vascular_age", "pulse_wave_velocity",
]


class _ValProxy:
    """Verhält sich wie ein DailyLog, liefert aber per-Feld den neuesten Wert."""
    __slots__ = ("_v",)

    def __init__(self, vals: dict):
        object.__setattr__(self, "_v", vals)

    def __getattr__(self, name):
        return object.__getattribute__(self, "_v").get(name)

    def __bool__(self):
        return any(v is not None for v in object.__getattribute__(self, "_v").values())


def _build_fallback(logs: list, fields: list[str]) -> tuple[dict, dict]:
    """
    Iteriert Logs (neueste zuerst) und nimmt für jedes Feld den ersten
    nicht-None-Wert. Gibt (values_dict, dates_dict) zurück.
    """
    vals: dict = {}
    dates: dict = {}
    remaining = set(fields)
    for log in logs:
        for f in list(remaining):
            v = getattr(log, f, None)
            if v is not None:
                vals[f] = v
                dates[f] = log.date
                remaining.discard(f)
        if not remaining:
            break
    return vals, dates


def _avg(logs, attr) -> Optional[float]:
    vals = [getattr(l, attr) for l in logs if getattr(l, attr) is not None]
    return round(sum(vals) / len(vals), 1) if vals else None


@router.get("/", include_in_schema=False)
async def log_overview(request: Request, d: str = None, db: Session = Depends(get_db)):
    today = date.today()

    try:
        view_date = date.fromisoformat(d) if d else today
    except ValueError:
        view_date = today

    # Log für diesen Tag
    current_log = db.query(DailyLog).filter(DailyLog.date == view_date).first()

    # Vor/Zurück-Navigation
    prev_date = view_date - timedelta(days=1)
    next_date = view_date + timedelta(days=1)

    # Wochen-Navigation: Montag bis Sonntag der aktuellen Woche
    week_start = view_date - timedelta(days=view_date.weekday())
    week_end   = week_start + timedelta(days=6)
    week_dates = [week_start + timedelta(days=i) for i in range(7)]
    week_logs_raw = db.query(DailyLog).filter(
        DailyLog.date >= week_start,
        DailyLog.date <= week_end
    ).all()
    week_logs = {l.date: l for l in week_logs_raw}

    # Vorherige Woche (für Pfeile)
    prev_week_start = week_start - timedelta(days=7)
    next_week_start = week_start + timedelta(days=7)

    # 7-Tage-Durchschnitt (Kontext-Werte)
    week_ago = view_date - timedelta(days=7)
    recent = db.query(DailyLog).filter(
        DailyLog.date > week_ago,
        DailyLog.date <= view_date
    ).all()

    avg7 = {
        "hrv":           _avg(recent, "hrv"),
        "sleep_score":   _avg(recent, "sleep_score"),
        "body_battery":  _avg(recent, "body_battery"),
        "deep_sleep_min":_avg(recent, "deep_sleep_min"),
        "weight":        _avg(recent, "weight"),
        "body_fat":      _avg(recent, "body_fat"),
        "steps":         _avg(recent, "steps"),
        "stress_avg":    _avg(recent, "stress_avg"),
        "heart_rate_night": _avg(recent, "heart_rate_night"),
        "breath_rate":   _avg(recent, "breath_rate"),
    }

    # ── Per-Feld-Fallback (90 Tage) ────────────────────────────────────────────
    since_fb = view_date - timedelta(days=90)
    fb_logs = (
        db.query(DailyLog)
        .filter(DailyLog.date >= since_fb, DailyLog.date <= view_date)
        .order_by(DailyLog.date.desc())
        .all()
    )

    g_vals, g_dates = _build_fallback(fb_logs, _GARMIN_FIELDS)
    w_vals, w_dates = _build_fallback(fb_logs, _WITHINGS_FIELDS)

    garmin_log   = _ValProxy(g_vals)
    withings_log = _ValProxy(w_vals)

    # "Letzter Wert"-Datum: nur anzeigen wenn Kernfelder nicht von heute sind.
    # Garmin-Kern: hrv oder sleep_score. Withings-Kern: weight oder body_fat.
    # Sekundärfelder (BP, PWV) werden täglich nicht gemessen → kein Label dafür.
    g_core = {"hrv", "sleep_score", "body_battery"}
    w_core = {"weight", "body_fat"}
    g_core_dates = {g_dates[f] for f in g_core if f in g_dates and g_dates[f] != view_date}
    w_core_dates = {w_dates[f] for f in w_core if f in w_dates and w_dates[f] != view_date}
    garmin_date   = max(g_core_dates) if g_core_dates else None
    withings_date = max(w_core_dates) if w_core_dates else None

    return templates.TemplateResponse("daily_log.html", {
        "request":         request,
        "today":           today,
        "view_date":       view_date,
        "is_today":        view_date == today,
        "current_log":     current_log,
        "withings_log":    withings_log,
        "withings_date":   withings_date,
        "garmin_log":      garmin_log,
        "garmin_date":     garmin_date,
        "prev_date":       prev_date,
        "next_date":       next_date,
        "week_dates":      week_dates,
        "week_logs":       week_logs,
        "week_start":      week_start,
        "prev_week_start": prev_week_start,
        "next_week_start": next_week_start,
        "wochentage":      WOCHENTAGE,
        "avg7":            avg7,
    })


@router.post("/eintragen", include_in_schema=False)
async def save_log(
    log_date:           str  = Form(default=None),
    hrv:                str  = Form(default=""),
    heart_rate_night:   str  = Form(default=""),
    sleep_score:        str  = Form(default=""),
    deep_sleep_min:     str  = Form(default=""),
    rem_sleep_min:      str  = Form(default=""),
    total_sleep_min:    str  = Form(default=""),
    light_sleep_min:    str  = Form(default=""),
    body_battery:       str  = Form(default=""),
    breath_rate:        str  = Form(default=""),
    steps:              str  = Form(default=""),
    stress_avg:         str  = Form(default=""),
    training_readiness: str  = Form(default=""),
    weight:             str  = Form(default=""),
    body_fat:           str  = Form(default=""),
    bp_systolic:        str  = Form(default=""),
    bp_diastolic:       str  = Form(default=""),
    resting_pulse:      str  = Form(default=""),
    energy_level:       str  = Form(default=""),
    libido:             str  = Form(default=""),
    mood:               str  = Form(default=""),
    training_feel:      str  = Form(default=""),
    water_retention:    str  = Form(default=""),
    acne:               str  = Form(default=""),
    night_sweat:        str  = Form(default=""),
    training_sessions:  str  = Form(default=""),
    notes:              str  = Form(default=""),
    db: Session = Depends(get_db)
):
    entry_date = date.fromisoformat(log_date) if log_date else date.today()

    existing = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
    if not existing:
        existing = DailyLog(date=entry_date, source="manuell")
        db.add(existing)

    def _f(s): return float(s.replace(",", ".")) if s.strip() else None
    def _i(s): return int(float(s)) if s.strip() else None

    existing.hrv               = _f(hrv)
    existing.heart_rate_night  = _f(heart_rate_night)
    existing.sleep_score       = _i(sleep_score)
    existing.deep_sleep_min    = _i(deep_sleep_min)
    existing.rem_sleep_min     = _i(rem_sleep_min)
    existing.total_sleep_min   = _i(total_sleep_min)
    existing.light_sleep_min   = _i(light_sleep_min)
    existing.body_battery      = _i(body_battery)
    existing.breath_rate       = _f(breath_rate)
    existing.steps             = _i(steps)
    existing.stress_avg        = _i(stress_avg)
    existing.training_readiness = _i(training_readiness)
    existing.weight            = _f(weight)
    existing.body_fat          = _f(body_fat)
    existing.bp_systolic       = _i(bp_systolic)
    existing.bp_diastolic      = _i(bp_diastolic)
    existing.resting_pulse     = _i(resting_pulse)
    existing.energy_level      = _i(energy_level)
    existing.libido            = _i(libido)
    existing.mood              = _i(mood)
    existing.training_feel     = _i(training_feel)
    existing.water_retention   = _i(water_retention)
    existing.acne              = _i(acne)
    existing.night_sweat       = night_sweat or None
    existing.training_sessions = _i(training_sessions)
    existing.notes             = notes or None

    db.commit()
    return RedirectResponse(f"/tageslog/?d={entry_date.isoformat()}", status_code=303)


@router.get("/api/chart")
async def chart_data(days: int = 30, db: Session = Depends(get_db)):
    """Chart-Daten als JSON für Chart.js."""
    since = date.today() - timedelta(days=days)
    logs = db.query(DailyLog).filter(DailyLog.date >= since).order_by(DailyLog.date.asc()).all()
    return {
        "dates":              [str(l.date) for l in logs],
        "hrv":                [l.hrv for l in logs],
        "weight":             [l.weight for l in logs],
        "body_fat":           [l.body_fat for l in logs],
        "sleep_score":        [l.sleep_score for l in logs],
        "heart_rate_night":   [l.heart_rate_night for l in logs],
        "body_battery":       [l.body_battery for l in logs],
        "deep_sleep":         [l.deep_sleep_min for l in logs],
        "rem_sleep":          [l.rem_sleep_min for l in logs],
        "light_sleep":        [l.light_sleep_min for l in logs],
        "steps":              [l.steps for l in logs],
        "training_readiness": [l.training_readiness for l in logs],
        "bp_systolic":        [l.bp_systolic for l in logs],
        "bp_diastolic":       [l.bp_diastolic for l in logs],
        "muscle_mass":        [l.muscle_mass for l in logs],
        "fat_mass_kg":        [l.fat_mass_kg for l in logs],
    }

from fastapi import APIRouter, Request, Depends
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from app.database import get_db
from app.models import Stack, DoseEvent, Substance, DailyLog, BloodPanel, BloodValue, Biomarker, MedicalEvent, JournalEntry
from app.services.supabase_health import latest_apple_health, fetch_apple_health
from app.services.apple_sync_meta import get_last_local_apple_import

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


def _latest_field(db: Session, field, days: int = 90) -> tuple:
    """Letzter bekannter Wert eines DailyLog-Feldes + zugehöriges Datum."""
    since = date.today() - timedelta(days=days)
    row = (
        db.query(DailyLog.date, field)
        .filter(DailyLog.date >= since, field != None)
        .order_by(DailyLog.date.desc())
        .first()
    )
    if row:
        return row[1], row[0]
    return None, None


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

    # Letzter Tageslog mit Gewicht
    last_log = (
        db.query(DailyLog)
        .filter(DailyLog.weight != None)
        .order_by(DailyLog.date.desc())
        .first()
    ) or db.query(DailyLog).order_by(DailyLog.date.desc()).first()

    # ── Garmin 90-Tage-Fallback ──────────────────────────────────────────────
    # Für jedes Garmin-Feld: aktueller Wert aus last_log ODER letzter bekannter
    def _fb(field_attr, field_col):
        val = getattr(last_log, field_attr, None) if last_log else None
        src = last_log.date if (last_log and val is not None) else None
        if val is None:
            val, src = _latest_field(db, field_col)
        days_old = (today - src).days if src else None
        return val, days_old

    hrv,               hrv_age               = _fb("hrv",               DailyLog.hrv)
    body_battery,      bb_age                = _fb("body_battery",       DailyLog.body_battery)
    sleep_score,       sleep_age             = _fb("sleep_score",        DailyLog.sleep_score)
    resting_pulse,     rp_age                = _fb("resting_pulse",      DailyLog.resting_pulse)
    training_readiness,tr_age                = _fb("training_readiness", DailyLog.training_readiness)
    training_status,   ts_age                = _fb("training_status",    DailyLog.training_status)
    breath_rate,       br_age                = _fb("breath_rate",        DailyLog.breath_rate)
    bp_systolic,       bp_age                = _fb("bp_systolic",        DailyLog.bp_systolic)
    bp_diastolic,      _                     = _fb("bp_diastolic",       DailyLog.bp_diastolic)
    pwv,               pwv_age               = _fb("pulse_wave_velocity",DailyLog.pulse_wave_velocity)
    stress_avg,        stress_age            = _fb("stress_avg",         DailyLog.stress_avg)
    vo2max,            vo2_age               = _fb("vo2max",             DailyLog.vo2max)

    # Letztes Blutbild
    last_panel = db.query(BloodPanel).order_by(BloodPanel.date.desc()).first()
    critical_values = []
    if last_panel:
        for bv, bm in (
            db.query(BloodValue, Biomarker)
            .join(Biomarker, BloodValue.biomarker_id == Biomarker.id)
            .filter(BloodValue.panel_id == last_panel.id)
            .all()
        ):
            if _value_status(bv.value, bv.ref_min, bv.ref_max) == "kritisch":
                critical_values.append({"name": bm.name, "value": bv.value, "unit": bv.unit or bm.unit})

    last_event = db.query(MedicalEvent).order_by(MedicalEvent.date.desc()).first()

    week_ago  = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    year_ago  = today - timedelta(days=365)

    recent_logs = (
        db.query(DailyLog)
        .filter(DailyLog.date >= week_ago)
        .order_by(DailyLog.date.asc())
        .all()
    )

    def _weight_delta(since: date) -> Optional[float]:
        old = (
            db.query(DailyLog.weight)
            .filter(DailyLog.date >= since, DailyLog.weight != None)
            .order_by(DailyLog.date.asc())
            .first()
        )
        if last_log and last_log.weight and old and old[0]:
            return round(last_log.weight - old[0], 1)
        return None

    weight_delta_week  = _weight_delta(week_ago)
    weight_delta_month = _weight_delta(month_ago)
    weight_delta_year  = _weight_delta(year_ago)

    # Stack-Fortschritt
    stack_progress = stack_days_total = stack_days_done = None
    if active_stack and active_stack.end_date:
        stack_days_total = (active_stack.end_date - active_stack.start_date).days
        stack_days_done  = (today - active_stack.start_date).days
        stack_progress   = min(100, int((stack_days_done / stack_days_total) * 100))

    # KFA-Ziel
    KFA_TARGET_MIN, KFA_TARGET_MAX = 8.0, 10.0
    kfa_current = last_log.body_fat if last_log else None
    kfa_progress = kfa_start_val = None
    if kfa_current:
        oldest_kfa = (
            db.query(DailyLog.body_fat)
            .filter(DailyLog.body_fat != None)
            .order_by(DailyLog.date.asc())
            .first()
        )
        if oldest_kfa and oldest_kfa[0]:
            kfa_start_val = round(oldest_kfa[0], 1)
            total_to_lose = kfa_start_val - KFA_TARGET_MIN
            if total_to_lose > 0:
                lost_so_far = kfa_start_val - kfa_current
                kfa_progress = max(0, min(100, round((lost_so_far / total_to_lose) * 100)))

    next_blood_date = date(2026, 5, 10)

    # Apple Health (Supabase) + letzter lokaler Import (POST /import/apple-health)
    apple_today = latest_apple_health()
    apple_week  = fetch_apple_health(days=7)
    apple_local = get_last_local_apple_import(db)

    # Gewicht + KFA aus Supabase wenn lokal keine Daten
    if apple_today:
        if (not last_log or not last_log.weight) and apple_today.get("body_mass_kg"):
            class _Stub: pass
            if not last_log:
                last_log = _Stub()
            last_log.weight   = apple_today["body_mass_kg"]
            last_log.body_fat = apple_today.get("body_fat_pct")
        if last_log and not getattr(last_log, "body_fat", None) and apple_today.get("body_fat_pct"):
            last_log.body_fat = apple_today["body_fat_pct"]

    # Ruhepuls aus Apple Health wenn kein Garmin-Wert
    if resting_pulse is None and apple_today and apple_today.get("resting_hr"):
        resting_pulse = apple_today["resting_hr"]
        rp_age = 0

    recent_journal = (
        db.query(JournalEntry)
        .order_by(JournalEntry.date.desc(), JournalEntry.id.desc())
        .limit(3)
        .all()
    )

    return templates.TemplateResponse("dashboard.html", {
        "request":            request,
        "today":              today,
        "active_stack":       active_stack,
        "active_doses":       active_doses,
        "last_log":           last_log,
        "last_panel":         last_panel,
        "critical_values":    critical_values,
        "last_event":         last_event,
        "recent_logs":        recent_logs,
        "stack_progress":     stack_progress,
        "stack_days_total":   stack_days_total,
        "stack_days_done":    stack_days_done,
        "next_blood_date":    next_blood_date,
        "recent_journal":     recent_journal,
        "weight_delta_week":  weight_delta_week,
        "weight_delta_month": weight_delta_month,
        "weight_delta_year":  weight_delta_year,
        "kfa_current":        kfa_current,
        "kfa_start_val":      kfa_start_val,
        "kfa_progress":       kfa_progress,
        "KFA_TARGET_MIN":     KFA_TARGET_MIN,
        "KFA_TARGET_MAX":     KFA_TARGET_MAX,
        "apple_today":        apple_today,
        "apple_week":         apple_week,
        "apple_local":        apple_local,
        # Garmin-Felder mit Fallback-Alter
        "hrv": hrv,                         "hrv_age": hrv_age,
        "body_battery": body_battery,       "bb_age": bb_age,
        "sleep_score": sleep_score,         "sleep_age": sleep_age,
        "resting_pulse": resting_pulse,     "rp_age": rp_age,
        "training_readiness": training_readiness, "tr_age": tr_age,
        "training_status": training_status, "ts_age": ts_age,
        "breath_rate": breath_rate,         "br_age": br_age,
        "bp_systolic": bp_systolic,         "bp_age": bp_age,
        "bp_diastolic": bp_diastolic,
        "pwv": pwv,                         "pwv_age": pwv_age,
        "stress_avg": stress_avg,           "stress_age": stress_age,
        "vo2max": vo2max,                   "vo2_age": vo2_age,
    })


def _value_status(value, ref_min, ref_max) -> str:
    if value is None:
        return "unbekannt"
    if ref_min is not None and value < ref_min:
        return "kritisch"
    if ref_max is not None and value > ref_max:
        return "kritisch"
    return "normal"

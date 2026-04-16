"""
MyFitnessPal → DailyLog (calories, protein, carbs, fat).
Nutzt python-myfitnesspal v2.x mit Browser-Cookies (browser_cookie3).

Voraussetzung: Im Browser (Chrome oder Firefox) bei myfitnesspal.com
eingeloggt sein. Die Library liest die Cookies automatisch aus.
Kein Passwort in .env nötig.
"""
import json
from datetime import date, timedelta
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models import DailyLog

BASE_DIR         = Path(__file__).resolve().parent.parent.parent
LAST_MFP_FILE    = BASE_DIR / ".last_mfp_fetch.json"

MFP_INITIAL_DAYS = 90
MFP_MAX_BACKFILL = 14


# ─── Letzte-Abruf-Tracking ───────────────────────────────────────────────────

def _load_last_mfp_fetch() -> Optional[date]:
    if LAST_MFP_FILE.exists():
        try:
            return date.fromisoformat(json.loads(LAST_MFP_FILE.read_text())["date"])
        except Exception:
            pass
    return None


def _save_last_mfp_fetch(d: date) -> None:
    LAST_MFP_FILE.write_text(json.dumps({"date": str(d)}))


# ─── Konfiguration ────────────────────────────────────────────────────────────

def mfp_configured() -> bool:
    """
    Prüft ob MFP-Browser-Cookies verfügbar sind.
    True sobald browser_cookie3 installiert ist – ob Cookies wirklich
    gültig sind, zeigt sich erst beim ersten Abruf.
    """
    try:
        import browser_cookie3  # noqa: F401
        return True
    except ImportError:
        return False


# ─── Client ──────────────────────────────────────────────────────────────────

def _get_mfp_client():
    """
    Erstellt einen MFP-Client der Browser-Cookies (Chrome/Firefox) nutzt.
    Voraussetzung: Im Browser bei myfitnesspal.com eingeloggt sein.
    """
    try:
        import myfitnesspal
    except ImportError:
        raise RuntimeError("myfitnesspal nicht installiert – pip install myfitnesspal")

    # v2.x liest Cookies automatisch via browser_cookie3 aus Chrome/Firefox
    try:
        client = myfitnesspal.Client()
    except Exception as e:
        raise RuntimeError(
            f"MFP-Login fehlgeschlagen – bitte im Browser (Chrome/Firefox) "
            f"bei myfitnesspal.com einloggen. Details: {e}"
        )
    return client


# ─── Schreiben in DailyLog ────────────────────────────────────────────────────

def _write_nutrition(db: Session, target_date: date,
                     cal: float, pro: float, carb: float, fat: float) -> list[str]:
    log = db.query(DailyLog).filter(DailyLog.date == target_date).first()
    if not log:
        log = DailyLog(date=target_date, source="myfitnesspal")
        db.add(log)
        db.flush()
    elif log.source not in ("myfitnesspal", "gemischt"):
        log.source = "gemischt"

    fields = []
    if cal  > 0: log.calories = round(cal);     fields.append("calories")
    if pro  > 0: log.protein  = round(pro,  1); fields.append("protein")
    if carb > 0: log.carbs    = round(carb, 1); fields.append("carbs")
    if fat  > 0: log.fat      = round(fat,  1); fields.append("fat")
    return fields


# ─── Einzel-Tag abrufen ───────────────────────────────────────────────────────

def fetch_mfp_day(db: Session, target_date: date) -> dict:
    """Holt MFP-Daten für einen einzelnen Tag und schreibt sie in DailyLog."""
    try:
        client = _get_mfp_client()
    except Exception as e:
        return {"error": str(e)}

    try:
        day = client.get_date(target_date.year, target_date.month, target_date.day)
        totals = day.totals
        if not totals:
            return {"date": str(target_date), "entries": 0, "fields": []}

        cal  = float(totals.get("calories",      0) or 0)
        pro  = float(totals.get("protein",        0) or 0)
        carb = float(totals.get("carbohydrates",  0) or 0)
        fat  = float(totals.get("fat",            0) or 0)

        if cal == 0 and pro == 0:
            return {"date": str(target_date), "entries": 0, "fields": []}

        fields = _write_nutrition(db, target_date, cal, pro, carb, fat)
        db.commit()
        return {"date": str(target_date), "entries": len(day.meals), "fields": fields}

    except Exception as e:
        return {"error": f"Abruf {target_date}: {e}"}


# ─── Bereich seit letztem Abruf ───────────────────────────────────────────────

def fetch_mfp_since_last(db: Session) -> dict:
    """
    Holt MFP-Daten seit dem letzten Abruf bis heute.
    Erster Aufruf: MFP_INITIAL_DAYS Tage zurück.
    Folgend: seit letztem Abruf (max. MFP_MAX_BACKFILL Tage).
    """
    today      = date.today()
    last_fetch = _load_last_mfp_fetch()

    if last_fetch is None:
        since = today - timedelta(days=MFP_INITIAL_DAYS)
    elif last_fetch >= today:
        since = today
    else:
        since = max(last_fetch + timedelta(days=1),
                    today - timedelta(days=MFP_MAX_BACKFILL - 1))

    dates_to_fetch = [
        since + timedelta(days=i)
        for i in range((today - since).days + 1)
    ]

    try:
        client = _get_mfp_client()
    except Exception as e:
        return {"error": str(e)}

    results = {
        "fetched_dates": [],
        "skipped":       0,
        "errors":        [],
        "since":         str(since),
    }

    for d in dates_to_fetch:
        try:
            day    = client.get_date(d.year, d.month, d.day)
            totals = day.totals or {}
            cal    = float(totals.get("calories",     0) or 0)
            pro    = float(totals.get("protein",       0) or 0)
            carb   = float(totals.get("carbohydrates", 0) or 0)
            fat    = float(totals.get("fat",           0) or 0)

            if cal == 0 and pro == 0:
                results["skipped"] += 1
                continue

            _write_nutrition(db, d, cal, pro, carb, fat)
            db.commit()
            results["fetched_dates"].append(str(d))

        except Exception as e:
            results["errors"].append(f"{d}: {e}")

    _save_last_mfp_fetch(today)
    return results

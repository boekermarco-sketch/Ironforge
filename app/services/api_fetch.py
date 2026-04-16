"""
Automatischer API-Abruf: Garmin Connect + Withings → DailyLog (SQLite).
Wird von /import/fetch-now getriggert.

Voraussetzungen:
- .env: GARMIN_EMAIL, GARMIN_PASSWORD, WITHINGS_CLIENT_ID, WITHINGS_CLIENT_SECRET
- .withings_credentials.json: einmalig via withings_auth.py erstellt
"""
import os
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv
from sqlalchemy.orm import Session
import requests

from app.models import DailyLog

BASE_DIR = Path(__file__).resolve().parent.parent.parent
CREDS_FILE = BASE_DIR / ".withings_credentials.json"
GARMIN_TOKEN_DIR = BASE_DIR / ".garth"
GARMIN_BLOCK_FILE = BASE_DIR / ".garmin_blocked.json"

# Stunden bis Garmin-Login nach 429 wieder versucht wird
GARMIN_BLOCK_HOURS = 72


def _is_garmin_blocked() -> Optional[datetime]:
    """Gibt den Freigabezeitpunkt zurück wenn Garmin gerade geblockt ist, sonst None."""
    if not GARMIN_BLOCK_FILE.exists():
        return None
    try:
        data = json.loads(GARMIN_BLOCK_FILE.read_text())
        unblock_at = datetime.fromisoformat(data["unblock_at"])
        if datetime.now() < unblock_at:
            return unblock_at
        GARMIN_BLOCK_FILE.unlink(missing_ok=True)
    except Exception:
        pass
    return None


def _set_garmin_block() -> datetime:
    """Setzt eine 72h-Sperre nach 429-Fehler und gibt Freigabezeitpunkt zurück."""
    unblock_at = datetime.now() + timedelta(hours=GARMIN_BLOCK_HOURS)
    GARMIN_BLOCK_FILE.write_text(json.dumps({"unblock_at": unblock_at.isoformat()}))
    return unblock_at


def clear_garmin_block() -> None:
    """Hebt die Garmin-Sperre manuell auf (z.B. nach Token-Import)."""
    GARMIN_BLOCK_FILE.unlink(missing_ok=True)

load_dotenv(BASE_DIR / ".env")

WITHINGS_TOKEN_URL = "https://wbsapi.withings.net/v2/oauth2"
WITHINGS_MEASURE_URL = "https://wbsapi.withings.net/measure"


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _float(val) -> Optional[float]:
    if val is None:
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


def _get_or_create_log(db: Session, entry_date: date) -> DailyLog:
    log = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
    if not log:
        log = DailyLog(date=entry_date, source="api")
        db.add(log)
        db.flush()
    return log


# ─── Withings OAuth-Hilfsfunktionen ──────────────────────────────────────────

def _load_withings_token() -> Optional[dict]:
    if not CREDS_FILE.exists():
        return None
    with open(CREDS_FILE) as f:
        return json.load(f)


def _save_withings_token(creds: dict) -> None:
    with open(CREDS_FILE, "w") as f:
        json.dump(creds, f, indent=2)


def _refresh_withings_token(creds: dict) -> Optional[dict]:
    """Holt ein neues Access-Token via Refresh-Token."""
    client_id = os.getenv("WITHINGS_CLIENT_ID")
    client_secret = os.getenv("WITHINGS_CLIENT_SECRET")
    if not client_id or not client_secret:
        return None

    resp = requests.post(WITHINGS_TOKEN_URL, data={
        "action": "requesttoken",
        "grant_type": "refresh_token",
        "client_id": client_id,
        "client_secret": client_secret,
        "refresh_token": creds["refresh_token"],
    }, timeout=15)
    data = resp.json()

    if data.get("status") != 0:
        return None

    body = data["body"]
    new_creds = {
        "access_token": body["access_token"],
        "refresh_token": body["refresh_token"],
        "expires_at": int(time.time()) + int(body.get("expires_in", 10800)),
        "userid": body.get("userid") or creds.get("userid"),
    }
    _save_withings_token(new_creds)
    return new_creds


def _get_valid_withings_token() -> Optional[tuple[str, str]]:
    """Gibt (access_token, error_msg) zurück. Refresht automatisch wenn nötig."""
    creds = _load_withings_token()
    if not creds:
        return None, f"{CREDS_FILE.name} fehlt – einmalig withings_auth.py ausführen"

    # Token abgelaufen oder läuft in < 60 Sek ab
    if int(time.time()) >= creds.get("expires_at", 0) - 60:
        creds = _refresh_withings_token(creds)
        if not creds:
            return None, "Token-Refresh fehlgeschlagen – WITHINGS_CLIENT_ID/SECRET in .env prüfen"

    return creds["access_token"], None


# ─── Garmin ──────────────────────────────────────────────────────────────────

def _get_garmin_client():
    """
    Gibt einen authentifizierten Garmin-Client zurück.
    Lädt gespeicherte OAuth-Tokens aus GARMIN_TOKEN_DIR, um 429-Sperren
    durch wiederholte Logins zu vermeiden.

    Nach einem 429-Fehler wird für GARMIN_BLOCK_HOURS Stunden kein Login
    mehr versucht, um die Cloudflare-IP-Sperre nicht zu verlängern.
    """
    from garminconnect import Garmin

    # IP-Sperre aktiv? Dann sofort abbrechen, nicht weiter versuchen.
    blocked_until = _is_garmin_blocked()
    if blocked_until:
        raise ValueError(
            f"Garmin gesperrt bis {blocked_until.strftime('%d.%m.%Y %H:%M')} "
            f"(Cloudflare-IP-Sperre – kein Login-Versuch um Sperre nicht zu verlängern)"
        )

    email = os.getenv("GARMIN_EMAIL")
    password = os.getenv("GARMIN_PASSWORD")
    if not email or not password:
        raise ValueError("GARMIN_EMAIL oder GARMIN_PASSWORD fehlt in .env")

    # Gespeicherte Tokens laden (kein Login-Request an Garmin nötig)
    if GARMIN_TOKEN_DIR.exists():
        try:
            client = Garmin(email, password)
            client.login(tokenstore=str(GARMIN_TOKEN_DIR))
            return client
        except Exception:
            pass  # Abgelaufen oder ungültig → frischer Login unten

    # Frischer Login – bei 429 sofort Sperre setzen
    client = Garmin(email, password)
    try:
        client.login()
    except Exception as e:
        err_str = str(e).lower()
        if "429" in err_str or "rate limit" in err_str or "too many" in err_str:
            unblock_at = _set_garmin_block()
            raise ValueError(
                f"Garmin 429 – IP-Sperre gesetzt bis {unblock_at.strftime('%d.%m.%Y %H:%M')}. "
                f"Bitte {GARMIN_BLOCK_HOURS}h warten und nicht erneut versuchen."
            ) from e
        raise

    # Tokens für nächsten Aufruf speichern (vermeidet künftige Login-Requests)
    try:
        GARMIN_TOKEN_DIR.mkdir(exist_ok=True)
        client.garth.dump(str(GARMIN_TOKEN_DIR))
    except Exception:
        pass

    return client


def _refresh_garmin_tokens(client) -> None:
    """Speichert ggf. erneuerte OAuth-Tokens nach API-Nutzung."""
    try:
        GARMIN_TOKEN_DIR.mkdir(exist_ok=True)
        client.garth.dump(str(GARMIN_TOKEN_DIR))
    except Exception:
        pass


def fetch_garmin(db: Session, target_date: date) -> dict:
    """Holt alle verfügbaren Garmin-Metriken für target_date via API."""
    try:
        from garminconnect import Garmin  # noqa: F401 – Import-Check
    except ImportError:
        return {"error": "garminconnect nicht installiert (pip install garminconnect)"}

    date_str = target_date.strftime("%Y-%m-%d")
    fields: list[str] = []
    errors: list[str] = []

    try:
        client = _get_garmin_client()
    except Exception as e:
        return {"error": f"Login fehlgeschlagen: {e}"}

    log = _get_or_create_log(db, target_date)

    # Tages-Zusammenfassung: Steps + Stress
    try:
        summary = client.get_stats(date_str) or {}
        if summary.get("totalSteps"):
            log.steps = int(summary["totalSteps"])
            fields.append("steps")
        if summary.get("averageStressLevel") is not None and summary["averageStressLevel"] > 0:
            log.stress_avg = int(summary["averageStressLevel"])
            fields.append("stress")
    except Exception as e:
        errors.append(f"stats: {e}")

    # Body Battery (letzter Wert des Tages)
    try:
        bb_list = client.get_body_battery(date_str) or []
        if bb_list:
            last = bb_list[-1]
            val = last.get("bodyBatteryLevel") or last.get("charged")
            if val is not None:
                log.body_battery = int(val)
                fields.append("body_battery")
    except Exception as e:
        errors.append(f"body_battery: {e}")

    # Resting Heart Rate
    try:
        rhr = client.get_rhr_day(date_str) or {}
        rhr_val = rhr.get("restingHeartRate") or rhr.get("value")
        if rhr_val:
            log.heart_rate_night = _float(rhr_val)
            fields.append("rhr")
    except Exception as e:
        errors.append(f"rhr: {e}")

    # HRV (Letzte Nacht)
    try:
        hrv_data = client.get_hrv_data(date_str) or {}
        hrv_summary = hrv_data.get("hrvSummary") or {}
        hrv_val = hrv_summary.get("lastNight") or hrv_summary.get("weeklyAvg")
        if hrv_val:
            log.hrv = _float(hrv_val)
            fields.append("hrv")
    except Exception as e:
        errors.append(f"hrv: {e}")

    # Schlaf
    try:
        sleep_data = client.get_sleep_data(date_str) or {}
        dto = sleep_data.get("dailySleepDTO") or sleep_data
        if dto:
            deep_s = _float(dto.get("deepSleepSeconds"))
            light_s = _float(dto.get("lightSleepSeconds"))
            rem_s = _float(dto.get("remSleepSeconds"))
            resp = _float(dto.get("averageRespiration"))

            scores = dto.get("sleepScores") or {}
            score_val = _float(scores.get("overallScore") or scores.get("qualityScore"))

            if deep_s:
                log.deep_sleep_min = int(deep_s / 60)
                fields.append("deep_sleep")
            if light_s:
                log.light_sleep_min = int(light_s / 60)
                fields.append("light_sleep")
            if rem_s:
                log.rem_sleep_min = int(rem_s / 60)
                fields.append("rem_sleep")
            if deep_s and light_s and rem_s:
                log.total_sleep_min = int((deep_s + light_s + rem_s) / 60)
                fields.append("total_sleep")
            if resp:
                log.breath_rate = resp
                fields.append("breath_rate")
            if score_val:
                log.sleep_score = int(score_val)
                fields.append("sleep_score")
    except Exception as e:
        errors.append(f"sleep: {e}")

    # Training Readiness
    try:
        tr_raw = client.get_training_readiness(date_str) or []
        tr = tr_raw[0] if isinstance(tr_raw, list) and tr_raw else tr_raw
        if isinstance(tr, dict) and tr.get("score"):
            log.training_readiness = int(tr["score"])
            fields.append("training_readiness")
    except Exception as e:
        errors.append(f"training_readiness: {e}")

    # Training Status
    try:
        ts_raw = client.get_training_status(date_str) or {}
        ts = ts_raw[0] if isinstance(ts_raw, list) and ts_raw else ts_raw
        if isinstance(ts, dict):
            status = (
                (ts.get("latestTrainingStatusData") or {}).get("trainingStatus")
                or ts.get("trainingStatus")
            )
            if status:
                log.training_status = str(status)
                fields.append("training_status")
    except Exception as e:
        errors.append(f"training_status: {e}")

    if log.source == "manuell":
        log.source = "api"
    elif log.source == "withings":
        log.source = "gemischt"

    # Ggf. erneuerte Tokens persistieren (verlängert Session ohne neuen Login)
    _refresh_garmin_tokens(client)

    return {"fields": fields, "errors": errors}


# ─── Withings ────────────────────────────────────────────────────────────────

def _parse_withings_measuregrps(measuregrps: list, height_m: float) -> dict[date, dict]:
    """
    Parst Withings measuregrps und gibt ein Dict {date: {field: value}} zurück.
    Verarbeitet alle Gruppen auf einmal (für range-Abrufe).
    """
    from collections import defaultdict
    day_data: dict = defaultdict(dict)

    for grp in measuregrps:
        grp_ts = grp.get("date")
        if not grp_ts:
            continue
        grp_date = datetime.fromtimestamp(grp_ts).date()
        measures: dict[int, float] = {}
        for m in grp.get("measures", []):
            mtype = m["type"]
            val   = m["value"] * (10 ** m["unit"])
            if mtype not in measures:
                measures[mtype] = val

        d = day_data[grp_date]
        weight_kg = measures.get(1)
        hydration = measures.get(77)
        h = measures.get(4) if (measures.get(4) and measures.get(4, 0) > 0.5) else height_m

        if weight_kg:
            d.setdefault("weight", round(weight_kg, 2))
            if h:
                d.setdefault("bmi", round(weight_kg / (h ** 2), 1))
            if hydration:
                d.setdefault("water_percent", round((hydration / weight_kg) * 100, 1))
        if measures.get(6) is not None:
            d.setdefault("body_fat",  round(measures[6], 1))
        if measures.get(8) is not None:
            d.setdefault("fat_mass_kg", round(measures[8], 2))
        if measures.get(76) is not None:
            d.setdefault("muscle_mass", round(measures[76], 2))
        if measures.get(9) is not None:
            d.setdefault("bp_diastolic", int(measures[9]))
        if measures.get(10) is not None:
            d.setdefault("bp_systolic", int(measures[10]))
        if measures.get(11) is not None:
            d.setdefault("resting_pulse", int(measures[11]))
        if measures.get(91) is not None:
            # Mehrere PWV-Messungen pro Tag → Durchschnitt
            pwv_list = d.get("_pwv_list", [])
            pwv_list.append(measures[91])
            d["_pwv_list"] = pwv_list

    # PWV: Durchschnitt aller Messungen pro Tag
    for grp_date, d in day_data.items():
        pwv_list = d.pop("_pwv_list", [])
        if pwv_list:
            d["pulse_wave_velocity"] = round(sum(pwv_list) / len(pwv_list), 3)

    return dict(day_data)


def _apply_withings_day(log: "DailyLog", day_fields: dict) -> list[str]:
    """Schreibt day_fields in einen DailyLog und gibt geänderte Felder zurück."""
    changed = []
    for field, val in day_fields.items():
        if getattr(log, field, None) is None:
            setattr(log, field, val)
            changed.append(field)
    return changed


LAST_WITHINGS_BACKFILL_FILE = BASE_DIR / ".last_withings_backfill.json"


def _load_last_withings_backfill() -> Optional[date]:
    if LAST_WITHINGS_BACKFILL_FILE.exists():
        try:
            data = json.loads(LAST_WITHINGS_BACKFILL_FILE.read_text())
            return date.fromisoformat(data["date"])
        except Exception:
            pass
    return None


def _save_last_withings_backfill(d: date) -> None:
    LAST_WITHINGS_BACKFILL_FILE.write_text(json.dumps({"date": str(d)}))


def fetch_withings_range(db: Session, days: int = None) -> dict:
    """
    Holt alle Withings-Messungen seit dem letzten Backfill (oder `days` Tage)
    in EINEM API-Call und befüllt alle DB-Einträge (PWV, BP etc.).
    Beim ersten Aufruf: 90 Tage. Danach: nur seit letztem Backfill.
    """
    import time as _time
    access_token, err = _get_valid_withings_token()
    if err:
        return {"error": err}

    today = date.today()
    last_backfill = _load_last_withings_backfill()

    if days is not None:
        # Explizite Anzahl Tage (Override)
        since = today - timedelta(days=days)
    elif last_backfill is None:
        # Erster Aufruf: 90 Tage
        since = today - timedelta(days=90)
    else:
        # Seit letztem Backfill (1 Tag Überlapp als Puffer)
        since = last_backfill - timedelta(days=1)

    try:
        height_m = float(os.getenv("BODY_HEIGHT_M", "1.78"))
    except ValueError:
        height_m = 1.78

    end_ts   = int(_time.time())
    start_ts = int(datetime.combine(since, datetime.min.time()).timestamp())

    try:
        resp = requests.post(
            WITHINGS_MEASURE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "action": "getmeas",
                "startdate": start_ts,
                "enddate": end_ts,
                "meastypes": "1,4,6,8,9,10,11,76,77,91",
            },
            timeout=20,
        )
        data = resp.json()
        if data.get("status") != 0:
            return {"error": f"Withings API Fehler (status={data.get('status')}): {data.get('error','')}"}

        measuregrps = data["body"].get("measuregrps", [])
        day_data = _parse_withings_measuregrps(measuregrps, height_m)

        updated_dates = []
        for entry_date, fields in day_data.items():
            log = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
            if not log:
                log = DailyLog(date=entry_date, source="withings")
                db.add(log)
            changed = _apply_withings_day(log, fields)
            if changed:
                if log.source == "manuell":
                    log.source = "withings"
                elif log.source == "garmin":
                    log.source = "gemischt"
                updated_dates.append(str(entry_date))

        db.commit()
        _save_last_withings_backfill(today)
        return {
            "updated_dates": sorted(updated_dates),
            "total": len(updated_dates),
            "since": str(since),
        }

    except Exception as e:
        return {"error": str(e)}


def fetch_withings(db: Session, target_date: date) -> dict:
    """Holt Withings-Messungen für target_date via REST API.

    Withings Measure-Typen:
      1=Gewicht(kg)  4=Größe(m)   6=Körperfett%   8=Fettmasse(kg)
      9=Diastole    10=Systole   11=Puls(bpm)     76=Muskelmasse(kg)
      77=Hydration(kg)  91=PWV(m/s)
    """
    access_token, err = _get_valid_withings_token()
    if err:
        return {"error": err}

    fields: list[str] = []
    errors: list[str] = []

    # Körpergröße aus .env für BMI-Berechnung (Standard: 1.78 m)
    try:
        height_m = float(os.getenv("BODY_HEIGHT_M", "1.78"))
    except ValueError:
        height_m = 1.78

    start_ts = int(datetime.combine(target_date, datetime.min.time()).timestamp())
    end_ts   = int(datetime.combine(target_date, datetime.max.time()).timestamp())

    try:
        resp = requests.post(
            WITHINGS_MEASURE_URL,
            headers={"Authorization": f"Bearer {access_token}"},
            data={
                "action": "getmeas",
                "startdate": start_ts,
                "enddate": end_ts,
                # Alle relevanten Typen inkl. Gefäßalter (168) und Größe (4)
                "meastypes": "1,4,6,8,9,10,11,76,77,91",
            },
            timeout=15,
        )
        data = resp.json()
        if data.get("status") != 0:
            return {"error": f"Withings API Fehler (status={data.get('status')}): {data.get('error', '')}"}

        log = _get_or_create_log(db, target_date)

        # Alle Messwerte in einem Dict sammeln → verhindert Reihenfolge-Probleme
        measures: dict[int, float] = {}
        for grp in data["body"].get("measuregrps", []):
            for m in grp.get("measures", []):
                mtype = m["type"]
                val   = m["value"] * (10 ** m["unit"])
                # Ersten Wert je Typ behalten (neueste Messung steht zuerst)
                if mtype not in measures:
                    measures[mtype] = val

        weight_kg  = measures.get(1)
        hydration  = measures.get(77)   # kg
        # Größe: aus Messung oder env-Konstante
        if measures.get(4) and measures[4] > 0.5:
            height_m = measures[4]

        if weight_kg:
            log.weight = round(weight_kg, 2)
            fields.append("weight")

            # BMI berechnen
            if height_m:
                log.bmi = round(weight_kg / (height_m ** 2), 1)
                fields.append("bmi")

            # Wassergehalt in %
            if hydration:
                log.water_percent = round((hydration / weight_kg) * 100, 1)
                fields.append("water_percent")

        if measures.get(6) is not None:
            log.body_fat = round(measures[6], 1)
            fields.append("body_fat")
        if measures.get(8) is not None:
            log.fat_mass_kg = round(measures[8], 2)
            fields.append("fat_mass_kg")
        if measures.get(76) is not None:
            log.muscle_mass = round(measures[76], 2)
            fields.append("muscle_mass")
        if measures.get(9) is not None:
            log.bp_diastolic = int(measures[9])
            fields.append("bp_diastolic")
        if measures.get(10) is not None:
            log.bp_systolic = int(measures[10])
            fields.append("bp_systolic")
        if measures.get(11) is not None:
            log.resting_pulse = int(measures[11])
            fields.append("resting_pulse")
        if measures.get(91) is not None:
            log.pulse_wave_velocity = round(measures[91], 2)
            fields.append("pwv")

        if log.source == "manuell":
            log.source = "api"
        elif log.source == "garmin":
            log.source = "gemischt"

    except Exception as e:
        errors.append(f"measure_get_meas: {e}")

    return {"fields": fields, "errors": errors}


# ─── Hauptfunktionen ──────────────────────────────────────────────────────────

LAST_FETCH_FILE = BASE_DIR / ".last_fetch.json"


def _load_last_fetch() -> date:
    if LAST_FETCH_FILE.exists():
        try:
            data = json.loads(LAST_FETCH_FILE.read_text())
            return date.fromisoformat(data["date"])
        except Exception:
            pass
    return None


def _save_last_fetch(d: date) -> None:
    LAST_FETCH_FILE.write_text(json.dumps({"date": str(d)}))


def fetch_today(db: Session, target_date: date = None) -> dict:
    """
    Holt Garmin + Withings Daten für target_date (Standard: heute) und
    schreibt sie direkt in die DailyLog-Tabelle.
    """
    if target_date is None:
        target_date = date.today()

    garmin_result = fetch_garmin(db, target_date)
    withings_result = fetch_withings(db, target_date)

    db.commit()

    return {
        "date": str(target_date),
        "garmin": garmin_result,
        "withings": withings_result,
    }


def fetch_missing(db: Session) -> dict:
    """
    Ermittelt den letzten Abruf-Tag und holt alle fehlenden Tage bis heute nach.
    Beim allerersten Aufruf: nur heute.
    """
    today = date.today()
    last_fetch = _load_last_fetch()

    if last_fetch is None or last_fetch >= today:
        dates_to_fetch = [today]
    else:
        days_gap = (today - last_fetch).days
        # Maximal 14 Tage rückwirkend um Garmin-Rate-Limits zu schonen
        start = max(last_fetch + timedelta(days=1), today - timedelta(days=13))
        dates_to_fetch = [
            start + timedelta(days=i)
            for i in range((today - start).days + 1)
        ]

    results = {"fetched_dates": [], "garmin_errors": [], "withings_errors": [], "skipped": 0}

    for d in dates_to_fetch:
        g = fetch_garmin(db, d)
        w = fetch_withings(db, d)
        db.commit()

        # Top-Level-Fehler (Login etc.)
        if g.get("error"):
            results["garmin_errors"].append(f"{d}: {g['error']}")
        elif g.get("errors"):
            # Teil-Fehler (einzelne API-Calls) – kompakt zusammenfassen
            results["garmin_errors"].append(f"{d} Teil-Fehler: {'; '.join(g['errors'][:3])}")
        if w.get("error"):
            results["withings_errors"].append(f"{d}: {w['error']}")
        elif w.get("errors"):
            results["withings_errors"].append(f"{d} Teil-Fehler: {'; '.join(w['errors'][:3])}")

        if g.get("fields") or w.get("fields"):
            results["fetched_dates"].append(str(d))
        else:
            results["skipped"] += 1

    _save_last_fetch(today)
    return results


def fetch_garmin_only(db: Session) -> dict:
    """Holt nur Garmin-Daten für heute und aktualisiert last_fetch."""
    today = date.today()
    g = fetch_garmin(db, today)
    db.commit()
    _save_last_fetch(today)
    if g.get("error"):
        return {"error": g["error"], "date": str(today)}
    return {"fields": g.get("fields", []), "date": str(today)}


def fetch_withings_only(db: Session) -> dict:
    """Holt nur Withings-Daten für heute."""
    today = date.today()
    w = fetch_withings(db, today)
    db.commit()
    if w.get("error"):
        return {"error": w["error"], "date": str(today)}
    return {"fields": w.get("fields", []), "date": str(today)}

"""
Bulk-Importer für Withings, Garmin und MyFitnessPal.
Verarbeitet automatisch alle relevanten Dateien aus den Export-Ordnern.
Kein manuelles Hochladen jeder Datei nötig.
"""
import csv
import json
import glob
import os
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models import DailyLog

BASE_DIR = Path(__file__).resolve().parent.parent.parent
WITHINGS_DIR = BASE_DIR / "Imports" / "Withings"
GARMIN_DIR   = BASE_DIR / "Imports" / "Garmin"


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> Optional[date]:
    import re
    s = date_str.strip()
    # Timezone-Suffix entfernen: +01:00, -05:00, +0100, Z
    s = re.sub(r'[+-]\d{2}:?\d{2}$', '', s).rstrip('Z').strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(s, fmt).date()
        except ValueError:
            continue
    return None


def _float(val) -> Optional[float]:
    if val is None or str(val).strip() in ("", "-", "None", "null"):
        return None
    try:
        return float(str(val).replace(",", "."))
    except (ValueError, TypeError):
        return None


def _get_or_create_log(db: Session, entry_date: date, cache: dict) -> DailyLog:
    """Cache verhindert Doppel-Inserts bei mehreren Messungen pro Tag."""
    if entry_date in cache:
        return cache[entry_date]
    log = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
    if not log:
        log = DailyLog(date=entry_date, source="manuell")
        db.add(log)
        db.flush()  # ID sofort vergeben, verhindert UNIQUE-Konflikt
    cache[entry_date] = log
    return log


# ─── Withings ────────────────────────────────────────────────────────────────

def import_withings_all(db: Session) -> dict:
    """
    Importiert alle relevanten Withings-Dateien aus Imports/Withings/.
    Verarbeitet: weight.csv, aggregates_steps.csv, sleep.csv, bp.csv
    """
    stats = {"weight": 0, "bp": 0, "steps": 0, "sleep": 0, "errors": []}
    cache: dict = {}

    if not WITHINGS_DIR.exists():
        return {"error": f"Ordner nicht gefunden: {WITHINGS_DIR}"}

    # ── weight.csv ────────────────────────────────────────────────────────────
    weight_file = WITHINGS_DIR / "weight.csv"
    if weight_file.exists():
        try:
            with open(weight_file, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_date = row.get("Date", "")
                    entry_date = _parse_date(raw_date)
                    if not entry_date:
                        continue

                    weight_kg = _float(
                        row.get("Gewicht (kg)") or row.get("Weight (kg)")
                    )
                    fat_kg = _float(
                        row.get("Fettmasse (kg)") or row.get("Fat mass (kg)")
                    )
                    muscle_kg = _float(
                        row.get("Muskelmasse (kg)") or row.get("Muscle mass (kg)")
                    )
                    # Withings exportiert Wasser in kg ("Wasseranteil (kg)")
                    water_kg = _float(
                        row.get("Wasseranteil (kg)") or
                        row.get("Hydratation (kg)") or
                        row.get("Hydration (kg)")
                    )
                    fat_pct = _float(
                        row.get("Körperfett (%)") or row.get("Fat mass (%)") or
                        row.get("Body Fat (%)")
                    )
                    vasc_age = _float(
                        row.get("Gefäßalter") or row.get("Vascular age")
                    )
                    pwv = _float(
                        row.get("Pulswellengeschwindigkeit (m/s)") or
                        row.get("Pulse Wave Velocity (m/s)")
                    )
                    bmi_val = _float(row.get("BMI") or row.get("Bmi"))
                    height_m = _float(
                        row.get("Größe (m)") or row.get("Height (m)") or
                        row.get("Size (m)")
                    )

                    if weight_kg is None:
                        continue

                    log = _get_or_create_log(db, entry_date, cache)
                    log.weight = weight_kg

                    if fat_pct is not None:
                        log.body_fat = fat_pct
                    elif fat_kg and weight_kg:
                        log.body_fat = round((fat_kg / weight_kg) * 100, 1)
                    if fat_kg:
                        log.fat_mass_kg = fat_kg
                    if muscle_kg:
                        log.muscle_mass = muscle_kg
                    # Wasser in % umrechnen
                    if water_kg and weight_kg:
                        log.water_percent = round((water_kg / weight_kg) * 100, 1)
                    if vasc_age:
                        log.vascular_age = int(vasc_age)
                    if pwv:
                        log.pulse_wave_velocity = pwv
                    # BMI: aus CSV oder aus Gewicht + Größe (Fallback: 1.78 m)
                    if bmi_val:
                        log.bmi = round(bmi_val, 1)
                    elif height_m and height_m > 0.5:
                        log.bmi = round(weight_kg / (height_m ** 2), 1)
                    else:
                        import os as _os
                        try:
                            h = float(_os.getenv("BODY_HEIGHT_M", "1.78"))
                        except ValueError:
                            h = 1.78
                        log.bmi = round(weight_kg / (h * h), 1)

                    if log.source == "manuell":
                        log.source = "withings"
                    stats["weight"] += 1
            db.flush()
        except Exception as e:
            stats["errors"].append(f"weight.csv: {e}")

    # ── aggregates_steps.csv ─────────────────────────────────────────────────
    steps_file = WITHINGS_DIR / "aggregates_steps.csv"
    if steps_file.exists():
        try:
            with open(steps_file, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Withings steps aggregates: "Date","Steps"
                    raw_date = row.get("Date", row.get("date", ""))
                    entry_date = _parse_date(raw_date)
                    if not entry_date:
                        continue
                    steps_val = _float(row.get("Steps") or row.get("steps") or row.get("value"))
                    if steps_val:
                        log = _get_or_create_log(db, entry_date, cache)
                        log.steps = int(steps_val)
                        stats["steps"] += 1
            db.flush()
        except Exception as e:
            stats["errors"].append(f"aggregates_steps.csv: {e}")

    # ── sleep.csv (Schlafdaten vom Withings-Watch) ───────────────────────────
    sleep_file = WITHINGS_DIR / "sleep.csv"
    if sleep_file.exists():
        try:
            with open(sleep_file, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    # Spalte "von" enthält Start-Timestamp (z.B. 2026-03-06T22:24:37+01:00)
                    raw_date = row.get("von", row.get("from", ""))
                    if not raw_date:
                        continue
                    # Einschlafzeit vor Mitternacht → Datum des nächsten Morgens verwenden
                    entry_date = _parse_date(raw_date)
                    if not entry_date:
                        continue
                    try:
                        hour = int(raw_date[11:13])
                        if hour >= 18:  # vor Mitternacht eingeschlafen
                            from datetime import timedelta
                            entry_date = entry_date + timedelta(days=1)
                    except Exception:
                        pass

                    light_s  = _float(row.get("leicht (s)") or row.get("light (s)"))
                    deep_s   = _float(row.get("tief (s)") or row.get("deep (s)"))
                    rem_s    = _float(row.get("rem (s)") or row.get("REM (s)"))
                    awake_s  = _float(row.get("wach (s)") or row.get("awake (s)"))
                    hr_avg   = _float(row.get("Durchschnittliche Herzfrequenz") or row.get("Average heart rate"))

                    deep_min  = int(deep_s / 60)  if deep_s  else None
                    rem_min   = int(rem_s / 60)   if rem_s   else None
                    light_min = int(light_s / 60) if light_s else None
                    total_min = (
                        int((deep_s + light_s + rem_s) / 60)
                        if deep_s and light_s and rem_s else None
                    )

                    if all(v is None for v in [deep_min, rem_min, total_min]):
                        continue

                    log = _get_or_create_log(db, entry_date, cache)
                    # Nur überschreiben wenn noch kein Wert vorhanden (Garmin hat Vorrang)
                    if deep_min  is not None and log.deep_sleep_min  is None:
                        log.deep_sleep_min  = deep_min
                    if rem_min   is not None and log.rem_sleep_min   is None:
                        log.rem_sleep_min   = rem_min
                    if total_min is not None and log.total_sleep_min is None:
                        log.total_sleep_min = total_min
                    if hr_avg    is not None and log.heart_rate_night is None:
                        log.heart_rate_night = hr_avg
                    if log.source == "manuell":
                        log.source = "withings"
                    stats["sleep"] += 1
            db.flush()
        except Exception as e:
            stats["errors"].append(f"sleep.csv: {e}")

    # ── bp.csv (Blutdruck) ────────────────────────────────────────────────────
    bp_file = WITHINGS_DIR / "bp.csv"
    if bp_file.exists():
        try:
            with open(bp_file, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    raw_date = row.get("Date", row.get("Datum", ""))
                    entry_date = _parse_date(raw_date)
                    if not entry_date:
                        continue
                    # Withings bp.csv: dt. Spaltennamen
                    systolic  = _float(
                        row.get("Systole") or row.get("Systolic (mmHg)") or
                        row.get("Systolisch (mmHg)") or row.get("Systolic")
                    )
                    diastolic = _float(
                        row.get("Diastole") or row.get("Diastolic (mmHg)") or
                        row.get("Diastolisch (mmHg)") or row.get("Diastolic")
                    )
                    pulse_val = _float(
                        row.get("Herzfrequenz") or row.get("Pulse (bpm)") or
                        row.get("Puls (bpm)") or row.get("Heart rate (bpm)") or
                        row.get("Heart Rate")
                    )
                    updated = False
                    if systolic and diastolic:
                        log = _get_or_create_log(db, entry_date, cache)
                        log.bp_systolic  = int(systolic)
                        log.bp_diastolic = int(diastolic)
                        updated = True
                        stats["bp"] += 1
                    if pulse_val:
                        log = _get_or_create_log(db, entry_date, cache)
                        log.resting_pulse = int(pulse_val)
                        updated = True
            db.flush()
        except Exception as e:
            stats["errors"].append(f"bp.csv: {e}")

    db.commit()
    return stats


# ─── Garmin ───────────────────────────────────────────────────────────────────

def import_garmin_all(db: Session) -> dict:
    """
    Importiert alle Garmin JSON-Dateien aus Imports/Garmin/.
    Verarbeitet:
    - *healthStatusData*.json  → HRV, HF, Atemfrequenz (täglich)
    - *sleepData*.json         → Schlaf-Phasen, Schlaf-Score, Atemfrequenz
    """
    stats = {"health": 0, "sleep": 0, "errors": []}
    cache: dict = {}

    wellness_dir = GARMIN_DIR / "DI_CONNECT" / "DI-Connect-Wellness"
    if not wellness_dir.exists():
        return {"error": f"Garmin-Ordner nicht gefunden: {wellness_dir}"}

    # ── healthStatusData JSONs ────────────────────────────────────────────────
    health_files = sorted(wellness_dir.glob("*healthStatusData*.json"))
    for hfile in health_files:
        try:
            with open(hfile, encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                continue
            for rec in records:
                entry_date = _parse_date(rec.get("calendarDate", ""))
                if not entry_date:
                    continue
                metrics = rec.get("metrics", [])
                if not metrics:
                    continue

                log = _get_or_create_log(db, entry_date, cache)

                for m in metrics:
                    mtype = m.get("type", "")
                    # Wert kann 'value' oder in nested sein
                    val = _float(m.get("value"))
                    if val is None:
                        continue

                    if mtype == "HRV" and log.hrv is None:
                        log.hrv = val
                    elif mtype == "HR" and log.heart_rate_night is None:
                        log.heart_rate_night = val
                    elif mtype == "RESPIRATION" and log.breath_rate is None:
                        log.breath_rate = val
                    elif mtype in ("TRAINING_READINESS", "trainingReadiness") and log.training_readiness is None:
                        log.training_readiness = int(val)

                if log.source == "manuell":
                    log.source = "garmin"
                elif log.source == "withings":
                    log.source = "gemischt"

                stats["health"] += 1
            db.flush()
        except Exception as e:
            stats["errors"].append(f"{hfile.name}: {e}")

    # ── sleepData JSONs ───────────────────────────────────────────────────────
    sleep_files = sorted(wellness_dir.glob("*sleepData*.json"))
    for sfile in sleep_files:
        try:
            with open(sfile, encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                continue
            for rec in records:
                entry_date = _parse_date(rec.get("calendarDate", ""))
                if not entry_date:
                    continue

                deep_s   = _float(rec.get("deepSleepSeconds"))
                light_s  = _float(rec.get("lightSleepSeconds"))
                rem_s    = _float(rec.get("remSleepSeconds"))
                awake_s  = _float(rec.get("awakeSleepSeconds"))
                resp     = _float(rec.get("averageRespiration"))

                # Sekunden → Minuten
                deep_min  = int(deep_s / 60)  if deep_s  else None
                rem_min   = int(rem_s / 60)   if rem_s   else None
                light_min = int(light_s / 60) if light_s else None
                total_min = (
                    int((deep_s + light_s + rem_s) / 60)
                    if deep_s and light_s and rem_s else None
                )

                # Sleep-Score aus nested sleepScores
                sleep_score = None
                scores = rec.get("sleepScores")
                if isinstance(scores, dict):
                    sleep_score = _float(scores.get("overallScore"))
                    if sleep_score is None:
                        sleep_score = _float(scores.get("qualityScore"))

                if all(v is None for v in [deep_min, rem_min, sleep_score]):
                    continue

                log = _get_or_create_log(db, entry_date, cache)
                if deep_min   is not None: log.deep_sleep_min  = deep_min
                if rem_min    is not None: log.rem_sleep_min   = rem_min
                if light_min  is not None: log.light_sleep_min = light_min
                if total_min  is not None: log.total_sleep_min = total_min
                if sleep_score is not None: log.sleep_score    = int(sleep_score)
                if resp is not None and log.breath_rate is None:
                    log.breath_rate = resp

                if log.source == "manuell":
                    log.source = "garmin"
                elif log.source == "withings":
                    log.source = "gemischt"

                stats["sleep"] += 1
            db.flush()
        except Exception as e:
            stats["errors"].append(f"{sfile.name}: {e}")

    # ── wellnessActivities JSONs → Stress (Fallback für ältere Daten) ──────────
    wellness_files = sorted(wellness_dir.glob("*wellnessActivities*.json"))
    for wfile in wellness_files:
        try:
            with open(wfile, encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                continue

            for rec in records:
                entry_date = _parse_date(rec.get("calendarDate", ""))
                if not entry_date:
                    continue
                for s in rec.get("summaryTypeDataList", []):
                    if s.get("summaryType") == "STRESS":
                        avg = _float(s.get("avgValue"))
                        if avg is not None:
                            log = _get_or_create_log(db, entry_date, cache)
                            if log.stress_avg is None:
                                log.stress_avg = int(avg)

            db.flush()
        except Exception as e:
            stats["errors"].append(f"{wfile.name}: {e}")

    # ── UDSFile JSONs → Stress, Body Battery, Steps, Ruhepuls ───────────────
    aggregator_dir = GARMIN_DIR / "DI_CONNECT" / "DI-Connect-Aggregator"
    uds_files = sorted(aggregator_dir.glob("UDSFile_*.json")) if aggregator_dir.exists() else []
    for ufile in uds_files:
        try:
            with open(ufile, encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                continue
            for rec in records:
                entry_date = _parse_date(rec.get("calendarDate", ""))
                if not entry_date:
                    continue
                log = _get_or_create_log(db, entry_date, cache)

                # Schritte
                steps = rec.get("totalSteps")
                if steps and log.steps is None:
                    log.steps = int(steps)

                # Ruhepuls
                rhr = rec.get("restingHeartRate") or rec.get("currentDayRestingHeartRate")
                if rhr and log.heart_rate_night is None:
                    log.heart_rate_night = float(rhr)

                # Stress (TOTAL aggregator)
                stress_data = rec.get("allDayStress") or {}
                for agg in (stress_data.get("aggregatorList") or []):
                    if agg.get("type") == "TOTAL":
                        sl = agg.get("averageStressLevel")
                        if sl is not None and log.stress_avg is None:
                            log.stress_avg = int(sl)
                        break

                # Body Battery: SLEEPEND-Wert (= Morgen-Wert nach Schlaf)
                bb_data = rec.get("bodyBattery") or {}
                bb_stats = bb_data.get("bodyBatteryStatList") or []
                sleepend_val = next(
                    (s["statsValue"] for s in bb_stats if s.get("bodyBatteryStatType") == "SLEEPEND"),
                    None
                )
                if sleepend_val is None:
                    sleepend_val = next(
                        (s["statsValue"] for s in bb_stats if s.get("bodyBatteryStatType") == "HIGHEST"),
                        None
                    )
                if sleepend_val is not None and log.body_battery is None:
                    log.body_battery = int(sleepend_val)

                if log.source == "manuell":
                    log.source = "garmin"
                elif log.source == "withings":
                    log.source = "gemischt"
                stats["health"] += 1

            db.flush()
        except Exception as e:
            stats["errors"].append(f"{ufile.name}: {e}")

    # ── TrainingReadinessDTO JSONs → Training Readiness Score ───────────────
    metrics_dir = GARMIN_DIR / "DI_CONNECT" / "DI-Connect-Metrics"
    tr_files = sorted(metrics_dir.glob("TrainingReadinessDTO_*.json")) if metrics_dir.exists() else []
    for tfile in tr_files:
        try:
            with open(tfile, encoding="utf-8") as f:
                records = json.load(f)
            if not isinstance(records, list):
                continue
            # Pro calendarDate: höchsten Score nehmen
            best: dict[date, int] = {}
            for rec in records:
                entry_date = _parse_date(rec.get("calendarDate", ""))
                score = rec.get("score")
                if entry_date and score is not None:
                    best[entry_date] = max(best.get(entry_date, 0), int(score))
            for entry_date, score in best.items():
                log = _get_or_create_log(db, entry_date, cache)
                if log.training_readiness is None:
                    log.training_readiness = score
                    if log.source == "manuell":
                        log.source = "garmin"
                    elif log.source == "withings":
                        log.source = "gemischt"
            db.flush()
        except Exception as e:
            stats["errors"].append(f"{tfile.name}: {e}")

    db.commit()
    return stats


# ─── Alles auf einmal (CSV/JSON aus Ordnern) ──────────────────────────────────

def import_all(db: Session) -> dict:
    """Importiert Withings + Garmin aus den Export-Ordnern."""
    results = {}
    results["withings"] = import_withings_all(db)
    results["garmin"]   = import_garmin_all(db)

    total = db.query(DailyLog).count()
    results["total_daily_logs"] = total
    return results

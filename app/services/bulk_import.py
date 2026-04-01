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
MFP_DIR      = BASE_DIR / "Imports" / "Myfitnesspal"


# ─── Hilfsfunktionen ─────────────────────────────────────────────────────────

def _parse_date(date_str: str) -> Optional[date]:
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d", "%d.%m.%Y"):
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
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
    Verarbeitet: weight.csv, bp.csv, aggregates_steps.csv
    """
    stats = {"weight": 0, "bp": 0, "steps": 0, "errors": []}
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

                    weight_kg    = _float(row.get("Gewicht (kg)") or row.get("Weight (kg)"))
                    fat_kg       = _float(row.get("Fettmasse (kg)") or row.get("Fat mass (kg)"))
                    muscle_kg    = _float(row.get("Muskelmasse (kg)") or row.get("Muscle mass (kg)"))

                    if weight_kg is None:
                        continue

                    log = _get_or_create_log(db, entry_date, cache)
                    log.weight = weight_kg
                    if fat_kg and weight_kg:
                        log.body_fat = round((fat_kg / weight_kg) * 100, 1)
                    if muscle_kg:
                        log.muscle_mass = muscle_kg
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

    # ── bp.csv (Blutdruck) ────────────────────────────────────────────────────
    # Wird aktuell nicht in DailyLog gespeichert, aber gezählt für Info
    bp_file = WITHINGS_DIR / "bp.csv"
    if bp_file.exists():
        try:
            with open(bp_file, newline="", encoding="utf-8-sig") as f:
                stats["bp"] = sum(1 for _ in csv.DictReader(f))
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
                if deep_min  is not None: log.deep_sleep_min  = deep_min
                if rem_min   is not None: log.rem_sleep_min   = rem_min
                if total_min is not None: log.total_sleep_min = total_min
                if sleep_score is not None: log.sleep_score   = int(sleep_score)
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

    db.commit()
    return stats


# ─── MyFitnessPal ────────────────────────────────────────────────────────────

def import_mfp_all(db: Session) -> dict:
    """
    Importiert MyFitnessPal Nährwerte-CSV.
    Summiert pro Tag: Kalorien, Protein, Kohlenhydrate, Fett.
    """
    stats = {"days": 0, "rows": 0, "errors": []}
    cache: dict = {}

    if not MFP_DIR.exists():
        return {"error": f"MFP-Ordner nicht gefunden: {MFP_DIR}"}

    # Neueste Nährwerte-Datei finden
    mfp_files = sorted(MFP_DIR.glob("Nährwerte-*.csv")) + sorted(MFP_DIR.glob("N*hrwerte-*.csv"))
    if not mfp_files:
        return {"error": "Keine MFP Nährwerte-CSV gefunden"}

    # Tagessummen
    day_totals: dict[date, dict] = {}

    for mfp_file in mfp_files:
        for enc in ("utf-8-sig", "cp1252", "latin-1"):
            try:
                with open(mfp_file, newline="", encoding=enc) as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        raw_date = row.get("Datum") or row.get("Date") or ""
                        entry_date = _parse_date(raw_date)
                        if not entry_date:
                            continue

                        # Tageszeile "Tagessummen" überspringen
                        meal = row.get("Mahlzeit", row.get("Meal", ""))
                        if "summe" in meal.lower() or "total" in meal.lower():
                            continue

                        cal  = _float(row.get("Kalorien") or row.get("Calories"))
                        prot = _float(row.get("Eiweiß (g)") or row.get("Protein (g)") or row.get("Protein"))
                        carb = _float(row.get("Kohlenhydrate (g)") or row.get("Carbohydrates (g)"))
                        fat  = _float(row.get("Fett (g)") or row.get("Fat (g)"))

                        if entry_date not in day_totals:
                            day_totals[entry_date] = {"cal": 0, "prot": 0, "carb": 0, "fat": 0}
                        if cal:  day_totals[entry_date]["cal"]  += cal
                        if prot: day_totals[entry_date]["prot"] += prot
                        if carb: day_totals[entry_date]["carb"] += carb
                        if fat:  day_totals[entry_date]["fat"]  += fat
                        stats["rows"] += 1
                break  # encoding war erfolgreich
            except (UnicodeDecodeError, UnicodeError):
                continue
            except Exception as e:
                stats["errors"].append(f"{mfp_file.name}: {e}")
                break

    for entry_date, totals in day_totals.items():
        log = _get_or_create_log(db, entry_date, cache)
        if totals["cal"] > 0:  log.calories = int(totals["cal"])
        if totals["prot"] > 0: log.protein  = round(totals["prot"], 1)
        if totals["carb"] > 0: log.carbs    = round(totals["carb"], 1)
        if totals["fat"] > 0:  log.fat      = round(totals["fat"], 1)
        if log.source == "manuell":
            log.source = "gemischt"
        stats["days"] += 1

    db.commit()
    return stats


# ─── Alles auf einmal ─────────────────────────────────────────────────────────

def import_all(db: Session) -> dict:
    """Importiert Withings + Garmin + MFP in einem Durchgang."""
    results = {}
    results["withings"] = import_withings_all(db)
    results["garmin"]   = import_garmin_all(db)
    results["mfp"]      = import_mfp_all(db)

    # Gesamtzahl importierter Tages-Logs
    total = db.query(DailyLog).count()
    results["total_daily_logs"] = total
    return results

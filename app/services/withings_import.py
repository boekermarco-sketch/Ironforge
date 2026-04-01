"""
Withings CSV-Import.
Erwartet die CSV-Datei aus dem Withings Daten-Export (account.withings.com).
Typische Spalten: Date, Weight, Fat mass weight, Bone mass, Muscle mass, BMI, etc.
"""
import csv
from datetime import date, datetime
from pathlib import Path
from typing import Optional
from sqlalchemy.orm import Session

from app.models import DailyLog


# Mapping Withings CSV-Spalten → DailyLog-Felder
_WITHINGS_COLUMNS = {
    "Weight (kg)": "weight",
    "Gewicht (kg)": "weight",
    "Fat mass (kg)": None,          # wird zu body_fat % umgerechnet
    "Fettmasse (kg)": None,
    "Fat ratio (%)": "body_fat",
    "Fettanteil (%)": "body_fat",
    "Muscle mass (kg)": "muscle_mass",
    "Muskelmasse (kg)": "muscle_mass",
    "Bone mass (kg)": None,
    "BMI (kg/m²)": "bmi",
    "BMI": "bmi",
    "Heart rate (bpm)": "resting_pulse",
    "Herzrate (bpm)": "resting_pulse",
    "Resting Heart Rate": "resting_pulse",
}

_DATE_FORMATS = [
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d",
    "%d.%m.%Y %H:%M:%S",
    "%d.%m.%Y",
    "%d/%m/%Y",
]


def _parse_date(date_str: str) -> Optional[date]:
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(date_str.strip(), fmt).date()
        except ValueError:
            continue
    return None


def _parse_float(val: str) -> Optional[float]:
    if not val or val.strip() in ("", "-", "N/A"):
        return None
    try:
        return float(val.strip().replace(",", "."))
    except ValueError:
        return None


def import_withings_csv(csv_path: Path, db: Session) -> dict:
    """
    Importiert eine Withings-Export-CSV in die daily_logs Tabelle.
    Bestehende Einträge werden aktualisiert (Withings-Daten ergänzt, manuell bleibt).
    Gibt Import-Statistik zurück.
    """
    if not csv_path.exists():
        return {"error": f"Datei nicht gefunden: {csv_path}"}

    stats = {"imported": 0, "updated": 0, "skipped": 0, "errors": 0}

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            # Spalten-Mapping aufbauen
            col_map = {}
            for header in headers:
                if header in _WITHINGS_COLUMNS and _WITHINGS_COLUMNS[header]:
                    col_map[header] = _WITHINGS_COLUMNS[header]

            # Datum-Spalte finden
            date_col = None
            for candidate in ("Date", "Datum", "date", "datetime"):
                if candidate in headers:
                    date_col = candidate
                    break

            if not date_col:
                return {"error": "Keine Datumsspalte in CSV gefunden"}

            for row in reader:
                raw_date = row.get(date_col, "")
                entry_date = _parse_date(raw_date)
                if not entry_date:
                    stats["skipped"] += 1
                    continue

                existing = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
                if not existing:
                    existing = DailyLog(date=entry_date, source="withings")
                    db.add(existing)
                    stats["imported"] += 1
                else:
                    stats["updated"] += 1

                for csv_col, field in col_map.items():
                    val = _parse_float(row.get(csv_col, ""))
                    if val is not None:
                        setattr(existing, field, val)

                # Körperfett aus kg berechnen wenn nur kg-Wert vorhanden
                fat_kg_col = next((c for c in headers if "Fat mass" in c or "Fettmasse" in c), None)
                weight_val = _parse_float(row.get("Weight (kg)", row.get("Gewicht (kg)", "")))
                fat_kg_val = _parse_float(row.get(fat_kg_col, "")) if fat_kg_col else None
                if fat_kg_val and weight_val and weight_val > 0 and not existing.body_fat:
                    existing.body_fat = round((fat_kg_val / weight_val) * 100, 1)

                if existing.source == "manuell":
                    existing.source = "gemischt"
                elif existing.source != "gemischt":
                    existing.source = "withings"

        db.commit()

    except Exception as e:
        stats["errors"] += 1
        stats["error_detail"] = str(e)
        db.rollback()

    return stats


def import_garmin_csv(csv_path: Path, db: Session) -> dict:
    """
    Importiert Garmin Connect Export-CSV.
    Typische Spalten (Garmin Connect export): Date, AvgHRV, SleepScore, etc.
    """
    if not csv_path.exists():
        return {"error": f"Datei nicht gefunden: {csv_path}"}

    # Garmin-Spalten Mapping (Connect Export)
    garmin_map = {
        "Date": "date",
        "Datum": "date",
        "Avg HRV": "hrv",
        "HRV": "hrv",
        "Resting Heart Rate": "heart_rate_night",
        "Ruhepuls": "heart_rate_night",
        "Sleep Score": "sleep_score",
        "Schlafscore": "sleep_score",
        "Deep Sleep (min)": "deep_sleep_min",
        "Tiefschlaf (Min)": "deep_sleep_min",
        "REM Sleep (min)": "rem_sleep_min",
        "REM-Schlaf (Min)": "rem_sleep_min",
        "Total Sleep (min)": "total_sleep_min",
        "Body Battery": "body_battery",
        "Avg Respiration": "breath_rate",
        "Atemfrequenz": "breath_rate",
        "Steps": "steps",
        "Schritte": "steps",
        "Avg Stress Level": "stress_avg",
        "VO2Max": "vo2max",
    }

    stats = {"imported": 0, "updated": 0, "skipped": 0, "errors": 0}

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames or []

            date_col = next((c for c in headers if c in ("Date", "Datum", "date")), None)
            if not date_col:
                return {"error": "Keine Datumsspalte gefunden"}

            for row in reader:
                entry_date = _parse_date(row.get(date_col, ""))
                if not entry_date:
                    stats["skipped"] += 1
                    continue

                existing = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
                if not existing:
                    existing = DailyLog(date=entry_date, source="garmin")
                    db.add(existing)
                    stats["imported"] += 1
                else:
                    stats["updated"] += 1

                for csv_col, field in garmin_map.items():
                    if field == "date" or csv_col not in headers:
                        continue
                    val_str = row.get(csv_col, "")
                    if not val_str or val_str.strip() in ("", "-"):
                        continue
                    try:
                        val = float(val_str.strip().replace(",", "."))
                        setattr(existing, field, val)
                    except ValueError:
                        pass

                if existing.source == "manuell":
                    existing.source = "gemischt"

        db.commit()

    except Exception as e:
        stats["errors"] += 1
        stats["error_detail"] = str(e)
        db.rollback()

    return stats

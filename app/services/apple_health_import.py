"""
Apple Health Import Service
- Nimmt tägliche Apple Health / MFP-Daten als JSON entgegen
- UPSERT in SQLite daily_logs (nur non-NULL Felder überschreiben)
- Optionaler Push in Supabase apple_health_daily
"""
from __future__ import annotations

import os
from datetime import date, datetime
from typing import Any

import requests
from sqlalchemy.orm import Session

from app.models import DailyLog


# Mapping Apple Health JSON-Feld → DailyLog-Attribut
_FIELD_MAP = {
    "calories":      "calories",
    "protein_g":     "protein",
    "carbs_g":       "carbs",
    "fat_g":         "fat",
    "body_mass_kg":  "weight",
    "body_fat_pct":  "body_fat",
    "steps":         "steps",
    "resting_hr":    "resting_pulse",
    "sleep_min":     "total_sleep_min",
}


def upsert_apple_health_day(payload: dict[str, Any], db: Session) -> dict:
    """
    UPSERT einen Tagesdatensatz aus Apple Health in daily_logs.
    Gibt {'date': str, 'action': 'created'|'updated', 'fields': [...]} zurück.
    """
    raw_date = payload.get("date")
    if not raw_date:
        raise ValueError("Feld 'date' fehlt im Payload")

    if isinstance(raw_date, date):
        entry_date = raw_date
    else:
        entry_date = date.fromisoformat(str(raw_date)[:10])

    log = db.query(DailyLog).filter(DailyLog.date == entry_date).first()
    action = "updated" if log else "created"

    if not log:
        log = DailyLog(date=entry_date, source="apple_health")
        db.add(log)
    elif log.source not in ("apple_health", "manuell"):
        # Bei Garmin/Withings-Einträgen die Quelle erweitern, nicht überschreiben
        log.source = "gemischt"

    updated_fields: list[str] = []
    for json_key, model_attr in _FIELD_MAP.items():
        val = payload.get(json_key)
        if val is None:
            continue
        # Integer-Konvertierung für ganzzahlige Felder
        if model_attr in ("calories", "steps", "resting_pulse", "total_sleep_min"):
            val = int(round(float(val)))
        else:
            val = float(val)
        setattr(log, model_attr, val)
        updated_fields.append(model_attr)

    db.commit()
    db.refresh(log)

    # Optionaler Supabase-Sync
    _push_to_supabase(entry_date, payload)

    return {"date": str(entry_date), "action": action, "fields": updated_fields}


def _push_to_supabase(entry_date: date, payload: dict[str, Any]) -> None:
    url = (os.environ.get("SUPABASE_URL") or "").strip()
    key = (os.environ.get("SUPABASE_ANON_KEY") or "").strip()
    if not url or not key:
        return

    row: dict[str, Any] = {"date": str(entry_date)}
    for json_key in (
        "calories", "protein_g", "carbs_g", "fat_g",
        "body_mass_kg", "body_fat_pct", "steps", "resting_hr", "sleep_min",
    ):
        if payload.get(json_key) is not None:
            row[json_key] = payload[json_key]
    row["synced_at"] = datetime.utcnow().isoformat()

    try:
        requests.post(
            f"{url}/rest/v1/apple_health_daily",
            headers={
                "apikey":           key,
                "Authorization":    f"Bearer {key}",
                "Content-Type":     "application/json",
                "Prefer":           "resolution=merge-duplicates",
            },
            json=row,
            timeout=8,
        )
    except Exception:
        pass  # Supabase-Fehler dürfen den lokalen Import nicht blockieren

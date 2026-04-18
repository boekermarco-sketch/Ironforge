"""
Lokale Metadaten für Apple-Health-Import (Shortcut → Supabase vs. POST /import/apple-health).
"""
from __future__ import annotations

import json
from datetime import date, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models import AppKVStore

APPLE_LAST_LOCAL_KEY = "apple_health_last_local"


def get_last_local_apple_import(db: Session) -> dict[str, Any] | None:
    row = db.query(AppKVStore).filter(AppKVStore.key == APPLE_LAST_LOCAL_KEY).first()
    if not row:
        return None
    try:
        return json.loads(row.value_json or "{}")
    except json.JSONDecodeError:
        return {"parse_error": True, "raw": row.value_json}


def record_local_apple_import(db: Session, entry_date: date, updated_fields: list[str]) -> None:
    payload = {
        "received_at": datetime.utcnow().replace(microsecond=0).isoformat() + "Z",
        "entry_date": str(entry_date),
        "fields": updated_fields,
    }
    raw = json.dumps(payload, ensure_ascii=False)
    row = db.query(AppKVStore).filter(AppKVStore.key == APPLE_LAST_LOCAL_KEY).first()
    if row:
        row.value_json = raw
        row.updated_at = datetime.utcnow()
    else:
        db.add(AppKVStore(key=APPLE_LAST_LOCAL_KEY, value_json=raw))

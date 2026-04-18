import os
import requests
from datetime import date, timedelta
from typing import Optional

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
}


def _sort_apple_rows_newest_first(rows: list[dict]) -> list[dict]:
    """Neueste Zeile zuerst: primär synced_at (Shortcut-Lauf), sekundär Kalenderdatum."""

    def key(r: dict) -> tuple[str, str]:
        return (str(r.get("synced_at") or ""), str(r.get("date") or ""))

    return sorted(rows or [], key=key, reverse=True)


def fetch_apple_health(days: int = 30, *, limit: int = 500) -> list[dict]:
    """Return apple_health_daily rows for the last N days, newest first (nach synced_at)."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return []
    since = (date.today() - timedelta(days=days)).isoformat()
    try:
        resp = requests.get(
            f"{SUPABASE_URL}/rest/v1/apple_health_daily",
            headers=_HEADERS,
            params={
                "select": "*",
                "date": f"gte.{since}",
                "limit": str(limit),
            },
            timeout=8,
        )
        resp.raise_for_status()
        return _sort_apple_rows_newest_first(resp.json())
    except Exception:
        return []


def latest_apple_health() -> Optional[dict]:
    """Letzte Zeile nach synced_at (falls gesetzt), sonst nach Datum."""
    rows = fetch_apple_health(days=21, limit=500)
    return rows[0] if rows else None

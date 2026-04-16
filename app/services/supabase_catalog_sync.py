from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any

import requests


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _infer_target(text: str) -> str:
    value = _normalize_text(text)
    if any(x in value for x in ["lat", "row", "rücken", "ruecken", "back"]):
        return "Rücken"
    if any(x in value for x in ["chest", "brust", "press"]):
        return "Brust"
    if any(x in value for x in ["leg", "quad", "ham", "bein", "glute"]):
        return "Beine"
    if any(x in value for x in ["shoulder", "schulter"]):
        return "Schulter"
    if any(x in value for x in ["biceps", "triceps", "bizeps", "trizeps"]):
        return "Arme"
    if any(x in value for x in ["core", "abdominal", "bauch"]):
        return "Core"
    if any(x in value for x in ["cardio", "bike", "treadmill", "elliptical", "climb"]):
        return "Cardio"
    return "Core"


def _infer_stype(target_name: str) -> str:
    target = _normalize_text(target_name)
    if target == "rücken" or target == "ruecken":
        return "pull"
    if target in ("beine", "cardio"):
        return "legs"
    if target == "core":
        return "free"
    return "push"


def _chunked(rows: list[dict[str, Any]], size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def _read_sqlite_catalog_rows(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows: list[dict[str, Any]] = []

        gym80 = conn.execute(
            "SELECT model, serie, image_url, muscle_groups, category FROM gym80_devices"
        ).fetchall()
        for r in gym80:
            model = (r["model"] or "").strip()
            serie = (r["serie"] or "").strip()
            category = (r["category"] or "").strip()
            target = _infer_target(f"{model} {r['muscle_groups'] or ''} {category}")
            rows.append(
                {
                    "brand": "gym80",
                    "name": model,
                    "type": "Machine",
                    "target": target,
                    "cat": target,
                    "s_type": _infer_stype(target),
                    "movement_group": serie or None,
                    "art": None,
                    "img": r["image_url"] or None,
                }
            )

        matrix_strength = conn.execute(
            "SELECT model, serie, image_url, muscle_groups, category FROM matrix_strength_devices"
        ).fetchall()
        for r in matrix_strength:
            model = (r["model"] or "").strip()
            serie = (r["serie"] or "").strip()
            category = (r["category"] or "").strip()
            target = _infer_target(f"{model} {r['muscle_groups'] or ''} {category}")
            rows.append(
                {
                    "brand": "Matrix",
                    "name": model,
                    "type": "Machine",
                    "target": target,
                    "cat": target,
                    "s_type": _infer_stype(target),
                    "movement_group": serie or None,
                    "art": None,
                    "img": r["image_url"] or None,
                }
            )

        matrix_cardio = conn.execute(
            "SELECT model, serie, image_url, cardio_type, category FROM matrix_cardio_devices"
        ).fetchall()
        for r in matrix_cardio:
            model = (r["model"] or "").strip()
            serie = (r["serie"] or "").strip()
            category = (r["category"] or "").strip()
            target = _infer_target(f"{model} {r['cardio_type'] or ''} {category}")
            rows.append(
                {
                    "brand": "Matrix",
                    "name": model,
                    "type": "Cardio",
                    "target": target,
                    "cat": target,
                    "s_type": _infer_stype(target),
                    "movement_group": serie or None,
                    "art": None,
                    "img": r["image_url"] or None,
                }
            )

        egym = conn.execute(
            "SELECT model, series, image_url, muscle_groups, category FROM egym_devices"
        ).fetchall()
        for r in egym:
            model = (r["model"] or "").strip()
            series = (r["series"] or "").strip()
            category = (r["category"] or "").strip()
            target = _infer_target(f"{model} {r['muscle_groups'] or ''} {category}")
            rows.append(
                {
                    "brand": "eGym",
                    "name": model,
                    "type": "Digital",
                    "target": target,
                    "cat": target,
                    "s_type": _infer_stype(target),
                    "movement_group": series or None,
                    "art": None,
                    "img": r["image_url"] or None,
                }
            )

        dedup: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = f"{_normalize_text(row['brand'])}|{_normalize_text(row['name'])}|{_normalize_text(row['target'])}"
            prev = dedup.get(key)
            if not prev:
                dedup[key] = row
                continue
            if not prev.get("img") and row.get("img"):
                dedup[key] = row
        return sorted(dedup.values(), key=lambda x: (x["brand"], x["name"]))
    finally:
        conn.close()


def sync_catalog_to_supabase(
    db_path: Path, supabase_url: str, supabase_anon_key: str, chunk_size: int = 500
) -> dict[str, Any]:
    if not supabase_url or not supabase_anon_key:
        return {"ok": False, "error": "SUPABASE_URL oder SUPABASE_ANON_KEY fehlt."}

    base = supabase_url.rstrip("/")
    endpoint = f"{base}/rest/v1/ifl_device_catalog"
    headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
    }

    rows = _read_sqlite_catalog_rows(db_path)
    if not rows:
        return {"ok": False, "error": "Keine lokalen Katalogdaten gefunden."}

    # Table smoke test (read)
    smoke = requests.get(f"{endpoint}?select=name&limit=1", headers=headers, timeout=30)
    if smoke.status_code >= 300:
        return {
            "ok": False,
            "error": f"Supabase Tabelle nicht erreichbar ({smoke.status_code}). Prüfe ifl_device_catalog + RLS.",
        }

    # Delete existing rows (table dedicated to catalog)
    delete_res = requests.delete(
        f"{endpoint}?name=not.is.null",
        headers={**headers, "Prefer": "return=minimal"},
        timeout=60,
    )
    if delete_res.status_code >= 300:
        return {
            "ok": False,
            "error": f"Löschen in Supabase fehlgeschlagen ({delete_res.status_code}). Prüfe RLS.",
        }

    inserted = 0
    for chunk in _chunked(rows, chunk_size):
        ins = requests.post(
            endpoint,
            headers={
                **headers,
                "Content-Type": "application/json",
                "Prefer": "return=minimal",
            },
            json=chunk,
            timeout=60,
        )
        if ins.status_code >= 300:
            return {
                "ok": False,
                "error": f"Insert fehlgeschlagen ({ins.status_code}). Prüfe Tabellenstruktur/RLS.",
            }
        inserted += len(chunk)

    verify = requests.get(f"{endpoint}?select=name", headers=headers, timeout=60)
    if verify.status_code >= 300:
        return {
            "ok": False,
            "error": f"Verifikation fehlgeschlagen ({verify.status_code}).",
        }
    total_in_supabase = len(verify.json() or [])

    return {
        "ok": True,
        "prepared_local_rows": len(rows),
        "inserted_rows": inserted,
        "supabase_rows": total_in_supabase,
    }


def get_supabase_catalog_status(supabase_url: str, supabase_anon_key: str) -> dict[str, Any]:
    if not supabase_url or not supabase_anon_key:
        return {
            "ok": False,
            "configured": False,
            "error": "SUPABASE_URL oder SUPABASE_ANON_KEY fehlt.",
            "total": 0,
            "by_brand": {},
        }

    base = supabase_url.rstrip("/")
    endpoint = f"{base}/rest/v1/ifl_device_catalog"
    headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
    }

    try:
        res = requests.get(f"{endpoint}?select=brand&limit=5000", headers=headers, timeout=30)
        if res.status_code >= 300:
            return {
                "ok": False,
                "configured": True,
                "error": f"Supabase antwortet mit {res.status_code}. Prüfe Tabelle/RLS.",
                "total": 0,
                "by_brand": {},
            }
        rows = res.json() or []
        by_brand: dict[str, int] = {}
        for row in rows:
            brand = (row.get("brand") or "Unbekannt").strip()
            by_brand[brand] = by_brand.get(brand, 0) + 1
        return {
            "ok": True,
            "configured": True,
            "error": None,
            "total": len(rows),
            "by_brand": dict(sorted(by_brand.items(), key=lambda x: x[0].lower())),
        }
    except Exception as exc:
        return {
            "ok": False,
            "configured": True,
            "error": f"Statusabfrage fehlgeschlagen: {exc}",
            "total": 0,
            "by_brand": {},
        }

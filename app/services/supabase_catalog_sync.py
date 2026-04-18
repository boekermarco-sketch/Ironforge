from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any

import requests

from app.services.catalog_overrides import load_override_rules, resolve_catalog_row_targets
from app.services.catalog_targets import infer_stype, infer_target, target_to_key


def _normalize_text(value: str | None) -> str:
    return (value or "").strip().lower()


def _chunked(rows: list[dict[str, Any]], size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def read_sqlite_device_catalog_rows(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rules = load_override_rules(conn)
        rows: list[dict[str, Any]] = []

        gym80 = conn.execute(
            "SELECT model, serie, image_url, muscle_groups, category FROM gym80_devices"
        ).fetchall()
        for r in gym80:
            model = (r["model"] or "").strip()
            serie = (r["serie"] or "").strip()
            category = (r["category"] or "").strip()
            mg = r["muscle_groups"] or ""
            target, movement = resolve_catalog_row_targets(
                "gym80", model, serie, mg, category, rules, infer_target_fn=infer_target
            )
            st = infer_stype(target)
            rows.append(
                {
                    "brand": "gym80",
                    "name": model,
                    "type": "Machine",
                    "target": target,
                    "cat": target,
                    "s_type": st,
                    "session_type": st,
                    "target_key": target_to_key(target),
                    "movement_group": movement,
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
            mg = r["muscle_groups"] or ""
            target, movement = resolve_catalog_row_targets(
                "Matrix", model, serie, mg, category, rules, infer_target_fn=infer_target
            )
            st = infer_stype(target)
            rows.append(
                {
                    "brand": "Matrix",
                    "name": model,
                    "type": "Machine",
                    "target": target,
                    "cat": target,
                    "s_type": st,
                    "session_type": st,
                    "target_key": target_to_key(target),
                    "movement_group": movement,
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
            ct = r["cardio_type"] or ""
            target, movement = resolve_catalog_row_targets(
                "Matrix", model, serie, ct, category, rules, infer_target_fn=infer_target
            )
            st = infer_stype(target, is_matrix_cardio_row=True)
            rows.append(
                {
                    "brand": "Matrix",
                    "name": model,
                    "type": "Cardio",
                    "target": target,
                    "cat": target,
                    "s_type": st,
                    "session_type": st,
                    "target_key": target_to_key(target),
                    "movement_group": movement,
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
            mg = r["muscle_groups"] or ""
            target, movement = resolve_catalog_row_targets(
                "eGym", model, series, mg, category, rules, infer_target_fn=infer_target
            )
            st = infer_stype(target)
            rows.append(
                {
                    "brand": "eGym",
                    "name": model,
                    "type": "Digital",
                    "target": target,
                    "cat": target,
                    "s_type": st,
                    "session_type": st,
                    "target_key": target_to_key(target),
                    "movement_group": movement,
                    "art": None,
                    "img": r["image_url"] or None,
                }
            )

        # Eine Zeile pro Marke+Modell (target ist Attribut, kein Schlüsselbestandteil)
        dedup: dict[str, dict[str, Any]] = {}
        for row in rows:
            key = f"{_normalize_text(row['brand'])}|{_normalize_text(row['name'])}"
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

    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parents[2] / ".env")
    except ImportError:
        pass

    base = supabase_url.rstrip("/")
    endpoint = f"{base}/rest/v1/ifl_device_catalog"
    headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
    }
    # Leeren braucht meist Bypass von RLS → Service Role, falls in .env
    service_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    delete_key = service_key if service_key else supabase_anon_key
    delete_headers = {
        "apikey": delete_key,
        "Authorization": f"Bearer {delete_key}",
    }

    rows = read_sqlite_device_catalog_rows(db_path)
    if not rows:
        return {"ok": False, "error": "Keine lokalen Katalogdaten gefunden."}

    # Table smoke test (read)
    smoke = requests.get(f"{endpoint}?select=name&limit=1", headers=headers, timeout=30)
    if smoke.status_code >= 300:
        return {
            "ok": False,
            "error": f"Supabase Tabelle nicht erreichbar ({smoke.status_code}). Prüfe ifl_device_catalog + RLS.",
        }

    # Tabelle leeren (id ist BIGSERIAL → alle Zeilen; zuverlässiger als nur name)
    delete_res = requests.delete(
        f"{endpoint}?id=not.is.null",
        headers={**delete_headers, "Prefer": "return=minimal"},
        timeout=120,
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

    verify = requests.get(
        f"{endpoint}?select=id",
        headers={**headers, "Prefer": "count=exact"},
        timeout=60,
    )
    if verify.status_code >= 300:
        return {
            "ok": False,
            "error": f"Verifikation fehlgeschlagen ({verify.status_code}).",
        }
    content_range = verify.headers.get("Content-Range")  # z.B. "0-140/141"
    total_in_supabase = len(verify.json() or [])
    if content_range and "/" in content_range:
        try:
            total_in_supabase = int(content_range.split("/")[-1])
        except ValueError:
            pass

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

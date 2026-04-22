from __future__ import annotations
# Letzte inhaltliche Änderung: 2026-04-18 14:27 MEZ — Insert-Fallback ohne target_key/session_type wenn Spalten fehlen

import os
import sqlite3
import re
import base64
from pathlib import Path
from typing import Any

import requests

from app.services.catalog_overrides import load_override_rules, resolve_catalog_row_targets
from app.services.catalog_targets import infer_stype, infer_target, target_to_key


def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=? LIMIT 1",
        (table,),
    ).fetchone()
    return bool(row)


def _table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    if not _table_exists(conn, table):
        return set()
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return {str(r[1]).lower() for r in rows}


MODEL_CODE_RE = re.compile(r"^\s*(\d{3,5}N?)\b", re.IGNORECASE)
IMAGE_EXT_TO_MIME = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".webp": "image/webp",
}
EGYM_LOCAL_IMAGE_MAP: tuple[tuple[str, str], ...] = (
    ("beinstrecker", "Beinstrecker.jpeg"),
    ("bauchtrainer", "Bauchtrainer.jpeg"),
    ("ruckenstrecker", "Rückenstrecker.jpeg"),
    ("rueckenstrecker", "Rückenstrecker.jpeg"),
    ("beinbeuger", "Beinbeuger.jpeg"),
    ("brustpresse", "Brustpresse.jpeg"),
    ("ruderzug", "Seitbeuger.jpeg"),
    ("latzug", "Latzug.jpeg"),
    ("hip thrust", "Glutaeus Hip Thrust.jpeg"),
    ("beinpresse", "Beinpresse.jpeg"),
    ("abduktor", "Abduktor.jpeg"),
    ("adduktor", "Adduktor.jpeg"),
    ("rumpfrotation", "Seitbeuger.jpeg"),
    ("butterfly reverse", "Butterfly Reverse.jpeg"),
    ("butterfly", "Butterfly.jpeg"),
    ("bizeps", "Bizepscurl.jpeg"),
    ("schulterpresse", "Schulterpresse.jpeg"),
    ("trizeps", "Trizeps-Dips.jpeg"),
    ("kniebeuge", "Kniebeugen.jpeg"),
    ("smart flex", "Seitbeuger.jpeg"),
)


def _model_to_local_asset(model: str | None) -> str | None:
    m = MODEL_CODE_RE.search(model or "")
    if not m:
        return None
    code = m.group(1).lower()
    return f"assets/gym80/{code}.webp"


def _blob_to_data_url(blob_value: Any) -> str | None:
    if not blob_value:
        return None
    try:
        payload = base64.b64encode(bytes(blob_value)).decode("ascii")
    except Exception:
        return None
    return f"data:image/webp;base64,{payload}"


def _image_file_to_data_url(path: Path) -> str | None:
    if not path.exists() or not path.is_file():
        return None
    mime = IMAGE_EXT_TO_MIME.get(path.suffix.lower(), "application/octet-stream")
    try:
        payload = base64.b64encode(path.read_bytes()).decode("ascii")
    except Exception:
        return None
    return f"data:{mime};base64,{payload}"


def _normalize_text(value: str | None) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
    )


def _resolve_matrix_image(image_url: str | None, root_dir: Path) -> str | None:
    value = (image_url or "").strip()
    if not value:
        return None
    if value.startswith(("http://", "https://", "data:")):
        return value
    local_path = (root_dir / "SQL" / "Matrix" / value).resolve()
    return _image_file_to_data_url(local_path) or value


def _resolve_egym_image(image_url: str | None, model: str | None, root_dir: Path) -> str | None:
    model_norm = _normalize_text(model)
    egym_dir = root_dir / "SQL" / "egym_dump"
    for key, filename in EGYM_LOCAL_IMAGE_MAP:
        if key in model_norm:
            img = _image_file_to_data_url(egym_dir / filename)
            if img:
                return img
    value = (image_url or "").strip()
    if not value:
        return None
    if value.startswith(("http://", "https://", "data:")):
        return value
    return _image_file_to_data_url(egym_dir / value) or value


def _chunked(rows: list[dict[str, Any]], size: int):
    for i in range(0, len(rows), size):
        yield rows[i : i + size]


def read_sqlite_device_catalog_rows(db_path: Path) -> list[dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    root_dir = Path(__file__).resolve().parents[2]
    try:
        rules = load_override_rules(conn)
        rows: list[dict[str, Any]] = []

        if _table_exists(conn, "gym80_devices"):
            gym80_cols = _table_columns(conn, "gym80_devices")
            img_expr = "image_url AS image_url" if "image_url" in gym80_cols else "NULL AS image_url"
            blob_expr = "image_blob AS image_blob" if "image_blob" in gym80_cols else "NULL AS image_blob"
            gym80 = conn.execute(
                f"SELECT model, serie, {img_expr}, {blob_expr}, muscle_groups, category FROM gym80_devices"
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
                img_value = (r["image_url"] or "").strip() if "image_url" in r.keys() else ""
                blob_img = _blob_to_data_url(r["image_blob"] if "image_blob" in r.keys() else None)
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
                        "img": img_value or blob_img or _model_to_local_asset(model),
                    }
                )

        if _table_exists(conn, "matrix_strength_devices"):
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
                        "img": _resolve_matrix_image(r["image_url"], root_dir),
                    }
                )

        if _table_exists(conn, "matrix_cardio_devices"):
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
                        "img": _resolve_matrix_image(r["image_url"], root_dir),
                    }
                )

        if _table_exists(conn, "egym_devices"):
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
                        "img": _resolve_egym_image(r["image_url"], model, root_dir),
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
    # Leeren braucht meist Bypass von RLS → Service Role, falls in .env
    service_key = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()
    read_headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
    }
    write_key = service_key if service_key else supabase_anon_key
    write_headers = {
        "apikey": write_key,
        "Authorization": f"Bearer {write_key}",
    }

    rows = read_sqlite_device_catalog_rows(db_path)
    if not rows:
        return {"ok": False, "error": "Keine lokalen Katalogdaten gefunden."}

    # Table smoke test (read)
    smoke = requests.get(f"{endpoint}?select=name&limit=1", headers=read_headers, timeout=30)
    if smoke.status_code >= 300:
        return {
            "ok": False,
            "error": f"Supabase Tabelle nicht erreichbar ({smoke.status_code}). Prüfe ifl_device_catalog + RLS.",
        }

    # Tabelle leeren (id ist BIGSERIAL → alle Zeilen; zuverlässiger als nur name)
    delete_res = requests.delete(
        f"{endpoint}?id=not.is.null",
        headers={**write_headers, "Prefer": "return=minimal"},
        timeout=120,
    )
    if delete_res.status_code >= 300:
        return {
            "ok": False,
            "error": f"Löschen in Supabase fehlgeschlagen ({delete_res.status_code}). Prüfe RLS.",
        }

    def _rows_without_extended_cols(src: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [{k: v for k, v in r.items() if k not in ("target_key", "session_type")} for r in src]

    def _attempt_insert(src: list[dict[str, Any]]) -> tuple[bool, int, str | None]:
        n = 0
        for chunk in _chunked(src, chunk_size):
            ins = requests.post(
                endpoint,
                headers={
                    **write_headers,
                    "Content-Type": "application/json",
                    "Prefer": "return=minimal",
                },
                json=chunk,
                timeout=60,
            )
            if ins.status_code >= 300:
                return False, n, ins.text[:400] if ins.text else ""
            n += len(chunk)
        return True, n, None

    inserted = 0
    used_extended = True
    ok_ins, inserted, err_txt = _attempt_insert(rows)
    if not ok_ins:
        requests.delete(
            f"{endpoint}?id=not.is.null",
            headers={**write_headers, "Prefer": "return=minimal"},
            timeout=120,
        )
        slim = _rows_without_extended_cols(rows)
        ok_ins, inserted, err_txt = _attempt_insert(slim)
        used_extended = False
    if not ok_ins:
        return {
            "ok": False,
            "error": f"Insert fehlgeschlagen. Zuletzt: {err_txt or 'ohne Text'} — prüfe Migration docs/supabase_migrations/ifl_device_catalog_target_key.sql und RLS.",
        }

    verify = requests.get(
        f"{endpoint}?select=id",
        headers={**read_headers, "Prefer": "count=exact"},
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
        "catalog_extended_cols": used_extended,
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

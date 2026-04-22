from fastapi import APIRouter, Request, Depends, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse, JSONResponse
from sqlalchemy.orm import Session
from pathlib import Path
from urllib.parse import quote
import asyncio
import os
import shutil

from app.database import get_db, DB_PATH
from app.services.withings_import import import_withings_csv, import_garmin_csv
from app.services.blood_pdf_parser import scan_folder_for_new_pdfs
from app.services.bulk_import import import_all, import_withings_all, import_garmin_all
from app.models import DailyLog, Gym80Device
from app.services.gym80_catalog_import import import_gym80_sql
from app.services.extra_catalog_import import import_extra_catalogs
from app.services.supabase_catalog_sync import sync_catalog_to_supabase, get_supabase_catalog_status
from app.services.training_equipment_seed import seed_training_equipment
from app.services.catalog_targets import infer_stype, infer_target, target_to_key
from app.services.catalog_overrides import load_override_rules, resolve_catalog_row_targets
import sqlite3
import subprocess
import datetime
import base64
import requests


def _norm_filter_text(value: str) -> str:
    return (
        (value or "")
        .strip()
        .lower()
        .replace("ä", "a")
        .replace("ö", "o")
        .replace("ü", "u")
        .replace("ß", "ss")
    )


def _tokenize_query(value: str) -> list[str]:
    norm = _norm_filter_text(value)
    return [p for p in norm.split(" ") if p]


TARGET_ALIASES: dict[str, tuple[str, ...]] = {
    "brust": ("brust", "chest", "pector", "pec", "butterfly", "press"),
    "rucken": ("rucken", "ruecken", "back", "lat", "row", "pull"),
    "beine": ("beine", "bein", "legs", "leg", "quad", "ham", "calf"),
    "glutes": ("glutes", "glute", "gesass", "gess", "gesa"),
    "schulter": ("schulter", "shoulder", "delt"),
    "arme": ("arme", "arm", "bizeps", "biceps", "trizeps", "triceps", "curl"),
    "core": ("core", "bauch", "abs", "abdominal", "oblique", "rumpf"),
    "cardio": ("cardio", "laufband", "treadmill", "bike", "cycle", "rower", "climbmill"),
}


def _target_tokens(target: str) -> list[str]:
    norm = _norm_filter_text(target)
    if not norm:
        return []
    return list(TARGET_ALIASES.get(norm, (norm,)))


def _sqlite_table_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    except sqlite3.DatabaseError:
        return set()
    return {str(r[1]).lower() for r in rows}


def _blob_to_data_url(blob_value) -> str | None:
    if not blob_value:
        return None
    try:
        payload = base64.b64encode(bytes(blob_value)).decode("ascii")
    except Exception:
        return None
    # gym80 source files are webp; browsers also tolerate generic octet-stream fallback.
    return f"data:image/webp;base64,{payload}"


def _redirect(path: str, msg: str) -> RedirectResponse:
    return RedirectResponse(f"{path}?msg={quote(msg)}", status_code=303)

router = APIRouter()
BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")
IMPORTS_DIR = BASE_DIR / "data" / "Imports"

WITHINGS_DIR = BASE_DIR / "Imports" / "Withings"
GARMIN_DIR   = BASE_DIR / "Imports" / "Garmin" / "DI_CONNECT" / "DI-Connect-Wellness"
CREDS_FILE   = BASE_DIR / ".withings_credentials.json"


DEFAULT_GYM80_SQL = Path.home() / "Downloads" / "gym80_devices.sql"
DEFAULT_MATRIX_STRENGTH_SQL = Path.home() / "Downloads" / "matrix_strength.sql"
DEFAULT_MATRIX_CARDIO_SQL = Path.home() / "Downloads" / "matrix_cardio.sql"
DEFAULT_EGYM_SQL = Path.home() / "Downloads" / "egym_deutsch.sql"
FINAL_GYM80_SQL = Path.home() / "Downloads" / "Gym80" / "gym80_devices_final.sql"
FINAL_MATRIX_STRENGTH_SQL = Path.home() / "Downloads" / "matrix_strength_final_complete.sql"
FINAL_MATRIX_CARDIO_SQL = Path.home() / "Downloads" / "matrix_cardio_final_complete.sql"
FINAL_EGYM_SQL = Path.home() / "Downloads" / "egym_deutsch_final_download.sql"


@router.get("/", include_in_schema=False)
async def imports_overview(request: Request, msg: str = None, db: Session = Depends(get_db)):
    from app.services.api_fetch import _load_last_fetch, _load_last_withings_backfill, _is_garmin_blocked
    from datetime import timedelta, date
    garmin_configured   = bool(os.getenv("GARMIN_EMAIL") and os.getenv("GARMIN_PASSWORD"))
    withings_configured = CREDS_FILE.exists()
    supabase_catalog_configured = bool(os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_ANON_KEY"))
    supabase_catalog_status = get_supabase_catalog_status(
        (os.getenv("SUPABASE_URL") or "").strip(),
        (os.getenv("SUPABASE_ANON_KEY") or "").strip(),
    )

    total_logs = db.query(DailyLog).count()
    last_fetch = _load_last_fetch()
    garmin_blocked_until = _is_garmin_blocked()

    return templates.TemplateResponse("imports.html", {
        "request": request,
        "msg": msg,
        "garmin_configured":    garmin_configured,
        "withings_configured":  withings_configured,
        "withings_ok": WITHINGS_DIR.exists(),
        "garmin_ok":   GARMIN_DIR.exists(),
        "supabase_catalog_configured": supabase_catalog_configured,
        "supabase_catalog_status": supabase_catalog_status,
        "total_logs":  total_logs,
        "withings_dir": str(WITHINGS_DIR),
        "garmin_dir":   str(GARMIN_DIR),
        "last_fetch":   last_fetch,
        "last_fetch_next": last_fetch + timedelta(days=1) if last_fetch else None,
        "last_withings_backfill": _load_last_withings_backfill(),
        "today": date.today(),
        "garmin_blocked_until": garmin_blocked_until,
    })


# ─── API-Abruf (Garmin + Withings live) ──────────────────────────────────────

@router.post("/fetch-now", include_in_schema=False)
async def fetch_now(db: Session = Depends(get_db)):
    from app.services.api_fetch import fetch_missing
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: fetch_missing(db))
    except Exception as exc:
        return _redirect("/import/", f"Unerwarteter Fehler: {exc}")

    fetched   = results.get("fetched_dates", [])
    skipped   = results.get("skipped", 0)
    g_errors  = results.get("garmin_errors", [])
    w_errors  = results.get("withings_errors", [])
    all_errors = g_errors + w_errors

    parts = []
    if fetched:
        parts.append(f"Abgerufen: {len(fetched)} Tag(e) ({', '.join(fetched)})")
    if skipped:
        parts.append(f"{skipped} Tag(e) bereits aktuell")
    if all_errors:
        parts.append(f"Fehler: {all_errors[0]}")
    if not parts:
        parts.append("Keine Daten abgerufen")

    return _redirect("/import/", " | ".join(parts))


@router.post("/clear-garmin-block", include_in_schema=False)
async def clear_garmin_block_route():
    from app.services.api_fetch import clear_garmin_block
    clear_garmin_block()
    return _redirect("/import/", "Garmin-Sperre manuell aufgehoben – Login wird beim nächsten Abruf versucht")


@router.post("/fetch-garmin", include_in_schema=False)
async def fetch_garmin_today(db: Session = Depends(get_db)):
    from app.services.api_fetch import fetch_garmin_only
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: fetch_garmin_only(db))
    except Exception as exc:
        return _redirect("/import/", f"Garmin Fehler: {exc}")
    if result.get("error"):
        return _redirect("/import/", f"Garmin Fehler: {result['error']}")
    n = len(result.get("fields", []))
    return _redirect("/import/", f"Garmin: {n} Felder für {result.get('date','')} abgerufen")


@router.post("/fetch-withings", include_in_schema=False)
async def fetch_withings_today(db: Session = Depends(get_db)):
    from app.services.api_fetch import fetch_withings_only
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: fetch_withings_only(db))
    except Exception as exc:
        return _redirect("/import/", f"Withings Fehler: {exc}")
    if result.get("error"):
        return _redirect("/import/", f"Withings Fehler: {result['error']}")
    n = len(result.get("fields", []))
    return _redirect("/import/", f"Withings: {n} Felder für {result.get('date','')} abgerufen")


# ─── Bulk-Import (CSV/JSON aus Ordnern) ───────────────────────────────────────

@router.post("/alles", include_in_schema=False)
async def import_everything(db: Session = Depends(get_db)):
    try:
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(None, lambda: import_all(db))
    except Exception as exc:
        return _redirect("/import/", f"Fehler: {exc}")

    w = results.get("withings", {})
    g = results.get("garmin", {})
    total = results.get("total_daily_logs", 0)
    parts = []
    if isinstance(w, dict) and not w.get("error"):
        parts.append(f"Withings: {w.get('weight',0)} Gewichts-Einträge")
    if isinstance(g, dict) and not g.get("error"):
        parts.append(f"Garmin: {g.get('health',0)} Gesundheits-Tage + {g.get('sleep',0)} Schlaf-Tage")
    errors = (w.get("errors", []) if isinstance(w, dict) else []) + \
             (g.get("errors", []) if isinstance(g, dict) else [])
    parts.append(f"Gesamt {total} Logs")
    if errors:
        parts.append(f"{len(errors)} Fehler (Server-Log)")
    return _redirect("/import/", " | ".join(parts))


@router.post("/withings-bulk", include_in_schema=False)
async def import_withings_bulk(db: Session = Depends(get_db)):
    try:
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, lambda: import_withings_all(db))
    except Exception as exc:
        return _redirect("/import/", f"Fehler: {exc}")
    if stats.get("error"):
        return _redirect("/import/", f"Fehler: {stats['error']}")
    msg = f"Withings: {stats.get('weight',0)} Gewichts-Einträge, {stats.get('steps',0)} Schritte-Tage, {stats.get('sleep',0)} Schlaf-Nächte"
    return _redirect("/import/", msg)


@router.post("/garmin-bulk", include_in_schema=False)
async def import_garmin_bulk(db: Session = Depends(get_db)):
    try:
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, lambda: import_garmin_all(db))
    except Exception as exc:
        return _redirect("/import/", f"Fehler: {exc}")
    if stats.get("error"):
        return _redirect("/import/", f"Fehler: {stats['error']}")
    msg = f"Garmin: {stats.get('health',0)} Gesundheitstage + {stats.get('sleep',0)} Schlaftage"
    return _redirect("/import/", msg)


# ─── Einzeldatei-Upload (Fallback) ───────────────────────────────────────────

@router.post("/withings", include_in_schema=False)
async def import_withings_single(file: UploadFile = File(...), db: Session = Depends(get_db)):
    dest = IMPORTS_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    stats = import_withings_csv(dest, db)
    msg = f"Withings (Einzeldatei): {stats.get('imported',0)} neu, {stats.get('updated',0)} aktualisiert"
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/garmin", include_in_schema=False)
async def import_garmin_single(file: UploadFile = File(...), db: Session = Depends(get_db)):
    dest = IMPORTS_DIR / file.filename
    with open(dest, "wb") as f:
        shutil.copyfileobj(file.file, f)
    stats = import_garmin_csv(dest, db)
    msg = f"Garmin (Einzeldatei): {stats.get('imported',0)} neu, {stats.get('updated',0)} aktualisiert"
    if stats.get("error"):
        msg = f"Fehler: {stats['error']}"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


# ─── Apple Health Import ─────────────────────────────────────────────────────

@router.post("/apple-health")
async def import_apple_health(request: Request, db: Session = Depends(get_db)):
    """
    UPSERT eines Tagesdatensatzes aus Apple Health.
    Erwartet JSON: { date, calories, protein_g, carbs_g, fat_g,
                     body_mass_kg, body_fat_pct, steps, resting_hr, sleep_min }
    Felder die fehlen oder None sind werden übersprungen.
    """
    from app.services.apple_health_import import upsert_apple_health_day
    try:
        payload = await request.json()
    except Exception:
        return JSONResponse({"error": "Ungültiges JSON"}, status_code=400)
    try:
        result = upsert_apple_health_day(payload, db)
        return JSONResponse(result, status_code=200)
    except ValueError as exc:
        return JSONResponse({"error": str(exc)}, status_code=422)
    except Exception as exc:
        return JSONResponse({"error": f"Interner Fehler: {exc}"}, status_code=500)


@router.post("/withings-backfill", include_in_schema=False)
async def withings_backfill(db: Session = Depends(get_db)):
    """Holt alle Withings-Daten der letzten 90 Tage (ein API-Call) → befüllt PWV etc."""
    from app.services.api_fetch import fetch_withings_range
    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, lambda: fetch_withings_range(db, days=90))
    except Exception as exc:
        return _redirect("/import/", f"Fehler: {exc}")
    if result.get("error"):
        return _redirect("/import/", f"Fehler: {result['error']}")
    n = result.get("total", 0)
    dates = result.get("updated_dates", [])
    msg = f"Withings Backfill: {n} Tage aktualisiert"
    if dates:
        msg += f" ({dates[0]} – {dates[-1]})"
    return _redirect("/import/", msg)


@router.get("/debug-withings", include_in_schema=False)
async def debug_withings():
    """Zeigt rohe Withings API-Antwort für die letzten 30 Tage."""
    from app.services.api_fetch import _get_valid_withings_token
    import requests, time
    from datetime import datetime, timedelta, date as date_cls
    from fastapi.responses import JSONResponse

    access_token, err = _get_valid_withings_token()
    if err:
        return JSONResponse({"error": err})

    end_ts   = int(time.time())
    start_ts = int((datetime.now() - timedelta(days=30)).timestamp())

    resp = requests.post(
        "https://wbsapi.withings.net/measure",
        headers={"Authorization": f"Bearer {access_token}"},
        data={
            "action": "getmeas",
            "startdate": start_ts,
            "enddate": end_ts,
            "meastypes": "1,4,6,8,9,10,11,76,77,91",
        },
        timeout=15,
    )
    data = resp.json()

    # Alle zurückgegebenen Typen zusammenfassen
    types_found = {}
    for grp in (data.get("body") or {}).get("measuregrps", []):
        d = grp.get("date", 0)
        date_str = datetime.fromtimestamp(d).strftime("%Y-%m-%d") if d else "?"
        for m in grp.get("measures", []):
            t = m["type"]
            val = m["value"] * (10 ** m["unit"])
            types_found.setdefault(t, []).append({"date": date_str, "value": round(val, 4)})

    return JSONResponse({"status": data.get("status"), "types_found": types_found})


@router.post("/fetch-all", include_in_schema=False)
async def fetch_all(db: Session = Depends(get_db)):
    """Garmin + Withings in einem Schritt."""
    from app.services.api_fetch import fetch_missing
    parts = []
    loop = asyncio.get_event_loop()
    try:
        gw = await loop.run_in_executor(None, lambda: fetch_missing(db))
        fetched = gw.get("fetched_dates", [])
        if fetched:
            parts.append(f"Garmin+Withings: {len(fetched)} Tag(e)")
        elif not gw.get("garmin_errors") and not gw.get("withings_errors"):
            parts.append("Garmin+Withings: aktuell")
        errors = gw.get("garmin_errors", []) + gw.get("withings_errors", [])
        if errors:
            parts.append(f"Fehler: {errors[0]}")
    except Exception as exc:
        parts.append(f"Fehler: {exc}")
    return _redirect("/import/", " | ".join(parts) or "Kein Ergebnis")


@router.post("/blutbilder-scan", include_in_schema=False)
async def scan_blutbilder(db: Session = Depends(get_db)):
    new_panels = scan_folder_for_new_pdfs(db)
    msg = f"{len(new_panels)} neue Blutbild-PDF(s) geparst"
    return RedirectResponse(f"/import/?msg={msg}", status_code=303)


@router.post("/gym80-catalog-import", include_in_schema=False)
async def import_gym80_catalog(db: Session = Depends(get_db)):
    """
    Importiert die finale gym80 SQL-Datei in die lokale SQLite-DB.
    Standardpfad: ~/Downloads/gym80_devices.sql
    """
    result = import_gym80_sql(DB_PATH, DEFAULT_GYM80_SQL)
    if not result.get("ok"):
        return _redirect("/import/", f"gym80 Katalog Fehler: {result.get('error', 'Unbekannt')}")
    return _redirect(
        "/import/",
        f"gym80 Katalog importiert: vorher {result['before']} · nachher {result['after']} · neu {result['imported']}",
    )


@router.get("/catalog/gym80", include_in_schema=False)
async def gym80_catalog_api(
    q: str = "",
    category: str = "",
    serie: str = "",
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    """Liefert Zusatzpool-Einträge aus der lokalen DB für Katalogsuche."""
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    query = db.query(Gym80Device)
    if category:
        query = query.filter(Gym80Device.category.ilike(f"%{category}%"))
    if serie:
        query = query.filter(Gym80Device.serie.ilike(f"%{serie}%"))
    if q:
        term = f"%{q}%"
        query = query.filter(
            Gym80Device.model.ilike(term)
            | Gym80Device.muscle_groups.ilike(term)
            | Gym80Device.notes.ilike(term)
        )

    total = query.count()
    rows = (
        query.order_by(Gym80Device.model.asc())
        .offset(offset)
        .limit(limit)
        .all()
    )
    return {
        "total": total,
        "offset": offset,
        "limit": limit,
        "items": [
            {
                "id": r.id,
                "category": r.category,
                "serie": r.serie,
                "model": r.model,
                "product_url": r.product_url,
                "image_url": r.image_url,
                "muscle_groups": r.muscle_groups,
                "notes": r.notes,
            }
            for r in rows
        ],
    }


@router.post("/catalog/import-extra", include_in_schema=False)
async def import_extra_catalogs_route():
    result = import_extra_catalogs(
        DB_PATH,
        DEFAULT_GYM80_SQL,
        DEFAULT_MATRIX_STRENGTH_SQL,
        DEFAULT_MATRIX_CARDIO_SQL,
        DEFAULT_EGYM_SQL,
    )
    if not result.get("ok"):
        return _redirect("/import/", f"Zusatzpool Import Fehler: {result.get('error', 'Unbekannt')}")
    before = result["before"]
    after = result["after"]
    msg = (
        f"Zusatzpool importiert | "
        f"gym80: {before['gym80_devices']}→{after['gym80_devices']} | "
        f"matrix_strength: {before['matrix_strength_devices']}→{after['matrix_strength_devices']} | "
        f"matrix_cardio: {before['matrix_cardio_devices']}→{after['matrix_cardio_devices']} | "
        f"egym: {before['egym_devices']}→{after['egym_devices']}"
    )
    return _redirect("/import/", msg)


@router.post("/catalog/import-final-replace-and-push", include_in_schema=False)
async def import_final_replace_and_push_route():
    result = import_extra_catalogs(
        DB_PATH,
        FINAL_GYM80_SQL,
        FINAL_MATRIX_STRENGTH_SQL,
        FINAL_MATRIX_CARDIO_SQL,
        FINAL_EGYM_SQL,
        replace_existing=True,
    )
    if not result.get("ok"):
        return _redirect("/import/", f"Final-Import Fehler: {result.get('error', 'Unbekannt')}")

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip()
    supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or "").strip()
    push_result = sync_catalog_to_supabase(DB_PATH, supabase_url, supabase_anon_key)
    if not push_result.get("ok"):
        return _redirect(
            "/import/",
            (
                "Final-Import OK, Supabase Push Fehler: "
                f"{push_result.get('error', 'Unbekannt')} | "
                f"Lokal gym80: {result['after'].get('gym80_devices', 0)}, "
                f"matrix_strength: {result['after'].get('matrix_strength_devices', 0)}, "
                f"matrix_cardio: {result['after'].get('matrix_cardio_devices', 0)}, "
                f"egym: {result['after'].get('egym_devices', 0)}"
            ),
        )

    return _redirect(
        "/import/",
        (
            "Final-Import + Supabase Push OK | "
            f"gym80: {result['after'].get('gym80_devices', 0)} | "
            f"matrix_strength: {result['after'].get('matrix_strength_devices', 0)} | "
            f"matrix_cardio: {result['after'].get('matrix_cardio_devices', 0)} | "
            f"egym: {result['after'].get('egym_devices', 0)} | "
            f"Supabase rows: {push_result.get('supabase_rows', 0)}"
        ),
    )


@router.post("/catalog/push-supabase", include_in_schema=False)
async def push_catalog_to_supabase_route():
    supabase_url = (os.getenv("SUPABASE_URL") or "").strip()
    supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or "").strip()
    result = sync_catalog_to_supabase(DB_PATH, supabase_url, supabase_anon_key)
    if not result.get("ok"):
        return _redirect("/import/", f"Supabase Katalog-Upload Fehler: {result.get('error', 'Unbekannt')}")
    return _redirect(
        "/import/",
        (
            f"Supabase Katalog-Upload OK | "
            f"Lokal vorbereitet: {result['prepared_local_rows']} | "
            f"Hochgeladen: {result['inserted_rows']} | "
            f"Supabase gesamt: {result['supabase_rows']}"
        ),
    )


@router.get("/catalog/sanity", include_in_schema=False)
async def catalog_sanity():
    """
    1-Klick Diagnose:
    - lokale gym80 Rows / image_blob vorhanden
    - Supabase-Katalog total / Rows mit img
    """
    local_total = 0
    local_blob_count = 0
    local_url_count = 0
    local_without_image = 0

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cols = _sqlite_table_columns(conn, "gym80_devices")
        if "model" in cols:
            local_total = conn.execute("SELECT COUNT(*) FROM gym80_devices").fetchone()[0]
        if "image_blob" in cols:
            local_blob_count = conn.execute(
                "SELECT COUNT(*) FROM gym80_devices WHERE image_blob IS NOT NULL AND length(image_blob) > 0"
            ).fetchone()[0]
        if "image_url" in cols:
            local_url_count = conn.execute(
                "SELECT COUNT(*) FROM gym80_devices WHERE image_url IS NOT NULL AND trim(image_url) <> ''"
            ).fetchone()[0]
        local_without_image = max(local_total - max(local_blob_count, local_url_count), 0)
    finally:
        conn.close()

    supabase_url = (os.getenv("SUPABASE_URL") or "").strip().rstrip("/")
    supabase_anon_key = (os.getenv("SUPABASE_ANON_KEY") or "").strip()
    if not supabase_url or not supabase_anon_key:
        return {
            "ok": False,
            "error": "SUPABASE_URL oder SUPABASE_ANON_KEY fehlt.",
            "local": {
                "gym80_total": local_total,
                "gym80_with_blob": local_blob_count,
                "gym80_with_image_url": local_url_count,
                "gym80_without_image": local_without_image,
            },
            "supabase": None,
        }

    endpoint = f"{supabase_url}/rest/v1/ifl_device_catalog"
    headers = {
        "apikey": supabase_anon_key,
        "Authorization": f"Bearer {supabase_anon_key}",
        "Prefer": "count=exact",
    }

    try:
        # total rows
        total_res = requests.get(f"{endpoint}?select=id&limit=1", headers=headers, timeout=30)
        if total_res.status_code >= 300:
            return {
                "ok": False,
                "error": f"Supabase total-Abfrage fehlgeschlagen ({total_res.status_code}).",
                "local": {
                    "gym80_total": local_total,
                    "gym80_with_blob": local_blob_count,
                    "gym80_with_image_url": local_url_count,
                    "gym80_without_image": local_without_image,
                },
                "supabase": None,
            }
        total_count = 0
        total_range = total_res.headers.get("Content-Range", "")
        if "/" in total_range:
            try:
                total_count = int(total_range.split("/")[-1])
            except Exception:
                total_count = 0

        # rows with img
        img_res = requests.get(
            f"{endpoint}?select=id&img=not.is.null&limit=1", headers=headers, timeout=30
        )
        if img_res.status_code >= 300:
            return {
                "ok": False,
                "error": f"Supabase img-Abfrage fehlgeschlagen ({img_res.status_code}).",
                "local": {
                    "gym80_total": local_total,
                    "gym80_with_blob": local_blob_count,
                    "gym80_with_image_url": local_url_count,
                    "gym80_without_image": local_without_image,
                },
                "supabase": {"catalog_total": total_count},
            }
        img_count = 0
        img_range = img_res.headers.get("Content-Range", "")
        if "/" in img_range:
            try:
                img_count = int(img_range.split("/")[-1])
            except Exception:
                img_count = 0

        return {
            "ok": True,
            "local": {
                "gym80_total": local_total,
                "gym80_with_blob": local_blob_count,
                "gym80_with_image_url": local_url_count,
                "gym80_without_image": local_without_image,
            },
            "supabase": {
                "catalog_total": total_count,
                "catalog_with_img": img_count,
            },
            "hint": "Wenn gym80_with_blob hoch ist, aber catalog_with_img niedrig: /import/catalog/push-supabase erneut ausführen.",
        }
    except Exception as exc:
        return {
            "ok": False,
            "error": f"Sanity-Check fehlgeschlagen: {exc}",
            "local": {
                "gym80_total": local_total,
                "gym80_with_blob": local_blob_count,
                "gym80_with_image_url": local_url_count,
                "gym80_without_image": local_without_image,
            },
            "supabase": None,
        }


@router.post("/catalog/seed-top-equipment", include_in_schema=False)
async def seed_top_equipment_route():
    result = seed_training_equipment(DB_PATH)
    if not result.get("ok"):
        return _redirect("/import/", f"Top-Equipment Seed Fehler: {result.get('error', 'Unbekannt')}")
    return _redirect(
        "/import/",
        f"Top-Equipment in DB: {result['before']}→{result['after']} (neu: {result['inserted']})",
    )


@router.get("/catalog/search", include_in_schema=False)
async def catalog_search_api(
    brand: str = "",
    q: str = "",
    target: str = "",
    session_type: str = "",
    limit: int = 100,
    offset: int = 0,
):
    """
    Einheitliche Zusatzpool-Suche über gym80 + matrix strength + matrix cardio + egym.
    """
    limit = max(1, min(limit, 500))
    offset = max(0, offset)
    b = (brand or "").strip().lower()
    t = (target or "").strip().lower()
    t_tokens = _target_tokens(t)
    st = (session_type or "").strip().lower()
    qq = (q or "").strip().lower()
    q_tokens = _tokenize_query(qq)

    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = []
        if b in ("", "gym80"):
            gym80_cols = _sqlite_table_columns(conn, "gym80_devices")
            has_image_blob = "image_blob" in gym80_cols
            img_blob_select = ", image_blob" if has_image_blob else ", NULL AS image_blob"
            rows.extend(
                conn.execute(
                    "SELECT model, serie, image_url, muscle_groups, product_url, category, notes, '' as brand, 'gym80' as src"
                    f"{img_blob_select} FROM gym80_devices"
                ).fetchall()
            )
        if b in ("", "matrix"):
            rows.extend(
                conn.execute(
                    "SELECT model, serie, image_url, muscle_groups, product_url, category, notes, '' as brand, 'matrix_strength' as src FROM matrix_strength_devices"
                ).fetchall()
            )
            rows.extend(
                conn.execute(
                    "SELECT model, serie, image_url, cardio_type as muscle_groups, product_url, category, notes, '' as brand, 'matrix_cardio' as src FROM matrix_cardio_devices"
                ).fetchall()
            )
        if b in ("", "egym"):
            rows.extend(
                conn.execute(
                    "SELECT model, series as serie, image_url, muscle_groups, product_url, category, notes, '' as brand, 'egym' as src FROM egym_devices"
                ).fetchall()
            )

        rules = load_override_rules(conn)

        norm = []
        for r in rows:
            model = (r["model"] or "").strip()
            serie = (r["serie"] or "").strip()
            mg = (r["muscle_groups"] or "").strip()
            category_raw = (r["category"] or "").strip()
            category = category_raw.lower()
            src = (r["src"] or "").strip().lower() if "src" in r.keys() else ""

            brand_name = (r["brand"] or "").strip() if "brand" in r.keys() else ""
            if not brand_name:
                brand_name = "gym80" if "pure kraft" in serie.lower() or category in ("plate_loaded", "weight_stack", "outdoor") else ("eGym" if "egym" in serie.lower() else "Matrix")

            target_name, group_resolved = resolve_catalog_row_targets(
                brand_name, model, serie, mg, category_raw, rules, infer_target_fn=infer_target
            )
            full_text = _norm_filter_text(
                f"{model} {serie} {mg} {category} {(r['notes'] or '')}"
            )
            s_type = infer_stype(target_name, is_matrix_cardio_row=(src == "matrix_cardio"))

            if b and b not in brand_name.lower():
                continue
            if qq and qq not in full_text and not all(tok in full_text for tok in q_tokens):
                continue
            if t_tokens:
                target_blob = _norm_filter_text(
                    f"{target_name} {group_resolved} {mg} {category_raw} {model}"
                )
                if not any(tok in target_blob for tok in t_tokens):
                    continue
            if st and st != s_type:
                continue

            norm.append({
                "brand": brand_name,
                "name": model,
                "type": "Digital" if brand_name == "eGym" else ("Cardio" if src == "matrix_cardio" or target_name == "Cardio" else "Machine"),
                "target": target_name,
                "cat": target_name,
                "sType": s_type,
                "targetKey": target_to_key(target_name),
                "sessionType": s_type,
                "group": group_resolved,
                "art": None,
                "img": (
                    (r["image_url"] or "").strip()
                    or _blob_to_data_url(r["image_blob"] if "image_blob" in r.keys() else None)
                ),
                "product_url": r["product_url"],
                "notes": r["notes"],
            })

        # Dedupe by brand+name
        dedup = {}
        for item in norm:
            k = f"{item['brand'].lower()}|{item['name'].lower()}"
            if k not in dedup or (not dedup[k]["img"] and item["img"]):
                dedup[k] = item
        def _query_score(item: dict) -> int:
            if not q_tokens and not qq:
                return 0
            hay = _norm_filter_text(
                f"{item.get('name', '')} {item.get('brand', '')} {item.get('target', '')} {item.get('group', '')}"
            )
            name_hay = _norm_filter_text(item.get("name", ""))
            target_hay = _norm_filter_text(item.get("target", ""))
            score = 0
            for tok in q_tokens:
                if tok and tok in hay:
                    score += 8
                    if tok in name_hay:
                        score += 12
                    if tok in target_hay:
                        score += 4
            if qq:
                if qq in name_hay:
                    score += 25
                elif qq in hay:
                    score += 10
            return score

        items = sorted(
            dedup.values(),
            key=lambda x: (-_query_score(x), x["name"].lower()),
        )

        total = len(items)
        sliced = items[offset: offset + limit]
        return {"total": total, "offset": offset, "limit": limit, "items": sliced}
    finally:
        conn.close()


# ── GitHub Sync ──────────────────────────────────────────────────────────────

@router.post("/import/github-sync")
async def github_sync():
    """git add + commit + push → GitHub. Requires GITHUB_TOKEN in .env and remote configured."""
    repo_dir = BASE_DIR
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if not token:
        return JSONResponse({"ok": False, "error": "GITHUB_TOKEN nicht gesetzt"}, status_code=400)

    def run(cmd, **kwargs):
        return subprocess.run(
            cmd, capture_output=True, text=True, cwd=str(repo_dir), **kwargs
        )

    # Detect current remote URL and inject token
    r = run(["git", "remote", "get-url", "origin"])
    raw_url = r.stdout.strip()
    if not raw_url:
        return JSONResponse({"ok": False, "error": "Kein git remote 'origin' konfiguriert"}, status_code=400)

    # Build authenticated URL
    if "@github.com" in raw_url:
        # Already has credentials – replace them
        auth_url = "https://boekermarco-sketch:" + token + "@github.com/" + raw_url.split("github.com/", 1)[1]
    else:
        auth_url = raw_url.replace("https://", f"https://boekermarco-sketch:{token}@")

    # Stage all changes
    run(["git", "add", "-A"])

    # Commit (skip if nothing staged)
    stamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    commit = run(["git", "commit", "-m", f"Auto-Sync {stamp}"])
    committed = commit.returncode == 0

    # Push
    push = run(["git", "push", "--force", auth_url, "HEAD:main"])
    if push.returncode != 0:
        return JSONResponse({
            "ok": False,
            "committed": committed,
            "error": push.stderr.strip() or push.stdout.strip(),
        }, status_code=500)

    return JSONResponse({
        "ok": True,
        "committed": committed,
        "message": f"Gepusht ({'neuer Commit' if committed else 'keine Änderungen, nur Push'}) · {stamp}",
    })

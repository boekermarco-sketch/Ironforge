"""
Supabase Storage Bucket Setup + Bild-Upload
- Erstellt Bucket 'device-images' (public)
- Laedt alle Matrix + eGym Bilder hoch
- Aktualisiert image_url in SQLite (matrix_strength/cardio/egym_devices)
- Aktualisiert img in Supabase ifl_device_catalog
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import requests

# ─────────────────────────────────────────────
# Config
# ─────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
DB_PATH    = BASE_DIR / "fitness.db"
STATIC_DIR = BASE_DIR / "static" / "img" / "catalog"

def _load_env():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip()
        if k:
            os.environ[k] = v

_load_env()

SUPABASE_URL      = os.environ.get("SUPABASE_URL", "")
SERVICE_ROLE_KEY  = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "")
ANON_KEY          = os.environ.get("SUPABASE_ANON_KEY", "")
BUCKET            = "device-images"


def _svc_headers(extra: dict | None = None) -> dict:
    h = {
        "apikey":        SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SERVICE_ROLE_KEY}",
    }
    if extra:
        h.update(extra)
    return h


def _anon_headers(extra: dict | None = None) -> dict:
    h = {
        "apikey":        ANON_KEY,
        "Authorization": f"Bearer {ANON_KEY}",
    }
    if extra:
        h.update(extra)
    return h


# ─────────────────────────────────────────────
# 1. Bucket erstellen
# ─────────────────────────────────────────────
def ensure_bucket() -> bool:
    url = f"{SUPABASE_URL}/storage/v1/bucket"

    # Pruefen ob Bucket existiert
    r = requests.get(url, headers=_svc_headers(), timeout=10)
    if r.status_code == 200:
        existing = [b.get("name") for b in r.json()]
        if BUCKET in existing:
            print(f"  Bucket '{BUCKET}' existiert bereits.")
            return True

    # Erstellen
    r = requests.post(
        url,
        headers=_svc_headers({"Content-Type": "application/json"}),
        json={"id": BUCKET, "name": BUCKET, "public": True},
        timeout=10,
    )
    if r.status_code in (200, 201):
        print(f"  Bucket '{BUCKET}' erstellt (public).")
        return True

    print(f"  Bucket-Fehler: {r.status_code} {r.text[:200]}")
    return False


# ─────────────────────────────────────────────
# 2. Bilder hochladen
# ─────────────────────────────────────────────
def upload_image(local_path: Path, storage_path: str) -> str | None:
    """Laedt ein Bild hoch, gibt die public URL zurueck."""
    content_type = "image/jpeg"
    upload_url = f"{SUPABASE_URL}/storage/v1/object/{BUCKET}/{storage_path}"

    # Upsert: vorhandene Datei ueberschreiben
    r = requests.post(
        upload_url,
        headers=_svc_headers({
            "Content-Type":    content_type,
            "x-upsert":        "true",
            "Cache-Control":   "3600",
        }),
        data=local_path.read_bytes(),
        timeout=30,
    )
    if r.status_code in (200, 201):
        public_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{storage_path}"
        return public_url

    print(f"  Upload-Fehler {local_path.name}: {r.status_code} {r.text[:100]}")
    return None


def upload_all_images() -> dict[str, str]:
    """Gibt {lokaler_pfad_key: public_url} zurueck."""
    url_map: dict[str, str] = {}

    matrix_dir = STATIC_DIR / "matrix"
    egym_dir   = STATIC_DIR / "egym"

    total = 0
    ok    = 0

    for img in sorted(matrix_dir.glob("*.jpg")):
        storage_path = f"matrix/{img.name}"
        local_key    = f"/static/img/catalog/matrix/{img.name}"
        pub_url = upload_image(img, storage_path)
        if pub_url:
            url_map[local_key] = pub_url
            ok += 1
        total += 1

    for img in sorted(egym_dir.glob("*.jpeg")):
        storage_path = f"egym/{img.name}"
        local_key    = f"/static/img/catalog/egym/{img.name}"
        pub_url = upload_image(img, storage_path)
        if pub_url:
            url_map[local_key] = pub_url
            ok += 1
        total += 1

    print(f"  Upload: {ok}/{total} Bilder hochgeladen")
    return url_map


# ─────────────────────────────────────────────
# 3. SQLite aktualisieren
# ─────────────────────────────────────────────
def update_sqlite(url_map: dict[str, str]) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    updated = 0
    try:
        for local_key, pub_url in url_map.items():
            for table in ("matrix_strength_devices", "matrix_cardio_devices"):
                c = conn.execute(
                    f"UPDATE {table} SET image_url = ? WHERE image_url = ?",
                    (pub_url, local_key)
                )
                updated += c.rowcount

            c = conn.execute(
                "UPDATE egym_devices SET image_url = ? WHERE image_url = ?",
                (pub_url, local_key)
            )
            updated += c.rowcount

        conn.commit()
        print(f"  SQLite: {updated} Zeilen aktualisiert")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 4. Supabase ifl_device_catalog aktualisieren
# ─────────────────────────────────────────────
def update_supabase_catalog(url_map: dict[str, str]) -> None:
    if not SUPABASE_URL or not ANON_KEY:
        print("  Supabase: keine Credentials")
        return

    headers = _anon_headers({"Content-Type": "application/json"})
    updated = 0

    # Alle Eintraege mit alten lokalen Pfaden holen
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/ifl_device_catalog"
        "?select=id,img&img=like./static/img/catalog/%&limit=500",
        headers=_anon_headers(),
        timeout=15,
    )
    if r.status_code != 200:
        print(f"  Supabase Catalog lesen: {r.status_code}")
        return

    entries = r.json()
    for entry in entries:
        old_img = entry.get("img")
        new_img = url_map.get(old_img)
        if not new_img:
            continue

        patch = requests.patch(
            f"{SUPABASE_URL}/rest/v1/ifl_device_catalog?id=eq.{entry['id']}",
            headers=headers,
            json={"img": new_img},
            timeout=10,
        )
        if patch.status_code in (200, 204):
            updated += 1
        else:
            print(f"  PATCH Fehler id={entry['id']}: {patch.status_code}")

    print(f"  Supabase Catalog: {updated} URLs aktualisiert")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n--- Supabase Storage Upload ---\n")

    if not SERVICE_ROLE_KEY:
        print("Fehler: SUPABASE_SERVICE_ROLE_KEY fehlt in .env")
        raise SystemExit(1)

    print("[1] Bucket sicherstellen...")
    if not ensure_bucket():
        raise SystemExit(1)

    print("[2] Bilder hochladen...")
    url_map = upload_all_images()

    if not url_map:
        print("Keine Bilder hochgeladen - Abbruch.")
        raise SystemExit(1)

    print("[3] SQLite URLs aktualisieren...")
    update_sqlite(url_map)

    print("[4] Supabase Catalog URLs aktualisieren...")
    update_supabase_catalog(url_map)

    print("\nFertig.\n")
    print("Beispiel-URL:")
    for k, v in list(url_map.items())[:2]:
        print(f"  {k}")
        print(f"  -> {v}")

"""
gym80 Bilder-Upload zu Supabase Storage + DB-Update

Ablauf:
1. DB: externe URLs auf lokale assets/ korrigieren
2. Supabase: Bucket 'fitness-assets' pruefen / anlegen
3. Alle 150 Bilder aus static/assets/gym80/ hochladen
4. DB: image_url auf Supabase-Public-URL setzen
"""

import os
import sqlite3
import mimetypes
from pathlib import Path

SUPABASE_URL = "https://dbamakgjtrgqplufwlca.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRiYW1ha2dqdHJncXBsdWZ3bGNhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzYwODY0MzMsImV4cCI6MjA5MTY2MjQzM30."
    "nXRtfxvgqg0Ccgo2FRtFYGrBjx-voNfQOpDCAzK_EME"
)
BUCKET = "fitness-assets"
STORAGE_PREFIX = "gym80"

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "fitness.db"
IMAGES_DIR = BASE_DIR / "static" / "assets" / "gym80"

PUBLIC_BASE = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET}/{STORAGE_PREFIX}"


def fix_external_urls(conn):
    """Ersetzt externe gym80.de-URLs durch lokale asset-Pfade."""
    cur = conn.cursor()
    cur.execute("SELECT id, model, image_url FROM gym80_devices WHERE image_url LIKE 'http%'")
    rows = cur.fetchall()
    fixed = 0
    for id_, model, url in rows:
        num = model.split()[0]
        for candidate in [f"{num}.webp", f"{num}n.webp"]:
            if (IMAGES_DIR / candidate).exists():
                cur.execute(
                    "UPDATE gym80_devices SET image_url = ? WHERE id = ?",
                    (f"assets/gym80/{candidate}", id_)
                )
                print(f"  Gefixt: {model[:45]} -> assets/gym80/{candidate}")
                fixed += 1
                break
    conn.commit()
    print(f"Externe URLs korrigiert: {fixed}/9\n")


def ensure_bucket(client):
    """Prueft Bucket-Erreichbarkeit per Test-Upload eines Dummy-Bytes."""
    try:
        # Anon key darf list_buckets nicht – Test per Mini-Upload
        client.storage.from_(BUCKET).upload(
            path=f"{STORAGE_PREFIX}/.keep",
            file=b"",
            file_options={"content-type": "text/plain", "x-upsert": "true"}
        )
        print(f"Bucket '{BUCKET}' erreichbar.")
        return True
    except Exception as e:
        err = str(e)
        if "already exists" in err.lower() or "duplicate" in err.lower():
            print(f"Bucket '{BUCKET}' erreichbar.")
            return True
        print(f"FEHLER Bucket nicht erreichbar: {e}")
        print("Bitte sicherstellen, dass Bucket 'fitness-assets' im Supabase Dashboard als Public angelegt ist.")
        return False


def upload_images(client):
    """Laedt alle .webp aus IMAGES_DIR nach Supabase hoch."""
    files = sorted(IMAGES_DIR.glob("*.webp"))
    print(f"Starte Upload: {len(files)} Bilder...\n")
    ok = 0
    skip = 0
    errors = []

    for fpath in files:
        dest = f"{STORAGE_PREFIX}/{fpath.name}"
        try:
            with open(fpath, "rb") as f:
                data = f.read()
            # Versuche Upload (upsert=True = Ueberschreiben erlaubt)
            client.storage.from_(BUCKET).upload(
                path=dest,
                file=data,
                file_options={
                    "content-type": "image/webp",
                    "x-upsert": "true",
                }
            )
            ok += 1
            if ok % 20 == 0:
                print(f"  {ok}/{len(files)} hochgeladen...")
        except Exception as e:
            err_str = str(e)
            if "Duplicate" in err_str or "already exists" in err_str.lower():
                skip += 1
            else:
                errors.append((fpath.name, err_str))

    print(f"\nUpload fertig: {ok} neu, {skip} bereits vorhanden, {len(errors)} Fehler")
    for fname, err in errors:
        print(f"  FEHLER {fname}: {err}")
    return len(errors) == 0


def update_db_urls(conn):
    """Setzt image_url in gym80_devices auf Supabase-Public-URLs."""
    cur = conn.cursor()
    cur.execute("SELECT id, image_url FROM gym80_devices WHERE image_url LIKE 'assets/gym80/%'")
    rows = cur.fetchall()

    updated = 0
    missing = []
    for id_, local_path in rows:
        fname = local_path.replace("assets/gym80/", "")
        supabase_url = f"{PUBLIC_BASE}/{fname}"
        cur.execute("UPDATE gym80_devices SET image_url = ? WHERE id = ?", (supabase_url, id_))
        updated += 1

    conn.commit()
    print(f"\nDB aktualisiert: {updated} Eintraege auf Supabase-URLs gesetzt")
    if missing:
        for m in missing:
            print(f"  FEHLT: {m}")


def verify(conn):
    """Kurze Verifikation des Ergebnisses."""
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM gym80_devices WHERE image_url LIKE 'http%'")
    total_http = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM gym80_devices WHERE image_url LIKE '%supabase%'")
    supabase_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM gym80_devices WHERE image_url LIKE 'assets/%'")
    local_count = cur.fetchone()[0]
    print(f"\nVerifikation:")
    print(f"  Supabase-URLs: {supabase_count}")
    print(f"  Noch lokale assets/: {local_count}")
    print(f"  Externe (gym80.de etc.): {total_http - supabase_count}")


def main():
    from supabase import create_client
    client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

    conn = sqlite3.connect(DB_PATH)

    print("=== Schritt 1: Externe URLs korrigieren ===")
    fix_external_urls(conn)

    print("=== Schritt 2: Supabase Bucket pruefen ===")
    if not ensure_bucket(client):
        print("Abbruch - Bucket nicht verfuegbar.")
        conn.close()
        return

    print("\n=== Schritt 3: Bilder hochladen ===")
    upload_ok = upload_images(client)

    print("\n=== Schritt 4: DB auf Supabase-URLs aktualisieren ===")
    update_db_urls(conn)

    verify(conn)
    conn.close()
    print("\nFertig.")


if __name__ == "__main__":
    main()

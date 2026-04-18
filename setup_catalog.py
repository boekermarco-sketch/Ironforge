"""
Katalog-Setup: Matrix + eGym
- Extrahiert Bilder aus matrix_geraete_mit_bildern.xlsx
- Kopiert eGym-Bilder
- Speichert alles unter static/img/catalog/
- Schreibt SQLite-DB (matrix_strength_devices, matrix_cardio_devices, egym_devices)
- Pusht in Supabase ifl_device_catalog (anon key)
"""
from __future__ import annotations

import os
import re
import shutil
import sqlite3
import zipfile
import xml.etree.ElementTree as ET
from pathlib import Path

import requests

from app.services.catalog_targets import infer_target

# ─────────────────────────────────────────────
# Pfade
# ─────────────────────────────────────────────
BASE_DIR    = Path(__file__).parent
DB_PATH     = BASE_DIR / "fitness.db"
STATIC_DIR  = BASE_DIR / "static" / "img" / "catalog"
MATRIX_IMG  = STATIC_DIR / "matrix"
EGYM_IMG    = STATIC_DIR / "egym"

XLSX_PATH   = Path.home() / "Downloads" / "matrix_export" / "matrix_geraete_mit_bildern.xlsx"
EGYM_DUMP   = Path.home() / "Downloads" / "egym_dump"
EGYM_SQL    = EGYM_DUMP / "egym_deutsch_final_download.sql"

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY", "")

# Versuche .env zu lesen falls env-vars nicht gesetzt
def _load_env():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, val = line.partition("=")
        key = key.strip()
        val = val.strip()
        if key and key not in os.environ:
            os.environ[key] = val

_load_env()
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_ANON_KEY", "")


# ─────────────────────────────────────────────
# Matrix: Deutsche Namen (Reihenfolge = xlsx-Zeilen)
# ─────────────────────────────────────────────
# Jeder Eintrag: (de_name, kategorie, muskelgruppe, session_type, filename_slug)
MATRIX_DEVICES = [
    # Cardio
    ("Laufband",                  "cardio",    "Ausdauer",                          "cardio", "laufband_1"),
    ("Laufband Pro",              "cardio",    "Ausdauer",                          "cardio", "laufband_2"),
    ("Crosstrainer",              "cardio",    "Ganzkörper, Ausdauer",              "cardio", "crosstrainer"),
    ("Stepper",                   "cardio",    "Beine, Gesäß, Ausdauer",            "cardio", "stepper"),
    ("Fahrrad-Ergometer",         "cardio",    "Beine, Ausdauer",                   "cardio", "fahrrad_ergometer_1"),
    ("Fahrrad-Ergometer Pro",     "cardio",    "Beine, Ausdauer",                   "cardio", "fahrrad_ergometer_2"),
    # Strength
    ("Lat Pulldown",              "strength",  "Latissimus, Bizeps, oberer Rücken", "pull",   "lat_pulldown"),
    ("Curl Maschine",             "strength",  "Bizeps",                            "push",   "curl_maschine"),
    ("Brustpresse",               "strength",  "Brust, Trizeps, vordere Schulter",  "push",   "brustpresse"),
    ("Bauchtrainer",              "strength",  "Bauch, Core",                       "free",   "bauchtrainer"),
    ("Rumpfrotation",             "strength",  "Core, schräge Bauchmuskulatur",     "free",   "rumpfrotation"),
    ("Beinpresse",                "strength",  "Quadrizeps, Gesäß, Hamstrings",     "legs",   "beinpresse_1"),
    ("Beinstrecker",              "strength",  "Quadrizeps",                        "legs",   "beinstrecker"),
    ("Beinbeuger",                "strength",  "Hamstrings",                        "legs",   "beinbeuger"),
    ("Multi-Station 1",           "strength",  "Ganzkörper",                        "push",   "multi_station_1"),
    ("Multi-Station 2",           "strength",  "Ganzkörper",                        "push",   "multi_station_2"),
    ("Multi-Station 3",           "strength",  "Ganzkörper",                        "push",   "multi_station_3"),
    ("Multi-Station 4",           "strength",  "Ganzkörper",                        "push",   "multi_station_4"),
    ("Multi-Station 5",           "strength",  "Ganzkörper",                        "push",   "multi_station_5"),
    ("Kabelzug",                  "strength",  "Ganzkörper, Rücken, Schulter",      "pull",   "kabelzug"),
    ("Multi-Station 6",           "strength",  "Ganzkörper",                        "push",   "multi_station_6"),
    ("Verstellbare Hantelbank",   "strength",  "Brust, Schulter, Trizeps",          "push",   "hantelbank_verstellbar_1"),
    ("Verstellbare Hantelbank 2", "strength",  "Brust, Schulter, Trizeps",          "push",   "hantelbank_verstellbar_2"),
    ("Hantelbank",                "strength",  "Brust, Schulter, Trizeps",          "push",   "hantelbank"),
    ("Verstellbare Hantelbank 3", "strength",  "Brust, Schulter, Trizeps",          "push",   "hantelbank_verstellbar_3"),
    ("Schulterpresse",            "strength",  "Schultern, Trizeps",                "push",   "schulterpresse"),
    ("Verstellbare Hantelbank 4", "strength",  "Brust, Schulter, Trizeps",          "push",   "hantelbank_verstellbar_4"),
    ("Verstellbare Hantelbank 5", "strength",  "Brust, Schulter, Trizeps",          "push",   "hantelbank_verstellbar_5"),
    ("Beinpresse Pro",            "strength",  "Quadrizeps, Gesäß, Hamstrings",     "legs",   "beinpresse_2"),
    ("Wadenmaschine",             "strength",  "Waden",                             "legs",   "wadenmaschine"),
    ("Kniebeugen Maschine",       "strength",  "Quadrizeps, Gesäß, Hamstrings",     "legs",   "kniebeugen_1"),
    ("Kniebeugen Maschine Pro",   "strength",  "Quadrizeps, Gesäß, Hamstrings",     "legs",   "kniebeugen_2"),
    ("Multi-Station 7",           "strength",  "Ganzkörper",                        "pull",   "multi_station_7"),
    ("Multi-Station 8",           "strength",  "Ganzkörper",                        "pull",   "multi_station_8"),
    ("Multi-Station 9",           "strength",  "Ganzkörper",                        "pull",   "multi_station_9"),
    ("Multi-Station 10",          "strength",  "Ganzkörper",                        "pull",   "multi_station_10"),
    ("Rudergerät",                "cardio",    "Rücken, Arme, Ausdauer",            "pull",   "rudergeraet"),
]

# eGym: code → (de_name, muskelgruppe, session_type, bild_datei_ohne_ext)
EGYM_DEVICES = [
    ("M1",  "Beinstrecker",      "Quadrizeps",                           "legs",  "Beinstrecker"),
    ("M2",  "Bauchtrainer",      "Bauch, Core",                          "free",  "Bauchtrainer"),
    ("M3",  "Rückenstrecker",    "unterer Rücken, Erector spinae",       "pull",  "Rückenstrecker"),
    ("M4",  "Beinbeuger",        "Hamstrings",                           "legs",  "Beinbeuger"),
    ("M5",  "Brustpresse",       "Brust, Trizeps, vordere Schulter",     "push",  "Brustpresse"),
    ("M6",  "Ruderzug",          "Rückenmitte, Latissimus, Bizeps",      "pull",  "Latzug"),
    ("M7",  "Lat Pulldown",      "Latissimus, oberer Rücken, Bizeps",    "pull",  "Latzug"),
    ("M8",  "Gluteus",           "Gesäß",                                "legs",  "Glutaeus Hip Thrust"),
    ("M9",  "Beinpresse",        "Quadrizeps, Gesäß, Hamstrings",        "legs",  "Beinpresse"),
    ("M10", "Abduktor",          "Abduktoren, Gesäß",                    "legs",  "Abduktor"),
    ("M11", "Adduktor",          "Adduktoren",                           "legs",  "Adduktor"),
    ("M12", "Rumpfrotation",     "Core, schräge Bauchmuskulatur",        "free",  "Seitbeuger"),
    ("M13", "Butterfly",         "Brust, vordere Schulter",              "push",  "Butterfly"),
    ("M14", "Reverse Butterfly", "hintere Schulter, oberer Rücken",      "pull",  "Butterfly Reverse"),
    ("M15", "Bizeps Curl",       "Bizeps",                               "push",  "Bizepscurl"),
    ("M16", "Wadenpresse",       "Waden",                                "legs",  None),
    ("M17", "Schulterpresse",    "Schultern, Trizeps",                   "push",  "Schulterpresse"),
    ("M18", "Trizeps",           "Trizeps",                              "push",  "Trizeps-Dips"),
    ("M19", "Hip Thrust",        "Gesäß, hintere Kette",                 "legs",  "Glutaeus Hip Thrust"),
    ("M20", "Kniebeuge",         "Quadrizeps, Gesäß, Hamstrings, Core",  "legs",  "Kniebeugen"),
]


# ─────────────────────────────────────────────
# 1. Bilder extrahieren
# ─────────────────────────────────────────────
def extract_matrix_images() -> dict[str, str]:
    """Extrahiert Bilder aus xlsx, benennt nach slug, gibt {xlsx_name: lokaler_pfad} zurück."""
    MATRIX_IMG.mkdir(parents=True, exist_ok=True)

    if not XLSX_PATH.exists():
        print(f"  XLSX nicht gefunden: {XLSX_PATH}")
        return {}

    # Mapping xlsx-intern rId → imageN.jpeg
    with zipfile.ZipFile(str(XLSX_PATH), "r") as z:
        drawing  = z.read("xl/drawings/drawing1.xml").decode("utf-8")
        rels_raw = z.read("xl/drawings/_rels/drawing1.xml.rels").decode("utf-8")

        rels_map = dict(re.findall(
            r'Id="(rId\d+)"[^>]*Target="\.\./media/(image\d+\.jpeg)"', rels_raw
        ))
        anchors = re.findall(
            r'<xdr:from><xdr:col>(\d+)</xdr:col><xdr:colOff>\d+</xdr:colOff>'
            r'<xdr:row>(\d+)</xdr:row>.*?r:embed="(rId\d+)"',
            drawing, re.DOTALL
        )
        # row (0-based) → image file
        row_to_img: dict[int, str] = {}
        for col, row, rid in anchors:
            img_name = rels_map.get(rid)
            if img_name:
                row_to_img[int(row) + 1] = img_name   # 1-based

        # Ziehe die Bilder in Reihenfolge der Anker (row 4, 6, 9 ... = erste bis letzte Zeile)
        ordered_imgs = [img for _, img in sorted(row_to_img.items())]

        saved: dict[str, str] = {}
        for i, (_, img_file) in enumerate(zip(MATRIX_DEVICES, ordered_imgs)):
            slug = MATRIX_DEVICES[i][4]
            dest = MATRIX_IMG / f"{slug}.jpg"
            if not dest.exists():
                data = z.read(f"xl/media/{img_file}")
                dest.write_bytes(data)
            saved[img_file] = f"/static/img/catalog/matrix/{slug}.jpg"

    print(f"  Matrix: {len(saved)} Bilder gespeichert")
    return saved


def copy_egym_images() -> dict[str, str]:
    """Kopiert eGym-JPEGs in den static-Ordner, gibt {bild_basis: lokaler_pfad} zurück."""
    EGYM_IMG.mkdir(parents=True, exist_ok=True)
    saved: dict[str, str] = {}
    for src in EGYM_DUMP.glob("*.jpeg"):
        dest = EGYM_IMG / src.name.lower().replace(" ", "_")
        if not dest.exists():
            shutil.copy2(str(src), str(dest))
        saved[src.stem] = f"/static/img/catalog/egym/{dest.name}"
    print(f"  eGym: {len(saved)} Bilder gespeichert")
    return saved


# ─────────────────────────────────────────────
# 2. SQLite befüllen
# ─────────────────────────────────────────────
MATRIX_STRENGTH_DDL = """
CREATE TABLE IF NOT EXISTS matrix_strength_devices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     VARCHAR(50)  NOT NULL,
    serie        VARCHAR(100),
    model        VARCHAR(255) NOT NULL,
    product_url  TEXT,
    image_url    TEXT,
    muscle_groups TEXT,
    notes        TEXT
);
"""

MATRIX_CARDIO_DDL = """
CREATE TABLE IF NOT EXISTS matrix_cardio_devices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     VARCHAR(50)  NOT NULL,
    serie        VARCHAR(100),
    model        VARCHAR(255) NOT NULL,
    product_url  TEXT,
    image_url    TEXT,
    cardio_type  VARCHAR(100),
    features     TEXT,
    notes        TEXT
);
"""

EGYM_DDL = """
CREATE TABLE IF NOT EXISTS egym_devices (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    category     VARCHAR(50)  NOT NULL,
    series       VARCHAR(100),
    code         VARCHAR(20),
    model        VARCHAR(255) NOT NULL,
    product_url  TEXT,
    image_url    TEXT,
    muscle_groups TEXT,
    notes        TEXT
);
"""

def populate_sqlite(matrix_img_map: dict, egym_img_map: dict) -> None:
    conn = sqlite3.connect(str(DB_PATH))
    try:
        conn.executescript(MATRIX_STRENGTH_DDL + MATRIX_CARDIO_DDL + EGYM_DDL)

        # Leere bestehende Matrix + eGym Einträge
        conn.execute("DELETE FROM matrix_strength_devices")
        conn.execute("DELETE FROM matrix_cardio_devices")
        conn.execute("DELETE FROM egym_devices")

        # Matrix: aufteilen in strength / cardio
        for i, (de_name, kat, muscle, stype, slug) in enumerate(MATRIX_DEVICES):
            img_url = f"/static/img/catalog/matrix/{slug}.jpg"
            if kat == "cardio":
                conn.execute(
                    "INSERT INTO matrix_cardio_devices (category, serie, model, image_url, cardio_type, notes)"
                    " VALUES (?,?,?,?,?,?)",
                    ("cardio", "Matrix", de_name, img_url, muscle, "Matrix Gerät")
                )
            else:
                conn.execute(
                    "INSERT INTO matrix_strength_devices (category, serie, model, image_url, muscle_groups, notes)"
                    " VALUES (?,?,?,?,?,?)",
                    ("strength", "Matrix", de_name, img_url, muscle, "Matrix Gerät")
                )

        # eGym
        for code, de_name, muscle, stype, img_stem in EGYM_DEVICES:
            img_url = None
            if img_stem:
                # Suche nach passendem Bild (case-insensitive)
                slug = img_stem.lower().replace(" ", "_") + ".jpeg"
                candidate = egym_img_map.get(img_stem)
                if not candidate:
                    for k, v in egym_img_map.items():
                        if k.lower() == img_stem.lower():
                            candidate = v
                            break
                img_url = candidate
            conn.execute(
                "INSERT INTO egym_devices (category, series, code, model, image_url, muscle_groups, notes)"
                " VALUES (?,?,?,?,?,?,?)",
                ("smartstrength", "EGYM Smart Strength", code, de_name, img_url, muscle, "eGym Smart Strength")
            )

        conn.commit()

        ms = conn.execute("SELECT COUNT(*) FROM matrix_strength_devices").fetchone()[0]
        mc = conn.execute("SELECT COUNT(*) FROM matrix_cardio_devices").fetchone()[0]
        eg = conn.execute("SELECT COUNT(*) FROM egym_devices").fetchone()[0]
        print(f"  SQLite: matrix_strength={ms}, matrix_cardio={mc}, egym={eg}")
    finally:
        conn.close()


# ─────────────────────────────────────────────
# 3. Supabase ifl_device_catalog befüllen
# ─────────────────────────────────────────────
def push_to_supabase() -> None:
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("  Supabase: keine Credentials → übersprungen")
        return

    headers = {
        "apikey":        SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type":  "application/json",
        "Prefer":        "resolution=merge-duplicates",
    }

    # Prüfe ob Tabelle existiert
    r = requests.get(
        f"{SUPABASE_URL}/rest/v1/ifl_device_catalog?limit=1",
        headers=headers, timeout=10
    )
    if r.status_code == 404 or (r.status_code == 200 and "ifl_device_catalog" in r.text and "relation" in r.text.lower()):
        print("  Supabase: ifl_device_catalog existiert nicht → bitte in Supabase SQL Editor anlegen:")
        print("""
  CREATE TABLE IF NOT EXISTS ifl_device_catalog (
    id             BIGSERIAL PRIMARY KEY,
    brand          TEXT,
    name           TEXT,
    type           TEXT,
    target         TEXT,
    cat            TEXT,
    s_type         TEXT,
    session_type   TEXT,
    target_key     TEXT,
    movement_group TEXT,
    art            TEXT,
    img            TEXT,
    UNIQUE (brand, name, target)
  );
  ALTER TABLE ifl_device_catalog ENABLE ROW LEVEL SECURITY;
  CREATE POLICY "anon read"   ON ifl_device_catalog FOR SELECT TO anon USING (true);
  CREATE POLICY "anon insert" ON ifl_device_catalog FOR INSERT TO anon WITH CHECK (true);
  CREATE POLICY "anon update" ON ifl_device_catalog FOR UPDATE TO anon USING (true);
        """)
        return

    rows = []

    # Matrix Strength
    for de_name, kat, muscle, stype, slug in MATRIX_DEVICES:
        target = infer_target(f"{de_name} {muscle} {kat}")
        rows.append({
            "brand":          "Matrix",
            "name":           de_name,
            "type":           "Cardio" if kat == "cardio" else "Machine",
            "target":         target,
            "cat":            target,
            "s_type":         stype,
            "movement_group": "Matrix",
            "art":            None,
            "img":            f"/static/img/catalog/matrix/{slug}.jpg",
        })

    # eGym
    for code, de_name, muscle, stype, img_stem in EGYM_DEVICES:
        target = infer_target(f"{de_name} {muscle} smartstrength")
        img = None
        if img_stem:
            slug = img_stem.lower().replace(" ", "_") + ".jpeg"
            img = f"/static/img/catalog/egym/{slug}"
        rows.append({
            "brand":          "eGym",
            "name":           de_name,
            "type":           "Digital",
            "target":         target,
            "cat":            target,
            "s_type":         stype,
            "movement_group": "EGYM Smart Strength",
            "art":            None,
            "img":            img,
        })

    # Deduplizieren
    seen: set[str] = set()
    dedup = []
    for row in rows:
        k = f"{row['brand']}|{row['name']}|{row['target']}"
        if k not in seen:
            seen.add(k)
            dedup.append(row)

    # In 100er-Chunks senden
    ok = 0
    for i in range(0, len(dedup), 100):
        chunk = dedup[i:i+100]
        resp = requests.post(
            f"{SUPABASE_URL}/rest/v1/ifl_device_catalog",
            headers=headers, json=chunk, timeout=30
        )
        if resp.status_code in (200, 201):
            ok += len(chunk)
        else:
            print(f"  Supabase Fehler: {resp.status_code} {resp.text[:200]}")

    print(f"  Supabase: {ok}/{len(dedup)} Eintraege gepusht -> ifl_device_catalog")


# ─────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("\n--- Ironforge Katalog Setup ---\n")

    print("[1] Matrix-Bilder extrahieren...")
    matrix_map = extract_matrix_images()

    print("[2] eGym-Bilder kopieren...")
    egym_map = copy_egym_images()

    print("[3] SQLite befüllen...")
    populate_sqlite(matrix_map, egym_map)

    print("[4] Supabase befüllen...")
    push_to_supabase()

    print("\nFertig.\n")

"""
Befüllt ifl_device_catalog in Supabase aus der lokalen SQLite-DB.
Quellen: gym80_devices, matrix_strength_devices, matrix_cardio_devices, egym_devices
Wird einmalig ausgeführt; service_role Key wird danach aus dem Script entfernt.
"""

import sqlite3
from pathlib import Path

SUPABASE_URL = "https://dbamakgjtrgqplufwlca.supabase.co"
SERVICE_ROLE_KEY = "PASTE_SERVICE_ROLE_KEY_HERE"

DB_PATH = Path(__file__).parent / "fitness.db"
TABLE = "ifl_device_catalog"


def infer_target(model: str, muscle_groups: str, category: str) -> str:
    v = f"{model} {muscle_groups} {category}".lower()
    if any(x in v for x in ["lat", "row", "rueck", "rücken", "back", "latissimus", "pulldown", "pull-over", "pullover", "rear"]):
        return "Rücken"
    if any(x in v for x in ["chest", "brust", "press", "butterfly", "pec", "crossover", "fly", "decline", "incline"]):
        return "Brust"
    if any(x in v for x in ["leg", "quad", "hamstring", "bein", "glute", "calf", "wade", "squat", "kniebeuge", "abdukt", "addukt", "hip", "lunge"]):
        return "Beine"
    if any(x in v for x in ["shoulder", "schulter", "delt", "seithebe", "lateral raise"]):
        return "Schulter"
    if any(x in v for x in ["bicep", "tricep", "bizeps", "trizeps", "curl", "dip", "arm"]):
        return "Arme"
    if any(x in v for x in ["core", "abdominal", "bauch", "crunch", "sit-up", "hyperext", "back ext"]):
        return "Core"
    if any(x in v for x in ["cardio", "treadmill", "bike", "elliptical", "rower", "stepper", "climb"]):
        return "Cardio"
    return "Brust"


def infer_stype(target: str) -> str:
    t = target.lower()
    if "rücken" in t or "back" in t:
        return "pull"
    if "beine" in t or "leg" in t:
        return "legs"
    if "cardio" in t:
        return "cardio"
    if "core" in t:
        return "free"
    return "push"


def infer_type(category: str, src: str) -> str:
    if src == "egym":
        return "Digital"
    if src == "matrix_cardio":
        return "Cardio"
    cat = (category or "").lower()
    if "plate" in cat:
        return "Plate"
    return "Block"


def extract_art(model: str) -> str:
    """Extrahiert Produktnummer aus Modellname (z.B. '4023 45 DEGREE...' -> '4023')."""
    parts = model.strip().split()
    if parts and (parts[0].isdigit() or (parts[0][:-1].isdigit() and parts[0][-1].lower() == 'n')):
        return parts[0].lower()
    return ""


def infer_movement_group(model: str, target: str) -> str:
    v = f"{model} {target}".lower()
    if any(x in v for x in ["lat pulldown", "latziehen", "lat pull"]): return "Latpresse"
    if any(x in v for x in ["row", "rudern", "rowing"]): return "Rudern"
    if any(x in v for x in ["pullover", "pull-over"]): return "Pullover"
    if any(x in v for x in ["leg press", "beinpresse"]): return "Beinpresse"
    if any(x in v for x in ["leg extension", "beinstrecker"]): return "Quad Isolation"
    if any(x in v for x in ["leg curl", "beinbeuger"]): return "Hamstring"
    if any(x in v for x in ["squat", "kniebeuge"]): return "Kniebeuge"
    if any(x in v for x in ["calf", "waden"]): return "Waden"
    if any(x in v for x in ["abdukt"]): return "Abduktoren"
    if any(x in v for x in ["addukt"]): return "Adduktoren"
    if any(x in v for x in ["hip", "hüfte", "glute"]): return "Hüfte"
    if any(x in v for x in ["shoulder press", "schulterdrück"]): return "Schulterdrücken"
    if any(x in v for x in ["lateral raise", "seithebe"]): return "Schulter Isolation"
    if any(x in v for x in ["chest press", "brustpresse", "bench press", "drückbank"]): return "Brustpresse flach"
    if any(x in v for x in ["incline", "schrägbank"]): return "Brustpresse schräg"
    if any(x in v for x in ["butterfly", "fly", "crossover"]): return "Brust Isolation"
    if any(x in v for x in ["bicep", "bizeps", "curl"]): return "Bizeps"
    if any(x in v for x in ["tricep", "trizeps", "dip"]): return "Trizeps"
    if any(x in v for x in ["core", "crunch", "bauch"]): return "Core"
    return ""


def load_devices(conn: sqlite3.Connection) -> list[dict]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    devices = []

    # gym80
    cur.execute("SELECT model, serie, image_url, muscle_groups, product_url, category, notes FROM gym80_devices")
    for r in cur.fetchall():
        model = (r["model"] or "").strip()
        muscle = (r["muscle_groups"] or "").replace("\ufffd", "ü").replace("Ges\ufffd", "Gesäß")
        category = (r["category"] or "").strip().lower().strip("('\"")
        serie = (r["serie"] or "").strip()
        target = infer_target(model, muscle, category)
        art = extract_art(model)
        devices.append({
            "brand": "gym80",
            "name": model,
            "type": infer_type(category, "gym80"),
            "target": target,
            "cat": target,
            "s_type": infer_stype(target),
            "movement_group": infer_movement_group(model, target),
            "art": art,
            "img": r["image_url"] or None,
            "product_url": r["product_url"] or None,
            "notes": f"{serie} – {r['notes']}".strip(" –") if r["notes"] else serie or None,
        })

    # matrix strength
    cur.execute("SELECT model, serie, image_url, muscle_groups, product_url, category, notes FROM matrix_strength_devices")
    for r in cur.fetchall():
        model = (r["model"] or "").strip()
        muscle = (r["muscle_groups"] or "")
        category = (r["category"] or "").strip().lower()
        target = infer_target(model, muscle, category)
        devices.append({
            "brand": "Matrix",
            "name": model,
            "type": infer_type(category, "matrix_strength"),
            "target": target,
            "cat": target,
            "s_type": infer_stype(target),
            "movement_group": infer_movement_group(model, target),
            "art": extract_art(model),
            "img": r["image_url"] or None,
            "product_url": r["product_url"] or None,
            "notes": r["notes"] or None,
        })

    # matrix cardio
    cur.execute("SELECT model, serie, image_url, cardio_type as muscle_groups, product_url, category, notes FROM matrix_cardio_devices")
    for r in cur.fetchall():
        model = (r["model"] or "").strip()
        devices.append({
            "brand": "Matrix",
            "name": model,
            "type": "Cardio",
            "target": "Cardio",
            "cat": "Cardio",
            "s_type": "cardio",
            "movement_group": model.lower().split()[0].capitalize() if model else "",
            "art": None,
            "img": None,  # matrix cardio URLs sind Katalogseiten, keine Bilder
            "product_url": r["product_url"] or None,
            "notes": r["notes"] or None,
        })

    # egym
    cur.execute("SELECT model, series as serie, image_url, muscle_groups, product_url, category, notes FROM egym_devices")
    for r in cur.fetchall():
        model = (r["model"] or "").strip()
        muscle = (r["muscle_groups"] or "")
        target = infer_target(model, muscle, "")
        devices.append({
            "brand": "eGym",
            "name": model,
            "type": "Digital",
            "target": target,
            "cat": target,
            "s_type": infer_stype(target),
            "movement_group": infer_movement_group(model, target),
            "art": None,
            "img": None,  # egym URLs sind Produktseiten, keine Bilder
            "product_url": r["product_url"] or None,
            "notes": r["notes"] or None,
        })

    return devices


def main():
    from supabase import create_client

    client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)
    conn = sqlite3.connect(DB_PATH)

    print("Lade Geräte aus lokaler DB...")
    devices = load_devices(conn)
    conn.close()
    print(f"Gefunden: {len(devices)} Geräte total")
    by_brand = {}
    for d in devices:
        by_brand[d["brand"]] = by_brand.get(d["brand"], 0) + 1
    for b, n in sorted(by_brand.items()):
        print(f"  {b}: {n}")

    # Ermittle vorhandene Spalten per Probe-Fetch
    probe = client.table(TABLE).select("*").limit(1).execute()
    if probe.data:
        existing_cols = set(probe.data[0].keys())
    else:
        # Tabelle leer – versuche mit allen Feldern, fange Fehler ab
        existing_cols = {"brand","name","type","target","cat","s_type","movement_group","art","img","product_url","notes"}
    print(f"Vorhandene Spalten: {sorted(existing_cols)}")

    # Felder auf sichere Kern-Spalten beschränken (notes ignorieren wegen Schema-Cache)
    # Nur Original-Spalten (product_url/notes noch nicht im PostgREST-Cache)
    SAFE_COLS = {"brand","name","type","target","cat","s_type","movement_group","art","img"}
    def filter_fields(d):
        return {k: v for k, v in d.items() if k in SAFE_COLS}

    print(f"\nLeere ifl_device_catalog und befülle neu...")
    client.table(TABLE).delete().neq("id", 0).execute()

    # Batch-Insert
    batch_size = 200
    inserted = 0
    for i in range(0, len(devices), batch_size):
        batch = [filter_fields(d) for d in devices[i:i + batch_size]]
        client.table(TABLE).insert(batch).execute()
        inserted += len(batch)
        print(f"  {inserted}/{len(devices)} eingefügt...")

    print(f"\nFertig: {inserted} Einträge in ifl_device_catalog")

    # Kurze Verifikation
    count = client.table(TABLE).select("id", count="exact").execute()
    print(f"Supabase-Zählung: {count.count} Einträge")


if __name__ == "__main__":
    main()

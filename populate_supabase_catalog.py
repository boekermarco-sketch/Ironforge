"""
Befüllt ifl_device_catalog in Supabase aus der lokalen SQLite-DB.
Nutzt dieselbe Zeilenlogik wie app.services.supabase_catalog_sync (infer_target + Overrides).

Aufruf: Service-Role-Key eintragen, dann: python populate_supabase_catalog.py
"""

from pathlib import Path

from app.services.supabase_catalog_sync import read_sqlite_device_catalog_rows

SUPABASE_URL = "https://dbamakgjtrgqplufwlca.supabase.co"
SERVICE_ROLE_KEY = "PASTE_SERVICE_ROLE_KEY_HERE"

DB_PATH = Path(__file__).parent / "fitness.db"
TABLE = "ifl_device_catalog"


def main():
    from supabase import create_client

    client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

    print("Lade Geräte aus lokaler DB (gleiche Logik wie supabase_catalog_sync)…")
    devices = read_sqlite_device_catalog_rows(DB_PATH)
    print(f"Gefunden: {len(devices)} Geräte total")
    by_brand = {}
    for d in devices:
        by_brand[d["brand"]] = by_brand.get(d["brand"], 0) + 1
    for b, n in sorted(by_brand.items()):
        print(f"  {b}: {n}")

    probe = client.table(TABLE).select("*").limit(1).execute()
    core = {
        "brand",
        "name",
        "type",
        "target",
        "cat",
        "s_type",
        "movement_group",
        "art",
        "img",
        "target_key",
        "session_type",
    }
    if probe.data:
        existing_cols = set(probe.data[0].keys())
    else:
        existing_cols = set(core)
    print(f"Vorhandene Spalten: {sorted(existing_cols)}")
    safe_cols = {k for k in core if k in existing_cols}

    def filter_fields(d):
        return {k: v for k, v in d.items() if k in safe_cols}

    print("\nLeere ifl_device_catalog und befülle neu…")
    client.table(TABLE).delete().neq("id", 0).execute()

    batch_size = 200
    inserted = 0
    for i in range(0, len(devices), batch_size):
        batch = [filter_fields(d) for d in devices[i : i + batch_size]]
        client.table(TABLE).insert(batch).execute()
        inserted += len(batch)
        print(f"  {inserted}/{len(devices)} eingefügt…")

    print(f"\nFertig: {inserted} Einträge in ifl_device_catalog")
    count = client.table(TABLE).select("id", count="exact").execute()
    print(f"Supabase-Zählung: {count.count} Einträge")


if __name__ == "__main__":
    main()

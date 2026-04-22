from __future__ import annotations

import sqlite3
from pathlib import Path
import sys

from dotenv import load_dotenv

import os


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from app.services.supabase_catalog_sync import sync_catalog_to_supabase

    load_dotenv(root / ".env")

    bundle_db = root / "SQL" / "catalog_bundle_preview.db"
    gym80_db = root / "SQL" / "gym80" / "gym80_devices_final.db"
    matrix_strength_sql = root / "SQL" / "Matrix" / "matrix_strength_final_complete.sql"
    matrix_cardio_sql = root / "SQL" / "Matrix" / "matrix_cardio_final_complete.sql"
    egym_sql = root / "SQL" / "egym_dump" / "egym_deutsch_final_download.sql"

    conn = sqlite3.connect(str(bundle_db))
    try:
        conn.executescript(
            """
            DROP TABLE IF EXISTS gym80_devices;
            DROP TABLE IF EXISTS matrix_strength_devices;
            DROP TABLE IF EXISTS matrix_cardio_devices;
            DROP TABLE IF EXISTS egym_devices;
            DROP TABLE IF EXISTS egym_programs;
            DROP TABLE IF EXISTS egym_modes;
            """
        )
        # gym80 from curated DB snapshot
        conn.executescript(
            """
            CREATE TABLE gym80_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(50) NOT NULL,
                serie VARCHAR(100),
                model VARCHAR(255) NOT NULL,
                product_url TEXT,
                image_blob BLOB,
                muscle_groups TEXT
            );
            """
        )
        src = sqlite3.connect(str(gym80_db))
        src.row_factory = sqlite3.Row
        try:
            rows = src.execute(
                "SELECT category, serie, model, product_url, image_blob, muscle_groups FROM gym80_devices"
            ).fetchall()
        finally:
            src.close()
        conn.executemany(
            """
            INSERT INTO gym80_devices (category, serie, model, product_url, image_blob, muscle_groups)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            [
                (r["category"], r["serie"], r["model"], r["product_url"], r["image_blob"], r["muscle_groups"])
                for r in rows
            ],
        )

        conn.executescript(matrix_strength_sql.read_text(encoding="utf-8"))
        conn.executescript(matrix_cardio_sql.read_text(encoding="utf-8"))
        conn.executescript(egym_sql.read_text(encoding="utf-8"))
        conn.commit()
    finally:
        conn.close()

    result = sync_catalog_to_supabase(
        bundle_db,
        os.getenv("SUPABASE_URL", "").strip(),
        os.getenv("SUPABASE_ANON_KEY", "").strip(),
    )
    print(result)


if __name__ == "__main__":
    main()

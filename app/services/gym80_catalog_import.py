from __future__ import annotations

import sqlite3
from pathlib import Path


def import_gym80_sql(db_path: Path, sql_path: Path) -> dict:
    """Importiert gym80 SQL-Katalog in SQLite und dedupliziert Einträge."""
    if not sql_path.exists():
        return {"ok": False, "error": f"SQL-Datei nicht gefunden: {sql_path}"}

    sql_text = sql_path.read_text(encoding="utf-8", errors="ignore")
    if "gym80_devices" not in sql_text.lower():
        return {"ok": False, "error": "SQL-Datei enthält keine gym80_devices-Statements."}

    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gym80_devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(50) NOT NULL,
                serie VARCHAR(100),
                model VARCHAR(255) NOT NULL,
                product_url TEXT,
                image_url TEXT,
                muscle_groups TEXT,
                notes TEXT
            )
            """
        )
        before = conn.execute("SELECT COUNT(*) FROM gym80_devices").fetchone()[0]

        conn.executescript(sql_text)

        # Dedupe nach (category, serie, model) – behält jeweils den ältesten Datensatz
        conn.execute(
            """
            DELETE FROM gym80_devices
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM gym80_devices
                GROUP BY
                    COALESCE(TRIM(category), ''),
                    COALESCE(TRIM(serie), ''),
                    COALESCE(TRIM(model), '')
            )
            """
        )
        conn.commit()

        after = conn.execute("SELECT COUNT(*) FROM gym80_devices").fetchone()[0]
        imported = max(0, after - before)
        return {"ok": True, "before": before, "after": after, "imported": imported}
    finally:
        conn.close()

from __future__ import annotations

import sqlite3
from pathlib import Path

from app.services.catalog_overrides import ensure_device_target_overrides_table


def _exec_sql_file(conn: sqlite3.Connection, sql_path: Path) -> None:
    sql_text = sql_path.read_text(encoding="utf-8", errors="ignore")
    conn.executescript(sql_text)


def import_extra_catalogs(
    db_path: Path,
    gym80_sql: Path,
    matrix_strength_sql: Path,
    matrix_cardio_sql: Path,
    egym_sql: Path,
    replace_existing: bool = False,
) -> dict:
    files = {
        "gym80_devices": gym80_sql,
        "matrix_strength_devices": matrix_strength_sql,
        "matrix_cardio_devices": matrix_cardio_sql,
        "egym_devices": egym_sql,
    }
    missing = [str(p) for p in files.values() if not p.exists()]
    if missing:
        return {"ok": False, "error": f"Dateien fehlen: {', '.join(missing)}"}

    conn = sqlite3.connect(str(db_path))
    try:
        before = {}
        for table in files.keys():
            try:
                before[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
            except sqlite3.OperationalError:
                before[table] = 0

        if replace_existing:
            for table in files.keys():
                try:
                    conn.execute(f"DELETE FROM {table}")
                except sqlite3.OperationalError:
                    pass

        _exec_sql_file(conn, gym80_sql)
        _exec_sql_file(conn, matrix_strength_sql)
        _exec_sql_file(conn, matrix_cardio_sql)
        _exec_sql_file(conn, egym_sql)

        # Dedupe je Tabelle (qualitativ: ältester Datensatz je Modell bleibt)
        conn.execute(
            """
            DELETE FROM gym80_devices
            WHERE id NOT IN (
                SELECT MIN(id) FROM gym80_devices
                GROUP BY COALESCE(TRIM(category),''), COALESCE(TRIM(serie),''), COALESCE(TRIM(model),'')
            )
            """
        )
        conn.execute(
            """
            DELETE FROM matrix_strength_devices
            WHERE id NOT IN (
                SELECT MIN(id) FROM matrix_strength_devices
                GROUP BY COALESCE(TRIM(category),''), COALESCE(TRIM(serie),''), COALESCE(TRIM(model),'')
            )
            """
        )
        conn.execute(
            """
            DELETE FROM matrix_cardio_devices
            WHERE id NOT IN (
                SELECT MIN(id) FROM matrix_cardio_devices
                GROUP BY COALESCE(TRIM(category),''), COALESCE(TRIM(serie),''), COALESCE(TRIM(model),'')
            )
            """
        )
        conn.execute(
            """
            DELETE FROM egym_devices
            WHERE id NOT IN (
                SELECT MIN(id) FROM egym_devices
                GROUP BY COALESCE(TRIM(category),''), COALESCE(TRIM(series),''), COALESCE(TRIM(model),'')
            )
            """
        )
        ensure_device_target_overrides_table(conn)
        conn.commit()

        after = {}
        for table in files.keys():
            after[table] = conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return {"ok": True, "before": before, "after": after}
    finally:
        conn.close()

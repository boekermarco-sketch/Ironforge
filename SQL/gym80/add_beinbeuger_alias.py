from __future__ import annotations

import sqlite3
from pathlib import Path


def main() -> None:
    db_path = Path(__file__).resolve().parent / "gym80_devices_final.db"
    conn = sqlite3.connect(str(db_path))
    try:
        rows = conn.execute(
            """
            SELECT id, muscle_groups
            FROM gym80_devices
            WHERE LOWER(COALESCE(muscle_groups, '')) LIKE '%hamstrings%'
            """
        ).fetchall()
        updated = 0
        for row_id, muscle_groups in rows:
            text = (muscle_groups or "").strip()
            if "beinbeuger" in text.lower():
                continue
            new_text = f"{text}, Beinbeuger" if text else "Hamstrings, Beinbeuger"
            conn.execute(
                "UPDATE gym80_devices SET muscle_groups = ? WHERE id = ?",
                (new_text, row_id),
            )
            updated += 1
        conn.commit()
        print(f"rows_with_hamstrings={len(rows)}")
        print(f"updated={updated}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

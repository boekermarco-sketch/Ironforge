from __future__ import annotations

import sqlite3
from pathlib import Path


CARDIO_KEEP_ORDER = ["treadmill", "elliptical", "climbmill", "cycle", "rower"]
SERIE_PRIORITY = {"performance": 0, "endurance": 1, "lifestyle": 2}

CARDIO_IMAGE_MAP = {
    "treadmill": "images/002_programmable-treadmill.jpg",
    "elliptical": "images/007_commercial-elliptical-trainer.jpg",
    "climbmill": "images/016_commercial-stepper.jpg",
    "cycle": "images/018_commercial-exercise-bike.jpg",
    "rower": "images/060_magnetic-rowing-machine.jpg",
}


def normalize_cardio_type(model: str, cardio_type: str) -> str | None:
    text = f"{model or ''} {cardio_type or ''}".lower()
    if any(x in text for x in ("treadmill",)):
        return "treadmill"
    if any(x in text for x in ("elliptical",)):
        return "elliptical"
    if any(x in text for x in ("climbmill", "climb trainer", "stepper", "stair")):
        return "climbmill"
    if any(x in text for x in ("bike", "cycle", "upright", "recumbent")):
        return "cycle"
    if any(x in text for x in ("rower", "rowing")):
        return "rower"
    return None


def choose_best(rows: list[sqlite3.Row]) -> sqlite3.Row:
    def rank(row: sqlite3.Row) -> tuple[int, int]:
        serie_rank = SERIE_PRIORITY.get((row["serie"] or "").strip().lower(), 99)
        model_len = len((row["model"] or "").strip())
        return (serie_rank, model_len)

    return sorted(rows, key=rank)[0]


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "matrix_catalog_preview.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        all_rows = conn.execute(
            """
            SELECT id, serie, model, cardio_type
            FROM matrix_cardio_devices
            """
        ).fetchall()

        grouped: dict[str, list[sqlite3.Row]] = {k: [] for k in CARDIO_KEEP_ORDER}
        for row in all_rows:
            key = normalize_cardio_type(row["model"] or "", row["cardio_type"] or "")
            if key:
                grouped[key].append(row)

        keep_ids: set[int] = set()
        for key in CARDIO_KEEP_ORDER:
            if grouped[key]:
                best = choose_best(grouped[key])
                keep_ids.add(int(best["id"]))

        # Delete all non-selected cardio rows.
        for row in all_rows:
            if int(row["id"]) not in keep_ids:
                conn.execute("DELETE FROM matrix_cardio_devices WHERE id = ?", (row["id"],))

        # Normalize remaining rows and set fixed local image.
        kept_rows = conn.execute(
            "SELECT id, model, cardio_type FROM matrix_cardio_devices ORDER BY id"
        ).fetchall()
        for row in kept_rows:
            key = normalize_cardio_type(row["model"] or "", row["cardio_type"] or "")
            if not key:
                continue
            conn.execute(
                """
                UPDATE matrix_cardio_devices
                SET cardio_type = ?, image_url = ?, notes = COALESCE(notes, '')
                WHERE id = ?
                """,
                (key.capitalize(), CARDIO_IMAGE_MAP[key], row["id"]),
            )

        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM matrix_cardio_devices").fetchone()[0]
        print(f"cardio_rows_after={total}")
        rows = conn.execute(
            "SELECT serie, model, cardio_type, image_url FROM matrix_cardio_devices ORDER BY cardio_type"
        ).fetchall()
        for r in rows:
            print(f"{r['cardio_type']} | {r['serie']} | {r['model']} | {r['image_url']}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

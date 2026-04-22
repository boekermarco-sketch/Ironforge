from __future__ import annotations

import re
import sqlite3
from pathlib import Path


RULES: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"\bLEG PRESS|SQUAT|LUNGE|PENDULUM\b", re.I), "Quadrizeps, Gesäß, Hamstrings"),
    (re.compile(r"\bLEG EXTENSION\b", re.I), "Quadrizeps"),
    (re.compile(r"\bLEG CURL\b", re.I), "Hamstrings"),
    (re.compile(r"\bCALF\b", re.I), "Waden"),
    (re.compile(r"\bLAT PULL|PULLDOWN|CHINNING\b", re.I), "Latissimus, oberer Rücken, Bizeps"),
    (re.compile(r"\bLOW ROW|ROW|HIGH ROW|ISO LAT|PULL OVER\b", re.I), "Rückenmitte, Latissimus, Bizeps"),
    (re.compile(r"\bCHEST PRESS|BENCH PRESS|DECLINE|INCLINE CHEST PRESS\b", re.I), "Brust, Trizeps, vordere Schulter"),
    (re.compile(r"\bBUTTERFLY|PEC FLY|INNER CHEST|CROSSOVER\b", re.I), "Brust, vordere Schulter"),
    (re.compile(r"\bREAR DELT|BUTTERFLY REVERSE\b", re.I), "hintere Schulter, oberer Rücken"),
    (re.compile(r"\bSHOULDER PRESS|VIKING PRESS|NECK PRESS\b", re.I), "Schultern, Trizeps"),
    (re.compile(r"\bLATERAL RAISE|SHOULDER LATERAL\b", re.I), "seitliche Schultern"),
    (re.compile(r"\bTRICEPS|DIP\b", re.I), "Trizeps"),
    (re.compile(r"\bBICEPS|CURLER\b", re.I), "Bizeps"),
    (re.compile(r"\bABDUCTION\b", re.I), "Abduktoren, Gesäß"),
    (re.compile(r"\bADDUCTION\b", re.I), "Adduktoren"),
    (re.compile(r"\bABDOMINAL|AB CRUNCH\b", re.I), "Bauchmuskeln"),
    (re.compile(r"\bLOWER BACK|BACK MACHINE\b", re.I), "unterer Rücken"),
    (re.compile(r"\bTWISTER\b", re.I), "Core, schräge Bauchmuskeln"),
    (re.compile(r"\bFOREARM\b", re.I), "Unterarme"),
]


def infer_groups(model: str) -> str:
    for pattern, groups in RULES:
        if pattern.search(model):
            return groups
    return "Ganzkörper"


def main() -> None:
    db_path = Path(__file__).resolve().parent / "gym80_devices_final.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, model
            FROM gym80_devices
            WHERE TRIM(COALESCE(muscle_groups, '')) = ''
            """
        ).fetchall()
        updates = 0
        for row in rows:
            groups = infer_groups(row["model"] or "")
            conn.execute("UPDATE gym80_devices SET muscle_groups = ? WHERE id = ?", (groups, row["id"]))
            updates += 1
        conn.commit()
        print(f"updated={updates}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

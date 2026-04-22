from __future__ import annotations

import sqlite3
from pathlib import Path


EN_TO_DE: dict[str, str] = {
    "quadriceps": "Quadrizeps",
    "quads": "Quadrizeps",
    "glutes": "Gesäß",
    "gluteus": "Gesäß",
    "hamstrings": "Beinbeuger",
    "rear thigh": "Beinbeuger",
    "calves": "Waden",
    "calf": "Waden",
    "lats": "Latissimus",
    "latissimus dorsi": "Latissimus",
    "upper back": "oberer Rücken",
    "mid back": "Rückenmitte",
    "middle back": "Rückenmitte",
    "rear delts": "hintere Schulter",
    "posterior deltoids": "hintere Schulter",
    "shoulders": "Schultern",
    "deltoids": "Schultern",
    "front delts": "vordere Schulter",
    "anterior deltoids": "vordere Schulter",
    "side delts": "seitliche Schultern",
    "lateral deltoids": "seitliche Schultern",
    "triceps": "Trizeps",
    "biceps": "Bizeps",
    "chest": "Brust",
    "pectorals": "Brust",
    "pecs": "Brust",
    "lower chest": "untere Brust",
    "upper chest": "obere Brust",
    "abductors": "Abduktoren",
    "adductors": "Adduktoren",
    "hips": "Hüfte",
    "hip flexors": "Hüfte",
    "leg muscles": "Beinmuskulatur",
    "forearms": "Unterarme",
    "traps": "Nacken",
    "neck": "Nacken",
    "lower back": "unterer Rücken",
    "erector spinae": "unterer Rücken",
    "abs": "Bauchmuskeln",
    "abdominals": "Bauchmuskeln",
    "core": "Rumpf",
    "obliques": "schräge Bauchmuskeln",
    "functional training": "funktionelles Training",
}


def split_terms(raw: str) -> list[str]:
    return [part.strip() for part in raw.split(",") if part.strip()]


def add_german_aliases(raw: str | None) -> str:
    parts = split_terms(raw or "")
    if not parts:
        return ""

    seen = {p.lower() for p in parts}
    result = list(parts)
    for term in parts:
        de = EN_TO_DE.get(term.lower())
        if de and de.lower() not in seen:
            result.append(de)
            seen.add(de.lower())
    return ", ".join(result)


def has_en_without_de(raw: str | None) -> bool:
    parts = split_terms(raw or "")
    existing = {p.lower() for p in parts}
    for term in parts:
        de = EN_TO_DE.get(term.lower())
        if de and de.lower() not in existing:
            return True
    return False


def main() -> None:
    db_path = Path(__file__).resolve().parent / "gym80_devices_final.db"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT id, muscle_groups FROM gym80_devices").fetchall()
        updated = 0
        for row in rows:
            current = row["muscle_groups"] or ""
            new_value = add_german_aliases(current)
            if new_value != current:
                conn.execute(
                    "UPDATE gym80_devices SET muscle_groups = ? WHERE id = ?",
                    (new_value, row["id"]),
                )
                updated += 1
        conn.commit()

        remaining = conn.execute("SELECT id, muscle_groups FROM gym80_devices").fetchall()
        unresolved = sum(1 for row in remaining if has_en_without_de(row["muscle_groups"]))
        print(f"updated={updated}")
        print(f"unresolved={unresolved}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()

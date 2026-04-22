from __future__ import annotations

import re
import sqlite3
from pathlib import Path


MODEL_CODE_RE = re.compile(r"^\s*(\d{3,5}N?)\b", re.IGNORECASE)

MUSCLE_TERM_MAP: dict[str, tuple[str, ...]] = {
    "quadrizeps": ("quadriceps", "quads"),
    "gesäß": ("glutes", "gluteus"),
    "hamstrings": ("hamstrings", "beinbeuger", "rear thigh"),
    "waden": ("calves", "calf"),
    "latissimus": ("lats", "latissimus dorsi"),
    "oberer rücken": ("upper back",),
    "rückenmitte": ("mid back", "middle back"),
    "hintere schulter": ("rear delts", "posterior deltoids"),
    "schultern": ("shoulders", "deltoids"),
    "vordere schulter": ("front delts", "anterior deltoids"),
    "seitliche schultern": ("side delts", "lateral deltoids"),
    "trizeps": ("triceps",),
    "bizeps": ("biceps",),
    "brust": ("chest", "pectorals", "pecs"),
    "untere brust": ("lower chest",),
    "obere brust": ("upper chest",),
    "abduktoren": ("abductors",),
    "adduktoren": ("adductors",),
    "hüfte": ("hips", "hip flexors"),
    "beinmuskulatur": ("leg muscles",),
    "unterarme": ("forearms",),
    "nacken": ("traps", "neck"),
    "unterer rücken": ("lower back", "erector spinae"),
    "bauchmuskeln": ("abs", "abdominals"),
    "core": ("core",),
    "schräge bauchmuskeln": ("obliques",),
    "serratus": ("serratus",),
}


def extract_model_code(model: str) -> str | None:
    match = MODEL_CODE_RE.search(model or "")
    if not match:
        return None
    return match.group(1).lower()


def resolve_image_path(image_dir: Path, model_code: str | None) -> Path | None:
    if not model_code:
        return None
    candidates = [f"{model_code}.webp"]
    # Manche Dateien liegen als 3012n.webp vor, obwohl Modell "3012 ..." lautet.
    if not model_code.endswith("n"):
        candidates.append(f"{model_code}n.webp")
    for name in candidates:
        image_path = image_dir / name
        if image_path.exists():
            return image_path
    return None


def enrich_muscle_groups(value: str | None) -> str:
    raw = (value or "").strip()
    if not raw:
        return ""

    parts = [x.strip() for x in raw.split(",") if x.strip()]
    result: list[str] = []
    seen: set[str] = set()

    def add_term(term: str) -> None:
        key = term.strip().lower()
        if not key or key in seen:
            return
        seen.add(key)
        result.append(term.strip())

    for part in parts:
        add_term(part)
        lookup = part.lower()
        for de_term, en_terms in MUSCLE_TERM_MAP.items():
            if de_term == lookup:
                for en in en_terms:
                    add_term(en)
                break

    return ", ".join(result)


def migrate(db_path: Path, image_dir: Path) -> dict[str, int]:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        conn.execute("BEGIN")

        # Temporär neue Struktur erzeugen: image_blob statt image_url, notes entfernt.
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS gym80_devices_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category VARCHAR(50) NOT NULL,
                serie VARCHAR(100),
                model VARCHAR(255) NOT NULL,
                product_url TEXT,
                image_blob BLOB,
                muscle_groups TEXT
            )
            """
        )
        conn.execute("DELETE FROM gym80_devices_new")

        rows = conn.execute(
            """
            SELECT id, category, serie, model, product_url, muscle_groups
            FROM gym80_devices
            ORDER BY id ASC
            """
        ).fetchall()

        assigned = 0
        missing = 0
        for row in rows:
            code = extract_model_code(row["model"] or "")
            blob = None
            image_path = resolve_image_path(image_dir, code)
            if image_path:
                blob = image_path.read_bytes()
                assigned += 1
            else:
                missing += 1

            conn.execute(
                """
                INSERT INTO gym80_devices_new
                    (id, category, serie, model, product_url, image_blob, muscle_groups)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["id"],
                    row["category"],
                    row["serie"],
                    row["model"],
                    row["product_url"],
                    blob,
                    enrich_muscle_groups(row["muscle_groups"]),
                ),
            )

        conn.execute("DROP TABLE gym80_devices")
        conn.execute("ALTER TABLE gym80_devices_new RENAME TO gym80_devices")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_gym80_devices_model ON gym80_devices(model)")
        conn.commit()

        total = conn.execute("SELECT COUNT(*) FROM gym80_devices").fetchone()[0]
        with_blob = conn.execute(
            "SELECT COUNT(*) FROM gym80_devices WHERE image_blob IS NOT NULL"
        ).fetchone()[0]
        return {
            "total": int(total),
            "with_blob": int(with_blob),
            "assigned": int(assigned),
            "missing": int(missing),
        }
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    base_dir = Path(__file__).resolve().parent
    db_file = base_dir / "gym80_devices_final.db"
    result = migrate(db_file, base_dir)
    print(
        "Migration OK | total={total} | with_blob={with_blob} | assigned={assigned} | missing={missing}".format(
            **result
        )
    )

"""
Lokale Overrides für Katalog-Zielgruppe / Bewegungsgruppe (SQLite).

Schlüssel: brand (gym80|matrix|egym) + name_match (Substring im Modellnamen, klein).
Längster passender name_match gewinnt — so kann man gezielt z.B. „klappsitz“ pflegen.
"""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from app.services.catalog_targets import normalize_catalog_brand_key

CREATE_SQL = """
CREATE TABLE IF NOT EXISTS device_target_overrides (
    brand TEXT NOT NULL,
    name_match TEXT NOT NULL,
    target TEXT NOT NULL,
    movement_group TEXT,
    PRIMARY KEY (brand, name_match)
)
"""

# Idempotente Defaults (Nutzer kann per SQL weitere Zeilen ergänzen)
DEFAULT_SEEDS: list[tuple[str, str, str, str | None]] = [
    ("gym80", "klappsitz", "Core", "Core"),
]


def ensure_device_target_overrides_table(conn: sqlite3.Connection) -> None:
    conn.execute(CREATE_SQL)
    for brand, needle, target, mg in DEFAULT_SEEDS:
        conn.execute(
            """
            INSERT OR IGNORE INTO device_target_overrides
                (brand, name_match, target, movement_group)
            VALUES (?,?,?,?)
            """,
            (brand, needle, target, mg),
        )
    conn.commit()


def load_override_rules(conn: sqlite3.Connection) -> list[tuple[str, str, str, str | None]]:
    ensure_device_target_overrides_table(conn)
    cur = conn.execute(
        "SELECT brand, name_match, target, movement_group FROM device_target_overrides"
    )
    return [(r[0], r[1], r[2], r[3]) for r in cur.fetchall()]


def pick_override(
    brand_display: str,
    model: str,
    rules: list[tuple[str, str, str, str | None]],
) -> tuple[str | None, str | None]:
    """Liefert (target, movement_group) oder (None, None)."""
    m = (model or "").lower()
    bk = normalize_catalog_brand_key(brand_display)
    best_tgt: str | None = None
    best_mg: str | None = None
    best_len = -1
    for brand, needle, tgt, mg in rules:
        if (brand or "").strip().lower() != bk:
            continue
        n = (needle or "").lower()
        if not n or n not in m:
            continue
        if len(n) > best_len:
            best_len = len(n)
            best_tgt, best_mg = tgt, mg
    return best_tgt, best_mg


def resolve_catalog_row_targets(
    brand_display: str,
    model: str,
    serie: str,
    muscle_groups: str,
    category: str,
    rules: list[tuple[str, str, str, str | None]],
    infer_target_fn: Callable[[str], str],
) -> tuple[str, str | None]:
    """
    infer_target + optionales Override.
    movement_group: Serie, außer Override setzt movement_group explizit (nicht NULL).
    """
    text = f"{model} {(muscle_groups or '')} {(category or '')}"
    base_target = infer_target_fn(text)
    base_group = (serie or "").strip() or None

    ot, omg = pick_override(brand_display, model, rules)
    if ot is None:
        return base_target, base_group

    final_group = base_group if omg is None else (omg.strip() or None)
    return ot, final_group

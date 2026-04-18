"""
Katalog-Audit: Dubletten je SQLite-Tabelle + Zielgruppen-Konflikte (gleiche Marke+Name, verschiedene Targets).

Aufruf vom Projektroot:
  python -m app.services.catalog_audit
"""
from __future__ import annotations

import sqlite3
from collections import defaultdict
from pathlib import Path
from typing import Any

from app.database import DB_PATH
from app.services.catalog_overrides import load_override_rules, resolve_catalog_row_targets
from app.services.catalog_targets import infer_target


def _dupes_in_table(conn: sqlite3.Connection, sql: str, label: str) -> list[dict[str, Any]]:
    cur = conn.execute(sql)
    by_key: dict[str, list[str]] = defaultdict(list)
    for r in cur.fetchall():
        name = (r[0] or "").strip()
        if not name:
            continue
        k = name.lower()
        by_key[k].append(name)
    out = []
    for k, names in by_key.items():
        uniq = sorted(set(names))
        if len(uniq) > 1:
            out.append({"table": label, "normalized": k, "variants": uniq})
    return out


def audit_table_duplicates(db_path: Path | None = None) -> list[dict[str, Any]]:
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    try:
        out: list[dict[str, Any]] = []
        out.extend(
            _dupes_in_table(conn, "SELECT model FROM gym80_devices", "gym80_devices")
        )
        out.extend(
            _dupes_in_table(conn, "SELECT model FROM matrix_strength_devices", "matrix_strength_devices")
        )
        out.extend(
            _dupes_in_table(conn, "SELECT model FROM matrix_cardio_devices", "matrix_cardio_devices")
        )
        out.extend(_dupes_in_table(conn, "SELECT model FROM egym_devices", "egym_devices"))
        return out
    finally:
        conn.close()


def audit_infer_conflicts(db_path: Path | None = None) -> list[dict[str, Any]]:
    """Gleicher API-Schlüssel brand|name (wie Katalog-Suche), aber unterschiedliches infer_target."""
    path = db_path or DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    try:
        rules = load_override_rules(conn)
        buckets: dict[str, set[str]] = defaultdict(set)

        def add_row(brand_name: str, model: str, serie: str, mg: str, category_raw: str, src: str):
            model = (model or "").strip()
            if not model:
                return
            tgt, _ = resolve_catalog_row_targets(
                brand_name, model, serie, mg, category_raw, rules, infer_target_fn=infer_target
            )
            key = f"{brand_name.lower()}|{model.lower()}"
            buckets[key].add(tgt)

        for r in conn.execute(
            "SELECT model, serie, muscle_groups, category FROM gym80_devices"
        ).fetchall():
            add_row("gym80", r["model"], r["serie"], r["muscle_groups"], r["category"], "gym80")

        for r in conn.execute(
            "SELECT model, serie, muscle_groups, category FROM matrix_strength_devices"
        ).fetchall():
            add_row("Matrix", r["model"], r["serie"], r["muscle_groups"], r["category"], "matrix")

        for r in conn.execute(
            "SELECT model, serie, cardio_type, category FROM matrix_cardio_devices"
        ).fetchall():
            add_row("Matrix", r["model"], r["serie"], r["cardio_type"], r["category"], "matrix_cardio")

        for r in conn.execute(
            "SELECT model, series, muscle_groups, category FROM egym_devices"
        ).fetchall():
            add_row("eGym", r["model"], r["series"], r["muscle_groups"], r["category"], "egym")

        conflicts = []
        for key, targets in buckets.items():
            if len(targets) <= 1:
                continue
            conflicts.append({"key": key, "targets": sorted(targets)})
        return sorted(conflicts, key=lambda x: x["key"])
    finally:
        conn.close()


def run_report(db_path: Path | None = None) -> str:
    dups = audit_table_duplicates(db_path)
    conf = audit_infer_conflicts(db_path)
    lines = ["=== Gerätekatalog-Audit ===", ""]
    lines.append(f"SQLite: {db_path or DB_PATH}")
    lines.append("")
    lines.append(f"Modell-Dubletten (Schreibvarianten gleicher Normalform): {len(dups)}")
    for row in dups[:40]:
        lines.append(f"  [{row['table']}] {row['variants']}")
    if len(dups) > 40:
        lines.append(f"  … {len(dups) - 40} weitere")
    lines.append("")
    lines.append(f"Zielgruppen-Konflikte (gleiche Marke+Name, verschiedene Targets): {len(conf)}")
    for row in conf[:50]:
        lines.append(f"  {row['key']}: {', '.join(row['targets'])}")
    if len(conf) > 50:
        lines.append(f"  … {len(conf) - 50} weitere")
    lines.append("")
    return "\n".join(lines)


def main() -> None:
    print(run_report())


if __name__ == "__main__":
    main()

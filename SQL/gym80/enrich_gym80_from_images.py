from __future__ import annotations

import html
import re
import sqlite3
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests


API_URL = "https://gym80.us/wp-json/wp/v2/product"
CODE_RE = re.compile(r"^\s*(\d{3,5}N?)\b", re.IGNORECASE)
SERIES_RE = re.compile(
    r"\b(PURE KRAFT(?:-STRONG)?|SYGNUM(?: COMBO| DUAL)?|80CLASSICS|OUTDOOR)\b",
    re.IGNORECASE,
)
MANUAL_FALLBACK: dict[str, dict[str, str]] = {
    "4382": {
        "model": "4382 PURE KRAFT HIGH ROW WITH MOVABLE HANDLES",
        "serie": "PURE KRAFT",
        "category": "plate_loaded",
        "product_url": "https://gym80.de/wp-content/uploads/2024/11/4382_PureKraftHighRowWithMovableHandles_EN.pdf",
    }
}


def extract_code(model: str) -> str | None:
    m = CODE_RE.search(model or "")
    if not m:
        return None
    return m.group(1).lower()


def infer_category(title_upper: str, serie_upper: str) -> str:
    if "OUTDOOR" in title_upper or "OUTDOOR" in serie_upper:
        return "outdoor"
    if "SYGNUM" in title_upper or "SYGNUM" in serie_upper:
        return "weight_stack"
    if "CARDIO" in title_upper:
        return "cardio"
    return "plate_loaded"


def extract_serie(title_upper: str) -> str:
    m = SERIES_RE.search(title_upper)
    if m:
        return m.group(1).upper()
    if "PURE KRAFT" in title_upper:
        return "PURE KRAFT"
    return ""


def fetch_product_for_code(code: str) -> dict | None:
    candidates = [code]
    # Falls Bilddatei "4329n.webp" heißt, die Site aber "4329" nutzt.
    if code.endswith("n"):
        candidates.append(code[:-1])

    for q in candidates:
        try:
            res = requests.get(
                API_URL,
                params={"search": q, "per_page": 6},
                timeout=6,
                headers={"User-Agent": "Mozilla/5.0"},
            )
            res.raise_for_status()
            items = res.json()
        except Exception:
            continue

        q_upper = q.upper()
        for item in items:
            title = html.unescape((item.get("title") or {}).get("rendered") or "").strip()
            if not title:
                continue
            title_upper = title.upper()
            if title_upper.startswith(q_upper) or f" {q_upper} " in f" {title_upper} ":
                return item
    return None


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "gym80_devices_final.db"
    image_dir = base_dir

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        existing_models = [r["model"] for r in conn.execute("SELECT model FROM gym80_devices")]
        db_codes = {extract_code(m or "") for m in existing_models}
        db_codes.discard(None)

        image_codes = {p.stem.lower() for p in image_dir.glob("*.webp")}
        missing_codes = sorted(c for c in image_codes if c not in db_codes)

        code_to_product: dict[str, dict] = {}
        unresolved: list[str] = []

        with ThreadPoolExecutor(max_workers=10) as pool:
            futures = {pool.submit(fetch_product_for_code, code): code for code in missing_codes}
            for fut in as_completed(futures):
                code = futures[fut]
                try:
                    product = fut.result()
                except Exception:
                    product = None
                if product:
                    code_to_product[code] = product
                else:
                    if code in MANUAL_FALLBACK:
                        code_to_product[code] = MANUAL_FALLBACK[code]
                    else:
                        unresolved.append(code)

        inserted = 0
        for code in missing_codes:
            product = code_to_product.get(code)
            if not product:
                continue
            if "title" in product:
                title_raw = html.unescape((product.get("title") or {}).get("rendered") or "").strip()
                title_clean = re.sub(r"\s+", " ", title_raw).upper()
                serie = extract_serie(title_clean)
                category = infer_category(title_clean, serie)
                product_url = (product.get("link") or "").strip() or None
            else:
                title_clean = product["model"].strip().upper()
                serie = product.get("serie", "").strip().upper()
                category = product.get("category", "plate_loaded").strip().lower()
                product_url = product.get("product_url") or None

            image_path = image_dir / f"{code}.webp"
            if not image_path.exists() and not code.endswith("n"):
                alt = image_dir / f"{code}n.webp"
                image_path = alt if alt.exists() else image_path

            image_blob = image_path.read_bytes() if image_path.exists() else None

            conn.execute(
                """
                INSERT INTO gym80_devices (category, serie, model, product_url, image_blob, muscle_groups)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (category, serie, title_clean, product_url, image_blob, ""),
            )
            inserted += 1

        conn.commit()
        total = conn.execute("SELECT COUNT(*) FROM gym80_devices").fetchone()[0]
        print(f"Inserted: {inserted}")
        print(f"Total rows: {total}")
        print(f"Still unresolved: {len(unresolved)}")
        if unresolved:
            print(",".join(unresolved))
    finally:
        conn.close()


if __name__ == "__main__":
    main()

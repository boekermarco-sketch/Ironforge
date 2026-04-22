from __future__ import annotations

import base64
import html
import sqlite3
import webbrowser
from pathlib import Path


def slug_text(value: str | None) -> str:
    raw = (value or "").lower()
    for ch in ["/", "-", "_", ",", ".", "(", ")", ":", ";"]:
        raw = raw.replace(ch, " ")
    return " ".join(raw.split())


def image_data_uri(image_path: Path) -> str:
    ext = image_path.suffix.lower()
    mime = "image/jpeg" if ext in {".jpg", ".jpeg"} else "image/png"
    encoded = base64.b64encode(image_path.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{encoded}"


def resolve_image_src(image_url: str | None, base_dir: Path) -> str | None:
    value = (image_url or "").strip()
    if not value:
        return None
    # Prefer local relative file paths like images/xxx.jpg
    local_path = base_dir / value
    if local_path.exists():
        return image_data_uri(local_path)
    return value


def collect_local_images(images_dir: Path) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for p in sorted(images_dir.glob("*")):
        if p.suffix.lower() not in {".jpg", ".jpeg", ".png", ".webp"}:
            continue
        rows.append({"path": str(p), "name": p.name, "slug": slug_text(p.stem)})
    return rows


def row_keywords(row: sqlite3.Row, mode: str) -> list[str]:
    keys = [slug_text(row["model"]), slug_text(row["serie"]), slug_text(row["category"])]
    if mode == "strength":
        keys.append(slug_text(row["muscle_groups"]))
    else:
        keys.append(slug_text(row["cardio_type"]))
        keys.append(slug_text(row["features"]))
    # normalize common synonyms for matching
    text = " ".join(keys)
    synonyms = {
        "lat pulldown": ["lat pulldown", "lat pull", "pulldown"],
        "leg extension": ["leg extension"],
        "leg curl": ["leg curl"],
        "leg press": ["leg press"],
        "squat": ["squat"],
        "lunge": ["lunge"],
        "glute": ["glute"],
        "abdominal": ["abdominal", "ab crunch", "abs"],
        "torso": ["torso", "core"],
        "press": ["press", "chest press"],
        "curl": ["curl", "biceps"],
        "cable": ["cable", "crossover"],
        "bench": ["bench"],
        "treadmill": ["treadmill"],
        "elliptical": ["elliptical"],
        "climbmill": ["climbmill", "climb trainer", "stepper", "stair"],
        "bike": ["bike", "cycle", "upright", "recumbent"],
        "rower": ["rower", "rowing"],
    }
    out: list[str] = []
    for canonical, words in synonyms.items():
        if any(w in text for w in words):
            out.append(canonical)
    out.extend(keys)
    return [x for x in out if x]


def assign_local_image(
    row: sqlite3.Row,
    mode: str,
    local_images: list[dict[str, str]],
    used_paths: set[str],
) -> str | None:
    keywords = row_keywords(row, mode)
    best_path: str | None = None
    best_score = 0

    for img in local_images:
        if img["path"] in used_paths:
            continue
        slug = img["slug"]
        score = 0
        for kw in keywords:
            if kw and kw in slug:
                score += len(kw)
        if score > best_score:
            best_score = score
            best_path = img["path"]

    if best_path and best_score >= 6:
        used_paths.add(best_path)
        return best_path

    # fallback by broad mode-type if no strong keyword hit
    fallback_groups = {
        "strength": ["weight training", "fitness machine", "bench", "squat", "lat", "press", "curl"],
        "cardio": ["treadmill", "elliptical", "stepper", "bike", "rowing"],
    }
    for img in local_images:
        if img["path"] in used_paths:
            continue
        if any(token in img["slug"] for token in fallback_groups[mode]):
            used_paths.add(img["path"])
            return img["path"]
    return None


def build_db(base_dir: Path) -> Path:
    db_path = base_dir / "matrix_catalog_preview.db"
    strength_sql = (base_dir / "matrix_strength_final_complete.sql").read_text(encoding="utf-8")
    cardio_sql = (base_dir / "matrix_cardio_final_complete.sql").read_text(encoding="utf-8")

    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript("DROP TABLE IF EXISTS matrix_strength_devices; DROP TABLE IF EXISTS matrix_cardio_devices;")
        conn.executescript(strength_sql)
        conn.executescript(cardio_sql)
        conn.commit()
    finally:
        conn.close()
    return db_path


def make_card(title: str, lines: list[tuple[str, str]], image_src: str | None) -> str:
    safe_title = html.escape(title)
    if image_src:
        safe_img = html.escape(image_src)
        image_html = f"<img src='{safe_img}' alt='{safe_title}' loading='lazy'>"
    else:
        image_html = "<div class='placeholder'>Kein Bild</div>"

    info = "".join(f"<p><b>{html.escape(k)}:</b> {html.escape(v or '')}</p>" for k, v in lines)
    return f"""
    <article class="card">
      <div class="img-wrap">{image_html}</div>
      <h3>{safe_title}</h3>
      {info}
    </article>
    """


def build_html(db_path: Path, out_path: Path) -> None:
    base_dir = out_path.parent
    images_dir = base_dir / "images"
    local_images = collect_local_images(images_dir)
    used_paths: set[str] = set()

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        strength_rows = conn.execute(
            """
            SELECT serie, model, category, muscle_groups, notes, image_url, product_url
            FROM matrix_strength_devices
            ORDER BY serie, model
            """
        ).fetchall()
        cardio_rows = conn.execute(
            """
            SELECT serie, model, category, cardio_type, features, notes, image_url, product_url
            FROM matrix_cardio_devices
            ORDER BY serie, model
            """
        ).fetchall()
    finally:
        conn.close()

    strength_cards = []
    for row in strength_rows:
        image_src = resolve_image_src(row["image_url"], base_dir)
        if not image_src:
            local_path = assign_local_image(row, "strength", local_images, used_paths)
            image_src = image_data_uri(Path(local_path)) if local_path else None
        strength_cards.append(
            make_card(
                row["model"] or "",
                [
                    ("Serie", row["serie"] or ""),
                    ("Kategorie", row["category"] or ""),
                    ("Muskelgruppen", row["muscle_groups"] or ""),
                    ("Notiz", row["notes"] or ""),
                    ("URL", row["product_url"] or ""),
                ],
                image_src,
            )
        )

    cardio_cards = []
    for row in cardio_rows:
        image_src = resolve_image_src(row["image_url"], base_dir)
        if not image_src:
            local_path = assign_local_image(row, "cardio", local_images, used_paths)
            image_src = image_data_uri(Path(local_path)) if local_path else None
        cardio_cards.append(
            make_card(
                row["model"] or "",
                [
                    ("Serie", row["serie"] or ""),
                    ("Kategorie", row["category"] or ""),
                    ("Cardio-Typ", row["cardio_type"] or ""),
                    ("Features", row["features"] or ""),
                    ("Notiz", row["notes"] or ""),
                    ("URL", row["product_url"] or ""),
                ],
                image_src,
            )
        )

    html_doc = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Matrix Katalog Vorschau</title>
  <style>
    body {{ margin:0; font-family:Arial,sans-serif; background:#101114; color:#e7e7e7; }}
    header {{ position:sticky; top:0; background:#171a20; border-bottom:1px solid #2a2f3a; padding:14px 18px; z-index:2; }}
    .container {{ padding:16px; }}
    .meta {{ color:#b8c1d1; font-size:13px; margin-bottom:12px; }}
    h2 {{ margin:16px 0 10px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(290px, 1fr)); gap:14px; }}
    .card {{ background:#1a1e26; border:1px solid #2b3140; border-radius:12px; padding:10px; }}
    .img-wrap {{ background:#0f1218; border-radius:10px; height:170px; display:grid; place-items:center; overflow:hidden; margin-bottom:10px; }}
    .img-wrap img {{ width:100%; height:100%; object-fit:contain; }}
    .placeholder {{ color:#98a1b3; font-size:12px; }}
    h3 {{ margin:8px 0; font-size:15px; line-height:1.3; }}
    p {{ margin:4px 0; font-size:12px; color:#c7cfde; word-break:break-word; }}
  </style>
</head>
<body>
  <header><strong>Matrix Katalog Vorschau</strong> - 1-Klick Ansicht aus SQL</header>
  <div class="container">
    <div class="meta">Strength: {len(strength_rows)} Einträge | Cardio: {len(cardio_rows)} Einträge</div>
    <h2>Strength</h2>
    <div class="grid">{''.join(strength_cards)}</div>
    <h2>Cardio</h2>
    <div class="grid">{''.join(cardio_cards)}</div>
  </div>
</body>
</html>
"""
    out_path.write_text(html_doc, encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = build_db(base_dir)
    out_path = base_dir / "matrix_catalog_visual.html"
    build_html(db_path, out_path)
    webbrowser.open(out_path.as_uri())
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()

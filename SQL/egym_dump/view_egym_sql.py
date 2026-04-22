from __future__ import annotations

import html
import sqlite3
import webbrowser
from pathlib import Path


def build_db(base_dir: Path) -> Path:
    db_path = base_dir / "egym_catalog_preview.db"
    sql_text = (base_dir / "egym_deutsch_final_download.sql").read_text(encoding="utf-8")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            "DROP TABLE IF EXISTS egym_devices; DROP TABLE IF EXISTS egym_programs; DROP TABLE IF EXISTS egym_modes;"
        )
        conn.executescript(sql_text)
        conn.commit()
    finally:
        conn.close()
    return db_path


def local_image_for_model(base_dir: Path, model: str) -> str | None:
    text = (model or "").lower()
    mapping = [
        ("beinstrecker", "Beinstrecker.jpeg"),
        ("bauchtrainer", "Bauchtrainer.jpeg"),
        ("rückenstrecker", "Rückenstrecker.jpeg"),
        ("beinbeuger", "Beinbeuger.jpeg"),
        ("brustpresse", "Brustpresse.jpeg"),
        ("ruderzug", "Seitbeuger.jpeg"),
        ("latzug", "Latzug.jpeg"),
        ("gluteus", "Glutaeus Hip Thrust.jpeg"),
        ("hip thrust", "Glutaeus Hip Thrust.jpeg"),
        ("beinpresse", "Beinpresse.jpeg"),
        ("abduktor", "Abduktor.jpeg"),
        ("adduktor", "Adduktor.jpeg"),
        ("rumprotation", "Seitbeuger.jpeg"),
        ("rumpfrotation", "Seitbeuger.jpeg"),
        ("butterfly reverse", "Butterfly Reverse.jpeg"),
        ("butterfly", "Butterfly.jpeg"),
        ("bizeps", "Bizepscurl.jpeg"),
        ("waden", "Beinpresse.jpeg"),
        ("schulterpresse", "Schulterpresse.jpeg"),
        ("trizeps", "Trizeps-Dips.jpeg"),
        ("kniebeuge", "Kniebeugen.jpeg"),
        ("smart strength zirkel", "Brustpresse.jpeg"),
        ("egym pro", "Brustpresse.jpeg"),
        ("smart flex", "Seitbeuger.jpeg"),
    ]
    for key, filename in mapping:
        if key in text:
            p = base_dir / filename
            if p.exists():
                return filename
    return None


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
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        devices = conn.execute(
            """
            SELECT series, code, model, product_url, image_url, muscle_groups, notes
            FROM egym_devices
            ORDER BY model
            """
        ).fetchall()
        programs = conn.execute(
            """
            SELECT series, program_name, training_goals, training_methods, notes
            FROM egym_programs
            ORDER BY program_name
            """
        ).fetchall()
        modes = conn.execute(
            """
            SELECT series, mode_name, description, notes
            FROM egym_modes
            ORDER BY mode_name
            """
        ).fetchall()
    finally:
        conn.close()

    device_cards = []
    for row in devices:
        local_img = local_image_for_model(base_dir, row["model"] or "")
        image_src = local_img if local_img else (row["image_url"] or None)
        device_cards.append(
            make_card(
                row["model"] or "",
                [
                    ("Serie", row["series"] or ""),
                    ("Code", row["code"] or ""),
                    ("Muskelgruppen", row["muscle_groups"] or ""),
                    ("Notiz", row["notes"] or ""),
                    ("URL", row["product_url"] or ""),
                ],
                image_src,
            )
        )

    program_cards = [
        make_card(
            row["program_name"] or "",
            [
                ("Serie", row["series"] or ""),
                ("Ziel", row["training_goals"] or ""),
                ("Methoden", row["training_methods"] or ""),
                ("Notiz", row["notes"] or ""),
            ],
            None,
        )
        for row in programs
    ]

    mode_cards = [
        make_card(
            row["mode_name"] or "",
            [
                ("Serie", row["series"] or ""),
                ("Beschreibung", row["description"] or ""),
                ("Notiz", row["notes"] or ""),
            ],
            None,
        )
        for row in modes
    ]

    html_doc = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>eGym Katalog Vorschau</title>
  <style>
    body {{ margin:0; font-family:Arial,sans-serif; background:#101114; color:#e7e7e7; }}
    header {{ position:sticky; top:0; background:#171a20; border-bottom:1px solid #2a2f3a; padding:14px 18px; z-index:2; }}
    .container {{ padding:16px; }}
    .meta {{ color:#b8c1d1; font-size:13px; margin-bottom:12px; }}
    h2 {{ margin:16px 0 10px; }}
    .grid {{ display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:14px; }}
    .card {{ background:#1a1e26; border:1px solid #2b3140; border-radius:12px; padding:10px; }}
    .img-wrap {{ background:#0f1218; border-radius:10px; height:170px; display:grid; place-items:center; overflow:hidden; margin-bottom:10px; }}
    .img-wrap img {{ width:100%; height:100%; object-fit:contain; }}
    .placeholder {{ color:#98a1b3; font-size:12px; }}
    h3 {{ margin:8px 0; font-size:15px; line-height:1.3; }}
    p {{ margin:4px 0; font-size:12px; color:#c7cfde; word-break:break-word; }}
  </style>
</head>
<body>
  <header><strong>eGym Katalog Vorschau</strong> - 1-Klick Ansicht aus SQL</header>
  <div class="container">
    <div class="meta">Geräte: {len(devices)} | Programme: {len(programs)} | Modi: {len(modes)}</div>
    <h2>Geräte</h2>
    <div class="grid">{''.join(device_cards)}</div>
    <h2>Programme</h2>
    <div class="grid">{''.join(program_cards)}</div>
    <h2>Modi</h2>
    <div class="grid">{''.join(mode_cards)}</div>
  </div>
</body>
</html>
"""
    out_path.write_text(html_doc, encoding="utf-8")


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = build_db(base_dir)
    out_path = base_dir / "egym_catalog_visual.html"
    build_html(db_path, out_path)
    webbrowser.open(out_path.as_uri())
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()

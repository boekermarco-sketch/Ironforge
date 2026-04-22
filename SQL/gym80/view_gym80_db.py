from __future__ import annotations

import base64
import html
import sqlite3
import webbrowser
from pathlib import Path


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = base_dir / "gym80_devices_final.db"
    output_path = base_dir / "gym80_devices_visual.html"

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT model, serie, category, muscle_groups, image_blob
        FROM gym80_devices
        ORDER BY model ASC
        """
    ).fetchall()
    conn.close()

    cards: list[str] = []
    for row in rows:
        image_blob = row["image_blob"]
        img_html = "<div class='placeholder'>Kein Bild</div>"
        if image_blob:
            b64 = base64.b64encode(image_blob).decode("ascii")
            img_html = f"<img src='data:image/webp;base64,{b64}' alt='{html.escape(row['model'] or '')}'>"

        muscle_groups = (row["muscle_groups"] or "").strip() or "Noch nicht zugeordnet"
        cards.append(
            f"""
            <article class="card">
                <div class="img-wrap">{img_html}</div>
                <h3>{html.escape(row["model"] or "")}</h3>
                <p><b>Serie:</b> {html.escape(row["serie"] or "")}</p>
                <p><b>Kategorie:</b> {html.escape(row["category"] or "")}</p>
                <p><b>Muskelgruppen:</b> {html.escape(muscle_groups)}</p>
            </article>
            """
        )

    html_doc = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>gym80 Geräteübersicht (DB-Blob)</title>
  <style>
    body {{
      margin: 0;
      font-family: Arial, sans-serif;
      background: #101114;
      color: #e7e7e7;
    }}
    header {{
      position: sticky;
      top: 0;
      background: #171a20;
      border-bottom: 1px solid #2a2f3a;
      padding: 14px 18px;
      z-index: 2;
    }}
    .container {{
      padding: 16px;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
      gap: 14px;
    }}
    .card {{
      background: #1a1e26;
      border: 1px solid #2b3140;
      border-radius: 12px;
      padding: 10px;
    }}
    .img-wrap {{
      background: #0f1218;
      border-radius: 10px;
      height: 180px;
      display: grid;
      place-items: center;
      overflow: hidden;
      margin-bottom: 10px;
    }}
    .img-wrap img {{
      width: 100%;
      height: 100%;
      object-fit: contain;
    }}
    .placeholder {{
      color: #98a1b3;
      font-size: 12px;
    }}
    h3 {{
      margin: 8px 0;
      font-size: 16px;
      line-height: 1.3;
    }}
    p {{
      margin: 4px 0;
      font-size: 13px;
      color: #c7cfde;
    }}
  </style>
</head>
<body>
  <header>
    <strong>gym80 Geräteübersicht</strong> - direkt aus SQLite BLOBs
  </header>
  <div class="container">
    <div class="grid">
      {''.join(cards)}
    </div>
  </div>
</body>
</html>
"""

    output_path.write_text(html_doc, encoding="utf-8")
    webbrowser.open(output_path.as_uri())
    print(f"OK: {output_path}")


if __name__ == "__main__":
    main()

from __future__ import annotations

import json
import sqlite3
from pathlib import Path


def build_preview_db(base_dir: Path) -> Path:
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


def main() -> None:
    base_dir = Path(__file__).resolve().parent
    db_path = build_preview_db(base_dir)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT model, image_url
            FROM matrix_strength_devices
            WHERE category IN ('plate_loaded', 'single_station')
            ORDER BY category, model
            """
        ).fetchall()
    finally:
        conn.close()

    image_files = sorted(
        [f"images/{p.name}" for p in (base_dir / "images").glob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
    )
    models = [{"model": r["model"], "image_url": r["image_url"] or ""} for r in rows]

    out_path = base_dir / "matrix_image_mapper.html"
    html = f"""<!doctype html>
<html lang="de">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Matrix Bild-Mapping Tool</title>
  <style>
    body {{ font-family: Arial, sans-serif; margin: 0; background:#101114; color:#e7e7e7; }}
    header {{ position: sticky; top: 0; background:#171a20; padding:12px 16px; border-bottom:1px solid #2a2f3a; }}
    .container {{ padding: 14px; }}
    .row {{ display:grid; grid-template-columns: 1fr 380px 220px; gap:10px; align-items:center; margin-bottom:10px; background:#1a1e26; border:1px solid #2b3140; border-radius:10px; padding:10px; }}
    .model {{ font-size:13px; }}
    select {{ width:100%; padding:8px; background:#0f1218; color:#e7e7e7; border:1px solid #2b3140; border-radius:8px; }}
    img {{ width:220px; height:140px; object-fit:contain; background:#0f1218; border-radius:8px; }}
    .toolbar {{ display:flex; gap:8px; margin-bottom:12px; }}
    button {{ background:#2f6feb; border:none; color:white; border-radius:8px; padding:8px 12px; cursor:pointer; }}
    textarea {{ width:100%; height:180px; background:#0f1218; color:#e7e7e7; border:1px solid #2b3140; border-radius:8px; padding:8px; }}
  </style>
</head>
<body>
  <header><strong>Matrix Bild-Mapping (Plate Loaded + Single Station)</strong></header>
  <div class="container">
    <div class="toolbar">
      <button onclick="exportJson()">Mapping JSON erzeugen</button>
      <button onclick="downloadJson()">JSON herunterladen</button>
    </div>
    <div id="rows"></div>
    <h3>Export</h3>
    <textarea id="output" placeholder="Hier erscheint das Mapping..."></textarea>
  </div>
  <script>
    const models = {json.dumps(models, ensure_ascii=False)};
    const imageOptions = {json.dumps(image_files, ensure_ascii=False)};

    function resolveImage(path) {{
      return path ? path : '';
    }}

    function makeRow(item) {{
      const row = document.createElement('div');
      row.className = 'row';
      const left = document.createElement('div');
      left.className = 'model';
      left.textContent = item.model;

      const sel = document.createElement('select');
      imageOptions.forEach((opt) => {{
        const o = document.createElement('option');
        o.value = opt;
        o.textContent = opt;
        if (opt === item.image_url) o.selected = true;
        sel.appendChild(o);
      }});
      if (!item.image_url || !imageOptions.includes(item.image_url)) {{
        const fallback = document.createElement('option');
        fallback.value = item.image_url || '';
        fallback.textContent = item.image_url ? ('(Aktuell extern) ' + item.image_url) : '(kein Bild)';
        fallback.selected = true;
        sel.insertBefore(fallback, sel.firstChild);
      }}

      const preview = document.createElement('img');
      preview.src = resolveImage(sel.value);
      sel.addEventListener('change', () => preview.src = resolveImage(sel.value));

      row.appendChild(left);
      row.appendChild(sel);
      row.appendChild(preview);
      return row;
    }}

    function exportJson() {{
      const rows = [...document.querySelectorAll('.row')];
      const data = rows.map((r) => {{
        const model = r.querySelector('.model').textContent;
        const image_url = r.querySelector('select').value;
        return {{ model, image_url }};
      }});
      document.getElementById('output').value = JSON.stringify(data, null, 2);
    }}

    function downloadJson() {{
      if (!document.getElementById('output').value.trim()) exportJson();
      const blob = new Blob([document.getElementById('output').value], {{ type:'application/json' }});
      const a = document.createElement('a');
      a.href = URL.createObjectURL(blob);
      a.download = 'matrix_strength_image_mapping.json';
      a.click();
    }}

    const wrap = document.getElementById('rows');
    models.forEach((m) => wrap.appendChild(makeRow(m)));
  </script>
</body>
</html>
"""
    out_path.write_text(html, encoding="utf-8")
    print(f"OK: {out_path}")


if __name__ == "__main__":
    main()

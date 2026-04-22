from __future__ import annotations

import json
import re
from pathlib import Path

import requests


def fetch_catalog_html(modality: str) -> str:
    url = f"https://world.matrixfitness.com/eng/strength/catalog?modalities={modality}"
    resp = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
    resp.raise_for_status()
    return resp.text


def extract_json_ld_products(html: str) -> list[dict]:
    products: list[dict] = []
    blocks = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        flags=re.DOTALL | re.IGNORECASE,
    )
    for block in blocks:
        txt = block.strip()
        if not txt:
            continue
        try:
            data = json.loads(txt)
        except Exception:
            continue
        if isinstance(data, dict):
            items = [data]
        elif isinstance(data, list):
            items = data
        else:
            items = []
        for item in items:
            if not isinstance(item, dict):
                continue
            typ = (item.get("@type") or "").lower()
            if typ == "product":
                products.append(item)
    return products


def main() -> None:
    out = {}
    for modality in ("plate-loaded", "single-station"):
        html = fetch_catalog_html(modality)
        html_path = Path(__file__).resolve().parent / f"catalog_{modality}.html"
        html_path.write_text(html, encoding="utf-8")
        products = extract_json_ld_products(html)
        out[modality] = [{"name": p.get("name"), "url": p.get("url"), "image": p.get("image")} for p in products]
        print(f"saved_html={html_path}")
        scripts = re.findall(r'<script[^>]+src="([^"]+)"', html, flags=re.IGNORECASE)
        print(f"{modality} scripts: {len(scripts)}")
        for s in scripts[:10]:
            print(f"  {s}")

    output_path = Path(__file__).resolve().parent / "matrix_catalog_extracted.json"
    output_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"written={output_path}")
    for key, items in out.items():
        print(f"{key}: {len(items)}")


if __name__ == "__main__":
    main()

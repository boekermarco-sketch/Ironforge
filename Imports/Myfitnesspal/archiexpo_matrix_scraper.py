import csv
import os
import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from playwright.sync_api import sync_playwright

URL = "https://www.archiexpo.com/prod/matrix-141371.html"
BASE_DIR = os.path.join(os.path.dirname(__file__), "archiexpo_matrix_export")
IMG_DIR = os.path.join(BASE_DIR, "bilder")
CSV_PATH = os.path.join(BASE_DIR, "matrix_produkte.csv")
TIMEOUT = 120000


def clean(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def safe_name(name: str) -> str:
    name = clean(name)
    name = re.sub(r"[^a-zA-Z0-9äöüÄÖÜß._-]+", "_", name)
    return name.strip("._")[:120] or "bild"


def normalize_img_url(src: str, page_url: str) -> str:
    if not src:
        return ""
    src = src.strip()
    if src.startswith("//"):
        return "https:" + src
    if src.startswith("http://") or src.startswith("https://"):
        return src
    return urljoin(page_url, src)


def download_image(url: str, dest_path: str) -> bool:
    try:
        r = requests.get(url, timeout=30, headers={"User-Agent": "Mozilla/5.0"})
        r.raise_for_status()
        with open(dest_path, "wb") as f:
            f.write(r.content)
        return True
    except Exception:
        return False


def extract_candidates(page):
    items = []
    seen = set()

    page.goto(URL, wait_until="domcontentloaded", timeout=TIMEOUT)
    page.wait_for_timeout(6000)

    for _ in range(10):
        page.mouse.wheel(0, 2500)
        page.wait_for_timeout(1200)

    selectors = ["a:has(img)", "article", "li", "div"]

    for selector in selectors:
        locator = page.locator(selector)
        count = min(locator.count(), 800)
        for i in range(count):
            try:
                node = locator.nth(i)
                text = clean(node.inner_text(timeout=500))
                img = node.locator("img").first
                if img.count() == 0:
                    continue

                src = (
                    img.get_attribute("src")
                    or img.get_attribute("data-src")
                    or img.get_attribute("data-original")
                    or img.get_attribute("data-lazy")
                    or img.get_attribute("srcset")
                    or ""
                )

                if "," in src and "http" in src:
                    src = src.split(",")[0].split()[0]

                img_url = normalize_img_url(src, page.url)
                alt = clean(img.get_attribute("alt") or "")
                href = ""
                try:
                    href = node.get_attribute("href") or ""
                except Exception:
                    pass

                name = text or alt
                if not name or len(name) < 3:
                    continue

                lowered = name.lower()
                if lowered in {"logo", "menu", "compare", "search"}:
                    continue

                key = (name, img_url)
                if key in seen:
                    continue
                seen.add(key)

                items.append({
                    "geraetebezeichnung": name,
                    "bild_url": img_url,
                    "seite": href,
                    "alt": alt,
                })
            except Exception:
                continue

    filtered = []
    seen_keys = set()
    for item in items:
        name = item["geraetebezeichnung"]
        url = item["bild_url"]
        if not url:
            continue
        if len(name.split()) > 20:
            continue
        key = (name, url)
        if key in seen_keys:
            continue
        seen_keys.add(key)
        filtered.append(item)

    return filtered


def main():
    os.makedirs(IMG_DIR, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 2200})
        items = extract_candidates(page)
        browser.close()

    saved_rows = []
    for idx, item in enumerate(items, start=1):
        img_url = item["bild_url"]
        ext = os.path.splitext(urlparse(img_url).path)[1].lower()
        if ext not in {".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif"}:
            ext = ".jpg"
        filename = f"{idx:03d}_{safe_name(item['geraetebezeichnung'])}{ext}"
        dest = os.path.join(IMG_DIR, filename)
        ok = download_image(img_url, dest)
        if ok:
            row = dict(item)
            row["gespeicherte_datei"] = os.path.relpath(dest, BASE_DIR)
            saved_rows.append(row)

    with open(CSV_PATH, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["geraetebezeichnung", "bild_url", "seite", "alt", "gespeicherte_datei"],
        )
        writer.writeheader()
        writer.writerows(saved_rows)

    print(f"Export abgeschlossen: {len(saved_rows)} Bilder gespeichert")
    print(f"CSV: {CSV_PATH}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Fehler: {e}", file=sys.stderr)
        sys.exit(1)

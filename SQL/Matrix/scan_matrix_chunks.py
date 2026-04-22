from __future__ import annotations

import re

import requests


BASE = "https://world.matrixfitness.com/eng/strength/"
CHUNKS = [
    "chunk-VVGMNDLG.js",
    "chunk-CYRCRLPN.js",
    "chunk-MG3A36JU.js",
    "chunk-4J7JCCRX.js",
    "chunk-LOFUKI3R.js",
    "chunk-7D6AMBKK.js",
    "chunk-USGDB2K6.js",
    "chunk-SO4KGCWO.js",
    "chunk-BHLJW42U.js",
    "chunk-I5BVC2ZK.js",
    "scripts-NRTAAW7D.js",
    "main-XUMUMUER.js",
]


def main() -> None:
    keywords = [
        "modalities",
        "plate-loaded",
        "single-station",
        "catalog",
        "api/",
        "graphql",
        "product",
        "strength",
    ]
    for name in CHUNKS:
        text = requests.get(BASE + name, timeout=30, headers={"User-Agent": "Mozilla/5.0"}).text
        counts = {k: text.lower().count(k) for k in keywords}
        if any(v > 0 for v in counts.values()):
            print(f"--- {name} len={len(text)}")
            for k, v in counts.items():
                if v > 0:
                    print(f"{k}: {v}")
            urls = re.findall(r"https?://[^\"' ]+", text)
            for u in urls[:8]:
                print(f"url: {u}")


if __name__ == "__main__":
    main()

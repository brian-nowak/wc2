#!/usr/bin/env python3
"""
Download a head-and-shoulders photo for each of the 48 World Cup 2026 managers
from Wikipedia and save them as images/01.jpg ... images/48.jpg.

Runs on GitHub Actions (which has internet access to Wikipedia). Uses only the
Python standard library plus Pillow (to normalise every image to a valid JPEG).

The id order here MUST match the card order in index.html.
"""

import io
import json
import os
import sys
import time
import urllib.parse
import urllib.request

from PIL import Image

API = "https://en.wikipedia.org/w/api.php"
UA = "wc26-gaffers/1.0 (github actions; static gallery; no contact)"
OUT_DIR = "images"
THUMB_SIZE = 640  # px on the long edge

# id -> list of candidate Wikipedia article titles (first hit wins).
# Most are exact article titles; ambiguous names get a disambiguated fallback.
COACHES = [
    ("01", ["Mauricio Pochettino"]),
    ("02", ["Javier Aguirre"]),
    ("03", ["Jesse Marsch"]),
    ("04", ["Dick Advocaat"]),
    ("05", ["Sébastien Migné"]),
    ("06", ["Thomas Christiansen (footballer)", "Thomas Christiansen"]),
    ("07", ["Lionel Scaloni"]),
    ("08", ["Carlo Ancelotti"]),
    ("09", ["Marcelo Bielsa"]),
    ("10", ["Néstor Lorenzo"]),
    ("11", ["Sebastián Beccacece"]),
    ("12", ["Gustavo Alfaro"]),
    ("13", ["Thomas Tuchel"]),
    ("14", ["Didier Deschamps"]),
    ("15", ["Julian Nagelsmann"]),
    ("16", ["Luis de la Fuente (footballer, born 1961)", "Luis de la Fuente (footballer)"]),
    ("17", ["Roberto Martínez"]),
    ("18", ["Ronald Koeman"]),
    ("19", ["Rudi Garcia"]),
    ("20", ["Zlatko Dalić"]),
    ("21", ["Murat Yakin"]),
    ("22", ["Ralf Rangnick"]),
    ("23", ["Steve Clarke"]),
    ("24", ["Ståle Solbakken"]),
    ("25", ["Graham Potter"]),
    ("26", ["Vincenzo Montella"]),
    ("27", ["Sergej Barbarez"]),
    ("28", ["Miroslav Koubek"]),
    ("29", ["Mohamed Ouahbi"]),
    ("30", ["Pape Thiaw"]),
    ("31", ["Hossam Hassan"]),
    ("32", ["Vladimir Petković"]),
    ("33", ["Hervé Renard"]),
    ("34", ["Carlos Queiroz"]),
    ("35", ["Emerse Faé"]),
    ("36", ["Hugo Broos"]),
    ("37", ["Bubista", "Pedro Leitão Brito"]),
    ("38", ["Sébastien Desabre"]),
    ("39", ["Hajime Moriyasu"]),
    ("40", ["Hong Myung-bo"]),
    ("41", ["Tony Popovic"]),
    ("42", ["Amir Ghalenoei"]),
    ("43", ["Fabio Cannavaro"]),
    ("44", ["Jamal Sellami"]),
    ("45", ["Julen Lopetegui"]),
    ("46", ["Graham Arnold"]),
    ("47", ["Giorgos Donis"]),
    ("48", ["Darren Bazeley"]),
]


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read()


def thumb_url(title):
    """Ask the Wikipedia API for the page's lead-image thumbnail URL."""
    params = {
        "action": "query",
        "format": "json",
        "redirects": "1",
        "prop": "pageimages",
        "piprop": "thumbnail|original",
        "pithumbsize": str(THUMB_SIZE),
        "titles": title,
    }
    url = API + "?" + urllib.parse.urlencode(params)
    data = json.loads(_get(url).decode("utf-8"))
    pages = data.get("query", {}).get("pages", {})
    for _, page in pages.items():
        if "thumbnail" in page and page["thumbnail"].get("source"):
            return page["thumbnail"]["source"]
        if "original" in page and page["original"].get("source"):
            return page["original"]["source"]
    return None


def save_jpeg(img_bytes, path):
    """Normalise whatever we downloaded (png/webp/jpg) to a clean JPEG."""
    im = Image.open(io.BytesIO(img_bytes))
    if im.mode not in ("RGB", "L"):
        im = im.convert("RGB")
    elif im.mode == "L":
        im = im.convert("RGB")
    im.save(path, "JPEG", quality=85, optimize=True)


def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    ok, missing = 0, []
    for cid, titles in COACHES:
        src = None
        for title in titles:
            try:
                src = thumb_url(title)
                if src:
                    break
            except Exception as e:
                print(f"  [{cid}] lookup failed for {title!r}: {e}")
            time.sleep(0.3)  # be polite to the API
        if not src:
            print(f"✗ {cid}: no image found")
            missing.append(cid)
            continue
        try:
            save_jpeg(_get(src), os.path.join(OUT_DIR, f"{cid}.jpg"))
            print(f"✓ {cid}: {src.split('/')[-1]}")
            ok += 1
        except Exception as e:
            print(f"✗ {cid}: download/convert failed: {e}")
            missing.append(cid)
        time.sleep(0.3)

    print(f"\nDone: {ok}/{len(COACHES)} images saved.")
    if missing:
        print("Missing ids (cards will show initials):", ", ".join(missing))
    # Non-zero exit only if literally nothing worked, so the Action still
    # commits partial results.
    sys.exit(1 if ok == 0 else 0)


if __name__ == "__main__":
    main()

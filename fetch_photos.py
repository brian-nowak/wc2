#!/usr/bin/env python3
"""Download a photo for each of the 48 WC2026 managers into images/NN.jpg.
Runs on GitHub Actions. Stdlib + Pillow. Order MUST match index.html."""

import io
import json
import os
import random
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

from PIL import Image

API = "https://en.wikipedia.org/w/api.php"
UA = "wc26-gaffers/1.1 (https://github.com/brian-nowak/wc2; static gallery)"
OUT_DIR = "images"
THUMB_SIZE = 640

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


def http_get(url, tries=5):
    last = None
    for attempt in range(tries):
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        try:
            with urllib.request.urlopen(req, timeout=45) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            last = e
            if e.code == 429 or 500 <= e.code < 600:
                ra = e.headers.get("Retry-After")
                wait = float(ra) if (ra and ra.isdigit()) else (2 ** attempt)
                time.sleep(min(wait, 30) + random.random())
                continue
            raise
        except (urllib.error.URLError, TimeoutError) as e:
            last = e
            time.sleep(2 ** attempt + random.random())
    raise last


def thumb_url(title):
    params = {
        "action": "query", "format": "json", "redirects": "1",
        "prop": "pageimages", "piprop": "thumbnail|original",
        "pithumbsize": str(THUMB_SIZE), "titles": title,
    }
    data = json.loads(http_get(API + "?" + urllib.parse.urlencode(params)).decode("utf-8"))
    for _, page in data.get("query", {}).get("pages", {}).items():
        if page.get("thumbnail", {}).get("source"):
            return page["thumbnail"]["source"]
        if page.get("original", {}).get("source"):
            return page["original"]["source"]
    return None


def save_jpeg(img_bytes, path):
    im = Image.open(io.BytesIO(img_bytes))
    if im.mode != "RGB":
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
            time.sleep(0.4)
        if not src:
            print(f"x {cid}: no image found")
            missing.append(cid)
            continue
        try:
            save_jpeg(http_get(src), os.path.join(OUT_DIR, f"{cid}.jpg"))
            print(f"ok {cid}")
            ok += 1
        except Exception as e:
            print(f"x {cid}: download/convert failed: {e}")
            missing.append(cid)
        time.sleep(0.6 + random.random() * 0.4)

    print(f"\nDone: {ok}/{len(COACHES)} images saved.")
    if missing:
        print("Missing ids:", ", ".join(missing))
    sys.exit(1 if ok == 0 else 0)


if __name__ == "__main__":
    main()

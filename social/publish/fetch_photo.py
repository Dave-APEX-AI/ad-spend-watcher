#!/usr/bin/env python3
"""
fetch_photo.py — grab a free, commercial-use trade photo from Pexels for use as a reel/
static background. Free, no attribution required.

Usage:  PEXELS_API_KEY=... python3 fetch_photo.py "plumber van" out.jpg
Get a free key (30 sec): https://www.pexels.com/api/  → it's instant.
"""
import os, sys, json, urllib.request, urllib.parse, urllib.error

KEY = os.environ.get("PEXELS_API_KEY", "").strip()


def main():
    if len(sys.argv) < 3:
        print("usage: fetch_photo.py <query> <out.jpg>"); return 1
    if not KEY:
        print("ERROR: set PEXELS_API_KEY (free at https://www.pexels.com/api/)"); return 1
    query, out = sys.argv[1], sys.argv[2]
    url = "https://api.pexels.com/v1/search?" + urllib.parse.urlencode(
        {"query": query, "orientation": "portrait", "per_page": 15, "size": "large"})
    req = urllib.request.Request(url, headers={
        "Authorization": KEY,
        "User-Agent": "CaillteAI/1.0 (+https://www.caillteai.com)",
        "Accept": "application/json",
    })
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        if e.code in (401, 403):
            print(f"ERROR: Pexels returned {e.code} — the PEXELS_API_KEY looks invalid. "
                  f"Check/regenerate it at https://www.pexels.com/api/ and update the secret.")
        else:
            print(f"ERROR: Pexels HTTP {e.code}")
        return 1
    photos = data.get("photos", [])
    if not photos:
        print(f"no results for '{query}'"); return 1
    # pick the first; prefer a tall/portrait source
    src = photos[0]["src"].get("portrait") or photos[0]["src"].get("large2x") or photos[0]["src"]["large"]
    imgreq = urllib.request.Request(src, headers={"User-Agent": "CaillteAI/1.0 (+https://www.caillteai.com)"})
    with urllib.request.urlopen(imgreq, timeout=60) as resp, open(out, "wb") as f:
        f.write(resp.read())
    print(out)
    return 0


if __name__ == "__main__":
    sys.exit(main())

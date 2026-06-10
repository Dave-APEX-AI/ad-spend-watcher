#!/usr/bin/env python3
"""
caillte-carousel — free, no-subscription carousel renderer.

Renders an on-brand multi-slide Instagram/Facebook carousel (1080x1350 PNGs)
from a JSON spec, using whatever headless Chromium/Chrome is on the machine.
No API, no account, no credits.

Usage:
    python3 render.py spec.json [--out OUTDIR]

spec.json shape:
{
  "name": "missed-call-maths",
  "slides": [
    {"type":"cover","kicker":"The maths","headline":"What missed calls cost you","body":"...","theme":"dark"},
    {"type":"stat","value":"£35k","label":"...lost per year","page":"2 / 6"},
    {"type":"point","index":"01","headline":"...","body":"..."},
    {"type":"quote","headline":"First to answer wins the job."},
    {"type":"cta","headline":"...","body":"Free audit — link in bio."}
  ]
}
Slide fields are documented in SKILL.md. Pages auto-number if omitted.
"""
import json, os, re, sys, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "templates", "carousel.html")
W, H = 1080, 1350

CHROME_CANDIDATES = [
    os.environ.get("CHROME_BIN", ""),
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
]

def find_chrome():
    for c in CHROME_CANDIDATES:
        if not c:
            continue
        if os.path.isfile(c) and os.access(c, os.X_OK):
            return c
        found = shutil.which(c)
        if found:
            return found
    return None

def build_slide_html(template, slide):
    payload = json.dumps(slide, ensure_ascii=False)
    # Replace the injection marker + its trailing default object literal.
    return re.sub(
        r"/\*__SLIDE_JSON__\*/\{.*?\};",
        "/*__SLIDE_JSON__*/" + payload + ";",
        template, count=1, flags=re.S,
    )

def shot(chrome, html_path, png_path):
    cmd = [
        chrome, "--headless=new", "--no-sandbox", "--hide-scrollbars",
        "--force-device-scale-factor=1", "--default-background-color=00000000",
        f"--window-size={W},{H}", f"--screenshot={png_path}",
        "file://" + html_path,
    ]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if not os.path.exists(png_path):
        # older chrome flag fallback
        cmd[1] = "--headless"
        subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(png_path)

def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec_path = sys.argv[1]
    out = "carousel-out"
    if "--out" in sys.argv:
        out = sys.argv[sys.argv.index("--out") + 1]

    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    slides = spec.get("slides", [])
    name = spec.get("name", "carousel")
    out_dir = os.path.join(out, name)
    os.makedirs(out_dir, exist_ok=True)

    chrome = find_chrome()
    if not chrome:
        print("ERROR: no Chrome/Chromium found. Set CHROME_BIN, or install with:")
        print("  apt-get install -y chromium   (Linux)   |   brew install chromium (mac)")
        print("Fallback: open templates/carousel.html in a browser, paste each slide's")
        print("JSON into the SLIDE marker, and screenshot at 1080x1350.")
        sys.exit(2)

    with open(TEMPLATE, encoding="utf-8") as f:
        template = f.read()

    n = len(slides)
    made = []
    with tempfile.TemporaryDirectory() as td:
        for i, slide in enumerate(slides, 1):
            slide.setdefault("page", f"{i} / {n}")
            html = build_slide_html(template, slide)
            hp = os.path.join(td, f"slide_{i:02d}.html")
            with open(hp, "w", encoding="utf-8") as f:
                f.write(html)
            pp = os.path.join(out_dir, f"slide_{i:02d}.png")
            ok = shot(chrome, hp, pp)
            print(("  ✓ " if ok else "  ✗ ") + pp)
            if ok:
                made.append(pp)

    print(f"\nDone: {len(made)}/{n} slides → {out_dir}/")
    if made:
        print("Post in order slide_01 → slide_%02d. Caption + hashtags: see spec or SKILL.md." % n)

if __name__ == "__main__":
    main()

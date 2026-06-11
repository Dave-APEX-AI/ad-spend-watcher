#!/usr/bin/env python3
"""
render_reel.py — free CaillteAI reel/video generator.

Renders each "card" of a reel spec to a 1080x1920 PNG (bundled Chromium, same brand
template as carousels), then stitches them into an MP4 with ffmpeg: per-card fade
in/out, a subtle slow zoom for life, and a silent AAC track (so Instagram's Reels API
accepts it). No paid tools — ffmpeg comes from the free imageio-ffmpeg package.

Usage:
  python3 render_reel.py spec.json [--out OUTDIR]

spec.json:
{
  "name": "im-your-missed-call-reel",
  "fps": 30,
  "cards": [
    {"seconds": 2.6, "type":"cover", "headline":"I'm your <span class='hl-amber'>missed call</span>.", "theme":"dark"},
    {"seconds": 2.2, "type":"quote", "headline":"You've never heard me. That's the point."},
    {"seconds": 2.6, "type":"stat",  "value":"£1,400", "label":"gone this week", "amberDot":true},
    {"seconds": 2.6, "type":"cta",   "headline":"The receptionist that never sleeps.", "body":"CaillteAI"}
  ]
}
Card fields are the carousel slide fields (cover/point/stat/quote/cta) + "seconds".
"""
import json, os, re, sys, shutil, subprocess, tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "templates", "reel.html")
W, H = 1080, 1920

CHROME_CANDIDATES = [
    os.environ.get("CHROME_BIN", ""),
    "/opt/pw-browsers/chromium-1194/chrome-linux/chrome",
    "google-chrome", "google-chrome-stable", "chromium", "chromium-browser",
]


def die(m): print("ERROR:", m, file=sys.stderr); sys.exit(1)


def find_chrome():
    for c in CHROME_CANDIDATES:
        if c and (os.path.isfile(c) and os.access(c, os.X_OK)):
            return c
        if c and shutil.which(c):
            return shutil.which(c)
    return None


def find_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg")


def build_card_html(template, card):
    payload = json.dumps(card, ensure_ascii=False)
    return re.sub(r"/\*__SLIDE_JSON__\*/\{.*?\};",
                  "/*__SLIDE_JSON__*/" + payload + ";",
                  template, count=1, flags=re.S)


def shot(chrome, html_path, png_path):
    cmd = [chrome, "--headless=new", "--no-sandbox", "--hide-scrollbars",
           "--force-device-scale-factor=1", "--default-background-color=00000000",
           f"--window-size={W},{H}", f"--screenshot={png_path}", "file://" + html_path]
    subprocess.run(cmd, capture_output=True, text=True)
    return os.path.exists(png_path)


def make_clip(ff, png, seconds, fps, clip_path):
    """Still PNG -> mp4 clip with slow zoom + fade in/out."""
    d = max(1, int(round(seconds * fps)))
    fade = min(0.4, seconds / 4)
    vf = (f"scale={W}:{H},zoompan=z='min(zoom+0.0006,1.07)':d={d}:s={W}x{H}:fps={fps},"
          f"fade=t=in:st=0:d={fade:.2f},fade=t=out:st={seconds - fade:.2f}:d={fade:.2f},"
          f"format=yuv420p")
    subprocess.run([ff, "-y", "-loop", "1", "-t", f"{seconds}", "-i", png,
                    "-vf", vf, "-r", str(fps), "-c:v", "libx264", "-preset", "veryfast",
                    clip_path], capture_output=True, text=True)
    return os.path.exists(clip_path)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "reel-out"
    name = spec.get("name", "reel")
    fps = int(spec.get("fps", 30))
    cards = spec.get("cards", [])
    if not cards:
        die("no cards in spec")

    chrome = find_chrome() or die("no Chromium found (set CHROME_BIN)")
    ff = find_ffmpeg() or die("no ffmpeg (pip install imageio-ffmpeg)")
    template = open(TEMPLATE, encoding="utf-8").read()

    out_dir = os.path.join(out, name)
    os.makedirs(out_dir, exist_ok=True)
    mp4 = os.path.join(out_dir, f"{name}.mp4")

    with tempfile.TemporaryDirectory() as td:
        clips = []
        for i, card in enumerate(cards, 1):
            card.setdefault("page", "")
            secs = float(card.get("seconds", 2.5))
            hp = os.path.join(td, f"c{i}.html"); open(hp, "w", encoding="utf-8").write(build_card_html(template, card))
            pp = os.path.join(td, f"c{i}.png")
            if not shot(chrome, hp, pp):
                die(f"failed to render card {i}")
            cp = os.path.join(td, f"c{i}.mp4")
            if not make_clip(ff, pp, secs, fps, cp):
                die(f"failed to build clip {i}")
            clips.append(cp)
            print(f"  ✓ card {i}/{len(cards)} ({secs}s)")

        concat = os.path.join(td, "list.txt")
        open(concat, "w").write("".join(f"file '{c}'\n" for c in clips))
        # concat + add a silent stereo AAC track (Instagram Reels API needs an audio stream)
        total = sum(float(c.get("seconds", 2.5)) for c in cards)
        r = subprocess.run([ff, "-y", "-f", "concat", "-safe", "0", "-i", concat,
                            "-f", "lavfi", "-t", f"{total}", "-i",
                            "anullsrc=channel_layout=stereo:sample_rate=44100",
                            "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                            "-c:a", "aac", "-shortest", "-movflags", "+faststart", mp4],
                           capture_output=True, text=True)
        if not os.path.exists(mp4):
            die("ffmpeg concat failed:\n" + r.stderr[-800:])

    size = os.path.getsize(mp4) // 1024
    print(f"\n✅ reel → {mp4}  ({size} KB, {total:.1f}s, {W}x{H})")
    print(mp4)


if __name__ == "__main__":
    main()

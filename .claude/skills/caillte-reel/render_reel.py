#!/usr/bin/env python3
"""
render_reel.py — free, GOOD CaillteAI reels.

True frame-by-frame animation (no fade-to-black, no static slideshow): an animated HTML
scene (kinetic text + live soundwave + drifting glow + progress bar) is rendered one frame
at a time with Playwright, then stitched to MP4 with ffmpeg (+ a silent AAC track so the
Instagram Reels API accepts it). All free.

Usage:  python3 render_reel.py spec.json [--out OUTDIR]
Spec: { "name":"...", "fps":30, "cards":[ {"seconds":2.4,"type":"cover","headline":"…"}, … ] }
Card types reuse the carousel set: cover / point / stat / quote / cta (+ amberDot, win, hl).
"""
import os, re, sys, json, shutil, subprocess, tempfile, math

HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "templates", "reel-anim.html")
W, H = 1080, 1920

CHROME = (os.environ.get("CHROME_BIN")
          or "/opt/pw-browsers/chromium-1194/chrome-linux/chrome")


def die(m): print("ERROR:", m, file=sys.stderr); sys.exit(1)


def find_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or die("no ffmpeg (pip install imageio-ffmpeg)")


def build_html(spec):
    tpl = open(TEMPLATE, encoding="utf-8").read()
    out = {"fps": int(spec.get("fps", 30)), "cards": spec["cards"]}
    photo = spec.get("photo")
    if photo and os.path.exists(photo):  # inline as data URL so the headless browser can load it
        import base64
        ext = os.path.splitext(photo)[1].lstrip(".").lower() or "jpeg"
        mime = "jpeg" if ext in ("jpg", "jpeg") else ext
        with open(photo, "rb") as f:
            out["photo"] = f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()
    payload = json.dumps(out, ensure_ascii=False)
    return re.sub(r"/\*__SCRIPT_JSON__\*/\{.*?\};",
                  "/*__SCRIPT_JSON__*/" + payload + ";", tpl, count=1, flags=re.S)


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "reel-out"
    name = spec.get("name", "reel")
    fps = int(spec.get("fps", 30))
    if not spec.get("cards"):
        die("spec has no cards")

    ff = find_ffmpeg()
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        die("Playwright not installed (pip install playwright). It drives the animation capture.")

    out_dir = os.path.join(out, name); os.makedirs(out_dir, exist_ok=True)
    mp4 = os.path.join(out_dir, f"{name}.mp4")
    html = build_html(spec)

    with tempfile.TemporaryDirectory() as td:
        hp = os.path.join(td, "reel.html"); open(hp, "w", encoding="utf-8").write(html)
        frames_dir = os.path.join(td, "frames"); os.makedirs(frames_dir)

        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            page.goto("file://" + hp)
            total = page.evaluate("window.__TOTAL__")
            N = max(1, int(math.ceil(total * fps)))
            for f in range(N):
                t = f / fps
                page.evaluate(f"window.renderAt({t})")
                page.screenshot(path=os.path.join(frames_dir, f"f{f:05d}.png"))
            browser.close()
        print(f"  captured {N} frames ({total:.1f}s @ {fps}fps)")

        # ── audio bed ────────────────────────────────────────────────────
        # spec "music": a file path → use it; "none" → silent; else a subtle
        # generated ambient pad (royalty-free, since it's synthesized).
        music = spec.get("music", "auto")
        common = [ff, "-y", "-framerate", str(fps), "-i", os.path.join(frames_dir, "f%05d.png")]
        if music and music not in ("auto", "none") and os.path.exists(music):
            audio_in = ["-stream_loop", "-1", "-i", music]
            amap = ["-filter:a", f"volume=0.55,afade=in:st=0:d=0.6,afade=out:st={max(0,total-1):.2f}:d=1"]
        elif music == "none":
            audio_in = ["-f", "lavfi", "-t", f"{total}",
                        "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
            amap = []
        else:  # generated subtle ambient bed (A2+E3 pad, gentle tremolo, low-passed, quiet)
            expr = "0.06*sin(2*PI*110*t)+0.045*sin(2*PI*164.81*t)+0.03*sin(2*PI*220*t)"
            audio_in = ["-f", "lavfi", "-t", f"{total}", "-i", f"aevalsrc={expr}:s=44100:c=stereo"]
            amap = ["-filter:a",
                    f"tremolo=f=4:d=0.35,lowpass=f=700,volume=0.9,afade=in:st=0:d=1,afade=out:st={max(0,total-1.2):.2f}:d=1.2"]
        r = subprocess.run(common + audio_in + amap +
                           ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
                            "-c:a", "aac", "-b:a", "128k", "-shortest", "-movflags", "+faststart", mp4],
                           capture_output=True, text=True)
        if not os.path.exists(mp4):
            die("ffmpeg failed:\n" + r.stderr[-800:])

    print(f"✅ reel → {mp4}  ({os.path.getsize(mp4)//1024} KB, {W}x{H})")
    print(mp4)


if __name__ == "__main__":
    main()

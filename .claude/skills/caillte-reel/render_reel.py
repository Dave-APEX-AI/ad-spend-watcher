#!/usr/bin/env python3
"""
render_reel.py — free, ROBUST CaillteAI reels (v3).

Re-think (2026-07-05): the old frame-by-frame animator faded every card to opacity 0
between cards, so with no photo the reel dipped to BLACK on every transition (and some
reels rendered 100% black). The audio bed was an inaudible 2 kb/s sine.

v3 fixes all three:
  1. NEVER BLACK. Each card is rendered as ONE complete still (full-bleed photo-or-gradient
     background with the text baked in). ffmpeg cross-fades between stills with a slow
     Ken Burns zoom. Two non-black stills can't cross-fade to black. If no photo is given,
     the background is a rich branded emerald gradient — never a black void.
  2. AUDIBLE MUSIC. A real synthesized bed (minor-chord pad + soft kick) mixed at a proper
     level (~0.32), 160 kbps AAC. Pass "music": "path.mp3" to use a licensed track instead.
  3. PHOTOS SHOW. Photo is inlined as a data URL and rendered full-bleed behind a legibility
     scrim. Per-card `photo` overrides the reel-level `photo`.

Usage:  python3 render_reel.py spec.json [--out OUTDIR]
Spec: { "name":"...", "fps":30, "photo":"bg.jpg"(optional),
        "cards":[ {"seconds":2.4,"type":"cover","headline":"…"}, … ] }
Card types: cover / point / stat / quote / cta / mascot  (+ amberDot, win, icon, index, kicker, body).
"""
import os, re, sys, json, shutil, subprocess, tempfile, base64, math

HERE = os.path.dirname(os.path.abspath(__file__))
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


# ── inline icon set (stroke = emerald / amber) ───────────────────────────────
ICONS = {
    "phone": '<svg viewBox="0 0 24 24" fill="none" stroke="#0FB97E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.24 11 11 0 0 0 3.5.56 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11 11 0 0 0 .56 3.5 1 1 0 0 1-.24 1z"/><path d="M16 3l5 5M21 3l-5 5" stroke="#FFC247"/></svg>',
    "alarm": '<svg viewBox="0 0 24 24" fill="none" stroke="#FFC247" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="13" r="8"/><path d="M12 9v4l2.5 2.5M5 3 2 6M19 3l3 3M9 21h6"/></svg>',
    "van": '<svg viewBox="0 0 24 24" fill="none" stroke="#0FB97E" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M3 6h11v9H3zM14 9h4l3 3v3h-7z"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/></svg>',
    "pound": '<svg viewBox="0 0 24 24" fill="none" stroke="#FFC247" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round"><path d="M16 6a4 4 0 0 0-7 2.6V12H7m0 0h6m-6 0v3.5C7 17 6 18 6 18h11"/></svg>',
}

CSS = """
*{margin:0;padding:0;box-sizing:border-box}
html,body{width:1080px;height:1920px;overflow:hidden;
  font-family:"Inter","Segoe UI",-apple-system,Roboto,Arial,sans-serif;
  color:#F5F3EC;-webkit-font-smoothing:antialiased}
#stage{position:relative;width:1080px;height:1920px;overflow:hidden;
  background:radial-gradient(1200px 900px at 70% 12%, #0f3b2c 0%, #0c241c 45%, #081511 100%)}
#photobg{position:absolute;inset:0;background-size:cover;background-position:center}
#scrim{position:absolute;inset:0;
  background:linear-gradient(180deg, rgba(8,21,17,.62) 0%, rgba(8,21,17,.72) 45%, rgba(8,21,17,.90) 100%)}
#glow{position:absolute;width:1400px;height:1400px;border-radius:50%;left:-260px;top:-320px;
  background:radial-gradient(circle, rgba(15,185,126,.30), rgba(15,185,126,0) 62%);filter:blur(10px)}
#grain{position:absolute;inset:0;opacity:.05;
  background-image:radial-gradient(rgba(255,255,255,.6) 1px, transparent 1px);background-size:6px 6px}
#brand{position:absolute;top:70px;left:84px;display:flex;align-items:center;gap:20px;
  font-size:36px;font-weight:800;letter-spacing:-.5px;z-index:6}
.dot{width:30px;height:30px;border-radius:50%;background:#FFC247;box-shadow:0 0 26px #FFC247}
#handle{position:absolute;bottom:96px;left:0;width:100%;text-align:center;
  font-size:32px;font-weight:700;color:#8fb8a8;z-index:6}
#wave{position:absolute;bottom:170px;left:0;width:100%;display:flex;justify-content:center;
  align-items:flex-end;gap:12px;height:96px;z-index:5}
#wave i{width:13px;border-radius:8px;background:#0FB97E}
#card{position:absolute;inset:0;display:flex;flex-direction:column;justify-content:center;
  padding:140px 96px;z-index:4}
.icon{width:190px;height:190px;margin-bottom:46px}.icon svg{width:100%;height:100%}
.kicker{font-size:38px;font-weight:800;letter-spacing:3px;text-transform:uppercase;color:#0FB97E;margin-bottom:34px}
.kicker.amber{color:#FFC247}
h1{font-size:130px;line-height:1.02;font-weight:900;letter-spacing:-4px;text-shadow:0 4px 30px rgba(0,0,0,.45)}
h2{font-size:100px;line-height:1.05;font-weight:900;letter-spacing:-2px;text-shadow:0 4px 30px rgba(0,0,0,.45)}
.body{font-size:54px;line-height:1.3;font-weight:500;color:#dfe7e2;margin-top:40px}
.index{font-size:150px;font-weight:900;color:#0FB97E;line-height:.9;letter-spacing:-6px;margin-bottom:20px}
.stat{font-size:360px;font-weight:900;line-height:.82;letter-spacing:-14px;color:#FFC247;text-shadow:0 6px 40px rgba(0,0,0,.5);white-space:nowrap}
.stat.win{color:#13d18d}
.stat-label{font-size:58px;font-weight:700;color:#b7c6be;margin-top:34px}
.quote{font-size:108px;line-height:1.12;font-weight:800;letter-spacing:-2px;text-shadow:0 4px 30px rgba(0,0,0,.45)}
.quote::before{content:"\\201C";color:#0FB97E;font-size:160px;line-height:0;display:block;margin-bottom:44px}
.hl{color:#0FB97E}.hl-amber{color:#FFC247}
.cta-card{background:#0FB97E;color:#08150f;border-radius:52px;padding:84px;box-shadow:0 30px 80px rgba(0,0,0,.4)}
.cta-card .big{font-size:88px;font-weight:900;letter-spacing:-2px;line-height:1.05}
.cta-card .sub{font-size:48px;font-weight:700;margin-top:24px}
"""


def card_html(c, photo_data, wave_bars):
    amber = "amber" if c.get("amberDot") else ""
    ic = f'<div class="icon">{ICONS[c["icon"]]}</div>' if c.get("icon") in ICONS else ""
    t = c.get("type", "cover")
    if t == "cover":
        inner = ic + (f'<div class="kicker {amber}">{c["kicker"]}</div>' if c.get("kicker") else "") \
                + f'<h1>{c.get("headline","")}</h1>' + (f'<div class="body">{c["body"]}</div>' if c.get("body") else "")
    elif t == "point":
        inner = ic + (f'<div class="index">{c["index"]}</div>' if c.get("index") else "") \
                + f'<h2>{c.get("headline","")}</h2>' + (f'<div class="body">{c["body"]}</div>' if c.get("body") else "")
    elif t == "stat":
        inner = ic + f'<div class="stat {"win" if c.get("win") else ""}">{c.get("value","")}</div>' \
                + (f'<div class="stat-label">{c["label"]}</div>' if c.get("label") else "")
    elif t == "quote":
        inner = f'<div class="quote">{c.get("headline","")}</div>'
    elif t == "cta":
        inner = f'<div class="cta-card"><div class="big">{c.get("headline","")}</div>' \
                + (f'<div class="sub">{c["body"]}</div>' if c.get("body") else "") + '</div>'
    else:
        inner = f'<h1>{c.get("headline","")}</h1>'

    photo = c.get("_photo_data") or photo_data
    photo_div = f'<div id="photobg" style="background-image:url({photo})"></div><div id="scrim"></div>' if photo else ""
    # a static soundwave silhouette (varied heights) so the frame reads as "audio / voice"
    bars = "".join(f'<i style="height:{h}px;opacity:{0.45+0.5*(h/86):.2f}"></i>' for h in wave_bars)
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>{CSS}</style></head><body>
<div id="stage">{photo_div}<div id="glow"></div><div id="grain"></div>
<div id="brand"><span class="dot"></span>CaillteAI</div>
<div id="card">{inner}</div>
<div id="wave">{bars}</div><div id="handle">@caillte_ai</div></div>
<script>
/* shrink oversized single-line text (stat/headline) so nothing clips the frame edge */
(function(){{
  var card=document.getElementById('card');
  var avail=card.clientWidth - 192;               // padding is 96px each side
  ['.stat','h1','h2','.quote'].forEach(function(sel){{
    var el=card.querySelector(sel); if(!el) return;
    var fs=parseFloat(getComputedStyle(el).fontSize), guard=0;
    while(el.scrollWidth>avail && fs>40 && guard++<80){{ fs*=0.94; el.style.fontSize=fs+'px'; }}
  }});
}})();
</script></body></html>"""


def inline_photo(path):
    if not path or not os.path.exists(path):
        return None
    ext = os.path.splitext(path)[1].lstrip(".").lower() or "jpeg"
    mime = "jpeg" if ext in ("jpg", "jpeg") else ext
    with open(path, "rb") as f:
        return f"data:image/{mime};base64," + base64.b64encode(f.read()).decode()


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "reel-out"
    name = spec.get("name", "reel")
    fps = int(spec.get("fps", 30))
    cards = spec.get("cards") or die("spec has no cards")
    XF = 0.3  # crossfade seconds between cards (short = crisp for big-number stats)

    ff = find_ffmpeg()
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        die("Playwright not installed (pip install playwright).")

    reel_photo = inline_photo(spec.get("photo"))
    for c in cards:  # per-card photo override
        if c.get("photo"):
            c["_photo_data"] = inline_photo(c["photo"])

    out_dir = os.path.join(out, name); os.makedirs(out_dir, exist_ok=True)
    mp4 = os.path.join(out_dir, f"{name}.mp4")

    with tempfile.TemporaryDirectory() as td:
        # 1) render each card to ONE still PNG (guaranteed non-black — bg + text baked in)
        stills = []
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            for i, c in enumerate(cards):
                # deterministic soundwave heights per card (no Math.random — reproducible)
                wave = [18 + int(68 * abs(math.sin(i * 1.3 + k * 0.55) * math.cos(k * 0.31))) for k in range(28)]
                hp = os.path.join(td, f"c{i}.html")
                open(hp, "w", encoding="utf-8").write(card_html(c, reel_photo, wave))
                page.goto("file://" + hp)
                png = os.path.join(td, f"c{i:02d}.png")
                page.screenshot(path=png)
                stills.append((png, float(c.get("seconds", 2.4))))
            browser.close()

        # 2) per-card segment: Ken Burns slow zoom on the still (never black)
        segs = []
        for i, (png, secs) in enumerate(stills):
            seg = os.path.join(td, f"seg{i:02d}.mp4")
            frames = max(1, int(round(secs * fps)))
            # gentle zoom 1.0 → 1.06 across the card
            zoom = f"scale=8000:-1,zoompan=z='min(1.0+0.06*on/{frames},1.06)':d={frames}:s={W}x{H}:fps={fps}"
            subprocess.run([ff, "-y", "-loop", "1", "-i", png, "-t", f"{secs}",
                            "-vf", zoom, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), seg],
                           capture_output=True, text=True)
            os.path.exists(seg) or die(f"segment {i} failed")
            segs.append((seg, secs))

        # 3) chain segments with xfade crossfades (two non-black stills → never black)
        video = os.path.join(td, "video.mp4")
        if len(segs) == 1:
            shutil.copy(segs[0][0], video)
            total = segs[0][1]
        else:
            inputs, filt, prev, offset = [], "", "[0:v]", 0.0
            for i, (seg, _) in enumerate(segs):
                inputs += ["-i", seg]
            for i in range(1, len(segs)):
                offset += segs[i - 1][1] - XF
                lbl = f"[v{i}]" if i < len(segs) - 1 else "[vout]"
                filt += f"{prev}[{i}:v]xfade=transition=fade:duration={XF}:offset={offset:.3f}{lbl};"
                prev = lbl
            filt = filt.rstrip(";")
            total = sum(s for _, s in segs) - XF * (len(segs) - 1)
            r = subprocess.run([ff, "-y"] + inputs + ["-filter_complex", filt,
                                "-map", "[vout]", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps), video],
                               capture_output=True, text=True)
            os.path.exists(video) or die("xfade assembly failed:\n" + r.stderr[-900:])

        # 4) audible music bed — real bed unless spec gives a licensed track
        music = spec.get("music", "auto")
        if music and music not in ("auto", "none") and os.path.exists(music):
            audio_in = ["-stream_loop", "-1", "-i", music]
            amap = ["-filter:a", f"volume=0.5,afade=in:st=0:d=0.6,afade=out:st={max(0,total-1):.2f}:d=1"]
        elif music == "none":
            audio_in = ["-f", "lavfi", "-t", f"{total}", "-i", "anullsrc=channel_layout=stereo:sample_rate=44100"]
            amap = []
        else:
            # minor-chord pad (A2/C4/E4) + soft 2/4 kick in ONE mono expr, upmixed to stereo.
            expr = ("0.10*sin(2*PI*110*t)+0.08*sin(2*PI*261.63*t)+0.06*sin(2*PI*329.63*t)"
                    "+0.5*sin(2*PI*55*t)*exp(-6*mod(t\\,0.5))")
            audio_in = ["-f", "lavfi", "-t", f"{total}", "-i", f"aevalsrc={expr}:s=44100:c=mono"]
            amap = ["-filter_complex",
                    "[1:a]lowpass=f=1200,tremolo=f=3:d=0.25,loudnorm=I=-16:TP=-1.5,"
                    f"afade=in:st=0:d=1,afade=out:st={max(0,total-1.2):.2f}:d=1.2,"
                    "aformat=channel_layouts=stereo[aud]",
                    "-map", "0:v", "-map", "[aud]"]

        cmd = [ff, "-y", "-i", video] + audio_in
        if "-filter_complex" in amap:
            cmd += amap
        else:
            cmd += (["-map", "0:v", "-map", "1:a"] + amap)
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4]
        r = subprocess.run(cmd, capture_output=True, text=True)
        os.path.exists(mp4) or die("mux failed:\n" + r.stderr[-900:])

    print(f"✅ reel → {mp4}  ({os.path.getsize(mp4)//1024} KB, {W}x{H}, {total:.1f}s)")
    print(mp4)


if __name__ == "__main__":
    main()

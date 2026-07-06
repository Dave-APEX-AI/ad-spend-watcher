#!/usr/bin/env python3
"""
render_phone_reel.py — CaillteAI "The Phone" reel engine.

A totally different format from text-on-photo cards: the reel IS a phone screen. An
incoming call that would've been missed gets answered by the AI; the conversation types
in bubble-by-bubble (with typing dots), then a "Job booked" card pops. It shows the
product working. Faceless, mobile-native, free (Chromium frame capture + ffmpeg).

Continuous scene (phone + emerald gradient always on screen → never black). renderAt(t)
reveals each turn at its time. Audio: a ring for the first ~1s, then a soft music bed,
plus a ding when the job books.

Usage: python3 render_phone_reel.py spec.json [--out OUTDIR]
Spec:
{
  "name":"phone-boiler", "fps":30,
  "caller":"New customer", "context":"8:47 PM · you're up a ladder",
  "turns":[ {"who":"cust","text":"...","at":1.3}, {"who":"ai","text":"...","at":3.6}, ... ],
  "booking":{"title":"Boiler repair — Tue 9:00 AM","meta":"Details texted to you.","at":7.4},
  "caption":"The call you'd have <hl>missed</hl>.", "total":9.6
}
"""
import os, re, sys, json, shutil, subprocess, tempfile, math

W, H = 1080, 1920
CHROME = os.environ.get("CHROME_BIN") or "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"


def die(m): print("ERROR:", m, file=sys.stderr); sys.exit(1)


def find_ffmpeg():
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except Exception:
        return shutil.which("ffmpeg") or die("no ffmpeg")


def build_html(spec):
    turns = spec.get("turns", [])
    booking = spec.get("booking")
    rows = ""
    for i, tn in enumerate(turns):
        side = "cust" if tn["who"] == "cust" else "ai"
        lbl = "Caller" if side == "cust" else "CaillteAI"
        rows += (f'<div class="item" data-at="{tn["at"]}" data-side="{side}">'
                 f'<div class="lbl {side}L">{lbl}</div>'
                 f'<div class="typing {side}"><i></i><i></i><i></i></div>'
                 f'<div class="bubble {side}">{tn["text"]}</div></div>')
    book_html = ""
    if booking:
        book_html = (f'<div class="item booked-wrap" data-at="{booking["at"]}" data-book="1">'
                     f'<div class="booked"><div class="t"><span class="check">✓</span>Job booked</div>'
                     f'<div class="big">{booking["title"]}</div>'
                     f'<div class="meta">{booking.get("meta","")}</div></div></div>')
    caption = spec.get("caption", "")
    ctx = spec.get("context", "")
    caller = spec.get("caller", "New customer")
    total = float(spec.get("total") or ((booking or turns[-1])["at"] + 2.4))
    return TEMPLATE.replace("__ROWS__", rows).replace("__BOOK__", book_html) \
        .replace("__CAPTION__", caption).replace("__CTX__", ctx).replace("__CALLER__", caller) \
        .replace("__TOTALV__", f"{total:.3f}"), total


TEMPLATE = r"""<!doctype html><html><head><meta charset="utf-8"><style>
*{margin:0;padding:0;box-sizing:border-box;font-family:-apple-system,"SF Pro Display","Inter","Segoe UI",Roboto,Arial,sans-serif}
html,body{width:1080px;height:1920px;overflow:hidden}
#stage{position:relative;width:1080px;height:1920px;
  background:radial-gradient(1200px 900px at 50% 16%, #0f3b2c 0%, #0c241c 46%, #071410 100%)}
#glow{position:absolute;width:1300px;height:1300px;border-radius:50%;left:-200px;top:-300px;
  background:radial-gradient(circle, rgba(15,185,126,.22), rgba(15,185,126,0) 62%);filter:blur(12px)}
#brand{position:absolute;top:74px;left:0;width:100%;text-align:center;color:#eafff6;font-size:34px;
  font-weight:800;letter-spacing:-.4px;z-index:6;display:flex;align-items:center;justify-content:center;gap:14px}
#brand .dot{width:24px;height:24px;border-radius:50%;background:#FFC247;box-shadow:0 0 20px #FFC247}
.phone{position:absolute;top:200px;left:50%;transform:translateX(-50%);width:648px;height:1300px;
  border-radius:80px;background:#05100c;border:14px solid #16241e;
  box-shadow:0 40px 120px rgba(0,0,0,.6), inset 0 0 0 3px #0b1712;overflow:hidden}
.notch{position:absolute;top:24px;left:50%;transform:translateX(-50%);width:176px;height:34px;background:#05100c;border-radius:20px;z-index:5}
.statusbar{position:absolute;top:26px;left:0;width:100%;display:flex;justify-content:space-between;padding:4px 46px;color:#eafff6;font-size:26px;font-weight:700;z-index:4}
.screen{position:absolute;inset:0;padding:118px 40px 40px;display:flex;flex-direction:column}
.callrow{display:flex;align-items:center;gap:20px;padding-bottom:22px;border-bottom:1px solid #16302738}
.avatar{width:92px;height:92px;border-radius:50%;flex:0 0 92px;background:linear-gradient(150deg,#0FB97E,#0a8f5f);
  display:flex;align-items:center;justify-content:center;box-shadow:0 0 34px rgba(15,185,126,.5)}
.avatar svg{width:46px;height:46px}
.who{color:#fff;font-size:38px;font-weight:800;letter-spacing:-.5px;line-height:1.05}
.sub{color:#7c8f87;font-size:24px;font-weight:600;margin-top:4px}
.tag{margin-left:auto;flex:0 0 auto;background:rgba(15,185,126,.16);color:#25d69a;font-size:23px;font-weight:800;
  padding:10px 16px;border-radius:999px;display:flex;align-items:center;gap:9px}
.tag .d{width:13px;height:13px;border-radius:50%;background:#25d69a}
.tscript{flex:1;display:flex;flex-direction:column;justify-content:flex-end;gap:22px;padding-top:22px;overflow:hidden}
.item{opacity:0}
.lbl{font-size:21px;font-weight:800;letter-spacing:1px;text-transform:uppercase;margin-bottom:8px}
.aiL{color:#25d69a}.custL{color:#0a8f5f;text-align:right}
.bubble{max-width:88%;padding:24px 28px;border-radius:28px;font-size:31px;line-height:1.3;font-weight:600}
.ai{align-self:flex-start;background:#12241d;color:#eafff6;border-bottom-left-radius:9px;border:1px solid #1d3a30}
.cust{align-self:flex-end;background:#0FB97E;color:#05231a;border-bottom-right-radius:9px;font-weight:700}
.typing{display:none;align-items:center;gap:10px;padding:22px 26px;border-radius:26px;width:118px}
.typing.ai{align-self:flex-start;background:#12241d;border:1px solid #1d3a30}
.typing.cust{align-self:flex-end;background:#0b7d55}
.typing i{width:14px;height:14px;border-radius:50%;background:#7fe9c0;opacity:.5}
.booked-wrap{align-self:stretch}
.booked{background:#0FB97E;border-radius:32px;padding:30px 32px;color:#05231a;box-shadow:0 18px 44px rgba(15,185,126,.4)}
.booked .t{font-size:27px;font-weight:900;letter-spacing:.5px;text-transform:uppercase;display:flex;align-items:center;gap:13px}
.booked .big{font-size:44px;font-weight:900;letter-spacing:-1px;margin-top:12px;line-height:1.05}
.booked .meta{font-size:26px;font-weight:700;margin-top:8px;opacity:.82;line-height:1.25}
.check{width:40px;height:40px;border-radius:50%;background:#05231a;color:#0FB97E;display:flex;align-items:center;justify-content:center;font-size:26px}
#caption{position:absolute;bottom:120px;left:0;width:100%;text-align:center;padding:0 90px;z-index:6}
#caption h1{color:#fff;font-size:78px;font-weight:900;letter-spacing:-2px;line-height:1.04;text-shadow:0 4px 30px rgba(0,0,0,.55)}
#caption h1 .hl{color:#25d69a}
</style></head><body>
<div id="stage">
  <div id="glow"></div>
  <div id="brand"><span class="dot"></span>CaillteAI</div>
  <div class="phone">
    <div class="notch"></div>
    <div class="statusbar"><span>9:41</span><span>5G ▪▪▪</span></div>
    <div class="screen">
      <div class="callrow">
        <div class="avatar"><svg viewBox="0 0 24 24" fill="none" stroke="#fff" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><path d="M6.6 10.8a15 15 0 0 0 6.6 6.6l2.2-2.2a1 1 0 0 1 1-.24 11 11 0 0 0 3.5.56 1 1 0 0 1 1 1V20a1 1 0 0 1-1 1A17 17 0 0 1 3 4a1 1 0 0 1 1-1h3.5a1 1 0 0 1 1 1 11 11 0 0 0 .56 3.5 1 1 0 0 1-.24 1z"/></svg></div>
        <div><div class="who">__CALLER__</div><div class="sub" id="callsub">Incoming…</div></div>
        <div class="tag" id="aitag"><span class="d"></span><span id="tagtxt">ringing</span></div>
      </div>
      <div class="tscript" id="tscript">__ROWS____BOOK__</div>
    </div>
  </div>
  <div id="caption"><h1>__CAPTION__</h1></div>
</div>
<script>
  const TOTAL=__TOTALV__;
  const items=[...document.querySelectorAll('.item')];
  const tag=document.getElementById('tagtxt'), aitag=document.getElementById('aitag'), callsub=document.getElementById('callsub');
  const easeOut=x=>1-Math.pow(1-x,3);
  window.renderAt=function(t){
    // header state: ringing → missed → AI answering
    if(t<1.0){ tag.textContent='ringing'; callsub.textContent='Incoming…'; aitag.style.background='rgba(255,194,71,.18)'; aitag.style.color='#FFC247'; aitag.querySelector('.d').style.background='#FFC247'; }
    else if(t<1.7){ tag.textContent='missed'; callsub.textContent="would've gone to voicemail"; aitag.style.background='rgba(255,90,90,.18)'; aitag.style.color='#ff7a7a'; aitag.querySelector('.d').style.background='#ff5a5a'; }
    else { const pulse=0.6+0.4*Math.abs(Math.sin(t*4)); tag.textContent='AI answering'; callsub.textContent='CaillteAI picked up'; aitag.style.background='rgba(15,185,126,.16)'; aitag.style.color='#25d69a'; const d=aitag.querySelector('.d'); d.style.background='#25d69a'; d.style.opacity=pulse; }
    for(const it of items){
      const at=parseFloat(it.dataset.at), isBook=it.dataset.book==='1', side=it.dataset.side;
      const typing=it.querySelector('.typing'), bubble=it.querySelector('.bubble, .booked'), lbl=it.querySelector('.lbl');
      const typeStart=at-0.6;
      if(t<typeStart){ it.style.opacity=0; }
      else if(t<at && !isBook){ // typing dots phase
        it.style.opacity=1; it.style.transform='none';
        if(lbl) lbl.style.opacity=0;
        if(typing){ typing.style.display='flex'; if(bubble) bubble.style.display='none';
          const dots=typing.querySelectorAll('i'); dots.forEach((d,k)=>d.style.opacity=(0.35+0.55*Math.abs(Math.sin(t*7+k*0.9))).toFixed(2)); }
      } else { // revealed bubble
        const p=Math.min(1,(t-at)/0.34), e=easeOut(p);
        it.style.opacity=1;
        if(typing) typing.style.display='none';
        if(bubble){ bubble.style.display=''; }
        if(lbl) lbl.style.opacity=1;
        const sc=(0.9+0.1*e).toFixed(3), ty=((1-e)*24).toFixed(1);
        it.style.transform=`translateY(${ty}px)`;
        if(bubble) bubble.style.transform=`scale(${sc})`;
        if(isBook && bubble){ bubble.style.transformOrigin='center'; bubble.style.transform=`scale(${(0.86+0.14*e).toFixed(3)})`; }
      }
    }
  };
  renderAt(0);
</script></body></html>"""


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec = json.load(open(sys.argv[1], encoding="utf-8"))
    out = sys.argv[sys.argv.index("--out") + 1] if "--out" in sys.argv else "reel-out"
    name = spec.get("name", "phone-reel")
    fps = int(spec.get("fps", 30))
    ff = find_ffmpeg()
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        die("Playwright not installed")

    html, total = build_html(spec)
    booking_at = float(spec["booking"]["at"]) if spec.get("booking") else total - 1.5
    out_dir = os.path.join(out, name); os.makedirs(out_dir, exist_ok=True)
    mp4 = os.path.join(out_dir, f"{name}.mp4")

    with tempfile.TemporaryDirectory() as td:
        hp = os.path.join(td, "p.html"); open(hp, "w", encoding="utf-8").write(html)
        frames = os.path.join(td, "f"); os.makedirs(frames)
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=CHROME, args=["--no-sandbox"])
            pg = b.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
            pg.goto("file://" + hp)
            N = max(1, int(math.ceil(total * fps)))
            for f in range(N):
                pg.evaluate(f"window.renderAt({f/fps})")
                pg.screenshot(path=os.path.join(frames, f"f{f:05d}.png"))
            b.close()
        print(f"  captured {N} frames ({total:.1f}s)")

        # audio: ring (first ~1s) → music bed; ding at booking
        bt = booking_at
        ring = "(0.28*sin(2*PI*440*t)+0.28*sin(2*PI*480*t))"
        bed = "(0.10*sin(2*PI*110*t)+0.08*sin(2*PI*261.63*t)+0.06*sin(2*PI*329.63*t))"
        ding = f"0.5*sin(2*PI*880*t)*exp(-7*max(0\\,t-{bt:.2f}))*gt(t\\,{bt:.2f})"
        expr = f"if(lt(t\\,1.05)\\,{ring}\\,{bed})+{ding}"
        audio_in = ["-f", "lavfi", "-t", f"{total}", "-i", f"aevalsrc={expr}:s=44100:c=mono"]
        af = ("[1:a]lowpass=f=2200,loudnorm=I=-16:TP=-1.5,"
              f"afade=in:st=0:d=0.4,afade=out:st={max(0,total-1.0):.2f}:d=1,"
              "aformat=channel_layouts=stereo[aud]")
        cmd = [ff, "-y", "-framerate", str(fps), "-i", os.path.join(frames, "f%05d.png")] + audio_in + \
              ["-filter_complex", af, "-map", "0:v", "-map", "[aud]",
               "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
               "-c:a", "aac", "-b:a", "160k", "-shortest", "-movflags", "+faststart", mp4]
        r = subprocess.run(cmd, capture_output=True, text=True)
        os.path.exists(mp4) or die("ffmpeg failed:\n" + r.stderr[-900:])

    print(f"✅ phone reel → {mp4}  ({os.path.getsize(mp4)//1024} KB, {total:.1f}s)")
    print(mp4)


if __name__ == "__main__":
    main()

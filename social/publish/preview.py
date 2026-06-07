#!/usr/bin/env python3
"""
preview.py — build a phone-friendly, swipeable HTML preview of a carousel spec.

No Chrome needed (it's just HTML your phone renders). Each slide is the EXACT
carousel template (faithful to the final PNG), shown in a scroll-snap swiper scaled
to the screen. Great for previewing on mobile before you render/post.

Usage:  python3 social/publish/preview.py social/content/week1/03-missed-call-maths.json
Output: social/out/preview-<name>.html
"""
import os, sys, json, html, importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
RENDER = os.path.join(HERE, "..", "..", ".claude", "skills", "caillte-carousel", "render.py")


def load_render():
    spec = importlib.util.spec_from_file_location("render", RENDER)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def main():
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    spec_path = sys.argv[1]
    r = load_render()
    template = open(r.TEMPLATE, encoding="utf-8").read()
    spec = json.load(open(spec_path, encoding="utf-8"))
    name = spec.get("name", "carousel")
    slides = spec.get("slides", [])
    n = len(slides)

    frames = []
    for i, slide in enumerate(slides, 1):
        slide.setdefault("page", f"{i} / {n}")
        srcdoc = html.escape(r.build_slide_html(template, slide), quote=True)
        frames.append(f'<div class="frame"><iframe loading="lazy" srcdoc="{srcdoc}"></iframe></div>')

    dots = "".join('<span class="dot"></span>' for _ in slides)
    out_html = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width,initial-scale=1,maximum-scale=1"/>
<title>CaillteAI preview — {html.escape(name)}</title>
<style>
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{background:#050806;color:#F5F3EC;font-family:-apple-system,Segoe UI,Roboto,Arial,sans-serif;
        min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:14px 0 22px}}
  .hd{{font-weight:800;letter-spacing:-.3px;font-size:15px;margin-bottom:4px}}
  .hd .g{{color:#0FB97E}}
  .sub{{color:#8A938F;font-size:12px;margin-bottom:12px}}
  .swiper{{display:flex;gap:14px;overflow-x:auto;scroll-snap-type:x mandatory;
           width:100%;padding:0 14px 6px;-webkit-overflow-scrolling:touch}}
  .swiper::-webkit-scrollbar{{display:none}}
  .frame{{flex:0 0 auto;scroll-snap-align:center;overflow:hidden;border-radius:16px;
          box-shadow:0 10px 40px rgba(0,0,0,.5)}}
  .frame iframe{{width:1080px;height:1350px;border:0;transform-origin:top left}}
  .counter{{margin-top:12px;font-size:12px;color:#8A938F}}
  .dots{{display:flex;gap:7px;margin-top:8px}}
  .dots .dot{{width:7px;height:7px;border-radius:50%;background:#2a3a31;transition:.2s}}
  .dots .dot.on{{background:#0FB97E;width:18px;border-radius:4px}}
  .tip{{color:#8A938F;font-size:11px;margin-top:14px}}
</style></head><body>
  <div class="hd">Caillte<span class="g">AI</span> · carousel preview</div>
  <div class="sub">{html.escape(name)} — swipe sideways →</div>
  <div class="swiper" id="sw">{''.join(frames)}</div>
  <div class="dots" id="dots">{dots}</div>
  <div class="counter" id="ct">1 / {n}</div>
  <div class="tip">This is a live preview of the slides — final posts render as crisp 1080×1350 PNGs.</div>
<script>
  const sw=document.getElementById('sw'), dots=[...document.querySelectorAll('#dots .dot')], ct=document.getElementById('ct');
  function fit(){{
    const w=Math.min(window.innerWidth-28, 430);
    const s=w/1080, h=1350*s;
    document.querySelectorAll('.frame').forEach(f=>{{f.style.width=w+'px';f.style.height=h+'px';
      f.querySelector('iframe').style.transform='scale('+s+')';}});
  }}
  function active(){{
    const i=Math.round(sw.scrollLeft/(sw.scrollWidth/{n}));
    dots.forEach((d,k)=>d.classList.toggle('on',k===Math.min(i,{n}-1)));
    ct.textContent=(Math.min(i,{n}-1)+1)+' / {n}';
  }}
  window.addEventListener('resize',fit); sw.addEventListener('scroll',active);
  fit(); dots[0].classList.add('on');
</script></body></html>"""

    out_dir = os.path.join(HERE, "..", "..", "social", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, f"preview-{name}.html"))
    open(out_path, "w", encoding="utf-8").write(out_html)
    print(out_path)


if __name__ == "__main__":
    main()

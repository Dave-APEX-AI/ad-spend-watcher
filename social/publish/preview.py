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
          box-shadow:0 10px 40px rgba(0,0,0,.5);position:relative}}
  .frame iframe{{width:1080px;height:1350px;border:0;transform-origin:top left;pointer-events:none}}
  .nav{{display:flex;align-items:center;gap:18px;margin-top:14px}}
  .nav button{{width:54px;height:54px;border-radius:50%;border:0;background:#0FB97E;color:#06120c;
    font-size:24px;font-weight:900;cursor:pointer;line-height:1;box-shadow:0 4px 18px rgba(15,185,126,.4)}}
  .nav button:disabled{{background:#243029;color:#5b6b62;box-shadow:none}}
  .tapzone{{position:fixed;top:0;bottom:0;width:32%;z-index:5}}
  .tapzone.l{{left:0}} .tapzone.r{{right:0}}
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
  <div class="nav"><button id="prev" aria-label="Previous">‹</button>
    <span class="counter" id="ct">1 / {n}</span>
    <button id="next" aria-label="Next">›</button></div>
  <div class="tip">Use the arrows, tap the screen edges, or swipe. Final posts render as 1080×1350 PNGs.</div>
  <div class="tapzone l" id="tzl"></div><div class="tapzone r" id="tzr"></div>
<script>
  const N={n};
  const sw=document.getElementById('sw'), frames=[...document.querySelectorAll('.frame')];
  const dots=[...document.querySelectorAll('#dots .dot')], ct=document.getElementById('ct');
  const prev=document.getElementById('prev'), next=document.getElementById('next');
  let cur=0;
  function fit(){{
    const w=Math.min(window.innerWidth-28, 430), s=w/1080, h=1350*s;
    frames.forEach(f=>{{f.style.width=w+'px';f.style.height=h+'px';
      f.querySelector('iframe').style.transform='scale('+s+')';}});
    go(cur,false);
  }}
  function paint(){{
    dots.forEach((d,k)=>d.classList.toggle('on',k===cur));
    ct.textContent=(cur+1)+' / '+N;
    prev.disabled=(cur===0); next.disabled=(cur===N-1);
  }}
  function go(i,smooth){{
    cur=Math.max(0,Math.min(N-1,i));
    frames[cur].scrollIntoView({{behavior:smooth?'smooth':'auto',inline:'center',block:'nearest'}});
    paint();
  }}
  prev.onclick=()=>go(cur-1,true); next.onclick=()=>go(cur+1,true);
  document.getElementById('tzl').onclick=()=>go(cur-1,true);
  document.getElementById('tzr').onclick=()=>go(cur+1,true);
  let t=null; sw.addEventListener('scroll',()=>{{clearTimeout(t);t=setTimeout(()=>{{
    cur=Math.round(sw.scrollLeft/(sw.scrollWidth/N)); cur=Math.max(0,Math.min(N-1,cur)); paint();
  }},90);}});
  window.addEventListener('resize',fit); fit();
</script></body></html>"""

    out_dir = os.path.join(HERE, "..", "..", "social", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, f"preview-{name}.html"))
    open(out_path, "w", encoding="utf-8").write(out_html)
    print(out_path)


if __name__ == "__main__":
    main()

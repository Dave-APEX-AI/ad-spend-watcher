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
        min-height:100vh;display:flex;flex-direction:column;align-items:center;padding:14px 0 26px}}
  .hd{{font-weight:800;letter-spacing:-.3px;font-size:15px;margin-bottom:4px}}
  .hd .g{{color:#0FB97E}}
  .sub{{color:#8A938F;font-size:12px;margin-bottom:12px}}
  .viewport{{overflow:hidden;border-radius:16px;box-shadow:0 10px 40px rgba(0,0,0,.5);position:relative}}
  .track{{display:flex;will-change:transform;transition:transform .28s ease}}
  .frame{{flex:0 0 100%;overflow:hidden}}
  .frame iframe{{width:1080px;height:1350px;border:0;transform-origin:top left;pointer-events:none}}
  /* tap halves over the slide to advance */
  .half{{position:absolute;top:0;bottom:0;width:50%;z-index:6}}
  .half.l{{left:0}} .half.r{{right:0}}
  .nav{{display:flex;align-items:center;gap:20px;margin-top:16px;z-index:10}}
  .nav button{{width:58px;height:58px;border-radius:50%;border:0;background:#0FB97E;color:#06120c;
    font-size:26px;font-weight:900;cursor:pointer;line-height:1;box-shadow:0 4px 18px rgba(15,185,126,.4)}}
  .nav button:active{{transform:scale(.92)}}
  .nav button:disabled{{background:#243029;color:#5b6b62;box-shadow:none}}
  .counter{{font-size:13px;color:#cfd6d1;font-weight:700;min-width:46px;text-align:center}}
  .dots{{display:flex;gap:7px;margin-top:10px;flex-wrap:wrap;justify-content:center;max-width:90%}}
  .dots .dot{{width:7px;height:7px;border-radius:50%;background:#2a3a31;transition:.2s}}
  .dots .dot.on{{background:#0FB97E;width:18px;border-radius:4px}}
  .tip{{color:#8A938F;font-size:11px;margin-top:14px;text-align:center;max-width:90%}}
</style></head><body>
  <div class="hd">Caillte<span class="g">AI</span> · carousel preview</div>
  <div class="sub">{html.escape(name)}</div>
  <div class="viewport" id="vp">
    <div class="track" id="track">{''.join(frames)}</div>
    <div class="half l" id="hl"></div><div class="half r" id="hr"></div>
  </div>
  <div class="nav"><button id="prev" aria-label="Previous">‹</button>
    <span class="counter" id="ct">1 / {n}</span>
    <button id="next" aria-label="Next">›</button></div>
  <div class="dots" id="dots">{dots}</div>
  <div class="tip">Tap the green arrows, or tap the right/left side of the slide. Final posts render as 1080×1350 PNGs.</div>
<script>
  const N={n};
  const vp=document.getElementById('vp'), track=document.getElementById('track');
  const frames=[...document.querySelectorAll('.frame')];
  const dots=[...document.querySelectorAll('#dots .dot')], ct=document.getElementById('ct');
  const prev=document.getElementById('prev'), next=document.getElementById('next');
  let cur=0, W=0;
  function fit(){{
    W=Math.min(window.innerWidth-28, 430);
    const s=W/1080, h=1350*s;
    vp.style.width=W+'px'; vp.style.height=h+'px';
    frames.forEach(f=>{{f.style.height=h+'px'; f.querySelector('iframe').style.transform='scale('+s+')';}});
    move(false);
  }}
  function paint(){{
    dots.forEach((d,k)=>d.classList.toggle('on',k===cur));
    ct.textContent=(cur+1)+' / '+N;
    prev.disabled=(cur===0); next.disabled=(cur===N-1);
  }}
  function move(anim){{
    track.style.transition = anim ? 'transform .28s ease' : 'none';
    track.style.transform='translateX('+(-cur*W)+'px)'; paint();
  }}
  function go(i){{ cur=Math.max(0,Math.min(N-1,i)); move(true); }}
  prev.onclick=()=>go(cur-1); next.onclick=()=>go(cur+1);
  document.getElementById('hl').onclick=()=>go(cur-1);
  document.getElementById('hr').onclick=()=>go(cur+1);
  // touch swipe on the viewport (independent of native scroll)
  let x0=null;
  vp.addEventListener('touchstart',e=>{{x0=e.touches[0].clientX;}},{{passive:true}});
  vp.addEventListener('touchend',e=>{{
    if(x0===null)return; const dx=e.changedTouches[0].clientX-x0;
    if(Math.abs(dx)>40) go(cur+(dx<0?1:-1)); x0=null;
  }});
  window.addEventListener('resize',fit); fit();
</script></body></html>"""

    out_dir = os.path.join(HERE, "..", "..", "social", "out")
    os.makedirs(out_dir, exist_ok=True)
    out_path = os.path.abspath(os.path.join(out_dir, f"preview-{name}.html"))
    open(out_path, "w", encoding="utf-8").write(out_html)
    print(out_path)


if __name__ == "__main__":
    main()

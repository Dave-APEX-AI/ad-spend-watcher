"""
Build a fully self-contained dashboard: same UI as intent/dashboard.html, but with
the JSON data baked in so it opens from anywhere (file://, email attachment, no
server, no login). Output: intent/dashboard_standalone.html

Run:  python intent/build_standalone.py
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(HERE, "dashboard.html")).read()
cdata = open(os.path.join(HERE, "data", "intent_companies.json")).read()
qdata = open(os.path.join(HERE, "data", "action_queue.json")).read()

FETCH_BLOCK = """    const [cRes, qRes] = await Promise.all([
      fetch('./data/intent_companies.json'),
      fetch('./data/action_queue.json')
    ]);
    if (!cRes.ok || !qRes.ok) throw new Error('fetch failed');
    const cData = await cRes.json();
    const qData = await qRes.json();"""

REPLACEMENT = f"""    const cData = {cdata.strip()};
    const qData = {qdata.strip()};"""

if FETCH_BLOCK not in src:
    raise SystemExit("fetch block not found — dashboard.html changed; update this script")

out = src.replace(FETCH_BLOCK, REPLACEMENT)
out = out.replace("<title>", "<title>[standalone] ", 1)
dest = os.path.join(HERE, "dashboard_standalone.html")
open(dest, "w").write(out)
print(f"wrote {dest} ({len(out):,} bytes, data embedded)")

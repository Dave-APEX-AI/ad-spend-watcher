#!/usr/bin/env python3
"""
refill.py — keep the publish queue full, autonomously.

Runs in GitHub Actions on a schedule. If the queue's unposted buffer is below TARGET_BUFFER,
it renders unused specs from social/content/library/ (carousels/reels/statics — each carries
its own caption) and appends them to the queue. No human needed: the channel never goes dark.

Env: TARGET_BUFFER (default 14 = ~7 days at 2/day), PUBLIC_BASE_URL, CHROME_BIN.
"""
import json, os, sys, glob, shutil, subprocess

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUEUE = os.path.join(ROOT, "social", "publish", "queue")
LIB = os.path.join(ROOT, "social", "content", "library")
SCHED = os.path.join(QUEUE, "schedule.json")
POSTED = os.path.join(QUEUE, ".posted")
CAROUSEL = os.path.join(ROOT, ".claude", "skills", "caillte-carousel", "render.py")
REEL = os.path.join(ROOT, ".claude", "skills", "caillte-reel", "render_reel.py")
OUT = os.path.join(ROOT, "social", "out")
TARGET = int(os.environ.get("TARGET_BUFFER", "14"))
BASE = os.environ.get("PUBLIC_BASE_URL",
                      "https://raw.githubusercontent.com/Dave-APEX-AI/ad-spend-watcher/main").rstrip("/")
IMG_EXT = (".png", ".jpg", ".jpeg")


def load(p, default):
    return json.load(open(p, encoding="utf-8")) if os.path.exists(p) else default


def main():
    sched = load(SCHED, {"jobs": []})
    jobs = sched["jobs"]
    posted = set(l.strip() for l in open(POSTED) if l.strip()) if os.path.exists(POSTED) else set()
    pending = [j for j in jobs if j not in posted]
    need = TARGET - len(pending)
    print(f"buffer: {len(pending)} pending / target {TARGET} → need {max(0, need)}")
    if need <= 0:
        print("queue healthy — nothing to refill.")
        return 0

    queued_names = set(j[:-5] for j in jobs)  # filename minus .json == spec name
    specs = []
    for f in sorted(glob.glob(os.path.join(LIB, "*.json"))):
        try:
            s = json.load(open(f, encoding="utf-8"))
        except Exception as e:
            print(f"⚠️ skipping invalid library spec {os.path.basename(f)}: {e}")
            continue
        if s.get("name") and s["name"] not in queued_names:
            specs.append(s)
    if not specs:
        print("⚠️ library exhausted — add specs to social/content/library/ (or run a weekly drop).")
        return 0

    # REEL-FIRST: weave reels and others ~2:1 so the queue leans video (reels win reach).
    reels = [s for s in specs if s.get("kind") == "reel"]
    others = [s for s in specs if s.get("kind") != "reel"]
    woven, ri, oi = [], 0, 0
    while ri < len(reels) or oi < len(others):
        for _ in range(2):
            if ri < len(reels): woven.append(reels[ri]); ri += 1
        if oi < len(others): woven.append(others[oi]); oi += 1
    specs = woven

    fetch = os.path.join(ROOT, "social", "publish", "fetch_photo.py")
    added = []
    for spec in specs[:need]:
        name, kind = spec["name"], spec.get("kind", "carousel")
        # reels get a real Pexels photo background when a key + query are present
        if kind == "reel" and os.environ.get("PEXELS_API_KEY") and spec.get("photo_query"):
            bg = os.path.join(OUT, f"{name}_bg.jpg")
            try:
                if subprocess.run([sys.executable, fetch, spec["photo_query"], bg]).returncode == 0 \
                        and os.path.exists(bg):
                    spec["photo"] = bg
                    print(f"   • photo for {name}: {spec['photo_query']}")
            except Exception as e:
                print(f"   • photo fetch failed for {name}: {e}")
        tmp = os.path.join(LIB, f".__{name}.json")
        json.dump(spec, open(tmp, "w", encoding="utf-8"), ensure_ascii=False)
        try:
            if kind == "reel":
                subprocess.run([sys.executable, REEL, tmp, "--out", OUT], check=True)
                src = os.path.join(OUT, name, f"{name}.mp4")
                dst_dir = os.path.join(QUEUE, name); os.makedirs(dst_dir, exist_ok=True)
                shutil.copy2(src, os.path.join(dst_dir, f"{name}.mp4"))
                job = {"type": "reel", "caption": spec.get("caption", ""),
                       "video_url": f"{BASE}/social/publish/queue/{name}/{name}.mp4",
                       "cross_post_facebook": False}
            else:  # carousel or static (single-slide carousel)
                subprocess.run([sys.executable, CAROUSEL, tmp, "--out", OUT], check=True)
                pngs = sorted(f for f in os.listdir(os.path.join(OUT, name)) if f.lower().endswith(IMG_EXT))
                dst_dir = os.path.join(QUEUE, name); os.makedirs(dst_dir, exist_ok=True)
                for p in pngs:
                    shutil.copy2(os.path.join(OUT, name, p), os.path.join(dst_dir, p))
                urls = [f"{BASE}/social/publish/queue/{name}/{p}" for p in pngs]
                job = {"type": "carousel" if len(urls) > 1 else "image",
                       "caption": spec.get("caption", ""), "image_urls": urls,
                       "cross_post_facebook": True}
        finally:
            os.path.exists(tmp) and os.remove(tmp)
        json.dump(job, open(os.path.join(QUEUE, f"{name}.json"), "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        jobs.append(f"{name}.json")
        added.append(f"{name} [{kind}]")
        print(f"  ✓ queued {name} [{kind}]")

    json.dump(sched, open(SCHED, "w", encoding="utf-8"), indent=2)
    print(f"\nRefilled {len(added)}: " + ", ".join(added))
    print(f"new buffer: {len([j for j in jobs if j not in posted])} pending")
    return 0


if __name__ == "__main__":
    sys.exit(main())

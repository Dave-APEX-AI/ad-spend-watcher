#!/usr/bin/env python3
"""
stage.py — wire the GitHub Pages hosting path for the publisher.

The Graph API fetches media by PUBLIC URL. `social/out/` is gitignored working output,
so this copies a rendered carousel's slides into `social/publish/queue/<name>/` (which IS
committed + served by GitHub Pages), builds public URLs from PUBLIC_BASE_URL, writes a
ready-to-publish job JSON, and prints the exact next commands.

Usage:
  python3 social/publish/stage.py --name 03-missed-call-maths \
        --caption-section "Day 3"            # caption pulled from week1/captions.md
  # or: --caption "your caption here"
  # source dir defaults to social/out/<name>; override with --src DIR

Env: PUBLIC_BASE_URL (e.g. https://dave-apex-ai.github.io/ad-spend-watcher)
"""
import os, sys, shutil, json, re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
QUEUE = os.path.join(ROOT, "social", "publish", "queue")
CAPTIONS = os.path.join(ROOT, "social", "content", "week1", "captions.md")
IMG_EXT = (".png", ".jpg", ".jpeg")


def die(m): print("ERROR:", m, file=sys.stderr); sys.exit(1)


def caption_from_md(section):
    if not os.path.exists(CAPTIONS):
        return ""
    text = open(CAPTIONS, encoding="utf-8").read()
    for b in re.split(r"\n## ", text):
        if b.lower().startswith(section.lower().lstrip("# ")):
            m = re.search(r"\*\*Caption\*\*\s*\n(.+?)(\n\*\*|\n---|\Z)", b, re.S)
            if m:
                return "\n".join(l.lstrip("> ").rstrip() for l in m.group(1).strip().splitlines())
    return ""


def main():
    a = sys.argv[1:]
    opts = {}
    i = 0
    while i < len(a):
        if a[i].startswith("--"):
            opts[a[i]] = a[i + 1] if i + 1 < len(a) and not a[i + 1].startswith("--") else "true"
            i += 2
        else:
            i += 1

    name = opts.get("--name") or die("pass --name <carousel-name>")
    src = opts.get("--src", os.path.join(ROOT, "social", "out", name))
    if not os.path.isdir(src):
        die(f"source dir not found: {src}\n  render first: "
            f"python3 .claude/skills/caillte-carousel/render.py "
            f"social/content/week1/{name}.json --out social/out")

    base = os.environ.get("PUBLIC_BASE_URL", "").rstrip("/")
    if not base:
        die("set PUBLIC_BASE_URL (e.g. https://dave-apex-ai.github.io/ad-spend-watcher)")

    slides = sorted(f for f in os.listdir(src) if f.lower().endswith(IMG_EXT))
    if not slides:
        die(f"no slides in {src}")

    dest = os.path.join(QUEUE, name)
    os.makedirs(dest, exist_ok=True)
    for f in slides:
        shutil.copy2(os.path.join(src, f), os.path.join(dest, f))

    urls = [f"{base}/social/publish/queue/{name}/{f}" for f in slides]
    caption = opts.get("--caption") or caption_from_md(opts.get("--caption-section", ""))

    job = {"type": "carousel" if len(urls) > 1 else "image",
           "caption": caption, "image_urls": urls, "cross_post_facebook": True}
    job_path = os.path.join(QUEUE, f"{name}.json")
    json.dump(job, open(job_path, "w", encoding="utf-8"), ensure_ascii=False, indent=2)

    rel = os.path.relpath(job_path, ROOT)
    print(f"✓ staged {len(slides)} slides → social/publish/queue/{name}/")
    print(f"✓ job written → {rel}")
    if not caption:
        print("⚠ no caption found — add one to the job file before publishing.")
    print("\nNext (publishes only after the PNGs are live on Pages):")
    print(f"  git add social/publish/queue/{name} {rel} && git commit -m 'queue {name}' && git push")
    print(f"  # wait for Pages to serve, then:")
    print(f"  set -a; source social/publish/.env; set +a")
    print(f"  python3 social/publish/ig_publish.py {rel} --dry-run   # preview")
    print(f"  python3 social/publish/ig_publish.py {rel}             # go live")


if __name__ == "__main__":
    main()

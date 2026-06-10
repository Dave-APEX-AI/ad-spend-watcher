#!/usr/bin/env python3
"""
ig_publish.py — publish CaillteAI posts to Instagram (+ cross-post to a Facebook Page)
via the Meta Graph API Content Publishing API. Zero third-party deps (stdlib urllib).
Free: organic publishing has no API cost.

Supports: single image, carousel (2–10 images), and Reels (video).

Images/videos must be at PUBLIC URLs (the API fetches them by URL). Since CaillteAI
already publishes to GitHub Pages, committed PNGs get a public URL you can use — set
PUBLIC_BASE_URL and pass --from-dir, or list image_urls explicitly in the job.

──────────────────────────────────────────────────────────────────────────────
USAGE
  python3 ig_publish.py job.json [--dry-run]
  python3 ig_publish.py --from-dir social/out/03-missed-call-maths \
        --caption-file social/content/week1/captions.md --caption-section "Day 3" [--dry-run]

ENV (see .env.example — never commit real values)
  IG_USER_ID            Instagram Business account id (required)
  IG_ACCESS_TOKEN       long-lived token with instagram_content_publish (required)
  FB_PAGE_ID            Facebook Page id (optional — enables cross-post)
  FB_PAGE_TOKEN         Page token with pages_manage_posts (optional; defaults to IG token)
  PUBLIC_BASE_URL       e.g. https://dave-apex-ai.github.io/ad-spend-watcher  (for --from-dir)
  GRAPH_API_VERSION     default v21.0 — bump if Meta deprecates it

JOB FILE shape
  { "type":"carousel"|"image"|"reel",
    "caption":"...",
    "image_urls":["https://.../slide_01.png", ...],   # image/carousel
    "video_url":"https://.../reel.mp4",               # reel
    "cover_url":"https://.../cover.png",              # reel cover (optional)
    "cross_post_facebook": true }
──────────────────────────────────────────────────────────────────────────────
"""
import json, os, sys, time, urllib.parse, urllib.request, urllib.error

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_API_VERSION", "v21.0")
IMG_EXT = (".png", ".jpg", ".jpeg")


def env(name, required=False):
    v = os.environ.get(name, "").strip()
    if required and not v:
        die(f"missing required env var: {name}  (see social/publish/.env.example)")
    return v


def die(msg):
    print("ERROR:", msg, file=sys.stderr)
    sys.exit(1)


def api(path, params, method="POST"):
    """Call the Graph API. Returns parsed JSON or raises with the API error message."""
    url = f"{GRAPH}/{path}"
    data = urllib.parse.urlencode(params).encode()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode(errors="replace")
        try:
            err = json.loads(body)["error"]
            die(f"Graph API {e.code}: {err.get('message')} "
                f"(type={err.get('type')}, code={err.get('code')})")
        except (ValueError, KeyError):
            die(f"Graph API {e.code}: {body[:400]}")


def get_status(creation_id, token):
    url = f"{GRAPH}/{creation_id}?" + urllib.parse.urlencode(
        {"fields": "status_code,status", "access_token": token})
    with urllib.request.urlopen(url, timeout=60) as r:
        return json.loads(r.read().decode())


def wait_ready(creation_id, token, timeout=300):
    """Poll a media container until FINISHED (needed for reels; quick for images)."""
    start = time.time()
    while time.time() - start < timeout:
        s = get_status(creation_id, token).get("status_code", "")
        if s == "FINISHED":
            return True
        if s in ("ERROR", "EXPIRED"):
            die(f"container {creation_id} status={s}")
        print(f"   …processing ({s or 'IN_PROGRESS'})")
        time.sleep(5)
    die(f"timed out waiting for container {creation_id}")


# ── Instagram publishers ──────────────────────────────────────────────────

def ig_image(ig_id, token, image_url, caption):
    c = api(f"{ig_id}/media", {"image_url": image_url, "caption": caption,
                               "access_token": token})["id"]
    wait_ready(c, token)
    return api(f"{ig_id}/media_publish", {"creation_id": c, "access_token": token})["id"]


def ig_carousel(ig_id, token, image_urls, caption):
    if not (2 <= len(image_urls) <= 10):
        die(f"carousel needs 2–10 images, got {len(image_urls)}")
    children = []
    for i, u in enumerate(image_urls, 1):
        print(f"   • uploading slide {i}/{len(image_urls)}")
        cid = api(f"{ig_id}/media", {"image_url": u, "is_carousel_item": "true",
                                     "access_token": token})["id"]
        wait_ready(cid, token)
        children.append(cid)
    parent = api(f"{ig_id}/media", {"media_type": "CAROUSEL",
                                    "children": ",".join(children),
                                    "caption": caption, "access_token": token})["id"]
    wait_ready(parent, token)
    return api(f"{ig_id}/media_publish", {"creation_id": parent, "access_token": token})["id"]


def ig_reel(ig_id, token, video_url, caption, cover_url=""):
    params = {"media_type": "REELS", "video_url": video_url,
              "caption": caption, "access_token": token}
    if cover_url:
        params["cover_url"] = cover_url
    c = api(f"{ig_id}/media", params)["id"]
    wait_ready(c, token, timeout=600)  # video transcoding takes longer
    return api(f"{ig_id}/media_publish", {"creation_id": c, "access_token": token})["id"]


# ── Facebook Page cross-post ───────────────────────────────────────────────

def fb_crosspost(page_id, page_token, image_urls, caption):
    if len(image_urls) == 1:
        return api(f"{page_id}/photos", {"url": image_urls[0], "caption": caption,
                                         "access_token": page_token}).get("post_id", "ok")
    media_ids = []
    for u in image_urls:
        pid = api(f"{page_id}/photos", {"url": u, "published": "false",
                                        "access_token": page_token})["id"]
        media_ids.append({"media_fbid": pid})
    params = {"message": caption, "access_token": page_token}
    for i, m in enumerate(media_ids):
        params[f"attached_media[{i}]"] = json.dumps(m)
    return api(f"{page_id}/feed", params).get("id", "ok")


# ── Caption helper: pull a "## Day N" section from captions.md ─────────────

def caption_from_markdown(path, section):
    import re
    text = open(path, encoding="utf-8").read()
    blocks = re.split(r"\n## ", text)
    for b in blocks:
        if b.lower().startswith(section.lower().lstrip("# ").lower()):
            m = re.search(r"\*\*Caption\*\*\s*\n(.+?)(\n\*\*|\n---|\Z)", b, re.S)
            if m:
                # strip leading "> " quote markers
                return "\n".join(l.lstrip("> ").rstrip() for l in m.group(1).strip().splitlines())
    die(f"could not find caption for section '{section}' in {path}")


# ── Job assembly ──────────────────────────────────────────────────────────

def job_from_dir(directory, base_url):
    if not base_url:
        die("--from-dir needs PUBLIC_BASE_URL set (where the committed PNGs are served)")
    files = sorted(f for f in os.listdir(directory) if f.lower().endswith(IMG_EXT))
    if not files:
        die(f"no images in {directory}")
    rel = directory.lstrip("./")
    urls = [f"{base_url.rstrip('/')}/{rel}/{f}" for f in files]
    return urls


def main():
    args = sys.argv[1:]
    dry = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    ig_id = env("IG_USER_ID", required=not dry)
    token = env("IG_ACCESS_TOKEN", required=not dry)
    fb_page = env("FB_PAGE_ID")
    fb_token = env("FB_PAGE_TOKEN") or token

    # Build the job either from a JSON file or from --from-dir flags.
    if args and args[0].endswith(".json"):
        job = json.load(open(args[0], encoding="utf-8"))
    else:
        opts = dict(zip(args[::2], args[1::2]))
        directory = opts.get("--from-dir") or die("pass a job.json or --from-dir DIR")
        urls = job_from_dir(directory, env("PUBLIC_BASE_URL"))
        caption = ""
        if "--caption-file" in opts:
            caption = caption_from_markdown(opts["--caption-file"], opts.get("--caption-section", "Day 1"))
        elif "--caption" in opts:
            caption = opts["--caption"]
        job = {"type": "carousel" if len(urls) > 1 else "image",
               "caption": caption, "image_urls": urls,
               "cross_post_facebook": bool(fb_page)}

    jtype = job.get("type", "carousel")
    caption = job.get("caption", "")
    urls = job.get("image_urls", [])

    print(f"▶ {jtype.upper()} — {len(urls) or 1} asset(s)")
    print(f"  caption: {caption[:70].replace(chr(10),' ')}…")
    for u in urls:
        print("   -", u)
    if job.get("video_url"):
        print("   - video:", job["video_url"])

    if dry:
        print("\n(dry run — nothing published. Remove --dry-run to go live.)")
        return

    if jtype == "image":
        pid = ig_image(ig_id, token, urls[0], caption)
    elif jtype == "carousel":
        pid = ig_carousel(ig_id, token, urls, caption)
    elif jtype == "reel":
        pid = ig_reel(ig_id, token, job["video_url"], caption, job.get("cover_url", ""))
    else:
        die(f"unknown type: {jtype}")
    print(f"✅ Instagram published — media id {pid}")

    if job.get("cross_post_facebook") and fb_page and jtype in ("image", "carousel"):
        fid = fb_crosspost(fb_page, fb_token, urls, caption)
        print(f"✅ Facebook Page cross-posted — {fid}")
    elif job.get("cross_post_facebook") and jtype == "reel":
        print("ℹ️  Reels aren't cross-posted by this script — share to FB from the IG app or Business Suite.")


if __name__ == "__main__":
    main()

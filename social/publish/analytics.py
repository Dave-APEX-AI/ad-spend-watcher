#!/usr/bin/env python3
"""
analytics.py — pull performance for CaillteAI's published Instagram posts and rank them.

Runs in GitHub Actions (where IG_ACCESS_TOKEN lives). Fetches the account's media, then
each post's insights (views/reach/saves/shares) — degrading gracefully if a metric or
permission isn't available — and prints a ranked Markdown table to the run log.

Note: views/reach/saves need the token to have `instagram_manage_insights`. Without it we
still get likes + comments (from the media object) and rank by those.

Env: IG_USER_ID, IG_ACCESS_TOKEN, GRAPH_API_VERSION (default v21.0).
"""
import os, sys, json, urllib.request, urllib.parse, urllib.error

GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_API_VERSION", "v21.0")
IG = os.environ.get("IG_USER_ID", "").strip()
TOK = os.environ.get("IG_ACCESS_TOKEN", "").strip()


def get(path, params):
    params = {**params, "access_token": TOK}
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def get_safe(path, params):
    try:
        return get(path, params), None
    except urllib.error.HTTPError as e:
        try:
            return None, json.loads(e.read().decode())["error"].get("message", str(e))
        except Exception:
            return None, f"HTTP {e.code}"
    except Exception as e:
        return None, str(e)


def insights(media_id, product_type):
    """Try a rich metric set, then fall back, so one missing metric doesn't kill the row."""
    for metrics in ("views,reach,saved,shares,total_interactions",
                    "reach,saved,shares", "reach"):
        data, err = get_safe(f"{media_id}/insights", {"metric": metrics})
        if data and "data" in data:
            return {m["name"]: (m.get("values", [{}])[0].get("value", 0)) for m in data["data"]}, None
    return {}, err  # err from the last attempt (often the permission message)


def short(caption, n=42):
    c = (caption or "").replace("\n", " ").strip()
    return (c[:n] + "…") if len(c) > n else c


def main():
    if not IG or not TOK:
        print("ERROR: IG_USER_ID / IG_ACCESS_TOKEN not set"); return 1

    rows, after, pages = [], None, 0
    perm_warning = None
    while pages < 5:
        params = {"fields": "id,caption,media_type,media_product_type,timestamp,permalink,"
                            "like_count,comments_count", "limit": 50}
        if after:
            params["after"] = after
        page, err = get_safe(f"{IG}/media", params)
        if not page:
            print("ERROR fetching media:", err); return 1
        for m in page.get("data", []):
            ins, ierr = insights(m["id"], m.get("media_product_type"))
            if ierr and not perm_warning:
                perm_warning = ierr
            rows.append({
                "type": m.get("media_product_type") or m.get("media_type"),
                "caption": short(m.get("caption")),
                "date": (m.get("timestamp") or "")[:10],
                "views": ins.get("views", 0),
                "reach": ins.get("reach", 0),
                "saved": ins.get("saved", 0),
                "shares": ins.get("shares", 0),
                "likes": m.get("like_count", 0),
                "comments": m.get("comments_count", 0),
                "url": m.get("permalink", ""),
            })
        after = page.get("paging", {}).get("cursors", {}).get("after")
        if not after:
            break
        pages += 1

    if not rows:
        print("No published posts found yet."); return 0

    have_views = any(r["views"] or r["reach"] for r in rows)
    key = (lambda r: (r["views"], r["reach"], r["likes"])) if have_views \
        else (lambda r: (r["likes"], r["comments"]))
    rows.sort(key=key, reverse=True)

    print(f"# CaillteAI post performance — {len(rows)} posts\n")
    if not have_views and perm_warning:
        print(f"> ⚠️ Views/reach unavailable (ranked by likes+comments instead).")
        print(f"> Reason: {perm_warning}")
        print(f"> Fix: regenerate the token with **instagram_manage_insights** ticked.\n")
    print("| # | Type | Post | Date | Views | Reach | Saves | Likes | Comments |")
    print("|---|------|------|------|------:|------:|------:|------:|---------:|")
    for i, r in enumerate(rows, 1):
        print(f"| {i} | {r['type']} | {r['caption']} | {r['date']} | "
              f"{r['views']} | {r['reach']} | {r['saved']} | {r['likes']} | {r['comments']} |")

    top = rows[0]
    print(f"\n**Top performer:** {top['caption']} "
          f"({top['type']}, {top['views'] or top['reach'] or top['likes']} "
          f"{'views' if have_views else 'likes'}).")
    return 0


if __name__ == "__main__":
    sys.exit(main())

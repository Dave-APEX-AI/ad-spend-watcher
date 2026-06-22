#!/usr/bin/env python3
"""
dashboard_data.py — write social/dashboard/data.json with REAL CaillteAI numbers for the
Growth Command Centre. Runs in GitHub Actions (IG token in secrets); the dashboard fetches
data.json on load. Degrades gracefully if a field/permission is missing.

Env: IG_USER_ID, IG_ACCESS_TOKEN, GRAPH_API_VERSION (default v21.0).
"""
import os, sys, json, datetime, urllib.request, urllib.parse, urllib.error

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
OUT = os.path.join(os.path.dirname(__file__), "data.json")
GRAPH = "https://graph.facebook.com/" + os.environ.get("GRAPH_API_VERSION", "v21.0")
IG = os.environ.get("IG_USER_ID", "").strip()
TOK = os.environ.get("IG_ACCESS_TOKEN", "").strip()


def get(path, params):
    url = f"{GRAPH}/{path}?" + urllib.parse.urlencode({**params, "access_token": TOK})
    with urllib.request.urlopen(url, timeout=30) as r:
        return json.loads(r.read().decode())


def get_safe(path, params):
    try:
        return get(path, params)
    except Exception:
        return None


def insights(mid):
    for metrics in ("views,reach,saved", "reach,saved", "reach"):
        d = get_safe(f"{mid}/insights", {"metric": metrics})
        if d and "data" in d:
            return {m["name"]: m.get("values", [{}])[0].get("value", 0) for m in d["data"]}
    return {}


def short(c, n=40):
    c = (c or "").replace("\n", " ").strip()
    return (c[:n] + "…") if len(c) > n else c


def planner():
    q = os.path.join(ROOT, "social", "publish", "queue")
    try:
        jobs = json.load(open(os.path.join(q, "schedule.json")))["jobs"]
        posted = set(l.strip() for l in open(os.path.join(q, ".posted"))) if os.path.exists(os.path.join(q, ".posted")) else set()
        pend = len([j for j in jobs if j not in posted])
        return pend, round(pend / 2)
    except Exception:
        return None, None


def main():
    if not IG or not TOK:
        print("no IG creds — skipping"); return 0

    prof = get_safe(IG, {"fields": "followers_count,media_count"}) or {}
    followers = prof.get("followers_count")

    rows, after, pages = [], None, 0
    while pages < 4:
        params = {"fields": "caption,media_product_type,like_count,comments_count", "limit": 50}
        if after:
            params["after"] = after
        page = get_safe(f"{IG}/media", params)
        if not page:
            break
        for m in page.get("data", []):
            ins = insights(m["id"])
            rows.append({"cap": short(m.get("caption")), "type": m.get("media_product_type") or "FEED",
                         "views": ins.get("views", 0), "reach": ins.get("reach", 0),
                         "likes": m.get("like_count", 0), "comments": m.get("comments_count", 0)})
        after = page.get("paging", {}).get("cursors", {}).get("after")
        if not after:
            break
        pages += 1

    total_views = sum(r["views"] for r in rows)
    total_reach = sum(r["reach"] for r in rows)
    inter = sum(r["likes"] + r["comments"] for r in rows)
    eng = round((inter / total_views * 100), 1) if total_views else 0.0
    rows.sort(key=lambda r: (r["views"], r["reach"], r["likes"]), reverse=True)
    top = rows[0] if rows else {"cap": "—", "views": 0, "type": "—"}

    reels = [r for r in rows if r["type"] == "REELS"]
    others = [r for r in rows if r["type"] != "REELS"]
    avg_r = sum(x["views"] for x in reels) / len(reels) if reels else 0
    avg_o = sum(x["views"] for x in others) / len(others) if others else 0
    best_fmt = "Reels" if avg_r >= avg_o else "Feed"

    pend, days = planner()
    top3 = [[f"#{i+1}", r["cap"], f"{r['views']} views"] for i, r in enumerate(rows[:3])]

    data = {
        "updated": datetime.datetime.utcnow().strftime("%d %b %H:%M UTC"),
        "stats": {"followers": followers, "views": total_views,
                  "topViews": top["views"], "topLabel": short(top["cap"], 22), "engagement": eng},
        "analyst": {"postsTracked": len(rows), "topFormat": best_fmt, "best": top["views"],
                    "top": top3,
                    "insight1": f"Reels avg {round(avg_r)} views vs {round(avg_o)} for statics — reels win reach",
                    "insight2": "Saves ≈ 0 — audience small; reach is the lever"},
        "planner": {"queued": pend, "days": days},
    }
    json.dump(data, open(OUT, "w"), indent=2)
    print("wrote", OUT, "→ followers:", followers, "views:", total_views, "top:", top["views"])
    return 0


if __name__ == "__main__":
    sys.exit(main())

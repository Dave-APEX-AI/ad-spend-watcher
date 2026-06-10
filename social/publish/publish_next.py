#!/usr/bin/env python3
"""
publish_next.py — publish the NEXT pending post in the queue, then stop.

Reads social/publish/queue/schedule.json (ordered job list), finds the first job not
already recorded in social/publish/queue/.posted, publishes it via ig_publish.py, and
appends it to .posted. Designed to be run once per scheduled GitHub Actions run (so the
queue drains one post at a time). Re-run / dispatch again to send the next one.

Env: same as ig_publish.py (IG_USER_ID, IG_ACCESS_TOKEN, FB_PAGE_ID, FB_PAGE_TOKEN).
     DRY_RUN=true → preview only, and do NOT mark as posted.

Exit codes: 0 = posted (or nothing left / dry-run), non-zero = a publish error.
The workflow commits .posted back so the next run picks the following job.
"""
import os, sys, json, subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
QUEUE = os.path.join(HERE, "queue")
SCHEDULE = os.path.join(QUEUE, "schedule.json")
POSTED = os.path.join(QUEUE, ".posted")
DRY = os.environ.get("DRY_RUN", "").lower() == "true"


def load_posted():
    if not os.path.exists(POSTED):
        return []
    return [l.strip() for l in open(POSTED, encoding="utf-8") if l.strip() and not l.startswith("#")]


def main():
    if not os.path.exists(SCHEDULE):
        print("no schedule.json — nothing to do"); return 0
    jobs = json.load(open(SCHEDULE, encoding="utf-8")).get("jobs", [])
    posted = load_posted()
    pending = [j for j in jobs if j not in posted]

    if not pending:
        print(f"✓ queue drained — all {len(jobs)} posts published. Add more to schedule.json.")
        return 0

    job = pending[0]
    job_path = os.path.join(QUEUE, job)
    if not os.path.exists(job_path):
        print(f"ERROR: job file missing: {job_path}", file=sys.stderr); return 1

    print(f"▶ next up: {job}  ({len(posted)} done, {len(pending)} pending)")
    cmd = [sys.executable, os.path.join(HERE, "ig_publish.py"), job_path]
    if DRY:
        cmd.append("--dry-run")
    rc = subprocess.run(cmd).returncode
    if rc != 0:
        print(f"✗ publish failed (rc={rc}) — not marking as posted; will retry next run.",
              file=sys.stderr)
        return rc

    if DRY:
        print("(dry run — not marked posted)")
        return 0

    with open(POSTED, "a", encoding="utf-8") as f:
        f.write(job + "\n")
    remaining = len(pending) - 1
    print(f"✅ posted {job}. {remaining} left in the queue.")
    return 0


if __name__ == "__main__":
    sys.exit(main())

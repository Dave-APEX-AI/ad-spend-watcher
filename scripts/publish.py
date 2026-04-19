"""
publish.py — commit + push after a weekly run
=============================================

Called at the end of scripts/weekly_run.py. Uses the PAT in
config/credentials.json to push to origin/main. GitHub Pages rebuilds
automatically within ~1 minute.

Safe by default: before pushing, it refuses if config/credentials.json
would be included in the commit (i.e. .gitignore is broken).
"""

from __future__ import annotations
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CRED = ROOT / "config" / "credentials.json"


def run(cmd: list[str], check: bool = True, capture: bool = False) -> str:
    """Run a shell command, return stdout."""
    result = subprocess.run(
        cmd,
        cwd=ROOT,
        check=check,
        capture_output=capture,
        text=True,
    )
    return (result.stdout or "").strip() if capture else ""


def assert_credentials_not_staged() -> None:
    """Abort if credentials.json is about to be committed."""
    staged = run(["git", "diff", "--cached", "--name-only"], capture=True)
    tracked = run(["git", "ls-files", "config/credentials.json"], capture=True)
    if "config/credentials.json" in staged.split() or tracked:
        print("\n✗ REFUSING TO PUSH: config/credentials.json is staged or tracked.")
        print("  Check .gitignore and run:  git rm --cached config/credentials.json")
        sys.exit(1)


def load_token() -> str:
    if not CRED.exists():
        print(f"✗ Missing {CRED} — create it from the template.")
        sys.exit(1)
    data = json.loads(CRED.read_text())
    token = data.get("GITHUB_TOKEN", "").strip()
    if not token:
        print("✗ GITHUB_TOKEN missing in config/credentials.json")
        sys.exit(1)
    return token


def publish(run_date: str | None = None) -> None:
    run_date = run_date or datetime.now().strftime("%Y-%m-%d")

    # Safety: refuse if repo isn't clean on a branch we expect
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture=True)
    if branch != "main":
        print(f"⚠ Not on main branch (on {branch}). Aborting.")
        sys.exit(1)

    # Stage everything except ignored
    run(["git", "add", "-A"])
    assert_credentials_not_staged()

    # Check if there's anything to commit
    status = run(["git", "status", "--porcelain"], capture=True)
    if not status:
        print(f"✓ Nothing to commit for {run_date}.")
        return

    msg = f"Weekly run {run_date}"
    run(["git", "commit", "-m", msg])
    print(f"✓ Committed: {msg}")

    # Push using token as Basic auth in URL, without persisting it
    token = load_token()
    owner = "Dave-APEX-AI"
    repo = "ad-spend-watcher"
    authed_url = f"https://{owner}:{token}@github.com/{owner}/{repo}.git"
    subprocess.run(
        ["git", "push", authed_url, "HEAD:main"],
        cwd=ROOT,
        check=True,
    )
    print(f"✓ Pushed to origin/main — GitHub Pages will rebuild in ~1 min")


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", help="Run date label (default: today)")
    args = parser.parse_args()
    publish(args.date)

#!/usr/bin/env python3
"""
notify.py — send a CaillteAI email notification via Web3Forms (free, no SMTP).

Used by the GitHub Actions workflows to email hello@caillteai.com:
  - a "weekly drop done" overview (manual dispatch of caillte-notify.yml)
  - a failure ALERT if a publish run errors (caillte-publish.yml, on failure)

Recipient is the inbox tied to the WEB3FORMS_KEY (register hello@caillteai.com at
web3forms.com). If WEB3FORMS_KEY isn't set, this no-ops cleanly (never fails a run).

Usage:  python3 notify.py "<subject>" "<message>"
"""
import os, sys, json, urllib.request, urllib.error

def main():
    key = os.environ.get("WEB3FORMS_KEY", "").strip()
    subject = sys.argv[1] if len(sys.argv) > 1 else "CaillteAI notification"
    message = sys.argv[2] if len(sys.argv) > 2 else ""
    if not key:
        print("ℹ️ WEB3FORMS_KEY not set — skipping email (add it to repo Secrets to enable).")
        return 0
    payload = json.dumps({
        "access_key": key,
        "subject": subject,
        "from_name": "CaillteAI Bot",
        "message": message,
    }).encode()
    req = urllib.request.Request("https://api.web3forms.com/submit", data=payload,
                                 headers={"Content-Type": "application/json",
                                          "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            ok = json.loads(r.read().decode()).get("success", False)
        print("✅ email sent" if ok else "⚠️ Web3Forms returned non-success")
    except urllib.error.HTTPError as e:
        print(f"⚠️ email send failed: HTTP {e.code} (non-fatal)")
    except Exception as e:
        print(f"⚠️ email send failed: {e} (non-fatal)")
    return 0  # never fail the workflow because of a notification

if __name__ == "__main__":
    sys.exit(main())

"""
Produce an artifact-ready page from the standalone dashboard: strip the outer
<!doctype>/<html>/<head>/<body> wrappers (the artifact host adds its own),
keeping the <title>, <style>, body markup and the data-embedded <script>.
Output: intent/artifact_dashboard.html
"""
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))
s = open(os.path.join(HERE, "dashboard_standalone.html")).read()

style = re.search(r"<style>.*?</style>", s, re.S).group(0)
body = re.search(r"<body[^>]*>(.*)</body>", s, re.S).group(1).strip()

# no external <link>/font tags to worry about (design tokens are inline);
# strip any just in case to satisfy the artifact CSP
body = re.sub(r"<link\b[^>]*>", "", body)

out = ("<title>Intent Radar — Inbound-Leak Signals</title>\n"
       + style + "\n" + body + "\n")
dest = os.path.join(HERE, "artifact_dashboard.html")
open(dest, "w").write(out)
print(f"wrote {dest} ({len(out):,} bytes)")

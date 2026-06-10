# publish/queue — public asset host for the auto-publisher

The Graph API fetches post media by **public URL**. `social/out/` is gitignored working
output, so anything you want to publish gets **staged here and committed** — this folder is
served by GitHub Pages, giving each slide a public URL the API can pull.

## Flow
```
render → social/out/<name>/slide_*.png        (working output, gitignored)
stage  → social/publish/queue/<name>/...       (committed → public on Pages)
       → social/publish/queue/<name>.json      (ready-to-publish job)
```

One command does the staging:
```
python3 social/publish/stage.py --name 03-missed-call-maths --caption-section "Day 3"
```
then `git commit` + `git push`, wait for Pages to serve, then run `ig_publish.py`.

## Important
- **GitHub Pages must serve the branch these files are on.** If Pages serves `main`, the
  queued PNGs must be on `main` to be public. Set `PUBLIC_BASE_URL` to your Pages base
  (e.g. `https://dave-apex-ai.github.io/ad-spend-watcher`) — or to `caillteai.com` if you
  host the slides there instead.
- Old posts can be pruned from here after they're published (they live on IG/FB now).

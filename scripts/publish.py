"""Instagram auto publisher (carousel posts).

Rules:
- Only posts whose post.json has "approved": true are published.
- Only posts whose "publish_at" time has passed are published.
- At most ONE post is published per run.
- Already published posts are recorded in published.csv and never re-posted.
- DRY_RUN=true (the default) only prints what would happen.

Environment variables:
  IG_ACCESS_TOKEN  Instagram User access token (GitHub Secret). Never printed.
  DRY_RUN          "false" to really publish. Anything else = dry run.
  IG_API_BASE      default https://graph.instagram.com
  GITHUB_REPOSITORY  owner/name (set automatically by GitHub Actions)
  IMAGE_BRANCH     branch that holds the images (default: main)
"""

import csv
import datetime
import json
import os
import pathlib
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
POSTS = ROOT / "posts"
LOG = ROOT / "published.csv"

API = os.environ.get("IG_API_BASE", "https://graph.instagram.com").rstrip("/")
TOKEN = os.environ.get("IG_ACCESS_TOKEN", "")
REPO = os.environ.get("GITHUB_REPOSITORY", "OWNER/REPO")
BRANCH = os.environ.get("IMAGE_BRANCH", "main")
DRY_RUN = os.environ.get("DRY_RUN", "true").strip().lower() != "false"


def log(msg):
    print(msg, flush=True)


def call(method, path, params=None):
    params = dict(params or {})
    params["access_token"] = TOKEN
    body = urllib.parse.urlencode(params)
    url = f"{API}/{path}"
    if method == "GET":
        req = urllib.request.Request(f"{url}?{body}")
    else:
        req = urllib.request.Request(url, data=body.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        detail = e.read().decode(errors="replace")
        if TOKEN:
            detail = detail.replace(TOKEN, "***")
        raise RuntimeError(f"{method} /{path} failed ({e.code}): {detail}") from None


def wait_ready(container_id, label):
    for _ in range(36):  # up to about 3 minutes
        st = call("GET", container_id, {"fields": "status_code"}).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            raise RuntimeError(f"{label}: container status {st}")
        time.sleep(5)
    raise RuntimeError(f"{label}: container not ready in time")


def published_ids():
    if not LOG.exists():
        return set()
    with LOG.open(encoding="utf-8") as f:
        return {row["post_id"] for row in csv.DictReader(f)}


def append_log(post_id, media_id):
    new = not LOG.exists()
    with LOG.open("a", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["post_id", "published_at", "media_id"])
        w.writerow([post_id, datetime.datetime.now(datetime.timezone.utc).isoformat(), media_id])


def image_url(post_id, name):
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/posts/{urllib.parse.quote(post_id)}/{urllib.parse.quote(name)}"


def due_posts():
    now = datetime.datetime.now(datetime.timezone.utc)
    done = published_ids()
    for d in sorted(p for p in POSTS.iterdir() if p.is_dir()):
        meta = json.loads((d / "post.json").read_text(encoding="utf-8"))
        pid = d.name
        if pid in done:
            log(f"[skip] {pid}: already published")
            continue
        if meta.get("approved") is not True:
            log(f"[skip] {pid}: not approved")
            continue
        at = datetime.datetime.fromisoformat(meta["publish_at"])
        if at.tzinfo is None:
            raise ValueError(f"{pid}: publish_at needs a timezone, e.g. +09:00")
        if at > now:
            log(f"[wait] {pid}: scheduled for {meta['publish_at']}")
            continue
        images = sorted(p.name for p in d.glob("*.jpg"))
        if not 2 <= len(images) <= 10:
            raise ValueError(f"{pid}: a carousel needs 2-10 JPEG images, found {len(images)}")
        caption = (d / "caption.txt").read_text(encoding="utf-8").strip()
        if len(caption) > 2200:
            raise ValueError(f"{pid}: caption is longer than 2200 characters")
        yield pid, images, caption


def publish(pid, images, caption):
    me = call("GET", "me", {"fields": "user_id,username"})
    ig_id = me.get("user_id") or me["id"]
    log(f"account: @{me.get('username')}")
    children = []
    for name in images:
        c = call("POST", f"{ig_id}/media", {"image_url": image_url(pid, name), "is_carousel_item": "true"})
        wait_ready(c["id"], name)
        children.append(c["id"])
        log(f"  uploaded {name}")
    parent = call("POST", f"{ig_id}/media", {"media_type": "CAROUSEL", "children": ",".join(children), "caption": caption})
    wait_ready(parent["id"], "carousel")
    res = call("POST", f"{ig_id}/media_publish", {"creation_id": parent["id"]})
    return res["id"]


def main():
    log(f"mode: {'DRY RUN (nothing is posted)' if DRY_RUN else 'LIVE'}")
    for pid, images, caption in due_posts():
        log(f"[due] {pid}: {len(images)} images")
        for name in images:
            log(f"  {image_url(pid, name)}")
        log("  caption: " + caption.splitlines()[0][:60] + " ...")
        if DRY_RUN:
            log("  (dry run) not posted")
            return 0
        if not TOKEN:
            log("ERROR: IG_ACCESS_TOKEN is not set")
            return 1
        media_id = publish(pid, images, caption)
        append_log(pid, media_id)
        log(f"  published: media_id={media_id}")
        return 0  # one post per run
    log("nothing to publish")
    return 0


if __name__ == "__main__":
    sys.exit(main())

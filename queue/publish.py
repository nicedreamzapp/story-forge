#!/usr/bin/env python3
"""
publish.py — push a finished Story Forge film out to the world.

Reuses Matt's EXISTING, working publish paths (no reinvention):
  - YouTube  -> ~/Desktop/PROJECTS/ineedhemp website/youtube/upload.py  (OAuth already set up; this is how Bear Sister shipped)
  - X/Twitter-> ~/.local/bin/tweet-publish                              (HQ token already wired)

Default policy = SAFE-UNATTENDED:
  Upload to YouTube as UNLISTED automatically, return the link. Nothing is made
  public and nothing is tweeted until Matt taps approve. Flip PUBLIC=1 (env or
  runner config) to go fully hands-off: public upload + auto-tweet the link.

Usage:
  publish.py VIDEO.mp4 --title T [--description D] [--tags a,b,c] [--public]
"""
import argparse, os, re, subprocess, sys
from pathlib import Path

YT_UPLOAD = Path.home() / "Desktop/PROJECTS/ineedhemp website/youtube/upload.py"
TWEET     = Path.home() / ".local/bin/tweet-publish"

YT_ID_RE = re.compile(r"(?:youtu\.be/|watch\?v=|video[ _]?id[:=]?\s*|\"id\":\s*\")([A-Za-z0-9_-]{11})")


def upload_youtube(mp4: Path, title: str, description: str, tags: list[str], public: bool) -> str | None:
    """Upload via the existing upload.py. Returns the youtu.be URL or None."""
    privacy = "public" if public else "unlisted"
    cmd = ["python3", str(YT_UPLOAD), str(mp4),
           "--title", title, "--description", description,
           "--privacy", privacy, "--tags", ",".join(tags)]
    print(f"[publish] youtube ({privacy}): {title}", flush=True)
    r = subprocess.run(cmd, capture_output=True, text=True)
    blob = (r.stdout or "") + "\n" + (r.stderr or "")
    if r.returncode != 0:
        print(f"[publish] youtube upload FAILED rc={r.returncode}\n{blob[-1200:]}", file=sys.stderr)
        return None
    m = YT_ID_RE.search(blob)
    if not m:
        print(f"[publish] uploaded but no video id parsed; raw tail:\n{blob[-600:]}", file=sys.stderr)
        return None
    return f"https://youtu.be/{m.group(1)}"


def post_tweet(text: str) -> bool:
    if not TWEET.exists():
        print("[publish] tweet-publish not found, skipping X", file=sys.stderr)
        return False
    r = subprocess.run([str(TWEET), text], capture_output=True, text=True)
    if r.returncode != 0:
        print(f"[publish] tweet FAILED\n{r.stderr[-600:]}", file=sys.stderr)
        return False
    print("[publish] tweeted", flush=True)
    return True


def publish(mp4: Path, title: str, description: str, tags: list[str], public: bool) -> dict:
    url = upload_youtube(mp4, title, description, tags, public)
    out = {"youtube": url, "tweeted": False, "public": public}
    if url and public:
        out["tweeted"] = post_tweet(f"{title}\n\n{url}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--title", required=True)
    ap.add_argument("--description", default="")
    ap.add_argument("--tags", default="animation,ai,local ai,story forge")
    ap.add_argument("--public", action="store_true", default=os.environ.get("PUBLIC") == "1")
    a = ap.parse_args()
    res = publish(Path(a.video), a.title, a.description, a.tags.split(","), a.public)
    print(res)
    return 0 if res["youtube"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

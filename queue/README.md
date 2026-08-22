# Story Forge Queue — your local "Make"

The thing the cloud guy gets from Make + rented GPUs: a pipeline that **produces
while you sleep**. Drop scripts in, walk away, wake up to finished films uploaded
to YouTube with a one-tap link on your phone. Runs 100% local on the M5 — zero
per-video cost, no Midjourney/Runway/Suno subscription, no terms-of-service rug-pull.

## How it works

```
inbox/<name>.sf  →  processing/  →  sf render (M5)  →  publish  →  done/
                                                  └→ (error) failed/
```

Renders run back-to-back, one at a time. Each finished film uploads to YouTube
(unlisted by default) and texts you the link. The 12-hour render stops mattering
because it's unattended and queued overnight.

## Daily use

```bash
# queue a script (runner picks it up within ~30s)
~/story-forge-queue/qadd ~/Desktop/PROJECTS/story-forge/story_forge/examples/test_tiny.sf

# or pipe a fresh script in under a name
qadd bear_part2.sf < /tmp/bear_part2.sf

# watch what's happening
tail -f ~/story-forge-queue/logs/runner.log
ls ~/story-forge-queue/{inbox,done,failed}
```

`done/<slug>.json` records each film: title, mp4 path, YouTube URL, render minutes.

## Publish policy

- **Default (PUBLIC=0):** upload **unlisted**, text you the link, you tap to make
  it public. Unattended production + a quality gate.
- **Hands-off (PUBLIC=1):** upload **public** and auto-tweet the link. True
  "he sleeps, it produces." Flip the value in the plist's `PUBLIC` env var.

## Turn it on (runs forever, restarts itself, survives reboot)

```bash
launchctl unload ~/Library/LaunchAgents/com.nicedreamz.storyforge-queue.plist 2>/dev/null
launchctl load   ~/Library/LaunchAgents/com.nicedreamz.storyforge-queue.plist
```

Off: `launchctl unload ~/Library/LaunchAgents/com.nicedreamz.storyforge-queue.plist`

## Pieces

| file | what |
|------|------|
| `runner.py`  | the daemon: claim → render → publish → notify, with lockfile + state |
| `publish.py` | reuses your existing YouTube upload.py + tweet-publish |
| `qadd`       | drop a script into the queue |
| `state.json` | what's been done / failed (dedupe + history) |

Reuses (does not reinvent): `~/Desktop/PROJECTS/story-forge/bin/sf`,
`~/Desktop/PROJECTS/ineedhemp website/youtube/upload.py`, `~/.local/bin/tweet-publish`,
`~/.claude/imessage-send.sh`.

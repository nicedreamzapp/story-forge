# Deploy: THE LAST SIGNAL on the Story Forge page + /software/ card (STAGED, not deployed)

Deploy only after the YouTube video (https://youtu.be/HSgm6hOsLTs) is public, or the embeds show "Video unavailable".

## One command
```bash
bash ~/Desktop/PROJECTS/story-forge/projects/last_signal/launch/page/deploy.sh
```
It pulls fresh live copies of both pages (the mini's site-syncer edits /software/ daily), rebuilds the staged pages with `build_pages.py`, backs up both live files as `index.html.bak-lastsignal-<stamp>`, uploads, flushes the cache, checks both live URLs, and prints the rollback command. It exits without changes if the section is already live.

## What changes
- `software/story-forge/index.html`: new `<section id="last-signal">` above The Oldest Tree (youtube-nocookie 16:9 embed, hook, stat pills, hardware callout, 17-step pipeline list with times, collapsible "How each step worked", honest notes, GitHub + YouTube buttons), a new first card in The Finished Films grid, Oldest Tree eyebrow now "October 2026 progress film". Styles are in a scoped `<style id="last-signal-pass">` before `</head>`.
- `software/index.html`: a THE LAST SIGNAL card right after Story Forge in the Creative grid, linking to `/software/story-forge/#last-signal`. It sits outside the GH-SHOWCASE auto block, so the syncer won't overwrite it.

## Previews (headless, checked at 1049 and 440, no horizontal overflow)
`page/previews/story-forge_1049.png`, `story-forge_440.png`, `story-forge_1049_details.png`, `story-forge_1049_films.png`, `story-forge_440_films.png`, `software_1049.png`, `software_440.png`.
Embeds show "Error 153" in the previews only because the page was loaded from local content; the live embeds are unaffected.

## After deploy
Check at 440 / 390 / 1049 in a hidden broker tab and close it. Don't open it on Matt's screen unless he asks.

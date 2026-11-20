# Story Forge page — add THE LAST SIGNAL (DRAFT, nothing deployed)

Page: https://nicedreamzwholesale.com/software/story-forge/

## How it's built and deployed (checked 10/31, read only)
- **It's a hand-built static HTML file, not WordPress.** `curl -I` returns `content-type: text/html`, `last-modified: Sun, 04 Oct 2026 08:54:31 GMT`, served by Hostinger's CDN (`server: hcdn`).
- File: Hostinger SSH alias `ineedhemp`, `domains/nicedreamzwholesale.com/public_html/software/story-forge/index.html` (48,621 bytes, 536 lines). Backups sit beside it in the house style `index.html.bak-<what>-<date>` (the latest is `index.html.bak-v2-20261004`).
- **No local source copy is the master.** Per `rules/sites.md` ("ALWAYS pull live files from VPS before editing"), pull the live file, edit, and push back.
- **Nothing will overwrite a hand edit.** The mini's site-syncer (`~/Scripts/site-syncer/watch.py`, 08:00 daily) only refreshes star and fork counts since 9/21 ("It used to rebuild every page from the template, which undid changes made by hand"). `story-forge` is also in its SKIP_REPOS list. The GH-SHOWCASE markers live on /software/, not on this page.
- The "complete README" `<details>` at the bottom (line ~492) is a pasted render of the GitHub README. It won't update itself, so after the github.md push, optionally refresh that block too.

## Deploy steps (when Matt says go)
```bash
cd /tmp && mkdir -p sfpage && cd sfpage
scp ineedhemp:domains/nicedreamzwholesale.com/public_html/software/story-forge/index.html index.html
ssh ineedhemp 'cd domains/nicedreamzwholesale.com/public_html/software/story-forge && cp index.html index.html.bak-lastsignal-20261031'
# edit index.html (the two inserts below), then:
scp index.html ineedhemp:domains/nicedreamzwholesale.com/public_html/software/story-forge/index.html
ssh ineedhemp 'cd domains/nicedreamzwholesale.com/public_html && wp cache flush'
curl -s https://nicedreamzwholesale.com/software/story-forge/ | grep -c "THE LAST SIGNAL"   # expect 2+
```
Then check it at 440 / 390 / 1049 px through a hidden broker tab, and close the tab (memory: check every instance, phone CSS at 440). Matt's "never open anything on his screen unasked" rule overrides the old "after deploy open a tab for Matt" line in sites.md: ask first.

## Insert 1: new top section, right ABOVE the Oldest Tree section (currently line ~378)
Also change the Oldest Tree eyebrow from "Newest film, October 2026" to "October 2026 progress film".
```html
  <section>
  <div class="section-eyebrow">Newest film, October 31 2026</div>
  <h2 class="section-title">THE LAST SIGNAL: a sci fi trailer made 100% local on one M5 Max 128GB.</h2>
  <div class="intro"><p style="text-align:center;"><iframe width="100%" height="450" style="max-width:800px;border-radius:12px;" src="https://www.youtube.com/embed/VIDEO_ID" title="THE LAST SIGNAL, a Story Forge trailer" frameborder="0" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen></iframe></p><p>A cargo ship follows a signal nobody has charted, and the planet at the end of it already knows the captain's name. 46 seconds, 50 cuts, a 4K deliverable with a 5.1 surround mix.</p><p>Every frame, voice and sound was generated on one MacBook Pro with an M5 Max and 128GB of memory. No cloud renders, no API calls, no subscriptions, and one model in memory at a time. The story was locked around 2 AM and the finished trailer was ready at 5:38 PM the same day.</p><p>What it took: a city sized ship built and rendered in Blender (Cycles on Metal); every still from Z-Image-Turbo in bf16, with the creature painted first in MattPaint and made photoreal from that layout; motion from LTX-2.5, with a fast previs draft of every shot, a rough cut, and the slow quality pass only on the shots that made the cut; SeedVR2 upscaling the held shots on the way to 4K (upscaled, not native 4K detail); sound effects from MMAudio generated from the picture itself, plus sub bass we wrote in numpy; ChatterBox voices; an ACE-Step score through Song Forge; our own color LUTs and our own 5.1 surround panner. A local vision model checked the finished cut before anyone saw it: 51 of 53 checks passed, and the two flags are the stone monster itself.</p><p><a href="https://github.com/nicedreamzapp/story-forge/tree/main/projects/last_signal">The full plan, time ledger and known defects on GitHub</a> · <a href="https://youtu.be/VIDEO_ID">Watch on YouTube</a></p></div>
</section>
```

## Insert 2: first card in "The Finished Films" grid (right after the grid's opening `<div style="display:grid;...">`, line ~395)
```html
    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);border-radius:12px;overflow:hidden;">
      <div style="aspect-ratio:16/9;"><iframe src="https://www.youtube.com/embed/VIDEO_ID" title="THE LAST SIGNAL" style="width:100%;height:100%;border:0;" allowfullscreen loading="lazy"></iframe></div>
      <div style="padding:14px 16px;"><h3 style="margin:0 0 6px;color:var(--fg,#fff);">THE LAST SIGNAL</h3><p style="margin:0;opacity:0.75;font-size:0.93rem;">October 31 2026 sci fi teaser. Blender ship, LTX-2.5 motion, 5.1 surround, made in one day on one M5 Max 128GB.</p></div>
    </div>
```

## Placeholders and order
- `VIDEO_ID` appears 3 times; fill it after the YouTube upload. **Deploy order: YouTube upload (public), then the GitHub push (the link points at `projects/last_signal`), then this page.**
- Copy rules: no tool credit for the coding assistant, no "solo" or one person, no dashes in the new prose. The page's existing copy uses em dashes; I left those alone.
- Optional: `og:image` is still the generic GitHub card. A frame from the trailer would make shares look better. Not needed for the launch.

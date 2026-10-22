---
stage: 04_footage
outputs:
  - acquired/
  - manifest.json
gate: none
---
# 04_footage — make the footage, with its papers, and check it against the design

One job: turn the coverage plan into takes on disk, every one with provenance and a design verdict.

## Sources, in order of trust (frozen rule 28)
1. **`blender-render` — PRIMARY for any physical product.** `promo.json "blender"` shots: GLB(s) of the
   exact CAD, PBR presets by material/object name (`carbon`, `aluminum`, `titanium`, `anodized_orange`,
   `steel`, `fabric`, `foam`, `glass_fiber`, `rubber`, `plastic_matte`, `mannequin`, `glow_teal`), a
   `studio` (dark sweep, orange/teal rims) or `hdri` world (shadow catcher), and ONE motivated camera move
   (`orbit`, `push`, `pull`, `truck`, `crane`, `static`). Cycles on Metal; a flat object-ID pass
   (`ids_####.png` + `ids.json`) lets a callout be checked against the real part's pixels. It cannot
   invent or drop a part, so it is what every other source is judged against. M5 speed: ~2 s/frame at
   1280x720 24 spp; previz first with `--preview`.
2. **Local i2v** (`promo.json "i2v"` → `bin/make-ltx25`, LTX-2.5): motion the CAD rig can't do. The
   prompt names an action or a motivated move; static is an explicit flag.
3. **Real footage** placed in `footage/` and listed in coverage.json.
4. **Browser takes (optional, never required):** `bin/browser-acquire projects/<film>/acquire.json`, only
   with `bin/make-promo --acquire`. Matt's Brave on the mini, hidden lease tabs, never an API, `refs[]` of
   matching CAD stills REQUIRED (best match first; Grok animates from the first), the fidelity clause on
   every prompt. Image edits (`grok-image`, `gemini-image`, `chatgpt-edit`) only re-light one CAD close-up.
   **ChatGPT is not for photoreal product shots** (it invents parts and legs). Test the tool with
   `--mock` only; never a live generation as a test.

## Commands (all inside `bin/make-promo`)
1. `python3 pipeline-tools/promo_footage.py projects/<film>` (Song Forge idle + mem-gate first; unchanged shots skip)
2. `python3 pipeline-tools/ingest_acquired.py projects/<film>` → `manifest.json`
3. `~/.local/mlx-server/bin/python pipeline-tools/design_check.py projects/<film> --votes 3` — exit 2 is never a pass

## Done when
Every take is in `manifest.json` with provenance and `checks.design` filled. Nothing acquired is
deleted before the film is approved (frozen rule 13 as amended); a take Matt declines dies now.

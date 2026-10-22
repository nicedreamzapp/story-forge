# Story Forge — the promo format (product films)

A narrated product promo, 16:9 1920x1080 @30 (`format=promo` in `story_forge/packs.py`), made
the way the Sitka promo was made by hand on 2026-10-22 (https://youtu.be/XvE-1hMoaXw): the real
CAD rendered photoreal in Blender, Matt's voice clone, every cut and callout landing on its word,
a ducked instrumental bed, a title slam, an end card whose slam and sting come AFTER the last
word, and nothing shown to Matt until the gates ran and the agent watched the whole cut.

The flow in one line: write it for the viewer, voice it and hear it back, plan way more coverage
than the cut needs, render it from the CAD, pick the best takes, cut to the words, point at the
parts, mix, gate, watch it whole, ship.

**One command:** `bin/make-promo projects/<film>` drives every stage below and stops at the first
failing gate with what to fix (`--from <stage>` to resume, `--only <stage>`, `--renderer remotion`,
`--acquire` for the optional browser takes). It never skips a human check: it builds a DRAFT cut
and says which approvals are still open.

**Start a promo:** `bin/film-status projects/<film> --init --format promo` stamps `_templates/promo/`
(script.md, promo.json, coverage.json, design.json, the stage notes) and writes `FORMAT`. The data
contract for every file is `SCHEMAS.md` next to this file. The worked example and test fixture is
`projects/sitka_demo/` (3 lines, ~27 s; `prepare_fixture.sh` rebuilds its local media).

| Stage | Job | Reads | Writes (in `projects/<film>/`) | Gate | Human check |
|---|---|---|---|---|---|
| `01_story` | the script, a sentiment per line | Matt's idea | `script.md`, `promo.json`, `stages/01_story/premise.md` | not the template | Matt approves the script |
| `02_voice` | matt2 clone, finish chain, heard back | 01 | `vo/final/part*.wav`, `vo/voice.json` | whisper hears every word (retakes, auto-reword) | none |
| `03_coverage` | coverage plan + design facts | 01 | `coverage.json`, `design.json` | `coverage_lint.py` | Matt confirms the design facts |
| `04_footage` | Blender CAD renders (+ local i2v, + optional browser takes), ingest, design check | 03 | `acquired/`, `manifest.json`, `design_report.md` | every take has provenance + a design verdict | none |
| `05_selects` | rank takes per line, with a why | 04 | `selects.json` | `coverage_gate.py` (>= 3x footage) | none |
| `06_edit` | words → cues → EDL, cut to words, end card after the last word | 05, 02 | `vo/words.json`, `cues.json`, `edl.json` | `cue_check.py` | none |
| `07_callouts` | arrows and diagrams on their words | 06 | `callouts.json`, overlays | `callout_check.py` (in 09) | none |
| `08_mix` | bed, duck, SFX, sting, static loudness, the render | 06, 07 | `music/`, `final/mix.wav`, `final/<film>.mp4`, `stages/08_mix/score_pick.md` | render probe | Matt picks the score by ear (at READY) |
| `09_gates` | every gate, strips, then the FULL watch | 08 | `final/*report*.md`, `final/strips/`, `stages/09_gates/known_defects.md` | `promo_gates.py` + cue + callout | Matt watches only at READY FOR MATT |
| `10_deliver` | thumbnail, youtube.json, publish | 09 | `final/thumbnail.png`, `final/youtube.json`, `stages/10_deliver/published.md` | none | Matt says ship it |

## The proven recipe (the defaults in `pipeline-tools/promo_common.py`)
- **Voice:** ChatterBox `matt2`, exaggeration 0.40, cfg 0.5; finish = silence trim → pitch 0.92 via
  `asetrate` (never rubberband) → EQ +3 dB @180 Hz, −3 dB @5 kHz → 0.25 s pad → −16 LUFS → 48 kHz mono.
  Every line is whispered back AFTER the finish (the pitch shift once turned "camp chair" into "cam chair").
- **Footage:** `blender-render` from the CAD GLBs is the PRIMARY photoreal source (PBR presets per
  material name, studio rims or an HDRI world, a motivated camera move, a flat object-ID pass for
  callouts). Local i2v (LTX-2.5) is allowed. Browser takes are an optional extra, never needed.
- **Coverage:** >= 3 setups per line from >= 2 sources; acquired seconds >= 3x the runtime.
- **Edit:** hard cuts on word onsets (mlx-whisper words), a dissolve only where a cue says `xfade`,
  shots never stretched or looped, a title slam (flash + hit) on the brand word, a corner bug.
- **Ending:** the end-card slam starts `slam_after` (0.15 s) after the last word ENDS; the bed's big
  downbeat is offset onto the slam, the bed fades into it, a resolved major sting rings out under the card.
- **Mix:** bed gain 0.55, sidechain-ducked by the voice (thr 0.015, ratio 8, 20/420 ms), SFX synthesised
  (hit, whoosh, blip, sting), two-pass loudnorm `linear=true` to −16 LUFS / TP −1.5 (a static gain).
- **Gates:** whisper the FINAL mix vs the script word for word, loudness −16 ± 1 LUFS and TP <= −1 dBFS,
  voice >= 10 dB over the ducked music, slam after the last word, sting rings, end card on screen,
  every used shot passed `design_check`, every cue on its word, every callout tip on its part,
  frame strips for the eyes, then the agent's full start-to-finish watch.

## Acquired footage and the browser (frozen rule 28)
Inference we run stays local by default. Acquired footage is allowed and gated exactly like our own:
CAD renders, real footage, and browser takes through `bin/browser-acquire` (Matt's logged-in Brave on
the mini, hidden lease tabs, never an API, `refs[]` of matching CAD stills required, the design.json
fidelity clause on every prompt). ChatGPT is NOT for photoreal product shots (it invents parts);
the image-edit backends only re-light one CAD close-up. Browser generation is never part of a test
run: `bin/browser-acquire --mock` exercises the plumbing with no browser at all.

The house rules that shape this format: frozen rules 11, 13 (as amended), 16, 28–32 and RULES.md
26–32. DONE, APPROVED.md and sending a film back work exactly as in `pipeline/CONTEXT.md`.

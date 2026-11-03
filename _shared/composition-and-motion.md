# Composition and motion: vertical, reference breakdown, motion tokens, posters

Added 2026-11-02. Four studio habits, each with a tool. Read this before making a 9:16, matching
a reference look, animating anything with code, or delivering.

## 1. A vertical is its own composition

Never crop the wide film to the middle and never pad it onto a blurred copy of itself (the old
Reels path). A 9:16 comes from the same story, takes, timeline and mix, laid out again:

- **Framing:** every shot gets a 9:16 window that follows the subject
  (`pipeline-tools/reframe.py`: Apple Vision faces, then people, then saliency; a callout's part
  is the subject while it is pointed at). The window is full source height, so heads are never
  cut, and every kept face sits inside it on every sample. The camera stays locked off unless the
  subject leaves a dead zone; moves use the camera token.
- **When it cannot be reframed** (a wide two-shot, a face wider than the window, a product wider
  than the window, a 16:9 title card) the shot is FLAGGED, not padded: `final/vertical/report.md`
  and `rerender_requests.json` list it with the reason, and `--write-spec` stamps it into the spec
  (`promo.json "vertical_rerender"` with the Blender job re-aimed at 1080x1920; `shots.json` /
  `film_shots.json` `"vertical": {"rerender": true, ...}`). A take named `<stem>_v.mp4`,
  `acquired/blender/<id>_v/`, or `"vertical_file"` on the EDL shot is picked up as native.
  The vertical is a DRAFT while anything is flagged.
- **Type and layout** (`pipeline-tools/layouts.py`): bigger type relative to the frame (a title
  ~18 % of the width tall vs ~10 % on 16:9), everything inside the safe box (top 12 %, bottom 22 %,
  right 12 % for the action rail), titles in the upper third, callout labels in a top or bottom band
  on the far side of their part, tips re-mapped through the crop path. At most 2 titles, callouts
  or overlays at once (titles outrank callouts outrank overlays); a callout whose part leaves the
  window is dropped and listed. 16:9 Manim overlays use `<stem>_v.mov` when it exists, else they are
  fitted to the safe width and requested.
- **Every composition has its own contact sheet:** `final/contact_sheet.jpg` (16:9) and
  `final/vertical/contact_sheet.jpg` (9:16, tiles tagged static / pan / native / FLAGGED), plus
  `final/vertical/reframe_plan.jpg` (the window drawn on the 16:9 frames, faces in yellow). Look at
  both before calling the vertical done.

Run: `~/chatterbox-env/bin/python pipeline-tools/vertical_compose.py projects/<film> --render
--write-spec` (promo: make-promo's `vertical` stage does it; film: add `--audio-from final/<Film>.mp4`).
Exit 3 = composed with flagged shots.

## 2. Break a reference down into numbers before making anything

`~/chatterbox-env/bin/python pipeline-tools/reference_analyze.py REF.mp4|REF_DIR projects/<film>`
writes `reference/reference_analysis.md` + `.json` + `palette.png`: the k-means Lab palette as real
hex with shares, tone (L* percentiles, contrast, crushed/clipped), saturation, cut rhythm (shot
lengths, cuts per minute, variation, trend), optical-flow motion per shot, text on screen (how
much, how big, where; never the words), letterbox bars removed first. The VL reading of typography
and composition runs only when the memory broker grants 22 GB; otherwise it is skipped and says
why. `style_contract.py` picks the json up as the measured target (or writes the contract from it
alone when no frames are approved yet). The DO NOT COPY section in the md is binding: numbers only,
never shots, characters, designs, words, footage, or the reference's name in a prompt.

## 3. Motion tokens: one rule per class of object

`pipeline-tools/motion_tokens.py`, pure functions of time and seed (seekable: any frame renders
alone, in any order, identically on any machine; no numpy, so Blender and Manim can import it).

| Token | For | Feel | Function |
|---|---|---|---|
| micro | blips, ticks, a dot landing | 0.12 s ease-out snap, no overshoot | `micro_snap(t)` |
| panel | label pills, cards, lower thirds | spring, one ~8 % overshoot, at rest ~0.5 s; readable by 0.09 s | `panel(t)`, `panel_alpha(t, dur)` |
| camera | pans, pushes, orbits, the vertical follow | quintic ease in AND out, never overshoots | `camera_ease(u)`, `camera_path(keys, t)`, `camera_path_ffmpeg(keys)` |
| headline | titles, brand slams | readable by 0.15 s, scale 1.22 to 1.0, dead-still hold, 0.30 s out, white flash | `headline(t, dur)` |
| mascot | characters, playful props | bouncy spring in + a seeded idle wobble and squash | `mascot(t, seed)` |

Wired in: `render_edl.py` titles (headline), callouts (panel pill, camera-eased arrow, micro dot),
end card; `vertical_compose` crop paths (camera); `blender_render.py` camera moves (camera).
Manim: `rate_func=motion_tokens.rate("camera")`. The headline and panel timings are the ones
`text_readtime_check.py` budgets for; change a feel in `TOKENS` and every renderer follows.

## 4. A poster for every deliverable

`pipeline-tools/poster_frame.py VIDEO --out poster.jpg --film projects/<film>`: a QC jury's pick when
a `final/*.json` names `"poster"` / `"poster_candidate"` / `"poster_t"`, else the best frame of the
final beat (promo: the last narration line before the end card; film: the last 25 % of the cut minus
black and title cards), scored on sharpness, exposure, contrast, colour and faces, never within two
frames of a cut. `promo_deliver.py` writes `final/poster.jpg` and `final/vertical/poster.jpg`
and lists them in `youtube.json "files"`. Film delivery (08) runs it by hand on each deliverable.

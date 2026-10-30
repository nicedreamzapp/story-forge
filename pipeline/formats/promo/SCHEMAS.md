# Promo format: the files every stage reads and writes

All paths are relative to `projects/<film>/`. Times are seconds on the FINAL timeline unless a
field says `src_`. Every tool refuses a file that breaks its schema rather than guessing.

## acquire.json (04_footage input, optional; written by the agent from coverage.json)
```json
{"jobs": [{"id": "l05_rearleg_trail", "line": 5, "setup": "rear leg plants, trail, side",
           "backend": "grok-video", "prompt": "...", "refs": ["footage/rearleg_still.png"],
           "count": 3, "duration": 6}]}
```
`backend` is `grok-image` / `gemini-image` / `chatgpt-edit` (ONE CAD close-up, edit materials + light only), `grok-video`, or `chatgpt-image` (never for photoreal product shots). Browser takes are optional; the primary product source is `blender-render`. `refs` is REQUIRED (CAD stills of the matching pose/angle; Grok animates from the first). `count` >= 3 (coverage, frozen rule 29). `refs` are
paths on the M5; browser-acquire copies them to the mini.

## acquired/ (04_footage output, never deleted before the film is approved, frozen rule 13 as amended)
`acquired/<id>_<n>.png|mp4` plus `acquired/provenance.json`:
```json
{"takes": [{"file": "acquired/l05_rearleg_trail_1.mp4", "id": "l05_rearleg_trail", "n": 1,
            "line": 5, "setup": "...", "backend": "grok-video", "tool": "grok.com/imagine (Brave on the mini)",
            "prompt": "...", "refs": [{"path": "footage/rearleg_still.png", "sha256": "..."}],
            "sha256": "...", "bytes": 1234, "created": "2026-10-22T00:41:00", "gen_secs": 95,
            "src_url": "https://assets.grok.com/...", "page": "https://grok.com/imagine/post/..."}]}
```
One `<file>.json` sidecar per take carries the same record.

## coverage.json (03_coverage)
```json
{"target_runtime": 90, "lines": [{"line": 5, "text": "Here's the science...", "sentiment": "curiosity, then 'oh, that's clever'",
  "setups": [{"setup": "rear leg deploy, side", "source": "cad", "file": "footage/rearleg_deploy.mp4"},
             {"setup": "hiker sits on the trail", "source": "grok-video"},
             {"setup": "macro of the foot planting", "source": "chatgpt-image"}]}]}
```
`source` is one of `blender-render` (primary for products), `cad`, `grok-image`, `gemini-image`, `chatgpt-edit`, `grok-video`, `chatgpt-image` (never for product geometry), `flux-img2img`, `ltx25`, `wan`, `still-kb` (a ken_burns move on a still), `manim`.

Screen-only promos (software, no CAD, Matt 2026-10-26): `still-kb` setups that carry `"still": "refs/<file>.png"`
count as one source per distinct still, so two pan/zooms over different real screenshots plus a third meet
">= 2 sources". Make them with promo.json `"kb"` jobs (`id`, `line`, `setup`, `still`, `move`: push-in |
pull-out | pan-left | pan-right | pan-down, `seconds`), rendered by promo_footage.py with ffmpeg (~1 GB, no
model). Never LTX/i2v on the M5 while the Liquid model is loaded (10/26 OOM freeze).

## acquired/blender/<shot>/ (blender-render, the primary product source)
`beauty_####.png` or `beauty.mp4`, `masks/<part>_####.png` (white = that part), `depth_####.exr`,
and a provenance take like the browser ones plus `"glb"`, `"glb_sha256"`, `"camera"`, `"materials"`
(part -> PBR preset), `"samples"`, `"tool": "Blender <ver> Cycles Metal"`. Part names match
`design.json` `"parts"` so masks, facts and callouts all speak the same names.

A coverage setup may name a design profile, `"design": "<name>"` (added 2026-10-22, sitka_v3): ingest copies it
to the candidate as `"design_profile"` and design_check judges that take against `design.json "profiles"[name]`
(its own references, facts, must_not) instead of the full-body facts. For close-ups of one part, a part on a
printer, the kit laid out flat, a parts table: takes the full-body facts can only ever call UNCHECKED.

## manifest.json (04_footage → 05_selects, written by `pipeline-tools/ingest_acquired.py`)
```json
{"fps": 30, "w": 1920, "h": 1080, "candidates": [
  {"cid": "l05_rearleg_trail_1", "file": "acquired/l05_rearleg_trail_1.mp4", "kind": "video",
   "source": "grok-video", "line": 5, "setup": "...", "dur": 6.04, "w": 854, "h": 480, "fps": 24,
   "shots": [[0.0, 6.04]], "checks": {"design": null, "faces": null}}]}
```
`shots` are PySceneDetect cuts inside the file. `checks.design` is filled by design_check.py
(`"pass"`, `"fail"`, `"unchecked"`).

## design.json (the physical-accuracy contract, 03_coverage)

**Screen-only promo (screenshots of software, no physical product): delete design.json.** `design_check` then marks every take n/a ("no product to check") and the coverage gate counts them; invented facts about a screenshot fail the VL judge (10/30 ladder: two models stalled here).

```json
{"product": "Sitka exoskeleton",
 "references": {"side": "footage/ref_side.png", "front": "footage/ref_front.png", "back": "footage/ref_back.png"},
 "facts": [{"q": "How many rear legs touch the ground on the left side of the body?", "expect": 1, "angle": "side"},
           {"q": "Does the rear leg swing down from behind the thigh (not from the hip or the shin)?", "expect": "yes", "angle": "side"}],
 "must_not": ["a rear leg in front of the knee", "more than one motor per knee", "wheels"],
 "parts": ["rear_leg_L", "knee_motor_L", "ratchet_L", "belt", "battery_L"],
 "materials": {"rear_leg_L": "matte black carbon tube", "knee_motor_L": "brushed 7075 aluminum"},
 "fidelity_clause": "Reproduce exactly the design in the reference: ... (appended to every browser-acquire prompt)"}
```

`"profiles": {"knee_closeup": {"references": {"side": "refs/knee.png"}, "facts": [...], "must_not": [...]}}` is
optional in design.json; a profile's missing keys come from the top level, the house must_not list always applies,
an unknown profile name is UNCHECKED.

## selects.json (05_selects)
```json
{"lines": [{"line": 5, "takes": [{"cid": "...", "rank": 1, "in": 0.4, "out": 3.2,
  "why": "foot plants on the word 'plants', clean geometry, best light"}]}]}
```
Every line ranks >= 2 takes. The coverage gate reads the ratio `(acquired + clips) / selects`.

## vo/words.json (06_edit, written by `pipeline-tools/words_align.py`)
```json
{"gap": 0.35, "lines": [{"line": 1, "wav": "vo/final/part000.wav", "start": 0.0, "end": 4.81, "text": "..."}],
 "words": [{"i": 0, "line": 1, "word": "What", "start": 0.12, "end": 0.31}]}
```
Line starts are the narration layout on the final timeline (lines in order, `gap` silence between).

## cues.json (06_edit, written by the agent; `promo_draft.py` drafts one)
```json
{"cues": [{"line": 3, "word": "motor", "nth": 1, "kind": "cut"},
          {"line": 3, "word": "knee", "kind": "callout", "callout": "knee_motor"},
          {"line": 2, "word": "Sitka", "kind": "title"},
          {"line": 6, "word": "triangle", "kind": "xfade", "dur": 0.4}]}
```
`kind`: `cut` (hard cut lands on the word onset), `xfade` (the only place a dissolve is allowed),
`callout`, `title`. `nth` picks which occurrence of the word in that line (default 1).

## edl.json (06_edit, written by `pipeline-tools/edit_to_words.py`, read by every renderer)
```json
{"fps": 30, "w": 1920, "h": 1080, "dur": 92.4,
 "shots": [{"cid": "...", "file": "acquired/...mp4", "src_in": 0.4, "src_out": 3.2,
            "rec_in": 0.0, "rec_out": 2.8, "line": 1, "transition": "cut", "xfade": 0.0,
            "anchor_word": 0, "speed": 1.0}],
 "audio": [{"file": "vo/final/part000.wav", "rec_in": 0.0, "kind": "vo", "line": 1}],
 "callouts": "callouts.json", "words": "vo/words.json"}
```
J-cut: a shot's `rec_in` may precede its line's first word (the picture leads the voice) or a
line's audio may start under the previous shot (the voice leads the picture). Min shot 0.8 s.

Overlays (added 2026-10-22): `"overlays": [{"file": "overlays/tripod.mov", "rec_in": 15.82, "rec_out": 18.6,
"x": 0.5, "y": 0.5, "w": 0.6, "opacity": 1.0, "cue_word": "Walking"}]` lays ALPHA clips (Manim ProRes 4444
.mov or VP9 WebM) over the shot track, under callouts and titles. `x`,`y` are the clip's CENTER and `w` its
width, normalized to the frame (height keeps the clip's aspect). Supplied by a cues.json entry
`{"line": 3, "word": "Walking", "kind": "overlay", "file": "overlays/tripod.mov", "dur": 2.8, "x": 0.5, "y": 0.5,
"w": 0.6, "opacity": 1.0}` (`overlay` joins the cue kinds; `dur` defaults to the clip's length and never loops).
`"whoosh": false` on an overlay cue (added 2026-10-22, sitka_v3) skips promo_mix's whoosh into it: an overlay
that starts ON a spoken word (kinetic type at a line's first word) must not lay a whoosh over that word.
cue_check gates overlay onsets like every other cue.

## callouts.json (07_callouts)
```json
{"callouts": [{"id": "knee_motor", "label": "Knee motor", "rec_in": 14.2, "rec_out": 17.0,
               "tip": [0.565, 0.61], "text_at": [0.70, 0.30], "cid": "...", "part": "the knee motor"}]}
```
`tip` and `text_at` are normalized 0..1 frame coordinates. `tip` may be a list of `[t, x, y]`
keyframes when the part moves. Renderers: `remotion` (promo-remotion/, tracked arrows, springs)
or `ffmpeg` (PIL PNG overlays, the preview path). `callout_check.py` asks the VL model whether the
arrow tip sits on the named part.

## Renderer plug
`edl.json` + `callouts.json` + `vo/words.json` are the whole interface. A renderer is
`pipeline-tools/render_edl.py --renderer ffmpeg|remotion projects/<film>` and writes `final/<film>.mp4`.

## promo.json (the project's settings, read by every promo tool; defaults = the Sitka recipe)
```json
{"title": "...", "brand": "SITKA",
 "voice": {"character": "matt2", "exaggeration": 0.40, "cfg": 0.5, "pitch": 0.92,
           "eq": [[180, 3.0], [5000, -3.0]], "lufs": -16.0, "retakes": 3},
 "gap": 0.6, "lead": 0.5,
 "music": {"bed": "music/bed.wav", "style": "...", "gain": 0.55, "hit": 81.0, "fade": 1.6, "tail": 1.1},
 "endcard": {"title": "SITKA", "tagline": "Come build one with us.", "url": "github.com/...", "dur": 5.0, "slam_after": 0.15},
 "bug": "SITKA", "renderer": "ffmpeg",
 "materials": {"carbon*": "carbon", "alu": "aluminum", "body": "mannequin"},
 "blender": [{"id": "l01_bl_hero_orbit", "line": 1, "setup": "...", "glb": ["assets/x.glb"], "world": "studio",
              "hdri": "assets/studio.exr", "hdri_rot": 0, "camera": {"move": "orbit", "start_deg": -50, "end_deg": 15,
              "elev_deg": 4, "lens": 50, "amount": 0.25, "frame_fill": 0.85}, "frames": 150, "res": [1920, 1080],
              "engine": "CYCLES", "samples": 48}],
 "i2v": [{"id": "l02_ltx_walk", "line": 2, "setup": "...", "still": "refs/x.png", "prompt": "...", "seconds": 5}],
 "extra_cues": [{"line": 2, "word": "pole", "kind": "overlay", "file": "overlays/d1.mov", "dur": 3, "x": 0.75, "y": 0.5, "w": 0.4}],
 "youtube": {"title": "...", "tags": [], "category": "Science & Technology", "description": "...", "thumb_text": ""},
 "gates": {"lufs": -16.0, "lufs_tol": 1.0, "true_peak_max": -1.0, "design_votes": 3}}
```
`youtube.chapters` (optional, added 2026-10-22): `[{"line": 1, "title": "What it is"}, {"line": 3, "title": "..."}]`;
promo_deliver turns each into a chapter at that line's first word on the final timeline (first forced to 0:00), refuses
fewer than 3 or any under 10 s, and writes them to youtube.json "chapters" and the description.
`music.sting_root` (Hz, optional, default 65.41 = C2): the end sting's major chord root, set to the bed's key
(A1 = 55.0 for a bed in A major) so the resolve does not clash.
`music.hit` = seconds into the bed of its big downbeat (null = auto-detect); it lands on the slam.
`camera.move`: orbit, push, pull, truck, crane, static. Material presets: see `pipeline-tools/blender_render.py`.

## vo/voice.json (02_voice, written by `pipeline-tools/promo_voice.py`)
```json
{"voice": {...}, "lines": [{"line": 1, "text": "...", "spoken": "...", "wav": "vo/final/part000.wav",
  "heard": "...", "match": true, "take": "retake1", "reworded": false, "hash": "...", "notes": []}]}
```
`spoken` is what was voiced (an `alt:` or auto re-wording when `reworded`); every later gate checks it.

## edl.json "endcard" (06_edit, from promo.json endcard)
`{"rec_in": <slam>, "rec_out": <dur>, "title", "tagline", "url", "after_word", "last_word_end"}`: the
shots stop at `rec_in` = last word end + slam_after; cue_check fails a slam before the last word ends.

## final/ (08_mix – 10_deliver)
`mix.wav` (+ `_vo.wav`, `_fx.wav`, `_music.wav` stems, `mix.json`: bed offset, slam, sfx events),
`<film>.mp4`, `promo_gates_report.md/.json`, `cue_check_report.md`, `strips/*.jpg`, `thumbnail.png`,
`youtube.json` (`title, description, tags, category, language, made_for_kids, files`).

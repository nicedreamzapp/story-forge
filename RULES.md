# The rules this pipeline enforces in code

Not advice. Every line here is a gate that runs, and the file the program reads when
someone asks why a shot was rejected. Earned the hard way; see git history for the
incident behind each one.

## What a shot must prove before it ships
1. **The picture must show the beat.** A local vision model describes the frame BLIND,
   then rules PASS/FAIL against the beat. Told the answer first, a model just agrees.
2. **A beat is a VISIBLE STATE.** No intent ("trying to reach"), no offscreen facts
   ("the frightened animal inside"), no change over time ("the door widens"). If a
   viewer with no script can't see it in one frame, the spec is wrong, not the judge.
3. **One instant is not a verdict.** Judgements vote across frames; every ballot prints.
4. **Every named character is checked against its locked master** — allowing for scale,
   distance and light, but never for "a generic cartoon animal of the right colour."
5. **No legible text in frame.** Diffusion paints prompt words onto props ("SHUT" on the
   doors, "FLWAIS" on a car). Signage is added deliberately or not at all.
6. **Sets are canon too.** Nothing locked the train, so one episode grew four of them.
7. **Nothing silently lowers a bar.** No passer → UNBUILT. Partly-good clip → trimmed to
   the part that holds, and the trim is declared. Unjudgeable → UNCHECKED, never a pass.

## How characters are made
8. **One master per character; every other view derives from it.** A LoRA locks identity,
   not colour or texture. Fresh generations drift.
9. **Render each character ALONE at full LoRA strength**, cut it out, composite, then weld
   at low strength. Two LoRAs stacked in one image dilute both — that is how a teddy bear
   and a yellow labrador replaced Hank and Doug.
10. **Parts face the camera in three-quarter view.** A rear view carries no identity.

## How motion is made
11. **Never prompt an impact.** The renderer cannot do collisions; "splinters bursting"
    became a five-second spray that reads as drilling. Felt, not shown.
12. **Never fake motion by shaking a still.** Whole-pixel crops vibrate. Real i2v, a real
    Ken Burns glide, or hold static.
13. **Judge the clip, not just the still** — and keep only the stretch that holds the beat.

## How the machine behaves
14. **It does not stop.** The director owns the film, finds the missing beats, and works
    until they exist or need a human. A queue that ends is an errand.
15. **Escalate, never repeat.** Fail → shorter clip and fresh seeds → still only →
    BLOCKED with a written reason, then move to the next beat.
16. **Every run leaves artifacts**: STATUS.md, WIP_REEL.mp4, QUESTIONS.md. Waking up to
    nothing is a bug.
17. **The memory gate refuses work the machine can't afford** rather than swap-storming.
18. **Audit the auditor.** A calibration set of shots with known human verdicts grades the
    judge every run and warns below 80% agreement.
19. **Learn once, not nightly.** Rejection reasons go to the project's lessons and the
    curated house rulebook, keyed by keyword so they fire on the next film.
20. **Speedups must earn it.** Any multiplier clears bin/measure-render: LPIPS < 0.05 and
    speedup > 1.10×, or it doesn't ship.

## How a film is judged before anyone watches it (added 2026-09-30, The Oldest Tree)
21. **The story must make sense on screen.** `pipeline-tools/continuity_check.py` runs every
    film's `continuity.json` state rules (what exists, what's lit, who wears what, what the
    tree looks like) AND writes a story sheet — one frame per shot beside the narration
    playing over it — that is read against the story before the film is shown. A viewer's
    confusion becomes a new rule the same day.
22. **The ears are measured, never assumed.** `pipeline-tools/audio_check.py`: score vocal
    stem ≥ 15 dB under the music, no sustained low drone, loops/jumps flagged, music never
    above the narration, every line re-heard in its own window. Scores are requested with
    `lyrics: "[instrumental]"`; the person who can hear picks the score.
23. **No dynamic loudness on a finished mix.** One measured static gain + limiter. loudnorm's
    dynamic mode pumps the music up between lines.
24. **Hands never move in close-up.** i2v morphs fingers. Hand inserts are a slow push on a
    clean locked still (`bin/ken_burns.py --size`), or they are cut.
25. **A shot that shows a false story state is cut, not kept for coverage.** A snapped tree
    in a story about a tree that survives is worse than no shot.

## How a film is shot, cut and handed over (added 2026-10-22, Fable review + Sitka promo)
26. **Coverage, then cut to the best.** Every line or beat gets at least 3 setups from at least
    2 sources, acquired seconds reach 3x the runtime, and selects rank at least 2 takes per line
    with a written why. `pipeline-tools/coverage_gate.py` blocks the edit until that holds
    (frozen rules 13 as amended, 29).
27. **Motion is motivated.** Every motion prompt names an action or a camera move chosen for that
    shot. Static is an explicit flag (`make-ltx25 --static`, `"static": true`); the old
    "gentle ambient motion, subtle camera push-in" and forced locked-off defaults are gone
    (frozen rule 31).
28. **Cut to words.** mlx-whisper word timings + `cues.json` drive the edit: hard cuts on word
    onsets, a dissolve only where a cue says `xfade`, never a blanket 0.5 s crossfade.
    `pipeline-tools/cue_check.py` checks every cut landed on its word (frozen rule 32).
29. **The product must be the product.** Every shot of a real object is checked against
    `design.json` (reference angles, counted facts, must_not) by `pipeline-tools/design_check.py`.
    A face check never sees a wrong leg count; the design check does.
30. **Acquired footage carries its papers and our design.** ChatGPT images and Grok Imagine video come only from
    the mini's Brave through `bin/browser-acquire` (never an API), each take with a provenance
    sidecar, and they pass every gate a rendered shot does. Every job uploads CAD stills of the
    matching angle as refs (best match first; Grok uses only the first) and carries the
    `design.json` fidelity clause; browser-acquire refuses empty refs (frozen rule 28).
31. **Nobody shows Matt a film the agent has not watched.** `bin/film-status` prints
    `READY FOR MATT: no` until the gate reports exist and `known_defects.md` is dated, confirms a
    full start-to-finish watch, and is newer than the newest cut (frozen rule 30).
32. **Write for the viewer, then make it judgeable.** Every beat carries a SENTIMENT line (what
    the viewer should feel). The VL judge's limits shape how a shot is staged; they never decide
    what the story is.

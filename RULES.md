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

# Action Lab — can we hold HIGH-ACTION, LONGER scenes? (Matt, 2026-07-31)

Matt: "we should experiment with high action longer scenes to see if we can pull
it off — I can be the judge." Machine gates filter first; every candidate that
survives goes to Matt's click queue at :17600/review (bin/review-add). His NO +
note becomes a lesson. Judging policy: Matt judges ANIMATIONS and character
shots, never empty-scene stills.

## What we know going in (paid-for lessons — motion transfer section, CLAUDE.md)
- Motion transfer is the proven action path: real footage → pose track → character
  performs it. Approved: bear cartwheel, strike combo, 3-beat action scene (7/25).
- Source must be LATERAL (constant camera distance), ONE person in frame.
- Full arc + room: 81 frames (5s) minimum for a move with wind-up and recovery.
- Q6_K GGUF only, never fp16. Bounce ComfyUI before every animate.
- Identity drifts ("Hank-ish, not Hank") — per-character video LoRA is the open fix.
- Straight i2v caps at ~3s before drift (s6_interior, 4 failed 5s takes) — long
  scenes come from motion transfer or from CUTTING short takes, not long renders.

## Experiment matrix (run cheapest-first, one variable at a time)
1. LENGTH LADDER: same proven move class, 81 → 113 → 129 frames (5s → 7s → 8s).
   Does the skeleton hold? Does identity drift grow with length?
2. ACTION LADDER at 81 frames: walk-and-turn → dance step → kick combo → tumble.
   Where does scale/coherence break?
3. TWO-SHOT COVERAGE: one long lateral take + static ffmpeg crops for closeups
   (crops are free and rule-12-safe) — does a 15s SCENE cut together from one
   8s master + crops?

## Needed before renders
- Source footage: none on disk (rule 13 swept the originals). Options: Matt films
  the move himself (best — he owns it, lateral by instruction), or CC0 stock
  (Pexels) pulled when we start. Requirements: side-on, one person, constant
  distance, full arc with lead-in/out.
- GPU window: never during circus_train finishing work or Song Forge customer
  traffic (customer jobs preempt — 4 hit on 2026-07-31 alone).

## Flow per candidate
motion_pose.py (CPU, seconds — read the QC sheet, check the ARC) → make-motion-video
→ beat_gate on the clip → identity vs master → review-add → Matt clicks.

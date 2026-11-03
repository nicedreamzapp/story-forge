---
stage: 08_deliver
outputs:
  - stages/08_deliver/published.md
gate: none
---
# 08_deliver — ship it

One job: publish the approved cut and record where it went.

## Inputs
- Working (this film): `final/<Film>.mp4`, `stages/07_gates/APPROVED.md`
- Reference (every film): `../../YOUTUBE_METADATA.md`

Do NOT load: anything upstream of 07.

## Process
1. Publish only the exact file named in `stages/07_gates/APPROVED.md`.
2. Write `published.md`: URL, date, title, description used.
3. Every deliverable is its own composition with its own poster (2026-11-02, `_shared/composition-and-motion.md`):
   the 9:16 comes from `pipeline-tools/vertical_compose.py projects/<film> --render --write-spec
   --audio-from final/<Film>.mp4` (flagged shots go back to 04 as vertical re-renders, never padded), and
   `pipeline-tools/poster_frame.py <deliverable>.mp4 --out <its folder>/poster.jpg --film projects/<film>`
   writes each poster.
4. Write any lesson from this film into `../../LESSONS.json` (frozen rule 15).

## Outputs
- `projects/<film>/stages/08_deliver/published.md`

## Human check
None. Matt already approved the cut in 07.

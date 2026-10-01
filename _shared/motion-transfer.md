## MOTION TRANSFER — real footage drives a character (2026-07-25, Matt-approved)

Breaks frozen rule 6's action ceiling. Take ANY video of a real person doing something
physical, trace their skeleton, and render OUR character performing it. Cartwheels,
flips, dances, falls, fights — anything we can find footage of. 100% local, Apple
Silicon, no Blender, no NVIDIA physics sim (NVIDIA's GPC needs rigged 3D + CUDA — wrong
stack for us; evaluated and rejected 2026-07-25).

```bash
# stage 1 — real video → pose track (CPU, seconds). ALWAYS read the QC sheet.
~/AI/ComfyUI/venv/bin/python bin/motion_pose.py source.mp4 pose.mp4 \
    --start 3.3 --dur 8.1 --frames 81
# stage 2 — locked still + pose track → the character doing the move (~14 min)
bin/make-motion-video --ref canon/hank_canon.png --pose pose.mp4 --frames 81 \
    "a cartoon brown bear does a fast athletic cartwheel on green grass"
```

Lessons paid for on the first four takes — do not re-derive:
1. **Q6_K GGUF, never fp16.** The 34GB fp16 Animate weights + Song Forge's resident
   45GB = swap storm at ~110 s/step and macOS kills the render. The 14GB Q6_K quant
   does the same job at ~10 s/step. (Rule 11 memory gate caught the aftermath, not the
   cause.)
2. **Never feed slow-motion at its recorded rate.** A 60fps source resampled 1:1 leaves
   the character hanging inverted; Matt read it as "upside down / backwards."
   `motion_pose.py --frames` resamples the window to natural speed.
3. **Give the move its FULL arc + room.** 49 frames truncated the cartwheel mid-flip —
   "only a half cartwheel, and the clip is so short." 81 frames (5s) covering wind-up →
   apex → landing → recovery is what he approved. Verify the arc on the QC sheet BEFORE
   spending render minutes; the pose sheet is the cheapest gate we have.
4. **Pick LATERAL source motion — the performer must stay at roughly constant
   distance from camera.** Wan scales the character to the skeleton, so a move that
   charges TOWARD camera blows the character up until a shapeless close-up rump fills
   the frame and the action becomes unreadable (action_test shot A, run-and-dive,
   2026-07-25 — dead on arrival). Side-on and stationary is what works: the approved
   cartwheel and the karate strike combo both hold scale across the whole clip. Also
   reject sources with more than one person in frame — the tracker locks onto the
   largest body, which is often a bystander closer to camera.
5. **Identity is NOT locked by this.** The character drifts toward a generic version of
   itself — a per-character video LoRA is the open fix (rule 10 still governs: derive
   from the locked master). Say "Hank-ish, not Hank" out loud; never paper over it.
   Also unfixed: fast-motion smear at draft res, and the face can stay upright while the
   body inverts (`face_video` input unused so far).

**Coverage comes free.** The close-up in the approved action scene is a STATIC ffmpeg
crop of the wide shot, not a second render — the multi-shot rule's crop path (default
rule 1a) applies to motion-transfer clips exactly as it does to stills. Static crops
only; frozen rule 12 still bans zoompan/fake pushes.

**Doug and other quadrupeds cannot take a human skeleton** — they get plain i2v reaction
shots. ~~OPEN BUG (2026-07-25): `make-video --i2v` has no GGUF path~~ **CLOSED, verified
2026-07-27:** `wan22_i2v_gguf_ready()` returns True and `build_wan22_i2v_gguf` is the
DEFAULT i2v path (`bin/make-video:72`); fp16 now requires an explicit `--fp16-i2v`.
Two Q6_K stages are ~12GB each rather than ~27GB.

**But GGUF alone is not enough headroom.** ComfyUI still died loading Wan at 20:39 on
2026-07-27 with the GGUF path active, because ~24GB was already parked in swap. The
reliable pattern, measured across every animate that night: an i2v render succeeds when
it starts right after a ComfyUI bounce has reclaimed swap, and dies when it starts on a
box that has been running a while. `mem-gate` before the animate is necessary and NOT
sufficient — it checks free RAM and swap totals, and 93% free RAM with a nearly-full
swap file still kills the render. Bounce ComfyUI immediately before any i2v, not merely
when the gate complains.

Approved clips + pose track: `good-clips/motion_transfer_*` (chmod 444) — the bear
cartwheel, the strike combo, and the 3-beat action scene Matt approved 2026-07-25
("yes this really works"). Project scraps in `projects/action_test/`.

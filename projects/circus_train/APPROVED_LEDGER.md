# Circus Train — APPROVED LEDGER (never reset)
- ✓ CANON sheet v2 (2026-07-22): doug_canon, hank_canon + derived faces — canon/, chmod 444
- ✓ SCENE 1 still: stills/s1_final_v3.png (2026-07-22, chmod 444)
  WINNING RECIPE: single-char LoRA gens → rough composite for layout → flux2 img2img
  weld (strength 0.38, scales hank 0.9 / doug 1.05, seed 3303) → collar removed
  (flux2-edit failed; bounded neck recolor + fur-grain transplant from chest) →
  Qwen3-VL judge PASS (grounding, naturalness, no collar) before showing Matt.
  RULE: every still gets judge PASS before Matt sees it. Doug drifts in dual-LoRA
  t2i — weld from on-model parts instead.
- RULE UPDATE (Matt caught curly-ear Doug passing, 2026-07-22 23:05): identity gates
  must judge by SIDE-BY-SIDE COMPARISON against the locked canon image, never by text
  description alone ("long dark floppy ears" admits spaniel curls). Gate validated on
  known-bad + known-good before trusting. Old-gate passes purged.
- BANNED (Matt, 2026-07-23 ~1am): compositing a pasted character into a wide shot —
  five attempts all read as "sitting on the wheel"/floating to Matt regardless of
  gates. Wide shots = pure diffusion frames only. Characters who can't survive
  dual-LoRA wides get their OWN shot (film grammar: wide + insert coverage).
- DOUG LoRA V2 (2026-07-23 ~3am): retrained on 12 master-derived images (recipe:
  lora_build2/), rank-16, 180 steps @768px, mlx-cache capped 24GB (jetsam killed
  uncapped runs). Passes insert/seated/two-shot validation. Production copy:
  ~/.hankdoug_seeds/DOUG_LORA_V2.safetensors (v1 kept).
- IDENTITY GATE V4: viewer-standard comparison against canon w/ hardened ear clause.
  VALIDATED 6/6 on the ground-truth suite (master, locked S1, stringy-ears NO,
  Matt-rejected curly-ears NO, V2 insert/two-shot YES). RULE: any future gate change
  must re-score 6/6 on this suite before deployment.
- ✓ LOCKED (Matt "ok/okay" 2026-07-23 ~4:20am): S2 wide = s2_hankweld (LOCKED_s2_wide),
  S3 = arrival PASS_1, S5 = doug_moment PASS_1 (nose at crack), S6 = hank_moment PASS_2
  (shoulder drive, splinters). All chmod 444. S4/S7/S8 still need staging rethink.
- ✓ ELLIE CANON (2026-07-24): canon/ellie_canon.png, chmod 444. Matt delegated the
  pick ("dont care") — seed 101 chosen: symmetrical front master, circus crown w/
  red plume, amber eyes. Losing candidates deleted per rule 13. All Ellie views
  DERIVE from this master (rule 10) — never fresh-generate her.
- ✓ SCENE 2 "THE CALL" still LOCKED (Matt "yes" 2026-07-25): stills/LOCKED_s2_call.png,
  chmod 444. Circus train crossing the trestle over the river at golden hour, smoke
  plume — the boys SEE the trouble instead of a bird announcing it (fixes rough-cut v1's
  missing call to adventure). Derived from s4_call_11 with the gibberish "FLWAIS"
  lettering painted off the yellow car (PIL colour-sampled fill, NOT flux inpaint —
  denoise-1.0 inpaint on a small mask smeared the panel into fake windows; rejected).
  Works for EITHER circus-train canon, so it does not pre-commit the episode conflict.
  Losing candidates deleted per rule 13.
- ✓ EPISODE_v1.mp4 BUILT 2026-07-25 via bin/build-episode (59.3s, 20 segments,
  832x480@24). Original Song Forge score "The Wild Rescue" (job
  22c04ef7ef054bcfa10b065d055fbbfe, 150s) laid under and sidechain-ducked. The four
  off-screen VO takes (L03/L08 bird+Ellie, L12 unused, L16 bird) finally placed.
  S6 trimmed to 2.3s (brace only) since the full take is rejected — declared in EDL.
  film_qc: 91 checks, 86 passed, 5 failed. ALL 12 lip-sync PASS, all 59 artifact
  sweeps clean, all silence checks clean. The 5 fails: 4 are transcript-matcher
  confusions on repeated phrases ("The Wild Rescue" appears twice; "circus train"
  twice) and 1 is a TRUNCATED VL identity answer, not a stated defect. Nothing in
  the picture is known-bad. NOT yet approved by Matt.
- QC TOOL FIXED same session: film_qc lip-sync now samples 3 instants per line
  (single-sample false FAILs sent 7 good a2v clips to "failed" 2026-07-23) and honours
  an "offscreen": true flag so voice-only characters are audio-verified, never
  mouth-checked. 11 defects → 5 with no change to the film itself.
- ✓ LOCKED (Matt "good one" 2026-07-29 03:39): s3_rollout = clips/s2_final.mp4 — the
  wagon animated from the Matt-approved LOCKED_s2_wide still (beat PASS 5/5). Replaces
  the 2026-07-28 19:14 auto-reroll whose bear had crossed eyes. chmod 444.
- ✓ LOCKED (Matt clicked YES in /review 2026-07-31 13:06): s6_interior =
  clips/s6_interior_final.mp4 — the bang felt from inside. NOT Wan: real motion
  graphics on the gate-passed still (s6_overlay.py — dust in the beam, sub-pixel
  shudder at 1.2s, dust burst rains and settles). beat_gate clip PASS 5/5 after
  five failed i2v attempts across two stills (Wan cannot hold a static dark
  interior with one light source — brightens/opens, hallucinated a human, or
  fades and fragments). Losing takes deleted per rule 13. chmod 444.
- ellie_eye TRIMMED to 3.9s (2026-07-31): the eye relaxes sleepy in the last
  second — cut before the drift, VO ends at 3.16s so nothing lost. beat_gate
  3/5 PASS on the trimmed take. Matt's standing rule: short clips are fine.
- EPISODE_v1.mp4 REBUILT 2026-07-31 13:24 (74.1s, 23 segments): new s6_interior
  (motion-graphics bang, Matt YES 13:06), ellie_eye trimmed 3.9s, all 9 beats
  PASS or set-drift-only. film_qc: 15 checks, 8 passed, 7 failed — but targeted
  whisper on the 27-45s window (with AND without music) hears ALL 6 "NOT HEARD"
  lines at their slots; full-pass whisper loses the scored middle (same class as
  the 7/23 false alarms). 7th fail is L05 manifest wording vs recorded take.
  Known set drift ships documented: s4_arrival, ellie_eye, s6_heave (door/car
  detail vs masters). NOT yet approved by Matt.
- s8_goodbye SKINNY-DOG TAKE TRASHED 2026-07-31 (Matt: declined in another
  session, was supposed to be deleted, resurfaced into the 13:24 cut). Locked
  still + final clip + kb copy all rm'd. The scene is UNBUILT until a sturdy
  on-model Doug passes gates AND Matt's click.
- s7_dooropen HINGED-DOORS TAKE TRASHED 2026-07-31 16:17 (Matt NO on the cut:
  "he's sliding on the door to open it, and then... the doors aren't hinged the
  same way. It's like they open differently" — plus a ladder and zero dust
  right after the bang). Locked still + final clip deleted same session per
  rule 13 corollary. Rebuilding as a SLIDING-door boxcar with settling dust.
- s7_dooropen REBUILT BY HAND 2026-07-31 20:55 (after ~5h/20+ seeds of roll
  failures): empty sliding-door plate (seed 34) + PIL composite of Ellie canon
  into the doorway + img2img weld denoise 0.5 seed 82. beat_gate 3/3 PASS,
  identity YES, text clean. Locked chmod 444. Losing weld + spare plates
  deleted per rule 13. Cap simplified vs canon (plain red w/ plume) — Matt to
  judge on the clip.

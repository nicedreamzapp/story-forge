## MANDATORY STORY + SOUND GATES — before ANY film is shown to Matt (added 2026-09-30)
film_qc checks faces, mouths and glitches. It passed The Oldest Tree while Matt, watching,
found a buzzing drone, a sung vocal in the "instrumental" score, music louder than the
narrator, melting fingers, a tree that looked burned to a stump, a flashlight that "went out"
and kept glowing, and an ending heart shot with no heart. "I'm surprised you're not noticing."
So four gates now run, in this order, and all four reports are read before showing:
1. `~/chatterbox-env/bin/python pipeline-tools/audio_check.py FILM --score S --timeline final/timeline.json --narration narration.json`
2. `~/.local/mlx-server/bin/python pipeline-tools/continuity_check.py projects/<film>` —
   needs `projects/<film>/continuity.json`; ALSO read `final/story_sheet.png` + `.md` yourself
   against the story and write down what a first-time viewer would misread.
3. `film_qc.py` (below).
4. `~/AI/ComfyUI/venv/bin/python pipeline-tools/face_check.py projects/<film>` (added 2026-10-03) —
   face-recognition match of every on-screen face against its canon portrait, 5 frames per shot.
   film_qc's identity sheet passed a different, younger girl in s4_walkback; Matt caught it by eye.
   FAIL = median match < 0.30 in the film (< 0.45 on a still). forge-shot now runs it on every
   still before lock and every clip before keep, including shots that list canon only under `refs`.
   Its age numbers are NOT reliable on children (canon 10-year-old reads 37); judge age by eye.
Then tell Matt what is still wrong BEFORE he finds it. Rules 21–25 in RULES.md.
Score requests: always `"lyrics": "[instrumental]"`; Matt picks the score by ear from 2–3 screened candidates.
Mix: static gain, never loudnorm dynamic. Hands: ken_burns on a locked still. Foley (MMAudio)
only after audio_check proves it isn't noise.

## MANDATORY QC STAGE — `pipeline-tools/film_qc.py` (added 2026-07-22, non-negotiable)
No film, scene, or demo is EVER reported to Matt as "checked/verified/done" until this
agent has run and its report is read. Frame-grid spot checks are NOT verification —
that shortcut shipped a broken film on 2026-07-22 ("Every Day" incident).

Run:
```bash
~/.local/mlx-server/bin/python "~/Desktop/PROJECTS/story-forge/pipeline-tools/film_qc.py" FILM.mp4 manifest.json
```
The manifest lists characters, scene time-ranges, and every dialogue line with its
final-timeline timestamp + speaker (schema in the script docstring). The agent uses
**Picture Eyes' Qwen3-VL-32B** (server :8181 if up, else loads in-process) as eyes and
**mlx-whisper** as ears, and checks: (1) correct character's mouth moving at each line,
(2) mouths shut during silence, (3) character identity consistent across scenes,
(4) 1s-interval artifact sweep (morphing/merging/extra limbs), (5) every line audible
at its expected time. Exit 0 = pass, 1 = defects (read the `_qc.md` report), 2 = QC
couldn't run — NEVER treat 2 as a pass.

Report results to Matt as: "film_qc ran N checks: X passed, Y failed — defects: …" and
attach/summarize the report. Anything film_qc cannot judge (phoneme-level lip precision,
taste) is stated as UNCHECKED and left to Matt's eyes — never papered over.

Upgrade path: finish downloading `mlx-community/NVIDIA-Nemotron-3-Nano-Omni-30B-A3B-4bit`
(audio+video jointly) and add a true AV-sync check — the Jul 15 download died at 4KB.

### QC gates — catch failures EARLY, not at the end (added 2026-07-22)
Run QC at three points, cheapest first, so bad work dies before it eats render time:
1. **Input gate (seconds):** before animating, show each still to the VL model (via
   film_qc's vl_ask or Picture Eyes :8181): characters on-model? composition right?
   Whisper-check every voice take for duds. Stills cost ~11s — re-roll freely.
2. **Draft gate (~2-3 min):** before any 15min+ render, generate a cheap draft of the
   same shot (e.g. 97 frames @ 480x256, same prompt/audio) and QC it. Kills bad
   staging/dead mouths/drift at ~1/6 the cost. Imperfect predictor, great filter.
3. **Scene gate (mid-queue):** in multi-scene queues, run film_qc on each scene AS IT
   COMPLETES and STOP the queue on failure — re-roll that scene before rendering the
   next. Never batch-render blind and discover defects at assembly.
Mid-render aborts aren't possible (no intermediate frames exposed); the draft gate is
the substitute.

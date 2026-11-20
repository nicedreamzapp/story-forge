# GitHub — push THE LAST SIGNAL pipeline (DRAFT, nothing committed or pushed)

Repo: `~/Desktop/PROJECTS/story-forge`, remote `origin https://github.com/nicedreamzapp/story-forge.git` (public), branch **main**, HEAD `c4cb021` (Merge PR #22 swap-mode-local-agents). The working tree has 9 modified and many untracked paths, most of them **not** ours (other films, backups). Stage by explicit path only. Never `git add -A`.

Matt (8:05 PM): the Reddit and YouTube posts link this repo as proof, so the push has to make the claims reproducible. Below: what to commit, the 3 small fixes to make first, the reproducibility gaps that stay, the scan, the commit message and the README section.

## 1. Fix before committing (3 small edits, not made yet)

a. **`pipeline/04_shots/CONTEXT.md` step 5c says the wrong engine.** It reads "Wan 2.2 14B bf16 renders ONLY what makes the cut", but this film's quality pass was **LTX-2.5 `--hq`** (Wan 2.2 isn't on the M5; it was deleted 10/25, per PRODUCTION-PLAN 3:25 AM and 4:43 AM). Proposed text for 5c and 5d:
```
   c. The quality engine (LTX-2.5 `make-ltx25 --hq`, dev transformer + CFG two-stage; Wan 2.2 14B bf16
      only if it is installed and the memory guard allows it) renders ONLY what makes the cut, at the
      cut's length plus ~0.5 s handles (never a blanket 5 s); 3 takes for hero shots, 1-2 for the rest.
      A previs draft that already holds up for a sub-second cut stays and skips the quality pass.
   d. Render at the 480p-class native size (832x480); SeedVR2-3B upscales at assembly (held shots
      >= ~0.9 s at 720p, then lanczos to 4K; sub-second cuts lanczos only; see LESSONS).
```
b. **`bin/make-sfx` shebang is hard-wired** to `#!/Users/dtribe/AI/ComfyUI/venv/bin/python`. Nobody else can run that, and it carries the username. Make it like `bin/surround-mix`: rename the Python to `tools/make_sfx.py` and make `bin/make-sfx` a 6 line bash wrapper that tries `$HOME/AI/ComfyUI/venv/bin/python`, then `python3`. (`projects/last_signal/tools/sfx_batch.py` has the same path once, so fix it the same way.)
c. **Absolute paths in the job files** (131 hits of `/Users/dtribe/Desktop/PROJECTS/story-forge/projects/...` across `tools/jobs_*.json` and `sfx/jobs*.json`). These hold the exact prompts, seeds, strengths and init images, which is the reproducibility, so keep them. Rewrite the prefix to repo-relative, and the batch scripts then run from the repo root (they open `Path(j["out"])` as given):
```bash
cd ~/Desktop/PROJECTS/story-forge
sed -i '' 's#/Users/dtribe/Desktop/PROJECTS/story-forge/##g' projects/last_signal/tools/jobs_*.json projects/last_signal/sfx/jobs*.json
```

## 2. Exactly what to commit

**New pipeline tools (generic, every future film uses them)**
- `bin/make-sfx` (+ `tools/make_sfx.py` after fix b): MMAudio large 44k v2, text or picture-synced, waits on Song Forge customer jobs, one generation then exit.
- `bin/grade`: ffmpeg lut3d + temporal grain + 2.39:1 scope bars.
- `tools/make_luts.py` + `luts/` (6 .cube files, 5.6 MB: teal_orange_blockbuster, cold_space_teal, warm_alien_haze, bleach_bypass, kodak_2383_style, neutral_filmic).
- `bin/surround-mix`, `tools/surround_mix.py` (the 5.1 panner: azimuth keyframes, LFE send, E-AC3 5.1 + stereo mux), `tools/test_surround_mix.py`.

**Contract edits (the method, baked in)**
- `pipeline/04_shots/CONTEXT.md` (previs first, after fix a), `pipeline/05_sound/CONTEXT.md` (SFX stage + mix_plan), `pipeline/06_assemble/CONTEXT.md` (surround + grade steps).
- `LESSONS.json` (+12 entries, all `learned_on: "THE LAST SIGNAL trailer 2026-10-31"`).

**The film's project folder (the receipts), `projects/last_signal/`**
- Plan and story: `PRODUCTION-PLAN.md` (decisions + both time ledgers), `stages/**.md` (premise, script v3, approvals, selects, score_pick, known_defects, published template).
- Shot data: `beats.json`, `shots.json`, `film_shots.json`, `renders.json`, `selects.json`, `coverage.json`, `continuity.json`, `manifest.json`, `narration.json`, `final_plan.json`.
- Edit and finish: `final/edl_final.json`, `final/edl_final_graded.json`, `final/previs_edl.json`, `final/timeline.json`, `final/segs/handles.json`.
- Gate reports: `final/film_qc_report.md`, `final/audio_check_report.md`, `final/continuity_report.md`, `final/face_report.md`, `final/story_sheet.md`.
- Sound data: `sfx/jobs.json`, `sfx/jobs_scream.json`, `sfx/mix_plan.json`, `sfx/synth_times.json`, `music/candidates/score_*.json`, `music/arranged/arrangement.json`, `voices/voice_check.json`.
- Every script: `tools/*.py`, `tools/*.sh`, `tools/jobs_*.json` (after fix c), `ship/build_ship.py`, `ship/shots.py`, `ship/render_anims.sh`, `ship/render_finals.sh`.
- Inputs someone needs to rerun the stills: `canon/*.png` (6 files, 8.3 MB: captain, crewmate, cockpit, ship, plain_monoliths, and the MattPaint creature guide, which is Matt's own art) and `stills/refs/creature_layout_nobanner.png`.
- Optional: `stills/LOCKED_*.png` (20 files, 9.8 MB, the approved start frames) and `ship/ship.blend` (9.8 MB). Both regenerate from the scripts. I'd include the LOCKED stills (they show the hybrid) and skip the .blend.

**Do NOT commit**
- Media: `*.mp4` / `*.wav` are already gitignored (final films, clips, voices, music, sfx audio). `ship/renders/` is 94 MB of PNG and regenerates with Blender, so leave it out.
- `logs/` is gitignored by `projects/**/*.log`, but `logs/*.json` and `*_report.md` are not. Skip `projects/last_signal/logs/` (machine run artifacts).
- Not ours, so leave them out of this commit: `bin/forge-session`, `pipeline-tools/ingest_acquired.py`, `pipeline-tools/promo_common.py`, `METRICS.jsonl` (other films' rows), `projects/oldest_tree/*`, the other untracked projects, every `*.bak*`, `sessions.png`.

**Stage command (after the 3 fixes; not run):**
```bash
cd ~/Desktop/PROJECTS/story-forge
git add bin/make-sfx tools/make_sfx.py bin/grade bin/surround-mix tools/make_luts.py tools/surround_mix.py tools/test_surround_mix.py luts/ \
  pipeline/04_shots/CONTEXT.md pipeline/05_sound/CONTEXT.md pipeline/06_assemble/CONTEXT.md LESSONS.json
cd projects/last_signal
git add PRODUCTION-PLAN.md beats.json shots.json film_shots.json renders.json selects.json coverage.json continuity.json manifest.json narration.json final_plan.json \
  stages final/*.json final/*_report.md final/story_sheet.md final/segs/handles.json \
  sfx/*.json music/candidates/*.json music/arranged/arrangement.json voices/voice_check.json \
  tools ship/*.py ship/*.sh canon stills/refs/creature_layout_nobanner.png stills/LOCKED_*.png
git status --short | grep -v '^??'   # review before commit
```

## 3. Reproducibility gaps that stay (say so in the README, don't hide them)
- **Memory lease client:** 5 batch scripts (`zimage_batch`, `seedvr2_batch`, `sfx_batch`, `voice_batch`, `qwen_batch`) import `mem_client` from `~/SongForgeM5`, which is private. `bin/make-ltx25`, already public, does the same. Suggest a fallback (`try: from mem_client import reserve` / `except ImportError: reserve = lambda *a, **k: contextlib.nullcontext()`) so they run anywhere.
- **Score:** `commission_score.py` calls the local Song Forge server (127.0.0.1:8767), which isn't public. Others would run ACE-Step 1.5 directly with the same prompt (it's in the script).
- **Voices:** the reference clips (the ruby EARS reference is CC-NC, the spare pool) aren't in the repo, and shouldn't be. ChatterBox with any clean reference reproduces the method.
- **Model weights** are downloaded, not vendored: Tongyi-MAI/Z-Image-Turbo, dgrauet/ltx-2.5-mlx, seedvr2_ema_3b_fp16, MMAudio large 44k v2, chatterbox-tts 0.1.7, Qwen3-VL-32B (4-bit MLX) for the gates, whisper-large-v3-turbo, insightface inswapper_128.
- `voice_batch.py` imports character casting from `~/AI/videopipe/bin`. The repo has `bin/character_voice.py`, so point it there.

## 4. Secrets / PII scan (run 10/31 on all 96 text files in the stage list, .cube excluded as pure numbers)
Patterns: API keys (sk-, ghp_, gho_, github_pat_, AKIA, hf_, xox, AIza, private key blocks, refresh_token, client_secret, password/token/secret assignments), IPv4, emails, US phone numbers, family names and home-area place names, home paths.
Result: **secrets 0, IPs 0, emails 0, phones 0, family/location 0.** Home paths: **133 hits in 11 files** (`/Users/dtribe/...`). 131 are in the job JSONs (fix c), 1 is the make-sfx shebang (fix b), and 1 is in sfx_batch.py (fix b). The repo already tracks 23 files with `/Users/dtribe` paths, so it isn't new exposure, but fixes b and c remove it from this push. Re-run the scan on `git diff --cached` right before committing.

## 5. Commit message (no AI attribution lines, no Co-Authored-By)
```
THE LAST SIGNAL: sci-fi teaser made fully local, plus the tools it added

A 46.6 s trailer made on one MacBook Pro M5 Max 128GB, one model in memory at a time:
Blender Cycles (Metal) ship, Z-Image-Turbo bf16 stills, LTX-2.5 previs then hq pass on
only the shots in the cut, SeedVR2-3B upscale, MMAudio picture-synced SFX plus numpy
sub-bass, ChatterBox voices, ACE-Step score, our own LUTs and 5.1 panner, film_qc 51/53.

New tools:
- bin/make-sfx: MMAudio text or picture-synced SFX, waits on Song Forge jobs
- bin/grade + luts/ + tools/make_luts.py: LUT grade, grain, 2.39:1 scope
- bin/surround-mix + tools/surround_mix.py: 5.1 panner, E-AC3 5.1 + stereo mux (tests)

Contracts: 04 previs-first motion order, 05 SFX stage + mix_plan, 06 surround + grade.
LESSONS: 12 entries from this film (model inventory, timing, SeedVR2 budget and batch bug,
clip-gate wording, mix clamp, SFX noise check).
projects/last_signal: plan with the real time ledger, scripts, job files, EDLs, gate
reports and known defects. Media stays out of git.
```

## 6. README section (insert above "### 🌲 Newest: The Oldest Tree", and change that heading to "### 🌲 The Oldest Tree (October 2026 progress film)")
```markdown
### 🛸 Newest: THE LAST SIGNAL (sci-fi teaser, October 31 2026)

[![THE LAST SIGNAL](./last-signal-hero.jpg)](https://youtu.be/VIDEO_ID)

A cargo ship follows a signal nobody has charted, and the planet at the end of it already knows the captain's name. **46.6 s**, 50 cuts, 4K deliverable, 5.1 surround plus stereo.

Made in one day on one **MacBook Pro M5 Max with 128GB**, one model in memory at a time: story locked around 2 AM, finished trailer at **5:38 PM**. About 5 h of that was LTX-2.5 motion, about 3.4 h the SeedVR2 upscale, and about 2 h were stalls (the full ledger is in the plan).

**New this film: previs first.** Every shot gets a fast LTX-2.5 distilled draft, a rough cut decides which seconds actually make the trailer, and only those get the slow hq pass. Also new: [`bin/make-sfx`](bin/make-sfx) (MMAudio, picture-synced), [`bin/grade`](bin/grade) with our own [LUTs](luts/), and [`bin/surround-mix`](bin/surround-mix), our 5.1 panner.

Stack: Blender 5.1.1 Cycles (Metal) ship · Z-Image-Turbo bf16 stills (creature from a MattPaint layout via img2img) · LTX-2.5 MLX bf16 previs + hq · SeedVR2-3B upscale (held shots at 720p, then resized to 4K, so not native 4K detail) · MMAudio SFX + numpy sub-bass · ChatterBox voices · ACE-Step score · Qwen3-VL-32B + Whisper QC (film_qc 51/53) · ArcFace face check + inswapper face lock · FFmpeg.

Honest about the rough spots: [known defects](projects/last_signal/stages/07_gates/known_defects.md).

[▶ Watch](https://youtu.be/VIDEO_ID) · [📁 Project folder](./projects/last_signal/) · [⏱ Plan and time ledger](./projects/last_signal/PRODUCTION-PLAN.md)
```
Needs: the YouTube ID after upload, and a `last-signal-hero.jpg` (the same frame as the thumbnail, about 1280 px wide, committed at repo root like `oldest-tree-hero.jpg`). The "Watch the films" SVG banners (`assets/readme/s02-*`) only name 3 films; leave them, or regenerate later.
README text is the repo's voice (it already uses hyphens and the · separator), not Matt's Reddit voice. No tool credit lines.

After the push: gh-watcher on the mini already watches nicedreamzapp repos (issues, PRs) every 15 min, so new issues on the repo will text Matt.

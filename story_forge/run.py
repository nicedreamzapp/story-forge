#!/usr/bin/env python3
"""Story Forge runner — translates a .storyplan.json into a real mp4.

Two render paths:
  - "lean"  (default): per-scene Flux still -> render-route (Wan/LTX) i2v ->
            optional Piper narration -> ffmpeg xfade stitch. Tight, fast,
            no overlays. Honors per-scene `motion.engine` from the DSL.
  - "full"  (--engine full): delegate to story_pipeline.py for the legacy
            Bear-Sister pipeline (overlays, chapter grades, particle layers).

The IR -> config translation for the full path lives in
`storyplan_to_pipeline_config()` so existing callers keep working.

LIPSYNC INTEGRATION CONTRACT
----------------------------
When a `narration_spec.lipsync` is truthy (set by the DSL via
`narrate <voice> with lipsync[=lp|=wav2lip]:`), the lean renderer:

  1. Renders the Piper wav for the narration line as usual.
  2. Spawns the avatar pipeline at
     `~/Desktop/PROJECTS/avatar-pipeline/LivePortrait/inference.py` (LP-only,
     Matt's preferred default) or — when `lipsync == "wav2lip"` — chains
     the Wav2Lip mouth pass on top of the LP output. Driver still defaults to
     `~/AI/videopipe/test_stills/walk_frame.png`; override via the
     `LIPSYNC_DRIVER_STILL` env var (per scene override TBD).
  3. Composites the resulting talking-head clip INTO the scene as a
     lower-third overlay: bottom-right, ~30% scene width, 32px inset,
     50ms crossfade in. The scene's base motion video is untouched
     underneath; only that scene gets the head overlay.

When `lipsync` is False (default) the renderer behaves exactly as before:
narration audio only, no per-scene overlay.

Backends understood:
  - False    -> no lipsync, no overlay
  - "lp"     -> LivePortrait only (body motion, mouth NOT phonetic). Default
                when the DSL says `with lipsync:`.
  - "wav2lip"-> LP + Wav2Lip whole-face pass (phonetic mouth but stiffer body).

The avatar pipeline call is invoked through `_render_lipsync_clip()`. When
the binaries are missing (no LP venv, no W2L checkpoint, no driver still)
the runner logs and falls back to audio-only — the storyplan still
renders, just without the head overlay.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# Every external path resolves through story_forge.config, which reads SF_*
# environment variables and otherwise falls back to this repo. These names stay
# module-level so tests can monkeypatch them the way they always have.
from story_forge import config as _cfg  # noqa: E402

REPO = _cfg.VIDEOPIPE
PIPELINE = _cfg.PIPELINE
RENDER_ROUTE = _cfg.RENDER_ROUTE
HOME = _cfg.HOME
FLUX = _cfg.FLUX_SCRIPT
WAN_OUT = _cfg.OUT_DIR
DEFAULT_OUT_DIR = _cfg.OUT_DIR
PIPER = _cfg.PIPER
PIPER_MODEL = _cfg.PIPER_MODEL

# --- Avatar pipeline (LivePortrait + Wav2Lip) --------------------------------
# Optional. Only `with lipsync` touches these; missing pieces fall back to
# audio-only rather than failing the render.
AVATAR_DIR = _cfg.AVATAR_DIR
LP_DIR = _cfg.LP_DIR
LP_VENV_PYTHON = _cfg.LP_VENV_PYTHON
LP_INFERENCE = _cfg.LP_INFERENCE
W2L_DIR = _cfg.W2L_DIR
W2L_CKPT = _cfg.W2L_CKPT
DEFAULT_DRIVER_STILL = _cfg.DRIVER_STILL

# Lower-third overlay knobs (kept in module scope so tests can monkeypatch).
LIPSYNC_OVERLAY_SCALE_W = "iw*0.30"   # ~30% of scene width
LIPSYNC_OVERLAY_INSET = 32            # pixels from the right and bottom edges
LIPSYNC_OVERLAY_FADE = 0.05           # 50ms crossfade in

# ---------------------------------------------------------------------------
# Full-pipeline config translation (kept for --engine full / legacy use)
# ---------------------------------------------------------------------------

def storyplan_to_pipeline_config(plan: dict[str, Any]) -> dict[str, Any]:
    """Convert a storyplan dict into the JSON shape story_pipeline.py expects."""
    meta = plan["film_meta"]
    scenes_dict: dict[str, dict[str, Any]] = plan["scenes"]

    pipeline_scenes = []
    for name, sc in scenes_dict.items():
        still = sc.get("still_spec") or {}
        motion = sc.get("motion_spec") or {}
        narrate = sc.get("narration_spec") or {}
        pipeline_scenes.append({
            "name": name,
            "still": still.get("prompt", ""),
            "motion": motion.get("prompt", ""),
            "narration": narrate.get("line", ""),
            "still_seed": still.get("seed"),
            "motion_seed": motion.get("seed"),
            "duration": float(motion.get("duration",
                                         meta.get("scene_duration", 8.5))),
        })

    voice_presets = plan.get("voice_presets", {})
    voice = "warm_female_storyteller" if voice_presets else "none"

    return {
        "title": meta.get("title", "Untitled"),
        "slug": meta.get("slug", "untitled"),
        "style": "",
        "character": "",
        "scenes": pipeline_scenes,
        "voice": voice,
        "scene_duration": meta.get("scene_duration", 8.5),
        "overlays": {
            "dust_all": True, "film_grain": True, "vignette": True,
            "chapter_grades": {},
        },
        "_storyplan": plan,
    }


# ---------------------------------------------------------------------------
# Lean per-scene renderer
# ---------------------------------------------------------------------------

def _sh(cmd: list[str], **kw) -> None:
    print(f"$ {' '.join(str(c) for c in cmd)}", flush=True)
    subprocess.run(cmd, check=True, **kw)


def _ffprobe_duration(path: Path) -> float:
    out = subprocess.check_output(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        text=True,
    ).strip()
    return float(out)


def _render_still(prompt: str, out_png: Path, seed: int,
                  width: int = 768, height: int = 512) -> None:
    """Flux T2I to out_png. Idempotent: skip if already there."""
    if out_png.exists():
        print(f"[still] cached: {out_png}")
        return
    out_png.parent.mkdir(parents=True, exist_ok=True)
    _sh([str(FLUX), prompt, "--out", str(out_png),
         "--w", str(width), "--h", str(height), "--seed", str(int(seed))])


def _render_motion(prompt: str, still_png: Path, out_mp4: Path,
                   engine: str, duration: float, label: str) -> None:
    """render-route i2v -> moves result into out_mp4. Idempotent."""
    if out_mp4.exists():
        print(f"[motion] cached: {out_mp4}")
        return
    WAN_OUT.mkdir(parents=True, exist_ok=True)

    # render-route writes into WAN_OUT/<label>_*<ts>.mp4; we glob for it after.
    before = set(WAN_OUT.glob(f"{label}_*.mp4"))
    eng_arg = engine if engine in ("wan", "ltx") else "auto"
    _sh(["python3", str(RENDER_ROUTE),
         "--still", str(still_png),
         "--duration", str(duration),
         "--label", label,
         "--engine", eng_arg,
         prompt])
    after = sorted(set(WAN_OUT.glob(f"{label}_*.mp4")) - before,
                   key=lambda p: p.stat().st_mtime, reverse=True)
    if not after:
        # Fallback: most-recent file with that label prefix
        all_match = sorted(WAN_OUT.glob(f"{label}_*.mp4"),
                           key=lambda p: p.stat().st_mtime, reverse=True)
        if not all_match:
            raise RuntimeError(f"render-route produced no output for {label}")
        produced = all_match[0]
    else:
        produced = after[0]
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(produced, out_mp4)


def _conform_clip(src: Path, dst: Path, scene_dur: float,
                  width: int = 1280, height: int = 720, fps: int = 30) -> None:
    """Resample to target res/fps/duration with letterbox-crop."""
    if dst.exists():
        return
    src_dur = _ffprobe_duration(src)
    pts_mult = scene_dur / max(0.1, src_dur)
    vf = (f"setpts=PTS*{pts_mult:.4f},"
          f"scale={width}:{height}:force_original_aspect_ratio=increase,"
          f"crop={width}:{height},fps={fps}")
    _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(src), "-vf", vf,
         "-an", "-c:v", "libx264", "-pix_fmt", "yuv420p", "-r", str(fps),
         "-t", str(scene_dur), str(dst)])


def _render_narration(line: str, voice_spec: dict[str, Any],
                      out_wav: Path) -> bool:
    """Piper one line -> wav. Returns True if file produced."""
    if out_wav.exists():
        return True
    if not line or not line.strip():
        return False
    if not PIPER.exists() or not PIPER_MODEL.exists():
        print(f"[narrate] piper or model missing; skipping line", flush=True)
        return False
    attrs = (voice_spec or {}).get("attrs", {}) if voice_spec else {}
    length_scale = str(attrs.get("length", 1.10))
    speaker = str(attrs.get("speaker", 0))
    out_wav.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [str(PIPER), "-m", str(PIPER_MODEL), "-f", str(out_wav),
         "--speaker", speaker,
         "--length-scale", length_scale,
         "--noise-scale", "0.5",
         "--noise-w-scale", "0.7"],
        input=line, text=True, check=True,
    )
    return out_wav.exists()


# ---------------------------------------------------------------------------
# Lipsync (talking-head) overlay support
# ---------------------------------------------------------------------------

def _resolve_lipsync_backend(value: Any) -> str | None:
    """Normalize `narration_spec.lipsync` into 'lp' | 'wav2lip' | None."""
    if value in (None, False, ""):
        return None
    if value is True:
        return "lp"
    if isinstance(value, str):
        v = value.lower().strip()
        if v in ("lp", "liveportrait", "live-portrait", "true", "yes", "on"):
            return "lp"
        if v in ("wav2lip", "w2l"):
            return "wav2lip"
        # Unknown — caller will log + fall back to None.
    return None


def _lipsync_inputs_available(backend: str, driver_still: Path) -> bool:
    """Return True iff the avatar pipeline can actually run for this backend."""
    if not driver_still.exists():
        print(f"[lipsync] driver still missing: {driver_still} — skipping",
              flush=True)
        return False
    if not LP_INFERENCE.exists() or not LP_VENV_PYTHON.exists():
        print(f"[lipsync] LP inference or venv missing under {LP_DIR} — skipping",
              flush=True)
        return False
    if backend == "wav2lip" and not W2L_CKPT.exists():
        print(f"[lipsync] wav2lip checkpoint missing: {W2L_CKPT} — falling back to lp",
              flush=True)
    return True


def _render_lipsync_clip(audio_wav: Path, backend: str,
                         driver_still: Path, out_mp4: Path,
                         work_dir: Path) -> Path | None:
    """Drive the avatar pipeline. Returns mp4 path on success, None on failure.

    backend:
        - "lp"      → LivePortrait inference.py, source=driver_still,
                      driving=<a short driver clip>. We synthesize a driver clip
                      from the still by holding it for the audio duration, then
                      LP animates it. This keeps the entry-point contract:
                      (source image, driving clip, output dir).
        - "wav2lip" → LP output is then re-passed through Wav2Lip whole-face
                      mouth rewrite, aligned to audio_wav.

    NOTE: This is the integration scaffolding. The actual avatar pipeline
    runs are slow (minutes per clip); the runner is expected to skip them
    in test mode by setting STORY_FORGE_SKIP_AVATAR=1.
    """
    if os.environ.get("STORY_FORGE_SKIP_AVATAR") == "1":
        print("[lipsync] STORY_FORGE_SKIP_AVATAR=1 — placeholder mp4 used",
              flush=True)
        # Touch a tiny placeholder so callers can still overlay something.
        out_mp4.parent.mkdir(parents=True, exist_ok=True)
        try:
            _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
                 "-loop", "1", "-i", str(driver_still),
                 "-i", str(audio_wav),
                 "-shortest", "-c:v", "libx264", "-pix_fmt", "yuv420p",
                 "-r", "25", "-vf", "scale=512:512",
                 "-c:a", "aac", str(out_mp4)])
            return out_mp4
        except Exception as exc:
            print(f"[lipsync] placeholder build failed: {exc}", flush=True)
            return None

    if not _lipsync_inputs_available(backend, driver_still):
        return None

    work_dir.mkdir(parents=True, exist_ok=True)
    # 1. Build a held-still driver clip matching the audio length so LP has
    #    a driving video. Wav2Lip later rewrites the mouth region anyway.
    driver_clip = work_dir / "driver_clip.mp4"
    audio_dur = _ffprobe_duration(audio_wav)
    try:
        _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-loop", "1", "-i", str(driver_still),
             "-t", f"{audio_dur:.3f}", "-r", "25",
             "-vf", "scale=512:512:force_original_aspect_ratio=increase,crop=512:512",
             "-c:v", "libx264", "-pix_fmt", "yuv420p", str(driver_clip)])
    except subprocess.CalledProcessError as exc:
        print(f"[lipsync] driver clip build failed: {exc}", flush=True)
        return None

    # 2. LivePortrait pass.
    lp_out_dir = work_dir / "lp"
    lp_out_dir.mkdir(exist_ok=True)
    lp_cmd = [
        str(LP_VENV_PYTHON), "inference.py",
        "-s", str(driver_still),
        "-d", str(driver_clip),
        "-o", str(lp_out_dir),
        "--flag_use_half_precision",
        "--no-flag_do_torch_compile",
    ]
    env = {**os.environ, "PYTORCH_ENABLE_MPS_FALLBACK": "1"}
    try:
        subprocess.run(lp_cmd, cwd=LP_DIR, env=env, check=True)
    except subprocess.CalledProcessError as exc:
        print(f"[lipsync] LP inference failed: {exc}", flush=True)
        return None

    lp_candidates = [p for p in lp_out_dir.glob("*.mp4") if "_concat" not in p.name]
    if not lp_candidates:
        print("[lipsync] LP produced no mp4 — aborting overlay", flush=True)
        return None
    lp_video = max(lp_candidates, key=lambda p: p.stat().st_size)

    # 3. Optional Wav2Lip mouth pass.
    if backend == "wav2lip" and W2L_CKPT.exists():
        w2l_out = work_dir / "w2l.mp4"
        w2l_cmd = [
            str(LP_VENV_PYTHON), "inference.py",
            "--checkpoint_path", str(W2L_CKPT),
            "--face", str(lp_video),
            "--audio", str(audio_wav),
            "--outfile", str(w2l_out),
            "--resize_factor", "1",
            "--pads", "0", "5", "0", "0",
            "--nosmooth",
        ]
        try:
            subprocess.run(w2l_cmd, cwd=W2L_DIR, env=env, check=True)
            final_src = w2l_out
        except subprocess.CalledProcessError as exc:
            print(f"[lipsync] Wav2Lip failed, using LP-only: {exc}", flush=True)
            final_src = lp_video
    else:
        final_src = lp_video

    # 4. Mux narration audio onto the head clip so the overlay carries voice
    #    when composited downstream (the scene base track stays muted).
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    try:
        _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(final_src), "-i", str(audio_wav),
             "-map", "0:v", "-map", "1:a",
             "-c:v", "copy", "-c:a", "aac", "-b:a", "192k",
             "-shortest", str(out_mp4)])
    except subprocess.CalledProcessError as exc:
        print(f"[lipsync] mux failed: {exc}", flush=True)
        return None
    return out_mp4


def _overlay_lipsync_on_scene(scene_clip: Path, head_clip: Path,
                              out_mp4: Path) -> None:
    """Composite the head clip as a lower-third on the scene clip.

    Bottom-right corner, ~30% scene width, 32px inset, 50ms crossfade in.
    The scene clip is muted under the overlay's mouth track.
    """
    if out_mp4.exists():
        out_mp4.unlink()
    inset = LIPSYNC_OVERLAY_INSET
    fade = LIPSYNC_OVERLAY_FADE
    scale = LIPSYNC_OVERLAY_SCALE_W
    # [1:v] scaled to ~30% width, with crossfade-in alpha; placed bottom-right.
    fc = (f"[1:v]scale={scale}:-2,format=yuva420p,"
          f"fade=in:st=0:d={fade}:alpha=1[ov];"
          f"[0:v][ov]overlay=W-w-{inset}:H-h-{inset}:format=auto[outv]")
    _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         "-i", str(scene_clip), "-i", str(head_clip),
         "-filter_complex", fc,
         "-map", "[outv]",
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-preset", "medium", "-crf", "18",
         "-an", str(out_mp4)])


def _stitch(clips: list[Path], out_mp4: Path,
            xfade: float = 0.5, scene_dur: float = 5.0) -> None:
    """xfade-stitch the visual track (no audio) -> out_mp4."""
    if len(clips) == 1:
        shutil.copy2(clips[0], out_mp4)
        return
    inputs: list[str] = []
    for c in clips:
        inputs += ["-i", str(c)]
    fc = []
    last = "[0:v]"
    off = scene_dur - xfade
    for i in range(1, len(clips)):
        label = f"v{i}"
        fc.append(f"{last}[{i}:v]xfade=transition=fade:"
                  f"duration={xfade}:offset={off:.3f}[{label}]")
        last = f"[{label}]"
        off += scene_dur - xfade
    _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
         *inputs, "-filter_complex", ";".join(fc),
         "-map", last,
         "-c:v", "libx264", "-pix_fmt", "yuv420p",
         "-preset", "medium", "-crf", "18",
         "-r", "30", "-an", str(out_mp4)])


def _mux_narration(visuals: Path, vo_wav: Path | None, out: Path) -> None:
    """Mux visuals + (optional) narration to final mp4 with fade in/out."""
    visuals_dur = _ffprobe_duration(visuals)
    fade_out = max(0.1, visuals_dur - 1.0)

    if vo_wav and vo_wav.exists():
        _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(visuals), "-i", str(vo_wav),
             "-filter_complex",
             f"[0:v]fade=in:st=0:d=0.5,fade=out:st={fade_out}:d=1.0[v];"
             f"[1:a]volume=1.0,afade=in:st=0:d=0.3,"
             f"afade=out:st={fade_out}:d=1.0,apad[a]",
             "-map", "[v]", "-map", "[a]",
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-preset", "medium", "-crf", "18",
             "-c:a", "aac", "-b:a", "192k", "-shortest",
             "-movflags", "+faststart", str(out)])
    else:
        _sh(["ffmpeg", "-y", "-hide_banner", "-loglevel", "error",
             "-i", str(visuals),
             "-vf", f"fade=in:st=0:d=0.5,fade=out:st={fade_out}:d=1.0",
             "-c:v", "libx264", "-pix_fmt", "yuv420p",
             "-preset", "medium", "-crf", "18",
             "-movflags", "+faststart", str(out)])


def render_lean(plan: dict[str, Any],
                out_path: Path | None = None,
                scene_filter: list[str] | None = None,
                work_dir: Path | None = None) -> dict[str, Any]:
    """End-to-end render via per-scene render-route + ffmpeg stitch."""
    meta = plan["film_meta"]
    slug = meta.get("slug", "untitled")
    scene_dur = float(meta.get("scene_duration", 5.0))
    scenes_all = plan["scenes"]  # dict preserves insertion order

    # Filter scenes if requested
    if scene_filter:
        wanted = set(scene_filter)
        scenes = {k: v for k, v in scenes_all.items() if k in wanted}
        missing = wanted - set(scenes.keys())
        if missing:
            raise RuntimeError(f"scenes not in plan: {sorted(missing)}")
        if not scenes:
            raise RuntimeError("no scenes left after --scenes filter")
    else:
        scenes = scenes_all

    work_dir = work_dir or (_cfg.WORK_DIR / slug)
    work_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_path or (DEFAULT_OUT_DIR / f"{slug}.mp4")
    out_path.parent.mkdir(parents=True, exist_ok=True)

    voice_presets = plan.get("voice_presets", {})
    # First voice preset = default narrator
    default_voice = (next(iter(voice_presets.values()))
                     if voice_presets else None)

    t0 = time.time()
    enhanced_clips: list[Path] = []
    narration_pieces: list[tuple[int, Path]] = []  # (scene_index_1based, wav)

    driver_still_env = os.environ.get("LIPSYNC_DRIVER_STILL")
    driver_still = (Path(driver_still_env) if driver_still_env
                    else DEFAULT_DRIVER_STILL)

    for idx, (name, sc) in enumerate(scenes.items(), start=1):
        print(f"\n=== scene {idx}/{len(scenes)}: {name} ===", flush=True)
        still_spec = sc.get("still_spec") or {}
        motion_spec = sc.get("motion_spec") or {}
        narrate_spec = sc.get("narration_spec") or {}
        # Prefer the plural list; fall back to singular for back-compat plans.
        narrate_specs = sc.get("narration_specs") or (
            [narrate_spec] if narrate_spec else [])

        still_prompt = still_spec.get("prompt", "")
        motion_prompt = motion_spec.get("prompt", "")
        engine = (motion_spec.get("engine") or "auto").lower()
        duration = float(motion_spec.get("duration", scene_dur))
        still_seed = int(still_spec.get("seed") or (1000 + idx * 17))

        label = f"{slug}_{idx:02d}_{name}"
        still_png = work_dir / f"still_{idx:02d}.png"
        raw_mp4 = work_dir / f"raw_{idx:02d}.mp4"
        conformed = work_dir / f"clip_{idx:02d}.mp4"

        # 1. Still (skip if motion engine doesn't need one — but both Wan-i2v
        #    and LTX-i2v do, so always render).
        if still_prompt:
            _render_still(still_prompt, still_png, seed=still_seed)
        else:
            raise RuntimeError(f"scene {name}: still.prompt is required")

        # 2. Motion
        _render_motion(motion_prompt or still_prompt, still_png, raw_mp4,
                       engine=engine, duration=duration, label=label)

        # 3. Conform
        _conform_clip(raw_mp4, conformed, scene_dur=duration)

        # 4. Narration pieces + per-spec lipsync overlay (per scene, in order).
        scene_visual = conformed
        for n_i, n_spec in enumerate(narrate_specs):
            line = (n_spec or {}).get("line", "").strip()
            if not line:
                continue
            voice_name = n_spec.get("voice") or n_spec.get("engine")
            voice_spec = voice_presets.get(voice_name) or default_voice
            piece = (work_dir / "vo_pieces"
                     / f"p_{idx:02d}_{n_i:02d}.wav")
            if not _render_narration(line, voice_spec, piece):
                continue
            narration_pieces.append((idx, piece))

            backend = _resolve_lipsync_backend(n_spec.get("lipsync"))
            if not backend:
                continue
            head_dir = work_dir / "lipsync" / f"s{idx:02d}_n{n_i:02d}"
            head_mp4 = head_dir / "head.mp4"
            print(f"[lipsync] scene={name} narrate#{n_i} backend={backend}",
                  flush=True)
            head_clip = _render_lipsync_clip(
                piece, backend, driver_still, head_mp4, head_dir)
            if head_clip and head_clip.exists():
                overlaid = work_dir / f"clip_{idx:02d}_overlay.mp4"
                try:
                    _overlay_lipsync_on_scene(
                        scene_visual, head_clip, overlaid)
                    scene_visual = overlaid
                except subprocess.CalledProcessError as exc:
                    print(f"[lipsync] overlay failed for {name}: {exc}",
                          flush=True)
        enhanced_clips.append(scene_visual)

    # 5. Stitch visuals (use the first scene's duration as scene_dur for offsets;
    #    when scenes differ in length this is approximate but acceptable for MVP)
    visuals = work_dir / "visuals.mp4"
    if visuals.exists():
        visuals.unlink()
    _stitch(enhanced_clips, visuals,
            xfade=0.5,
            scene_dur=float(next(iter(scenes.values()))
                            .get("motion_spec", {}).get("duration", scene_dur)))

    # 6. Build narration track (adelay+amix, scene-synced) if we have any
    vo_wav: Path | None = None
    if narration_pieces:
        xfade = 0.5
        per_scene = float(next(iter(scenes.values()))
                          .get("motion_spec", {}).get("duration", scene_dur))
        scene_advance = per_scene - xfade
        total_audio_dur = (len(scenes) - 1) * scene_advance + per_scene
        args = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "warning"]
        fc_parts = []
        mix_labels = []
        for inp_i, (scene_i, piece) in enumerate(narration_pieces):
            args += ["-i", str(piece)]
            delay_ms = int((scene_i - 1) * scene_advance * 1000)
            fc_parts.append(f"[{inp_i}:a]adelay={delay_ms}|{delay_ms}"
                            f"[a{inp_i}]")
            mix_labels.append(f"[a{inp_i}]")
        fc = (";".join(fc_parts) + ";" + "".join(mix_labels)
              + f"amix=inputs={len(narration_pieces)}:"
                f"duration=longest:normalize=0,"
              + f"apad=whole_dur={total_audio_dur}[amixed]")
        vo_wav = work_dir / "vo.wav"
        args += ["-filter_complex", fc, "-map", "[amixed]",
                 "-t", str(total_audio_dur),
                 "-c:a", "pcm_s16le", str(vo_wav)]
        _sh(args)

    # 7. Final mux
    _mux_narration(visuals, vo_wav, out_path)

    elapsed = time.time() - t0
    return {
        "output": str(out_path),
        "scenes": len(scenes),
        "seconds": round(elapsed, 1),
        "narration_lines": len(narration_pieces),
        "work_dir": str(work_dir),
    }


# ---------------------------------------------------------------------------
# Top-level dispatch
# ---------------------------------------------------------------------------

def render(plan_path: Path, dry_run: bool = False,
           engine: str = "lean",
           out: Path | None = None,
           scenes: list[str] | None = None) -> dict[str, Any]:
    plan = json.loads(Path(plan_path).read_text())
    if dry_run:
        return storyplan_to_pipeline_config(plan)

    if engine == "full":
        cfg = storyplan_to_pipeline_config(plan)
        proc = subprocess.run(
            [sys.executable, str(PIPELINE)],
            input=json.dumps(cfg), text=True, check=True,
        )
        return {"returncode": proc.returncode, "engine": "full",
                "config": cfg}

    # default lean path
    result = render_lean(plan, out_path=out, scene_filter=scenes)
    result["engine"] = "lean"
    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("plan", help="path to .storyplan.json")
    ap.add_argument("--dry", action="store_true")
    ap.add_argument("--engine", choices=["lean", "full"], default="lean")
    ap.add_argument("--out", default=None,
                    help="output mp4 path (default: ~/AI/videopipe/outputs/<slug>.mp4)")
    ap.add_argument("--scenes", default=None,
                    help="comma-separated scene names to render (default: all)")
    args = ap.parse_args()
    scene_filter = ([s.strip() for s in args.scenes.split(",") if s.strip()]
                    if args.scenes else None)
    out = Path(args.out) if args.out else None
    res = render(Path(args.plan), dry_run=args.dry, engine=args.engine,
                 out=out, scenes=scene_filter)
    print(json.dumps(res, indent=2, default=str))

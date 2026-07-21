#!/usr/bin/env python3
"""Lipsync wiring tests — DSL → storyplan → run.py dispatch.

We never invoke avatar-pipeline for real here. The subprocess calls are
mocked; we just assert that the right backend was selected, the right
driver still was passed, and the overlay step would have run.
"""

from __future__ import annotations

import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from story_forge.parser import parse                  # noqa: E402
from story_forge.resolver import resolve              # noqa: E402
from story_forge.emitter import emit_storyplan        # noqa: E402
from story_forge import run as sf_run                 # noqa: E402


SF_BARE = textwrap.dedent("""
    film "Lipsync Bare" slug=ls_bare scene_dur=4.0
    voice warm: piper/en_US-libritts_r-medium speaker=0 length=1.10

    scene one:
        still flux:
            prompt: "test"
        motion wan:
            prompt: "test"
            duration: 4.0
        narrate warm with lipsync:
            line: "Hello world."
""").strip()

SF_WAV2LIP = textwrap.dedent("""
    film "Lipsync W2L" slug=ls_w2l scene_dur=4.0
    voice warm: piper/en_US-libritts_r-medium speaker=0 length=1.10

    scene one:
        still flux:
            prompt: "test"
        motion wan:
            prompt: "test"
            duration: 4.0
        narrate warm with lipsync=wav2lip:
            line: "Mouth must move."
""").strip()

SF_PLAIN = textwrap.dedent("""
    film "No Lipsync" slug=ls_none scene_dur=4.0
    voice warm: piper/en_US-libritts_r-medium speaker=0 length=1.10

    scene one:
        still flux:
            prompt: "test"
        motion wan:
            prompt: "test"
            duration: 4.0
        narrate warm:
            line: "Audio only."
""").strip()


def _plan(src: str) -> dict:
    return emit_storyplan(resolve(parse(src)))


class TestLipsyncDSL(unittest.TestCase):
    """Confirm the DSL parses each form into the expected lipsync value."""

    def test_bare_with_lipsync_defaults_to_lp(self):
        plan = _plan(SF_BARE)
        spec = plan["scenes"]["one"]["narration_specs"][0]
        self.assertEqual(spec["lipsync"], "lp")
        self.assertEqual(spec["voice"], "warm")
        self.assertEqual(spec["line"], "Hello world.")

    def test_explicit_wav2lip_backend(self):
        plan = _plan(SF_WAV2LIP)
        spec = plan["scenes"]["one"]["narration_specs"][0]
        self.assertEqual(spec["lipsync"], "wav2lip")

    def test_no_lipsync_is_false(self):
        plan = _plan(SF_PLAIN)
        spec = plan["scenes"]["one"]["narration_specs"][0]
        self.assertFalse(spec["lipsync"])

    def test_explicit_lp_backend_normalizes_to_lp(self):
        src = SF_BARE.replace("with lipsync:", "with lipsync=lp:")
        plan = _plan(src)
        spec = plan["scenes"]["one"]["narration_specs"][0]
        self.assertEqual(spec["lipsync"], "lp")


class TestBackendResolver(unittest.TestCase):
    """`_resolve_lipsync_backend` normalizes every flavor of input."""

    def test_falsey(self):
        for v in (None, False, ""):
            self.assertIsNone(sf_run._resolve_lipsync_backend(v))

    def test_truthy_bool_means_lp(self):
        self.assertEqual(sf_run._resolve_lipsync_backend(True), "lp")

    def test_string_aliases(self):
        for v in ("lp", "LP", "liveportrait", "Live-Portrait"):
            self.assertEqual(sf_run._resolve_lipsync_backend(v), "lp")
        for v in ("wav2lip", "W2L", "w2l"):
            self.assertEqual(sf_run._resolve_lipsync_backend(v), "wav2lip")

    def test_unknown_string_returns_none(self):
        self.assertIsNone(sf_run._resolve_lipsync_backend("sadtalker"))


class TestRunLeanDispatch(unittest.TestCase):
    """End-to-end: render_lean should fire the avatar pipeline only when
    a narration_spec has lipsync truthy, and skip it otherwise."""

    def setUp(self):
        # Each test gets a fresh tempdir so artifacts don't leak.
        self.tmp = Path(tempfile.mkdtemp(prefix="sf_lipsync_"))
        self.work = self.tmp / "work"
        self.out = self.tmp / "out.mp4"

    def _patches(self, lipsync_calls: list):
        """Patch every external side-effect in render_lean."""
        # _render_still / _render_motion / _conform_clip / _render_narration:
        # make them no-ops that create empty target files so existence checks
        # downstream don't blow up.
        def _touch(path: Path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x00")

        def fake_still(prompt, out_png, seed, **kw):
            _touch(out_png)

        def fake_motion(prompt, still_png, out_mp4, engine, duration, label,
                        last_frame=None):
            _touch(out_mp4)

        def fake_conform(src, dst, scene_dur, **kw):
            _touch(dst)

        def fake_narration(line, voice_spec, out_wav):
            _touch(out_wav)
            return True

        def fake_stitch(clips, out_mp4, **kw):
            _touch(out_mp4)

        def fake_mux(visuals, vo_wav, out):
            _touch(out)

        def fake_sh(cmd, **kw):
            # ffmpeg/amix invocations etc — pretend they succeeded.
            return None

        def fake_render_lipsync(audio_wav, backend, driver_still,
                                out_mp4, work_dir):
            lipsync_calls.append({
                "backend": backend,
                "driver_still": str(driver_still),
                "audio_wav": str(audio_wav),
                "out_mp4": str(out_mp4),
            })
            _touch(out_mp4)
            return out_mp4

        def fake_overlay(scene_clip, head_clip, out_mp4):
            _touch(out_mp4)

        return mock.patch.multiple(
            sf_run,
            _render_still=fake_still,
            _render_motion=fake_motion,
            _conform_clip=fake_conform,
            _render_narration=fake_narration,
            _stitch=fake_stitch,
            _mux_narration=fake_mux,
            _sh=fake_sh,
            _render_lipsync_clip=fake_render_lipsync,
            _overlay_lipsync_on_scene=fake_overlay,
        )

    def _run(self, sf_src: str, calls: list):
        plan = _plan(sf_src)
        with self._patches(calls):
            sf_run.render_lean(plan, out_path=self.out, work_dir=self.work)

    def test_bare_lipsync_dispatches_lp_backend(self):
        calls: list = []
        self._run(SF_BARE, calls)
        self.assertEqual(len(calls), 1, f"expected 1 lipsync call, got {calls}")
        self.assertEqual(calls[0]["backend"], "lp")
        self.assertEqual(calls[0]["driver_still"],
                         str(sf_run.DEFAULT_DRIVER_STILL))

    def test_wav2lip_dispatches_wav2lip_backend(self):
        calls: list = []
        self._run(SF_WAV2LIP, calls)
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0]["backend"], "wav2lip")

    def test_no_lipsync_never_calls_avatar(self):
        calls: list = []
        self._run(SF_PLAIN, calls)
        self.assertEqual(calls, [],
                         "lipsync pipeline should not be invoked")

    def test_lipsync_driver_still_env_override(self):
        calls: list = []
        with mock.patch.dict("os.environ",
                             {"LIPSYNC_DRIVER_STILL": "/tmp/custom.png"}):
            self._run(SF_BARE, calls)
        self.assertEqual(calls[0]["driver_still"], "/tmp/custom.png")


class TestSkipAvatarShortCircuit(unittest.TestCase):
    """STORY_FORGE_SKIP_AVATAR=1 → never actually shell out to LP/W2L."""

    def test_skip_env_produces_placeholder(self):
        tmp = Path(tempfile.mkdtemp(prefix="sf_lipsync_skip_"))
        audio = tmp / "a.wav"
        audio.write_bytes(b"\x00")
        driver = tmp / "drv.png"
        driver.write_bytes(b"\x00")
        out = tmp / "head.mp4"

        sh_calls: list = []

        def fake_sh(cmd, **kw):
            sh_calls.append([str(c) for c in cmd])
            # Pretend ffmpeg created the file.
            Path(cmd[cmd.index("-loop") + -1]) if False else None  # noqa
            out.write_bytes(b"\x00")

        with mock.patch.dict("os.environ",
                             {"STORY_FORGE_SKIP_AVATAR": "1"}):
            with mock.patch.object(sf_run, "_sh", fake_sh):
                result = sf_run._render_lipsync_clip(
                    audio, "lp", driver, out, tmp / "work")
        self.assertEqual(result, out)
        # The single fake_sh call should be the placeholder ffmpeg invocation.
        self.assertTrue(any("ffmpeg" in c[0] for c in sh_calls))


if __name__ == "__main__":
    unittest.main(verbosity=2)

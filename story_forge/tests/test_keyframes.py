"""FFLF keyframe wiring — DSL → storyplan → run.py → render-route.

The premise, from a conversation with foxdit on r/StableDiffusion: a shot that
is conditioned only on its first frame is free to drift, and by the end of a
clip the character can be someone else. Anchoring the last frame too gives the
model a reference it has to land on.

These tests check the wiring, not the pixels: that an `end_prompt` produces a
second still, that it reaches the renderer as `last_frame`, and that scenes
without one behave exactly as they did before.
"""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest import mock

from story_forge import run as sf_run
from story_forge.emitter import emit_storyplan
from story_forge.parser import parse
from story_forge.resolver import resolve

SF_FFLF = '''
film "FFLF" slug=fflf scene_dur=3.0

scene ridge:
    still flux:
        prompt: "a lone hiker on a ridge at sunset"
        end_prompt: "the same hiker further along the ridge, sun lower"
        seed: 42
    motion ltx:
        prompt: "the hiker walks steadily along the ridge"
        duration: 3.0
'''

SF_PLAIN = '''
film "Plain" slug=plain scene_dur=3.0

scene ridge:
    still flux:
        prompt: "a lone hiker on a ridge at sunset"
        seed: 42
    motion ltx:
        prompt: "the hiker walks steadily along the ridge"
        duration: 3.0
'''


def _plan(src: str) -> dict:
    return emit_storyplan(resolve(parse(src)))


class TestKeyframeWiring(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.work = Path(self.tmp.name) / "work"
        self.out = Path(self.tmp.name) / "out.mp4"

    def tearDown(self):
        self.tmp.cleanup()

    def _run(self, src: str) -> tuple[list, list]:
        stills, motions = [], []

        def _touch(path: Path):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"\x00")

        def fake_still(prompt, out_png, seed, **kw):
            stills.append({"prompt": prompt, "out": Path(out_png), "seed": seed})
            _touch(Path(out_png))

        def fake_motion(prompt, still_png, out_mp4, engine, duration, label,
                        last_frame=None):
            motions.append({"still": Path(still_png), "last_frame": last_frame})
            _touch(Path(out_mp4))

        def fake_conform(src_, dst, scene_dur, **kw):
            _touch(Path(dst))

        def fake_stitch(clips, out_mp4, **kw):
            _touch(Path(out_mp4))

        def fake_narration(line, voice_spec, out_wav):
            _touch(Path(out_wav))
            return True

        def fake_mux(visuals, vo_wav, out):
            _touch(Path(out))

        with mock.patch.multiple(
            sf_run,
            _render_still=fake_still,
            _render_motion=fake_motion,
            _conform_clip=fake_conform,
            _stitch=fake_stitch,
            _render_narration=fake_narration,
            _mux_narration=fake_mux,
            _sh=lambda cmd, **kw: None,
        ):
            sf_run.render_lean(_plan(src), out_path=self.out, work_dir=self.work)
        return stills, motions

    def test_end_prompt_renders_a_second_still(self):
        stills, _ = self._run(SF_FFLF)
        self.assertEqual(len(stills), 2, "expected an opening and an end still")
        self.assertTrue(stills[1]["out"].name.endswith("_end.png"))

    def test_end_still_reuses_the_opening_seed(self):
        """Same seed means the same look, not a second character that merely
        matches the words."""
        stills, _ = self._run(SF_FFLF)
        self.assertEqual(stills[0]["seed"], stills[1]["seed"])

    def test_end_still_is_passed_as_last_frame(self):
        stills, motions = self._run(SF_FFLF)
        self.assertEqual(len(motions), 1)
        self.assertEqual(motions[0]["last_frame"], stills[1]["out"])

    def test_plain_scene_passes_no_last_frame(self):
        stills, motions = self._run(SF_PLAIN)
        self.assertEqual(len(stills), 1)
        self.assertIsNone(motions[0]["last_frame"])

    def test_end_path_uses_an_existing_image(self):
        existing = Path(self.tmp.name) / "hero_ref.png"
        existing.write_bytes(b"\x00")
        src = SF_PLAIN.replace(
            '        seed: 42',
            f'        end_path: "{existing}"\n        seed: 42')
        stills, motions = self._run(src)
        self.assertEqual(len(stills), 1, "end_path should not render a still")
        self.assertEqual(motions[0]["last_frame"], existing)

    def test_missing_end_path_fails_loudly(self):
        src = SF_PLAIN.replace(
            '        seed: 42',
            '        end_path: "/nope/not/here.png"\n        seed: 42')
        with self.assertRaises(RuntimeError) as ctx:
            self._run(src)
        self.assertIn("end_path", str(ctx.exception))


if __name__ == "__main__":
    unittest.main()

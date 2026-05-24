#!/usr/bin/env python3
"""Smoke test: cabin_open.sf parses + resolves + emits to a valid storyplan dict."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from story_forge.parser import parse                  # noqa: E402
from story_forge.resolver import resolve              # noqa: E402
from story_forge.emitter import emit_storyplan        # noqa: E402

EXAMPLE = (Path(__file__).resolve().parents[1]
           / "examples" / "cabin_open.sf")


class TestStoryForgeMVP(unittest.TestCase):

    def setUp(self) -> None:
        self.ast = parse(EXAMPLE)
        self.resolved = resolve(self.ast)
        self.plan = emit_storyplan(self.resolved)

    def test_ast_has_film_node(self):
        film_nodes = [n for n in self.ast if n["type"] == "film"]
        self.assertEqual(len(film_nodes), 1)
        self.assertEqual(film_nodes[0]["title"], "Cabin Open")

    def test_vars_captured(self):
        self.assertIn("style", self.resolved["vars"])
        self.assertIn("child", self.resolved["vars"])
        self.assertIn("cabin", self.resolved["vars"])

    def test_three_scenes(self):
        scenes = self.plan["scenes"]
        self.assertEqual(len(scenes), 3)
        self.assertIn("snow_walk", scenes)
        self.assertIn("cabin_glow", scenes)
        self.assertIn("fireside", scenes)

    def test_each_scene_has_still_motion_narration(self):
        for name, sc in self.plan["scenes"].items():
            self.assertIsNotNone(sc["still_spec"], f"{name} missing still")
            self.assertIsNotNone(sc["motion_spec"], f"{name} missing motion")
            self.assertIsNotNone(sc["narration_spec"],
                                 f"{name} missing narration")

    def test_variable_interpolation(self):
        prompt = self.plan["scenes"]["snow_walk"]["still_spec"]["prompt"]
        self.assertIn("Studio Ghibli watercolor", prompt)
        self.assertIn("a small child in a red hooded cloak", prompt)
        self.assertNotIn("{$", prompt)

    def test_deterministic_seeds(self):
        s1 = self.plan["scenes"]["snow_walk"]["still_spec"]["seed"]
        s2 = self.plan["scenes"]["cabin_glow"]["still_spec"]["seed"]
        # Both must be ints in the 32-bit unsigned range and distinct per scene.
        self.assertIsInstance(s1, int)
        self.assertIsInstance(s2, int)
        self.assertNotEqual(s1, s2)
        # Re-emit and confirm reproducibility.
        again = emit_storyplan(resolve(parse(EXAMPLE)))
        self.assertEqual(
            again["scenes"]["snow_walk"]["still_spec"]["seed"], s1)

    def test_voice_preset_defined(self):
        vp = self.plan["voice_presets"]
        self.assertIn("warm", vp)
        self.assertTrue(vp["warm"]["value"].startswith("piper/"))

    def test_music_preset_and_per_scene_ref(self):
        self.assertIn("wintry", self.plan["music_presets"])
        music = self.plan["scenes"]["snow_walk"]["music_spec"]
        self.assertEqual(music["preset"], "wintry")
        self.assertAlmostEqual(music["attrs"]["vol"], 0.30, places=3)

    def test_directives_captured(self):
        t_names = [t["name"] for t in self.plan["transitions"]]
        self.assertIn("xfade", t_names)
        self.assertEqual(len(self.plan["mixes"]), 1)
        self.assertEqual(self.plan["mixes"][0]["args"][0], "duck")

    def test_film_meta(self):
        meta = self.plan["film_meta"]
        self.assertEqual(meta["slug"], "cabin_open")
        self.assertEqual(meta["target"], "m5+mini")
        self.assertAlmostEqual(meta["scene_duration"], 8.5, places=3)

    # ------------------------------------------------------------------
    # Multi-voice routing
    # ------------------------------------------------------------------

    def test_multi_voice_presets_defined(self):
        """All three top-level voice presets should be registered."""
        vp = self.plan["voice_presets"]
        self.assertIn("warm", vp)
        self.assertIn("gravel", vp)
        self.assertIn("child", vp)
        # gravel uses speaker=14, child uses length=1.30
        self.assertEqual(vp["gravel"]["attrs"]["speaker"], 14)
        self.assertAlmostEqual(vp["child"]["attrs"]["length"], 1.30, places=3)

    def test_multi_voice_per_scene_narration_specs(self):
        """cabin_glow has two narrate blocks: warm then child."""
        scene = self.plan["scenes"]["cabin_glow"]
        specs = scene["narration_specs"]
        self.assertEqual(len(specs), 2)
        self.assertEqual(specs[0]["voice"], "warm")
        self.assertEqual(specs[1]["voice"], "child")
        self.assertIn("kettle", specs[0]["line"])
        self.assertEqual(specs[1]["line"], "Mama? Are you home?")
        # Back-compat: singular narration_spec == first entry.
        self.assertEqual(scene["narration_spec"]["voice"], "warm")
        # Each line has its own deterministic seed.
        self.assertNotEqual(specs[0]["seed"], specs[1]["seed"])

    # ------------------------------------------------------------------
    # SFX library
    # ------------------------------------------------------------------

    def test_sfx_presets_defined(self):
        """Top-level sfx blocks should populate sfx_presets with engine + attrs."""
        sp = self.plan["sfx_presets"]
        self.assertIn("fire_crackle", sp)
        self.assertIn("wind_low", sp)
        self.assertEqual(sp["fire_crackle"]["value"], "ace/sfx")
        self.assertEqual(sp["fire_crackle"]["attrs"]["duration"], 8)
        self.assertEqual(
            sp["fire_crackle"]["attrs"]["prompt"],
            "fire crackling, warm hearth")
        self.assertAlmostEqual(sp["wind_low"]["attrs"]["vol"], 0.20, places=3)

    def test_sfx_per_scene_refs_with_offset(self):
        """Scene-level `sfx <name> at=N.N` lands in sfx_specs with merged attrs."""
        fireside = self.plan["scenes"]["fireside"]
        sfx_specs = fireside["sfx_specs"]
        self.assertEqual(len(sfx_specs), 1)
        self.assertEqual(sfx_specs[0]["preset"], "fire_crackle")
        self.assertEqual(sfx_specs[0]["value"], "ace/sfx")
        # Preset attrs (prompt/duration/vol) and ref attrs (at) merge.
        self.assertEqual(sfx_specs[0]["attrs"]["duration"], 8)
        self.assertAlmostEqual(sfx_specs[0]["attrs"]["at"], 2.0, places=3)
        # snow_walk has wind_low at=0.0
        snow = self.plan["scenes"]["snow_walk"]
        self.assertEqual(len(snow["sfx_specs"]), 1)
        self.assertEqual(snow["sfx_specs"][0]["preset"], "wind_low")
        self.assertAlmostEqual(snow["sfx_specs"][0]["attrs"]["at"], 0.0, places=3)

    # ------------------------------------------------------------------
    # Lip sync
    # ------------------------------------------------------------------

    def test_lipsync_flag_set_on_fireside_narration(self):
        """`narrate warm with lipsync:` flips narration_spec.lipsync = True."""
        fireside = self.plan["scenes"]["fireside"]
        spec = fireside["narration_specs"][0]
        self.assertTrue(spec["lipsync"])
        self.assertEqual(spec["voice"], "warm")
        # Sanity: the spoken line passes through.
        self.assertIn("cold outside", spec["line"])

    def test_lipsync_default_false_elsewhere(self):
        """Narration blocks without `with lipsync` default to lipsync=False."""
        snow_specs = self.plan["scenes"]["snow_walk"]["narration_specs"]
        glow_specs = self.plan["scenes"]["cabin_glow"]["narration_specs"]
        self.assertEqual(len(snow_specs), 1)
        self.assertFalse(snow_specs[0]["lipsync"])
        # Both narrates in cabin_glow are plain (no lipsync).
        for s in glow_specs:
            self.assertFalse(s["lipsync"])


if __name__ == "__main__":
    unittest.main(verbosity=2)

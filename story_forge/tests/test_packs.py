#!/usr/bin/env python3
"""Tests for style/format packs and their expansion into the storyplan."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from story_forge import packs                          # noqa: E402
from story_forge.parser import parse                   # noqa: E402
from story_forge.resolver import resolve               # noqa: E402
from story_forge.emitter import emit_storyplan         # noqa: E402


def _plan(sf_text: str) -> dict:
    return emit_storyplan(resolve(parse(sf_text)))


class TestPackLookups(unittest.TestCase):

    def test_known_style(self):
        s = packs.get_style("pixar-3d")
        self.assertEqual(s["name"], "pixar-3d")
        self.assertTrue(s["still_suffix"])

    def test_known_format(self):
        f = packs.get_format("reel")
        self.assertEqual((f["width"], f["height"]), (720, 1280))

    def test_falsy_returns_none(self):
        self.assertIsNone(packs.get_style(None))
        self.assertIsNone(packs.get_format(""))

    def test_case_insensitive(self):
        self.assertEqual(packs.get_style("PIXAR-3D")["name"], "pixar-3d")

    def test_unknown_style_raises(self):
        with self.assertRaises(packs.PackError):
            packs.get_style("does-not-exist")

    def test_unknown_format_raises(self):
        with self.assertRaises(packs.PackError):
            packs.get_format("imax")

    def test_listings_nonempty(self):
        self.assertTrue(packs.list_styles())
        self.assertTrue(packs.list_formats())


class TestPackExpansionInPlan(unittest.TestCase):

    SF_STYLED = (
        'film "S" slug=s style=pixar-3d format=reel\n'
        "scene a:\n"
        "    still flux:\n"
        '        prompt: "x"\n'
        "    motion ltx:\n"
        '        prompt: "y"\n'
    )

    def test_format_sets_dims(self):
        fm = _plan(self.SF_STYLED)["film_meta"]
        self.assertEqual((fm["width"], fm["height"]), (720, 1280))
        self.assertEqual(fm["fps"], 30)
        self.assertEqual(fm["aspect"], "9:16")

    def test_style_pack_attached(self):
        fm = _plan(self.SF_STYLED)["film_meta"]
        self.assertEqual(fm["style"], "pixar-3d")
        self.assertIn("still_suffix", fm["style_pack"])

    def test_format_supplies_default_scene_dur(self):
        fm = _plan(self.SF_STYLED)["film_meta"]
        self.assertEqual(fm["scene_duration"], 5.0)  # reel default

    def test_explicit_scene_dur_wins(self):
        sf = ('film "S" slug=s format=reel scene_dur=9.0\n'
              "scene a:\n    still flux:\n        prompt: \"x\"\n"
              "    motion ltx:\n        prompt: \"y\"\n")
        self.assertEqual(_plan(sf)["film_meta"]["scene_duration"], 9.0)

    def test_no_packs_is_unchanged(self):
        sf = ('film "Plain" slug=plain scene_dur=3.0\n'
              "scene a:\n    still flux:\n        prompt: \"x\"\n"
              "    motion ltx:\n        prompt: \"y\"\n")
        fm = _plan(sf)["film_meta"]
        self.assertNotIn("width", fm)
        self.assertNotIn("style_pack", fm)
        self.assertEqual(fm["scene_duration"], 3.0)


class CompanionTests(unittest.TestCase):
    """2026-11-02: a 16:9 format delivers its 9:16 as a separate composition."""

    def test_promo_has_a_vertical_companion(self):
        comp = packs.companions("promo")
        self.assertEqual([c["name"] for c in comp], ["promo-vertical"])
        v = comp[0]
        self.assertTrue(v["vertical"])
        self.assertEqual((v["width"], v["height"]), (1080, 1920))
        x0, y0, x1, y1 = v["safe"]
        self.assertTrue(0 < x0 < x1 < 1 and 0 < y0 < y1 < 1)

    def test_vertical_has_no_companion(self):
        self.assertEqual(packs.companions("reel"), [])


if __name__ == "__main__":
    unittest.main()

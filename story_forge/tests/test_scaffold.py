#!/usr/bin/env python3
"""Tests for the `story-new` project scaffold CLI."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from story_forge.parser import parse                   # noqa: E402
from story_forge.resolver import resolve               # noqa: E402
from story_forge.emitter import emit_storyplan         # noqa: E402

# Load bin/story-new (no .py extension) as a module via an explicit loader,
# since spec_from_file_location can't infer one for an extensionless file.
_LOADER = importlib.machinery.SourceFileLoader(
    "story_new", str(REPO / "bin" / "story-new"))
_SPEC = importlib.util.spec_from_loader("story_new", _LOADER)
story_new = importlib.util.module_from_spec(_SPEC)
_LOADER.exec_module(story_new)


class TestSlugify(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(story_new.slugify("My Short Film"), "my_short_film")

    def test_punctuation_collapsed(self):
        self.assertEqual(story_new.slugify("Hank & Doug: Ep 2!"), "hank_doug_ep_2")

    def test_empty_falls_back(self):
        self.assertEqual(story_new.slugify("!!!"), "untitled")


class TestScaffold(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.parent = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def _make(self, *args):
        return story_new.main(["--dir", str(self.parent), "--force", *args])

    def test_creates_structure(self):
        rc = self._make("Test Show", "--style", "pixar-3d", "--format", "reel")
        self.assertEqual(rc, 0)
        proj = self.parent / "test_show"
        self.assertTrue((proj / "test_show.sf").is_file())
        self.assertTrue((proj / "README.md").is_file())
        self.assertTrue((proj / "stills").is_dir())
        self.assertTrue((proj / "voices").is_dir())

    def test_generated_sf_compiles_with_packs(self):
        self._make("Styled One", "--style", "anime", "--format", "square", "--scenes", "2")
        sf = (self.parent / "styled_one" / "styled_one.sf").read_text()
        fm = emit_storyplan(resolve(parse(sf)))["film_meta"]
        self.assertEqual(fm["style"], "anime")
        self.assertEqual((fm["width"], fm["height"]), (1080, 1080))

    def test_default_no_packs_compiles(self):
        self._make("Plain Show", "--scenes", "1")
        sf = (self.parent / "plain_show" / "plain_show.sf").read_text()
        plan = emit_storyplan(resolve(parse(sf)))
        self.assertEqual(len(plan["scenes"]), 1)
        self.assertNotIn("width", plan["film_meta"])

    def test_invalid_style_returns_error(self):
        rc = self._make("Bad", "--style", "not-a-style")
        self.assertEqual(rc, 2)

    def test_existing_without_force_fails(self):
        story_new.main(["--dir", str(self.parent), "Dup Show"])
        rc = story_new.main(["--dir", str(self.parent), "Dup Show"])  # no --force
        self.assertEqual(rc, 1)


if __name__ == "__main__":
    unittest.main()

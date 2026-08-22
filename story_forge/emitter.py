#!/usr/bin/env python3
"""Story Forge emitter — resolved IR -> .storyplan.json shape."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from . import packs


SCHEMA_VERSION = "0.1"


def emit_storyplan(resolved: dict[str, Any]) -> dict[str, Any]:
    """Convert the resolver output into the canonical .storyplan.json dict."""
    film = resolved["film"]
    attrs = film.get("attrs", {})

    plan: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "film_meta": {
            "title": film.get("title", "Untitled"),
            "slug": attrs.get("slug", "untitled"),
            "target": attrs.get("target", "m5"),
            "scene_duration": float(attrs.get("scene_dur", 8.5)),
            "extras": {k: v for k, v in attrs.items()
                       if k not in ("slug", "target", "scene_dur")},
        },
        "voice_presets": resolved.get("voice_presets", {}),
        "music_presets": resolved.get("music_presets", {}),
        "sfx_presets": resolved.get("sfx_presets", {}),
        "transitions": resolved.get("transitions", []),
        "mixes": resolved.get("mixes", []),
        "vars": resolved.get("vars", {}),
        "scenes": {},
    }

    for s in resolved.get("scenes", []):
        plan["scenes"][s["name"]] = {
            "still_spec": s.get("still"),
            "motion_spec": s.get("motion"),
            # Back-compat: singular narration_spec is the first narrate block
            # (or None if the scene has no narration). All narrate blocks live
            # in the plural narration_specs list, in declaration order.
            "narration_spec": s.get("narrate"),
            "narration_specs": s.get("narrates", []),
            "music_spec": s.get("music"),
            "sfx_specs": s.get("sfx", []),
            "attrs": s.get("attrs", {}),
            "extras": s.get("extras", {}),
        }

    # Expand style/format packs into concrete film_meta fields. The .sf always
    # wins on scene duration, so only let a format default fill it in when the
    # script didn't set scene_dur itself.
    packs.apply_packs(plan["film_meta"],
                      explicit_scene_dur=("scene_dur" in attrs))

    return plan


def write_storyplan(plan: dict[str, Any], out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.write_text(json.dumps(plan, indent=2, default=str))
    return out_path

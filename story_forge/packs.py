#!/usr/bin/env python3
"""Story Forge style & format packs — one shared source of truth.

This is how Story Forge does "any style, any format" without bolting on a new
model or a new dependency. It builds off what already works:

  * A STYLE pack rides on the existing Flux still prompt. It contributes a
    `still_suffix` (appended to every Flux still prompt) and a `negative` hint.
    No new model, no new code path — just better prompts, consistently applied.

  * A FORMAT pack rides on the existing film_meta dimensions. It sets width /
    height / fps / aspect and a default scene duration. The lean renderer
    already conforms every clip to a target size; the format pack just tells it
    which size.

The emitter, the `story-new` scaffold CLI, the web UI dropdowns, and the tests
all import THIS module so a new look or shape is added in exactly one place.

Design rule (the ethos): perfect what works and extend from it. Styles/formats
are declared as plain `film` attrs we already parse:

    film "My Short" slug=my_short style=pixar-3d format=reel

When neither attr is present, behavior is byte-for-byte identical to before —
prompts pass through untouched and the renderer keeps its historic defaults.
"""

from __future__ import annotations

from typing import Any

# ---------------------------------------------------------------------------
# Style packs — the LOOK (Flux still prompt suffix + negative hint)
# ---------------------------------------------------------------------------
# Keep names hyphenated and dot-free so the DSL coercer keeps them as strings.

STYLE_PACKS: dict[str, dict[str, str]] = {
    "pixar-3d": {
        "label": "Pixar-style 3D",
        "still_suffix": (
            "Pixar-style 3D animated film still, soft cinematic key lighting, "
            "subsurface skin scattering, expressive stylized characters, "
            "shallow depth of field, warm color grade, highly detailed"
        ),
        "negative": "live-action, real photograph, text, watermark, lowres",
    },
    "flat-2d": {
        "label": "Flat 2D cartoon",
        "still_suffix": (
            "flat 2D cartoon illustration, bold clean line art, cel shading, "
            "vibrant flat colors, simple confident shapes, storybook composition"
        ),
        "negative": "3D render, photoreal, gradient banding, text, watermark",
    },
    "photoreal": {
        "label": "Photoreal cinematic",
        "still_suffix": (
            "photorealistic cinematic film still, natural motivated lighting, "
            "subtle film grain, 35mm look, high dynamic range, detailed textures"
        ),
        "negative": "cartoon, illustration, cgi look, text, watermark",
    },
    "watercolor": {
        "label": "Watercolor storybook",
        "still_suffix": (
            "soft watercolor storybook illustration, painterly washes, "
            "gentle paper texture, muted pastel palette, hand-painted edges"
        ),
        "negative": "3D render, photoreal, hard vector edges, text, watermark",
    },
    "anime": {
        "label": "Anime key visual",
        "still_suffix": (
            "anime style key visual, crisp cel shading, expressive eyes, "
            "detailed painted backgrounds, vivid saturated colors"
        ),
        "negative": "photoreal, 3D render, western cartoon, text, watermark",
    },
    "claymation": {
        "label": "Claymation / stop-motion",
        "still_suffix": (
            "claymation stop-motion still, handmade plasticine characters, "
            "subtle fingerprint texture, miniature practical set, soft studio light"
        ),
        "negative": "2D drawing, photoreal, smooth slick cgi, text, watermark",
    },
    "noir": {
        "label": "Black-and-white noir",
        "still_suffix": (
            "high-contrast black and white film noir still, hard chiaroscuro "
            "lighting, deep shadows, venetian-blind light, 1940s cinematic mood"
        ),
        "negative": "color, flat lighting, cartoon, text, watermark",
    },
}

# ---------------------------------------------------------------------------
# Format packs — the SHAPE (dimensions + fps + default scene duration)
# ---------------------------------------------------------------------------

FORMAT_PACKS: dict[str, dict[str, Any]] = {
    "film": {
        "label": "16:9 film", "width": 1280, "height": 720,
        "fps": 30, "aspect": "16:9", "scene_dur": 5.0,
    },
    "reel": {
        "label": "9:16 vertical reel", "width": 720, "height": 1280,
        "fps": 30, "aspect": "9:16", "scene_dur": 5.0,
    },
    "square": {
        "label": "1:1 square", "width": 1080, "height": 1080,
        "fps": 30, "aspect": "1:1", "scene_dur": 5.0,
    },
    "narrated-doc": {
        "label": "16:9 narrated documentary", "width": 1280, "height": 720,
        "fps": 30, "aspect": "16:9", "scene_dur": 8.0,
    },
    "cinematic": {
        "label": "2.39:1 widescreen", "width": 1280, "height": 536,
        "fps": 24, "aspect": "2.39:1", "scene_dur": 6.0,
    },
}

DEFAULT_FORMAT = "film"   # only applied when a film explicitly asks for a format


class PackError(Exception):
    """Raised when a .sf names a style/format pack that doesn't exist."""


# ---------------------------------------------------------------------------
# Lookups
# ---------------------------------------------------------------------------

def _normalize(name: Any) -> str | None:
    if name in (None, "", False):
        return None
    return str(name).strip().lower()


def get_style(name: Any) -> dict[str, str] | None:
    """Return the style pack dict, or None for a falsy/absent name.

    Raises PackError with a helpful message for an unknown non-empty name.
    """
    key = _normalize(name)
    if key is None:
        return None
    if key not in STYLE_PACKS:
        raise PackError(
            f"unknown style '{name}'. Known styles: {', '.join(sorted(STYLE_PACKS))}"
        )
    return {"name": key, **STYLE_PACKS[key]}


def get_format(name: Any) -> dict[str, Any] | None:
    """Return the format pack dict, or None for a falsy/absent name."""
    key = _normalize(name)
    if key is None:
        return None
    if key not in FORMAT_PACKS:
        raise PackError(
            f"unknown format '{name}'. Known formats: {', '.join(sorted(FORMAT_PACKS))}"
        )
    return {"name": key, **FORMAT_PACKS[key]}


def list_styles() -> list[dict[str, str]]:
    return [{"name": k, **v} for k, v in STYLE_PACKS.items()]


def list_formats() -> list[dict[str, Any]]:
    return [{"name": k, **v} for k, v in FORMAT_PACKS.items()]


# ---------------------------------------------------------------------------
# The one integration point the emitter calls
# ---------------------------------------------------------------------------

def apply_packs(film_meta: dict[str, Any],
                explicit_scene_dur: bool = False) -> dict[str, Any]:
    """Expand `style=` / `format=` (found in film_meta['extras']) into concrete
    fields on film_meta. Returns the same dict, mutated, for chaining.

    Adds (only when the relevant pack is named):
        film_meta['width'], ['height'], ['fps'], ['aspect']   (from format)
        film_meta['style_pack'] = {name, label, still_suffix, negative}

    scene_duration is overridden by the format's default ONLY when the .sf did
    not set `scene_dur` itself (explicit_scene_dur=False). The .sf always wins.

    With no style/format named, film_meta is returned unchanged — the renderer
    then falls back to its historic defaults, so existing films are untouched.
    """
    extras = film_meta.get("extras", {}) or {}

    fmt = get_format(extras.get("format"))
    if fmt:
        film_meta["format"] = fmt["name"]
        film_meta["width"] = fmt["width"]
        film_meta["height"] = fmt["height"]
        film_meta["fps"] = fmt["fps"]
        film_meta["aspect"] = fmt["aspect"]
        if not explicit_scene_dur:
            film_meta["scene_duration"] = float(fmt["scene_dur"])

    style = get_style(extras.get("style"))
    if style:
        film_meta["style"] = style["name"]
        film_meta["style_pack"] = style

    return film_meta


# ---------------------------------------------------------------------------
# CLI: `python -m story_forge.packs` lists everything available
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("STYLES:")
    for s in list_styles():
        print(f"  {s['name']:<14} {s['label']}")
    print("\nFORMATS:")
    for f in list_formats():
        print(f"  {f['name']:<14} {f['label']:<26} "
              f"{f['width']}x{f['height']} @ {f['fps']}fps  ({f['aspect']})")

#!/usr/bin/env python3
"""Story Forge resolver — walks the AST, applies $vars, derives seeds, looks up presets."""

from __future__ import annotations

import hashlib
import re
from typing import Any


class ResolveError(Exception):
    pass


_VAR_RE = re.compile(r"\{\$([A-Za-z_][A-Za-z0-9_]*)\}")


def _interpolate(value: Any, vars_: dict[str, Any]) -> Any:
    if not isinstance(value, str):
        return value

    def repl(m: re.Match) -> str:
        name = m.group(1)
        if name not in vars_:
            raise ResolveError(f"undefined variable ${name}")
        return str(vars_[name])

    return _VAR_RE.sub(repl, value)


def _deterministic_seed(slug: str, scene_name: str, role: str) -> int:
    """sha1(slug + scene_name + role)[:8] → int."""
    h = hashlib.sha1(f"{slug}::{scene_name}::{role}".encode()).hexdigest()
    return int(h[:8], 16)


def _resolve_attrs(attrs: dict[str, Any], vars_: dict[str, Any]) -> dict[str, Any]:
    return {k: _interpolate(v, vars_) for k, v in attrs.items()}


def _resolve_kv_children(children: list[dict[str, Any]],
                         vars_: dict[str, Any]) -> dict[str, Any]:
    """Flatten a block's child kv nodes into a {key:value} dict, interpolating strings."""
    out: dict[str, Any] = {}
    for ch in children:
        if ch["type"] != "kv":
            continue
        out[ch["key"]] = _interpolate(ch["value"], vars_)
    return out


def resolve(ast: list[dict[str, Any]]) -> dict[str, Any]:
    """Walk the parsed AST, return a normalized intermediate dict ready for emission.

    Output shape:
        {
          "film": {"title": ..., "attrs": {...}},   # attrs e.g. slug, target, scene_dur
          "vars": {...},
          "voice_presets": {name: {"value": ..., "attrs": {...}}},
          "music_presets": {name: {"value": ..., "attrs": {...}}},
          "transitions":   [{"name":..., "args":[...], "attrs":{...}}],
          "mixes":         [{"args":[...], "attrs":{...}}],
          "scenes":        [{"name": ..., "still": {...}, "motion": {...},
                             "narrate": {...}, "music": {...}}]
        }
    """
    film_meta: dict[str, Any] = {"title": "Untitled", "attrs": {}}
    vars_: dict[str, Any] = {}
    voice_presets: dict[str, dict[str, Any]] = {}
    music_presets: dict[str, dict[str, Any]] = {}
    sfx_presets: dict[str, dict[str, Any]] = {}
    transitions: list[dict[str, Any]] = []
    mixes: list[dict[str, Any]] = []
    scenes_raw: list[dict[str, Any]] = []

    # Single film node expected at the top, but be tolerant.
    film_node = None
    top_nodes = list(ast)

    # First pass: pull $vars at the very top so they're available everywhere.
    for node in top_nodes:
        if node["type"] == "var":
            vars_[node["name"]] = node["value"]

    # Find the film node (if any) and treat its children as the rest of the document.
    for node in top_nodes:
        if node["type"] == "film":
            film_node = node
            break

    if film_node:
        film_meta["title"] = _interpolate(film_node["title"], vars_)
        film_meta["attrs"] = _resolve_attrs(film_node.get("attrs", {}), vars_)
        # The film header is a declaration line, not necessarily a containing
        # block — siblings at the same indent are still part of the same film.
        # Concatenate the film node's own children with everything else at the
        # top level (excluding $vars and the film node itself).
        document_nodes = list(film_node["children"]) + [
            n for n in top_nodes
            if n is not film_node and n["type"] != "var"
        ]
    else:
        document_nodes = [n for n in top_nodes if n["type"] != "var"]

    slug = film_meta["attrs"].get("slug", "untitled")

    for node in document_nodes:
        t = node["type"]

        if t == "var":
            vars_[node["name"]] = node["value"]

        elif t == "voice":
            voice_presets[node["name"]] = {
                "value": _interpolate(node.get("value"), vars_),
                "attrs": _resolve_attrs(node.get("attrs", {}), vars_),
            }

        elif t == "music":
            music_presets[node["name"]] = {
                "value": _interpolate(node.get("value"), vars_),
                "attrs": _resolve_attrs(node.get("attrs", {}), vars_),
            }

        elif t == "sfx":
            sfx_presets[node["name"]] = {
                "value": _interpolate(node.get("value"), vars_),
                "attrs": _resolve_attrs(node.get("attrs", {}), vars_),
            }

        elif t == "directive":
            if node["name"] == "transition":
                transitions.append({
                    "name": node["args"][0] if node["args"] else "xfade",
                    "args": node["args"][1:],
                    "attrs": _resolve_attrs(node["attrs"], vars_),
                })
            elif node["name"] == "mix":
                mixes.append({
                    "args": node["args"],
                    "attrs": _resolve_attrs(node["attrs"], vars_),
                })
            else:
                # Unknown directive — keep it in transitions bucket for visibility.
                transitions.append({
                    "name": node["name"],
                    "args": node["args"],
                    "attrs": _resolve_attrs(node["attrs"], vars_),
                })

        elif t == "scene":
            scenes_raw.append(node)

    # Resolve each scene now that vars/presets exist.
    scenes_out: list[dict[str, Any]] = []
    for s in scenes_raw:
        scene = {
            "name": s["name"],
            "attrs": _resolve_attrs(s.get("attrs", {}), vars_),
            "still": None,
            "motion": None,
            "narrate": None,        # back-compat: first narrate block
            "narrates": [],         # all narrate blocks, in order
            "music": None,
            "sfx": [],              # all sfx_refs in this scene, in order
        }

        narrate_index = 0
        for child in s["children"]:
            ct = child["type"]
            if ct == "block":
                kind = child["kind"]
                engine = child.get("engine")
                kv = _resolve_kv_children(child.get("children", []), vars_)
                spec = {"engine": engine,
                        "attrs": _resolve_attrs(child.get("attrs", {}), vars_),
                        **kv}
                if kind == "narrate":
                    # Lipsync flag travels with each narrate block.
                    spec["lipsync"] = bool(child.get("lipsync", False))
                    spec["voice"] = engine  # preset name lookup convenience
                    # Per-narrate deterministic seed — each line gets a unique seed.
                    role = f"narrate_{narrate_index}"
                    if spec.get("seed", "auto") in ("auto", None):
                        spec["seed"] = _deterministic_seed(
                            slug, s["name"], role)
                    scene["narrates"].append(spec)
                    if scene["narrate"] is None:
                        scene["narrate"] = spec
                    narrate_index += 1
                else:
                    # still / motion — deterministic seed if auto.
                    seed_val = spec.get("seed", "auto")
                    if seed_val == "auto" or seed_val is None:
                        spec["seed"] = _deterministic_seed(
                            slug, s["name"], kind)
                    scene[kind] = spec
            elif ct == "music_ref":
                ref_name = child["name"]
                ref_attrs = _resolve_attrs(child.get("attrs", {}), vars_)
                preset = music_presets.get(ref_name)
                scene["music"] = {
                    "preset": ref_name,
                    "value": preset["value"] if preset else None,
                    "attrs": {**(preset["attrs"] if preset else {}), **ref_attrs},
                }
            elif ct == "sfx_ref":
                ref_name = child["name"]
                ref_attrs = _resolve_attrs(child.get("attrs", {}), vars_)
                preset = sfx_presets.get(ref_name)
                scene["sfx"].append({
                    "preset": ref_name,
                    "value": preset["value"] if preset else None,
                    "attrs": {**(preset["attrs"] if preset else {}), **ref_attrs},
                })
            elif ct == "kv":
                scene.setdefault("extras", {})[child["key"]] = _interpolate(
                    child["value"], vars_)

        scenes_out.append(scene)

    return {
        "film": film_meta,
        "vars": vars_,
        "voice_presets": voice_presets,
        "music_presets": music_presets,
        "sfx_presets": sfx_presets,
        "transitions": transitions,
        "mixes": mixes,
        "scenes": scenes_out,
    }

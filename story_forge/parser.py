#!/usr/bin/env python3
"""Story Forge DSL parser — hand-rolled, indentation-aware, stdlib only.

Grammar (informal):

    file        := (line)*
    line        := comment | blank | var_assign | directive | block_head | kv
    comment     := '#' .*
    var_assign  := '$' NAME '=' value
    directive   := '@' NAME (TOKEN | KV)*                  # @transition xfade dur=0.5
    block_head  := HEAD ':'                                # film "T" slug=foo  /  scene a:  /  still flux: / motion wan: / narrate warm: / voice warm:
    kv          := KEY ':' value                           # inside a block

Top-level constructs we expect:

    film "Title" slug=foo target=m5+mini scene_dur=8.5
        # children are scenes, presets, directives

    scene name:
        still flux:
            prompt: "..."
            seed:   auto
        motion wan:
            prompt: "..."
            duration: 5.0
        narrate warm:
            line: "..."
        music wintry vol=0.35

    voice warm: piper/en_US-libritts_r-medium speaker=0 length=1.18
    music wintry: ace/wintry-soft-piano vol=0.35

    @transition xfade dur=0.5
    @mix duck voice -> music threshold=-22 ratio=4

AST shape — a list of nodes. Each node is a dict:
    {"type":"film", "title":..., "attrs":{...}, "children":[...], "line":N}
    {"type":"scene", "name":..., "children":[...], "line":N}
    {"type":"block", "kind":"still", "engine":"flux", "attrs":{...}, "children":[...], "line":N}
    {"type":"narrate", "preset":"warm", "attrs":{}, "children":[...], "line":N}
    {"type":"voice", "name":"warm", "value":"piper/...", "attrs":{...}, "line":N}
    {"type":"music", "name":"wintry", "value":"ace/...", "attrs":{...}, "line":N}
    {"type":"sfx",   "name":"fire_crackle", "value":"ace/sfx", "attrs":{...}, "line":N}
    {"type":"music_ref", "name":"wintry", "attrs":{"vol":0.35}, "line":N}
    {"type":"sfx_ref",   "name":"fire_crackle", "attrs":{"at":2.0}, "line":N}
    {"type":"narrate", "preset":"warm", "lipsync":False, "attrs":{...}, "children":[...], "line":N}
    {"type":"var", "name":"child", "value":"a small child...", "line":N}
    {"type":"directive", "name":"transition", "args":["xfade"], "attrs":{"dur":0.5}, "line":N}
    {"type":"kv", "key":"prompt", "value":"...", "line":N}
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


class ParseError(Exception):
    def __init__(self, msg: str, line: int = 0, col: int = 0):
        super().__init__(f"line {line}: {msg}")
        self.line = line
        self.col = col


# ---------------------------------------------------------------------------
# Lexing helpers
# ---------------------------------------------------------------------------

_KV_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(\"[^\"]*\"|'[^']*'|[^\s]+)")
_QUOTED = re.compile(r"\"([^\"]*)\"|'([^']*)'")


def _strip_comment(s: str) -> str:
    """Remove trailing # comment but respect quotes."""
    out = []
    in_q = None
    for i, ch in enumerate(s):
        if in_q:
            out.append(ch)
            if ch == in_q:
                in_q = None
        else:
            if ch in ('"', "'"):
                in_q = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
    return "".join(out).rstrip()


def _coerce(v: str) -> Any:
    """Turn '42' -> 42, '0.5' -> 0.5, '"foo"' -> 'foo', 'true' -> True."""
    if v is None:
        return None
    v = v.strip()
    if len(v) >= 2 and v[0] == v[-1] and v[0] in ('"', "'"):
        return v[1:-1]
    if v.lower() in ("true", "yes", "on"):
        return True
    if v.lower() in ("false", "no", "off"):
        return False
    if v.lower() in ("none", "null"):
        return None
    try:
        if "." in v or "e" in v.lower():
            return float(v)
        return int(v)
    except ValueError:
        return v


def _parse_kvs(tail: str) -> tuple[list[str], dict[str, Any]]:
    """Split a header tail into positional args + key=value attrs.

    e.g. `xfade dur=0.5` -> (["xfade"], {"dur": 0.5})
    e.g. `"The Bear Sister" slug=bear target=m5+mini scene_dur=8.5`
         -> (["The Bear Sister"], {"slug":"bear","target":"m5+mini","scene_dur":8.5})
    """
    attrs: dict[str, Any] = {}
    # Pull KVs out first, remember their spans.
    spans: list[tuple[int, int]] = []
    for m in _KV_RE.finditer(tail):
        attrs[m.group(1)] = _coerce(m.group(2))
        spans.append(m.span())

    # Strip the KV spans from the tail to get the positional portion.
    keep = []
    i = 0
    for s, e in spans:
        keep.append(tail[i:s])
        i = e
    keep.append(tail[i:])
    rest = "".join(keep).strip()

    args: list[str] = []
    # Split positional tokens, respecting quoted strings.
    j = 0
    while j < len(rest):
        ch = rest[j]
        if ch.isspace():
            j += 1
            continue
        if ch in ('"', "'"):
            end = rest.find(ch, j + 1)
            if end == -1:
                raise ParseError(f"unterminated string in {tail!r}")
            args.append(rest[j + 1:end])
            j = end + 1
        else:
            k = j
            while k < len(rest) and not rest[k].isspace():
                k += 1
            args.append(rest[j:k])
            j = k
    return args, attrs


# ---------------------------------------------------------------------------
# Indentation handling
# ---------------------------------------------------------------------------

def _indent_of(raw: str) -> int:
    n = 0
    for ch in raw:
        if ch == " ":
            n += 1
        elif ch == "\t":
            n += 4  # treat tabs as 4 spaces
        else:
            break
    return n


# ---------------------------------------------------------------------------
# Line classification
# ---------------------------------------------------------------------------

_HEAD_TOKENS = {"film", "scene", "still", "motion", "narrate", "voice", "music", "sfx"}


def _classify(stripped: str, lineno: int) -> dict[str, Any]:
    """Turn one already-stripped, non-blank, non-pure-comment line into a raw node."""
    # Variable assignment
    if stripped.startswith("$"):
        m = re.match(r"^\$([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.+)$", stripped)
        if not m:
            raise ParseError(f"bad variable assignment: {stripped!r}", lineno)
        return {"type": "var", "name": m.group(1),
                "value": _coerce(m.group(2)), "line": lineno}

    # Directive
    if stripped.startswith("@"):
        rest = stripped[1:].strip()
        # split off the first token (directive name)
        parts = rest.split(None, 1)
        name = parts[0]
        tail = parts[1] if len(parts) > 1 else ""
        # @mix special form:  duck voice -> music threshold=-22 ratio=4
        # We just collect every non-kv token as a positional arg, including '->'.
        args, attrs = _parse_kvs(tail)
        return {"type": "directive", "name": name,
                "args": args, "attrs": attrs, "line": lineno}

    # Block head ends with ':' (with optional attrs on same line for certain blocks)
    # vs. plain kv (key: value)
    # Strategy: find the FIRST ':' not inside quotes. Everything before it is the head.
    head, sep, value = _split_first_colon(stripped)
    if not sep:
        raise ParseError(f"unrecognized line (no colon, no $/@): {stripped!r}", lineno)

    head_tokens = head.strip().split(None, 1)
    head_word = head_tokens[0] if head_tokens else ""
    head_tail = head_tokens[1] if len(head_tokens) > 1 else ""

    # block-head form?
    if head_word in _HEAD_TOKENS:
        return _build_block_head(head_word, head_tail, value.strip(), lineno)

    # plain kv
    return {"type": "kv", "key": head.strip(),
            "value": _coerce(value.strip()), "line": lineno}


def _split_first_colon(s: str) -> tuple[str, str, str]:
    in_q = None
    for i, ch in enumerate(s):
        if in_q:
            if ch == in_q:
                in_q = None
        elif ch in ('"', "'"):
            in_q = ch
        elif ch == ":":
            return s[:i], ":", s[i + 1:]
    return s, "", ""


def _build_block_head(word: str, tail: str, after_colon: str,
                      lineno: int) -> dict[str, Any]:
    """Construct a block-head node.

    Forms handled:
        film "Title" slug=foo target=m5+mini scene_dur=8.5      (after_colon empty)
        scene snow_walk:                                         (tail="snow_walk")
        still flux:                                              (tail="flux")
        motion wan:                                              (tail="wan")
        motion ltx:                                              (tail="ltx")
        narrate warm:                                            (tail="warm")
        voice warm: piper/model speaker=0 length=1.18            (tail="warm", value present)
        music wintry: ace/wintry-soft vol=0.35                   (tail="wintry", value present)
        music wintry vol=0.35                                    (NOT block-head — handled as ref below)
    """
    args, attrs = _parse_kvs(tail)

    if word == "film":
        title = args[0] if args else attrs.pop("title", "Untitled")
        return {"type": "film", "title": title, "attrs": attrs,
                "children": [], "line": lineno}

    if word == "scene":
        if not args:
            raise ParseError("scene needs a name", lineno)
        return {"type": "scene", "name": args[0], "attrs": attrs,
                "children": [], "line": lineno}

    if word in ("still", "motion"):
        engine = args[0] if args else None
        return {"type": "block", "kind": word, "engine": engine,
                "attrs": attrs, "children": [], "line": lineno}

    if word == "narrate":
        # narrate <voice>:                         (block w/ line: child)
        # narrate <voice> with lipsync:            (lipsync flag set)
        # narrate <voice>: "Inline line text"      (inline single-line form)
        # narrate <voice> with lipsync: "..."      (inline + lipsync)
        lipsync = False
        # Strip "with lipsync" from args, if present.
        cleaned_args: list[str] = []
        i = 0
        while i < len(args):
            tok = args[i]
            if tok == "with" and i + 1 < len(args) and args[i + 1] == "lipsync":
                lipsync = True
                i += 2
                continue
            cleaned_args.append(tok)
            i += 1
        preset = cleaned_args[0] if cleaned_args else None
        # If there's content after the colon, treat it as an inline "line".
        node: dict[str, Any] = {"type": "block", "kind": "narrate",
                                "engine": preset, "lipsync": lipsync,
                                "attrs": attrs, "children": [], "line": lineno}
        if after_colon.strip():
            # Inline: the value after the colon is the spoken line. Use the
            # quoted-string-or-bareword logic to capture it cleanly.
            inline_args, _ = _parse_kvs(after_colon)
            inline_value = inline_args[0] if inline_args else after_colon.strip()
            node["children"].append({"type": "kv", "key": "line",
                                     "value": _coerce(inline_value) if not isinstance(inline_value, str) else inline_value,
                                     "line": lineno})
        return node

    if word == "voice":
        # voice <name>: piper/model speaker=0 ...
        name = args[0] if args else "default"
        v_args, v_attrs = _parse_kvs(after_colon)
        value = v_args[0] if v_args else None
        return {"type": "voice", "name": name, "value": value,
                "attrs": v_attrs, "line": lineno}

    if word == "music":
        # music <name>: ace/foo vol=0.35    (preset definition)
        name = args[0] if args else "default"
        m_args, m_attrs = _parse_kvs(after_colon)
        value = m_args[0] if m_args else None
        # merge in attrs that hung off the head (rare but legal)
        m_attrs = {**attrs, **m_attrs}
        return {"type": "music", "name": name, "value": value,
                "attrs": m_attrs, "line": lineno}

    if word == "sfx":
        # sfx <name>: ace/sfx prompt="..." duration=8 vol=0.25   (preset definition)
        name = args[0] if args else "default"
        s_args, s_attrs = _parse_kvs(after_colon)
        value = s_args[0] if s_args else None
        s_attrs = {**attrs, **s_attrs}
        return {"type": "sfx", "name": name, "value": value,
                "attrs": s_attrs, "line": lineno}

    raise ParseError(f"unknown block head: {word}", lineno)


# ---------------------------------------------------------------------------
# Tree assembly via indent stack
# ---------------------------------------------------------------------------

def parse(source: str | Path) -> list[dict[str, Any]]:
    """Parse a .sf string or file path into an AST (list of top-level nodes)."""
    if isinstance(source, Path):
        text = source.read_text()
    elif isinstance(source, str) and "\n" not in source and Path(source).exists():
        text = Path(source).read_text()
    else:
        text = source

    raw_lines = text.splitlines()
    top: list[dict[str, Any]] = []
    # Stack of (indent, children_list_to_append_into).
    stack: list[tuple[int, list[dict[str, Any]]]] = [(-1, top)]

    for i, raw in enumerate(raw_lines, start=1):
        if not raw.strip():
            continue
        stripped_no_comment = _strip_comment(raw)
        if not stripped_no_comment.strip():
            continue
        indent = _indent_of(raw)
        content = stripped_no_comment.strip()

        # Special: bare "music <name> vol=0.35" inside a scene — no colon, treat as music_ref.
        if (content.startswith("music ") and ":" not in content
                and not content.startswith("@")):
            tail = content[len("music"):].strip()
            args, attrs = _parse_kvs(tail)
            name = args[0] if args else "default"
            node = {"type": "music_ref", "name": name,
                    "attrs": attrs, "line": i}
        # Special: bare "sfx <name> at=2.0 vol=0.3" inside a scene — no colon, treat as sfx_ref.
        elif (content.startswith("sfx ") and ":" not in content
                and not content.startswith("@")):
            tail = content[len("sfx"):].strip()
            args, attrs = _parse_kvs(tail)
            name = args[0] if args else "default"
            node = {"type": "sfx_ref", "name": name,
                    "attrs": attrs, "line": i}
        # Special: colon-less film header — `film "Title" slug=foo target=m5+mini scene_dur=8.5`
        elif content.startswith("film ") and ":" not in _split_first_colon(content)[0]:
            # Use the block-head builder directly so we get a node with children=[].
            head_tail = content[len("film"):].strip()
            node = _build_block_head("film", head_tail, "", i)
        else:
            node = _classify(content, i)

        # Pop stack until current indent is greater than the top of stack's indent.
        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            stack = [(-1, top)]
        parent_indent, parent_children = stack[-1]
        parent_children.append(node)

        # If this node can have children, push it.
        if node["type"] in ("film", "scene", "block"):
            stack.append((indent, node["children"]))

    return top


# ---------------------------------------------------------------------------
# CLI smoke-test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import json
    import sys
    if len(sys.argv) != 2:
        print("usage: parser.py FILE.sf", file=sys.stderr)
        raise SystemExit(2)
    print(json.dumps(parse(Path(sys.argv[1])), indent=2, default=str))

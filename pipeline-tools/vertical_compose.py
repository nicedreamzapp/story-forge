#!/usr/bin/env python3
"""vertical_compose.py — the 9:16 deliverable as its OWN composition, from the same story, assets and timeline.

WHY THIS EXISTS (2026-11-02): the reel used to be the wide film scaled into the middle of a blurred copy
of itself (SESSION_HANDOFF "9:16 vertical with blurred-background extension"). That is a crop-or-pad of a
16:9 picture: the subject is small, the type is 56 % of its size, three things fight for a narrow band and
the platform buttons sit on top of the callouts. Motion-design practice for vertical is different: same
story, same takes, same timeline, but a new composition: the camera follows the subject inside a 9:16
window, type is bigger relative to the frame, fewer elements share the screen, the hierarchy runs top to
bottom and nothing lands in the phone UI's zones. This tool builds that:

  1. per shot, a subject-aware crop path (reframe.py: Apple Vision faces > people > saliency, eased camera
     moves, never cutting a face). A take already shot vertical (`<stem>_v.mp4`, `acquired/blender/<id>_v/`,
     or `"vertical_file"` on the EDL shot) is used as is ("native").
  2. a shot that cannot be reframed (wide two-shot, extreme close-up, a product wider than the window, a
     16:9 title card) is FLAGGED: listed in report.md and rerender_requests.json, and with --write-spec
     stamped into the shot spec (promo.json "vertical_rerender" with the Blender job re-aimed at 1080x1920;
     shots.json / film_shots.json `"vertical": {"rerender": true, ...}` on film projects). Its draft
     stand-in is the closest crop (or a letterbox for title cards), never a silent pad.
  3. titles, callouts and the end card re-laid from the SAME timing data (layouts.py vertical: safe box,
     larger type, labels in the top or bottom band, tips re-mapped through the crop path; a callout whose
     part leaves the window is dropped and listed). At most N elements at once (default 2; titles outrank
     callouts outrank overlays). 16:9 alpha overlays (Manim) use a `<stem>_v.mov` vertical variant when it
     exists, else they are fitted to the safe width and listed as a re-render request.
  4. renders final/vertical/<film>_vertical.mp4 with render_edl.py (same mix, same cut points) and writes a
     contact sheet for EACH composition (final/contact_sheet.jpg for 16:9, final/vertical/contact_sheet.jpg)
     plus final/vertical/reframe_plan.jpg (the 16:9 frames with the window and the detected faces drawn on).

Usage:
  ~/chatterbox-env/bin/python pipeline-tools/vertical_compose.py projects/<film> [--render] [--write-spec]
        [--max-elements 2] [--size 1080x1920] [--audio-from final/<Film>.mp4]
Promo projects read edl.json (+ callouts.json); film projects read final/edl_final.json.
Exit 0 = composed (and rendered with --render), every shot reframed or native; 3 = composed but some shots
are FLAGGED for a vertical re-render (the vertical is a DRAFT until they come back); 1 = render failed;
2 = could not read the project.
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import reframe  # noqa: E402
from layouts import layout_for  # noqa: E402

SF = HERE.parent
TEXTY = re.compile(r"(title|credit|card|endcard|text)", re.I)


# ----------------------------------------------------------------------------- timeline in
def load_timeline(film: Path):
    fmt = (film / "FORMAT").read_text().strip() if (film / "FORMAT").exists() else "film"
    if fmt == "promo" or (film / "edl.json").exists():
        edl = json.loads((film / "edl.json").read_text())
        cp = film / edl.get("callouts", "callouts.json")
        callouts = json.loads(cp.read_text()).get("callouts", []) if cp.exists() else []
        return "promo", edl, callouts
    ef = film / "final" / "edl_final.json"
    if not ef.exists():
        raise FileNotFoundError(f"{film.name}: no edl.json (promo) and no final/edl_final.json (film)")
    e = json.loads(ef.read_text())
    shots = []
    for c in e["cuts"]:
        src = c.get("src")
        shots.append({"cid": c["id"], "file": src, "kind": "black" if not src else "video",
                      "src_in": float(c.get("in", 0)), "src_out": float(c.get("in", 0)) + float(c["len"]),
                      "rec_in": float(c["start"]), "rec_out": float(c["start"]) + float(c["len"]),
                      "transition": "cut", "xfade": 0.0, "section": c.get("section", "")})
    edl = {"fps": int(e.get("fps", 24)), "w": int(e["size"][0]), "h": int(e["size"][1]),
           "dur": float(e.get("duration") or max(s["rec_out"] for s in shots)), "shots": shots, "audio": []}
    return "film", edl, []


def native_vertical(film: Path, s: dict) -> str | None:
    if s.get("vertical_file") and (film / s["vertical_file"]).exists():
        return s["vertical_file"]
    f = s.get("file")
    if not f:
        return None
    p = Path(f)
    cands = [p.with_name(f"{p.stem}_v{p.suffix}"), p.with_name(f"{p.stem}_vertical{p.suffix}")]
    if p.parent.parent.name == "blender":
        cands.insert(0, p.parent.with_name(p.parent.name + "_v") / p.name)
    for c in cands:
        if (film / c).exists():
            return str(c)
    return None


# ----------------------------------------------------------------------------- the plan
def pins_for(s: dict, callouts: list) -> list:
    """Callouts that point into shot s, as (src_t0, src_t1, tip x) pins for the reframer. A moving tip
    contributes its mean x over the shot (the planner keeps the whole span in frame through PIN_PAD)."""
    out = []
    for co in callouts:
        a, b = max(float(co["rec_in"]), s["rec_in"]), min(float(co["rec_out"]), s["rec_out"])
        if b <= a:
            continue
        tip = co["tip"]
        if tip and isinstance(tip[0], (list, tuple)):
            xs = [k[1] for k in tip if a - 1e-6 <= k[0] <= b + 1e-6] or [tip[0][1]]
            x = sum(xs) / len(xs)
        else:
            x = tip[0]
        out.append((src_time(s, a), src_time(s, b), x))
    return out


def plan_shots(film: Path, edl: dict, aspect: float, work: Path, fmt: str, callouts: list | None = None) -> list:
    plans = []
    cw_for = lambda w, h: min(1.0, (h * aspect) / w)  # noqa: E731
    for k, s in enumerate(edl["shots"]):
        cid = s.get("cid", f"shot{k}")
        base = {"cid": cid, "file": s.get("file"), "line": s.get("line"), "rec_in": s["rec_in"], "rec_out": s["rec_out"]}
        if s.get("kind") == "black":
            plans.append({**base, "verdict": "static", "reason": "black", "keys": [], "cw": 1.0})
            continue
        nv = native_vertical(film, s)
        if nv:
            plans.append({**base, "verdict": "native", "reason": f"vertical take {nv}", "vertical_file": nv})
            continue
        if TEXTY.search(str(s.get("section", ""))) or TEXTY.search(Path(str(s.get("file", ""))).stem):
            sw, sh = reframe.video_size(film / s["file"]) if s.get("kind") != "image" else (16, 9)
            plans.append({**base, "verdict": "flagged", "fallback": "pad", "keys": [], "cw": 1.0,
                          "src_w": sw, "src_h": sh,
                          "reason": "a 16:9 title/text card: lay it out again for 9:16 (letterboxed stand-in)"})
            continue
        f = film / s["file"]
        if not f.exists():
            plans.append({**base, "verdict": "flagged", "reason": f"source missing: {s['file']}", "keys": [], "cw": 1.0})
            continue
        t0 = time.time()
        p, dets, pngs, times = reframe.plan_file(f, float(s["src_in"]), float(s["src_out"]), s.get("kind", "video"),
                                          cw_for, f"s{k:03d}", work, pins_for(s, callouts or []))
        p.update(base)
        p["samples"] = [{"png": str(png), "t": t, "faces": d.get("faces", []), "humans": d.get("humans", []),
                         "saliency": d.get("saliency", [])} for png, t, d in
                        zip(pngs, times, dets)]
        lowres = p.get("cw", 1) * p.get("src_w", 0)
        if lowres and lowres < 540:
            p["warn"] = f"the window is only {int(lowres)} px wide in the source: x{1080 / lowres:.1f} upscale"
        plans.append(p)
        print(f"[vertical] {cid:<34} {p['verdict']:<8} {p.get('reason', '')[:90]}  ({time.time() - t0:.1f}s)", flush=True)
    return plans


def src_time(s: dict, t_rec: float) -> float:
    return float(s["src_in"]) + (t_rec - float(s["rec_in"])) * float(s.get("speed", 1.0) or 1.0)


def remap_callouts(callouts: list, edl: dict, plans: dict, lay) -> tuple:
    """Tips through the crop path; labels into the vertical bands. Returns (kept, dropped)."""
    kept, dropped = [], []
    shots = edl["shots"]
    for co in callouts:
        t0, t1 = float(co["rec_in"]), float(co["rec_out"])
        tip = co["tip"]
        keys = tip if (tip and isinstance(tip[0], (list, tuple))) else None
        ts = [k[0] for k in keys] if keys else [t0 + (t1 - t0) * j / 12 for j in range(13)]
        new, bad, ys = [], None, []
        for t in ts:
            s = next((x for x in shots if x["rec_in"] <= t < x["rec_out"]), None)
            if keys:
                x, y = next(([k[1], k[2]] for k in keys if abs(k[0] - t) < 1e-9))
            else:
                x, y = tip
            if s is None:
                continue
            pl = plans.get(s.get("cid"))
            if not pl or pl["verdict"] in ("native",):
                bad = f"the shot under it ({s.get('cid')}) is a native vertical take: aim the callout on that take"
                break
            if pl["verdict"] == "flagged":
                bad = f"the shot under it ({s.get('cid')}) is flagged for a vertical re-render"
                break
            cw = float(pl["cw"])
            c = reframe.window_at(pl, src_time(s, t)) if pl.get("keys") else 0.5
            xv = (x - (c - cw / 2)) / cw
            if not 0.03 <= xv <= 0.97:
                bad = f"its part leaves the 9:16 window (x {xv:.2f} at {t:.2f}s)"
                break
            new.append([round(t, 3), round(xv, 4), round(y, 4)])
            ys.append(y)
        if bad or not new:
            dropped.append({"id": co.get("id"), "label": co.get("label"), "why": bad or "no shot under it"})
            continue
        v = copy.deepcopy(co)
        v["tip"] = new if (keys or len({(a, b) for _, a, b in new}) > 1) else [new[0][1], new[0][2]]
        avg_y = sum(ys) / len(ys)
        band = lay.label_bands[1] if avg_y < 0.5 else lay.label_bands[0]   # label on the far side of the part
        v["text_at"] = [round((lay.safe[0] + lay.safe[2]) / 2, 3), band]
        kept.append(v)
    return kept, dropped


def limit_elements(titles: list, callouts: list, overlays: list, n: int) -> list:
    """At most n titles + callouts + overlays on screen at once; lower priority, later start loses."""
    items = ([(3, float(t["rec_in"]), float(t["rec_out"]), "title", t) for t in titles] +
             [(2, float(c["rec_in"]), float(c["rec_out"]), "callout", c) for c in callouts] +
             [(1, float(o["rec_in"]), float(o["rec_out"]), "overlay", o) for o in overlays])
    dropped = []
    while True:
        live = [i for i in items if i[4] is not None]
        worst = None
        for a in live:
            over = [b for b in live if b[1] < a[2] - 1e-6 and a[1] < b[2] - 1e-6]
            # count what is on screen at the moment `a` starts
            at = [b for b in over if b[1] <= a[1] + 1e-6 < b[2]]
            if len(at) > n:
                cand = min(at, key=lambda b: (b[0], -b[1]))
                worst = cand
                break
        if not worst:
            break
        dropped.append({"kind": worst[3], "what": worst[4].get("text") or worst[4].get("label") or
                        worst[4].get("file"), "rec_in": worst[1],
                        "why": f"more than {n} elements on screen at once (vertical keeps it to {n})"})
        items = [i if i is not worst else (i[0], i[1], i[2], i[3], None) for i in items]
    keep = {id(i[4]) for i in items if i[4] is not None}
    return ([t for t in titles if id(t) in keep], [c for c in callouts if id(c) in keep],
            [o for o in overlays if id(o) in keep], dropped)


def vertical_overlays(film: Path, edl: dict, lay) -> tuple:
    out, reqs = [], []
    for o in edl.get("overlays", []):
        v = dict(o)
        p = Path(o["file"])
        vf = p.with_name(f"{p.stem}_v{p.suffix}")
        if (film / vf).exists():
            v.update(file=str(vf), x=0.5, y=0.5, w=1.0)
        else:
            # a 16:9 alpha clip: fitted to the safe width, centered in the safe box; listed for a 9:16 version
            sw = lay.safe[2] - lay.safe[0]
            v.update(x=round((lay.safe[0] + lay.safe[2]) / 2, 3), y=round((lay.safe[1] + lay.safe[3]) / 2, 3),
                     w=round(min(sw, float(o.get("w", 1.0)) * sw), 3))
            reqs.append({"kind": "overlay", "file": o["file"], "rec_in": o["rec_in"],
                         "why": "16:9 overlay reused at the safe width (smaller type than a vertical layout)",
                         "ask": f"render a 9:16 version as {vf} (Manim: --size {lay.W}x{lay.H}, re-laid top to bottom)"})
        out.append(v)
    return out, reqs


# ----------------------------------------------------------------------------- re-render requests
def rerender_requests(film: Path, fmt: str, plans: list, size: tuple) -> list:
    reqs = []
    promo = json.loads((film / "promo.json").read_text()) if (film / "promo.json").exists() else {}
    jobs = promo.get("blender", [])
    for p in plans:
        if p["verdict"] != "flagged":
            continue
        r = {"cid": p["cid"], "file": p.get("file"), "line": p.get("line"), "why": p.get("reason"),
             "aspect": "9:16", "res": list(size)}
        job = next((j for j in jobs if p["cid"].startswith(j["id"])), None)
        if job:
            nj = copy.deepcopy(job)
            nj["id"] = job["id"] + "_v"
            nj["res"] = list(size)
            nj.setdefault("camera", {})["frame_fill"] = min(0.9, float(nj["camera"].get("frame_fill", 0.8)))
            r.update(kind="blender", job=nj, ask=f"render promo.json blender job '{nj['id']}' (1080x1920); "
                                                    f"vertical_compose picks up acquired/blender/{nj['id']}/ by itself")
        elif p.get("file"):
            stem = Path(p["file"])
            r.update(kind="footage", ask=f"re-render this setup framed for 9:16 ({size[0]}x{size[1]}, subject "
                                         f"centered, heads clear) and save it as {stem.with_name(stem.stem + '_v' + stem.suffix)}")
        reqs.append(r)
    return reqs


def write_spec(film: Path, fmt: str, reqs: list) -> list:
    """Stamp the requests into the shot spec. Returns what was written where."""
    done = []
    if fmt == "promo" and (film / "promo.json").exists():
        pj = film / "promo.json"
        cfg = json.loads(pj.read_text())
        cfg["vertical_rerender"] = [r for r in reqs if r.get("cid")]
        pj.write_text(json.dumps(cfg, indent=1))
        done.append(f"promo.json vertical_rerender ({len(cfg['vertical_rerender'])})")
        return done
    for name in ("shots.json", "film_shots.json"):
        sp = film / name
        if not sp.exists():
            continue
        d = json.loads(sp.read_text())
        shots = d["shots"] if isinstance(d, dict) else d
        for s in shots:   # a fresh plan replaces the last one's requests (a fixed shot loses its stamp)
            if isinstance(s.get("vertical"), dict) and s["vertical"].get("rerender"):
                s.pop("vertical")
        n = 0
        for r in reqs:
            if not r.get("cid"):
                continue
            src = Path(str(r.get("file") or "")).stem
            for s in shots:
                sid = s.get("id", "")
                if sid and (sid == r["cid"] or (src and src.startswith(sid))):
                    s["vertical"] = {"rerender": True, "aspect": "9:16", "res": r["res"], "why": r["why"],
                                     "cut": r["cid"], "requested": time.strftime("%Y-%m-%d")}
                    n += 1
        if n:
            sp.write_text(json.dumps(d, indent=1))
            done.append(f"{name} ({n} shots)")
    return done


# ----------------------------------------------------------------------------- pictures for the eye
def plan_sheet(plans: list, out: Path) -> None:
    """The 16:9 source frames (middle sample of every planned shot) with the 9:16 window and faces drawn on."""
    from PIL import Image, ImageDraw, ImageFont
    tiles = []
    for p in plans:
        smp = p.get("samples") or []
        if not smp:
            continue
        m = smp[len(smp) // 2]
        if not Path(m["png"]).exists():
            continue
        im = Image.open(m["png"]).convert("RGB")
        w, h = im.size
        d = ImageDraw.Draw(im)
        for f in m.get("faces", []):
            d.rectangle([f[0] * w, f[1] * h, (f[0] + f[2]) * w, (f[1] + f[3]) * h], outline=(250, 204, 21), width=2)
        if p.get("keys"):
            c = reframe.window_at(p, m["t"])
            cw = float(p["cw"])
            col = (248, 113, 113) if p["verdict"] == "flagged" else (45, 212, 191)
            shade = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            sd = ImageDraw.Draw(shade)
            sd.rectangle([0, 0, (c - cw / 2) * w, h], fill=(0, 0, 0, 140))
            sd.rectangle([(c + cw / 2) * w, 0, w, h], fill=(0, 0, 0, 140))
            im = Image.alpha_composite(im.convert("RGBA"), shade).convert("RGB")
            d = ImageDraw.Draw(im)
            d.rectangle([(c - cw / 2) * w, 1, (c + cw / 2) * w, h - 2], outline=col, width=3)
        f_ = ImageFont.truetype("/System/Library/Fonts/Avenir Next.ttc", 18, index=8)
        d.rectangle([0, h - 28, w, h], fill=(0, 0, 0))
        d.text((6, h - 26), f"{p['cid'][:40]}  {p['verdict'].upper()}", font=f_,
               fill=(248, 113, 113) if p["verdict"] == "flagged" else (230, 230, 230))
        tiles.append(im.resize((420, round(420 * h / w))))
    if not tiles:
        return
    cols = 4
    tw, th = tiles[0].size
    sheet = Image.new("RGB", (cols * (tw + 8) + 8, ((len(tiles) + cols - 1) // cols) * (th + 8) + 8), (12, 14, 18))
    for k, t in enumerate(tiles):
        sheet.paste(t, (8 + (k % cols) * (tw + 8), 8 + (k // cols) * (th + 8)))
    sheet.save(out, quality=86)


# ----------------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("film")
    ap.add_argument("--render", action="store_true", help="render final/vertical/<film>_vertical.mp4")
    ap.add_argument("--write-spec", action="store_true", help="stamp re-render requests into the shot spec")
    ap.add_argument("--max-elements", type=int, default=None)
    ap.add_argument("--size", default="1080x1920")
    ap.add_argument("--audio-from", default=None, help="film projects: the mp4/wav whose audio the vertical uses")
    ap.add_argument("--bug", default=None)
    a = ap.parse_args()
    film = Path(a.film).resolve()
    try:
        fmt, edl, callouts = load_timeline(film)
    except Exception as e:
        print(f"[vertical] {e}", file=sys.stderr)
        return 2
    W, H = (int(x) for x in a.size.split("x"))
    lay = layout_for(W, H)
    n_max = a.max_elements or lay.max_elements
    out_dir = film / "final" / "vertical"
    out_dir.mkdir(parents=True, exist_ok=True)
    work = out_dir / "_samples"
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir()
    print(f"[vertical] {film.name} ({fmt}): {len(edl['shots'])} shots, {edl['w']}x{edl['h']} -> {W}x{H}")
    plans = plan_shots(film, edl, W / H, work, fmt, callouts)
    pmap = {p["cid"]: p for p in plans}

    # the vertical EDL: same cut points, same audio, its own picture
    v = copy.deepcopy(edl)
    v.update(w=W, h=H, layout="vertical", source_edl="edl.json" if fmt == "promo" else "final/edl_final.json")
    for s in v["shots"]:
        p = pmap[s.get("cid")]
        if p["verdict"] == "native":
            s["file"] = p["vertical_file"]
            s.pop("reframe", None)
        elif p.get("fallback") == "pad":
            s["fit"] = "pad"
        elif p.get("keys"):
            s["reframe"] = {"keys": p["keys"], "cw": p["cw"], "src_w": p["src_w"], "src_h": p["src_h"]}
        if p["verdict"] == "flagged":
            s["vertical_flag"] = p.get("reason")
    vcall, dropped_co = remap_callouts(callouts, edl, pmap, lay)
    vover, over_reqs = vertical_overlays(film, edl, lay)
    titles, vcall, vover, dropped_el = limit_elements(v.get("titles", []), vcall, vover, n_max)
    v["titles"], v["overlays"] = titles, vover
    v["callouts"] = "final/vertical/callouts.json"
    (out_dir / "callouts.json").write_text(json.dumps({"callouts": vcall}, indent=1))
    (out_dir / "edl.json").write_text(json.dumps(v, indent=1))
    reqs = rerender_requests(film, fmt, plans, (W, H)) + over_reqs
    (out_dir / "rerender_requests.json").write_text(json.dumps({"requests": reqs}, indent=1))
    spec_done = write_spec(film, fmt, reqs) if a.write_spec else []
    slim = [{k: x for k, x in p.items() if k != "samples"} for p in plans]
    (out_dir / "plan.json").write_text(json.dumps({"size": [W, H], "max_elements": n_max, "shots": slim,
                                                   "callouts_dropped": dropped_co, "elements_dropped": dropped_el},
                                                  indent=1))
    plan_sheet(plans, out_dir / "reframe_plan.jpg")

    rc = 0
    mp4 = out_dir / f"{film.name}_vertical.mp4"
    if a.render:
        audio = None
        if fmt == "promo" and (film / "final" / "mix.wav").exists():
            audio = film / "final" / "mix.wav"
        elif a.audio_from:
            audio = (film / a.audio_from) if not Path(a.audio_from).is_absolute() else Path(a.audio_from)
        cmd = [sys.executable, str(HERE / "render_edl.py"), "--renderer", "ffmpeg", str(film), "--edl",
               "final/vertical/edl.json", "--out", str(mp4)]
        if audio:
            cmd += ["--audio", str(audio)]
        bug = a.bug
        if bug is None and (film / "promo.json").exists():
            bug = json.loads((film / "promo.json").read_text()).get("bug")
        if bug:
            cmd += ["--bug", bug]
        print(f"[vertical] rendering {mp4.relative_to(film)}", flush=True)
        r = subprocess.run(cmd)
        if r.returncode != 0:
            print(f"[vertical] render_edl exited {r.returncode}", file=sys.stderr)
            rc = 1
        else:
            from contact_sheet import items_from_edl, make_sheet
            make_sheet(mp4, items_from_edl(v, {"shots": slim}), out_dir / "contact_sheet.jpg",
                       f"{film.name} 9:16 vertical composition")
            wide = film / "final" / f"{film.name}.mp4"
            if fmt == "promo" and wide.exists():
                make_sheet(wide, items_from_edl(edl), film / "final" / "contact_sheet.jpg",
                           f"{film.name} 16:9 composition")

    # the report
    counts = {}
    for p in plans:
        counts[p["verdict"]] = counts.get(p["verdict"], 0) + 1
    flagged = [p for p in plans if p["verdict"] == "flagged"]
    lines = [f"# Vertical composition: {film.name}", "",
             f"{time.strftime('%Y-%m-%d %H:%M')}, {W}x{H}, from {v['source_edl']} ({len(plans)} shots). "
             f"Max {n_max} text/overlay elements at once.", "",
             "**Status: " + (f"DRAFT, {len(flagged)} shot(s) need a vertical re-render" if flagged else
                            "every shot reframed or native") + "**  ",
             "Verdicts: " + ", ".join(f"{k} {n}" for k, n in sorted(counts.items())), "",
             "| Shot | Verdict | Why | Pan speed (width/s) | Note |", "|---|---|---|---|---|"]
    for p in plans:
        lines.append(f"| {p['cid']} | {p['verdict'].upper() if p['verdict'] == 'flagged' else p['verdict']} | "
                     f"{p.get('reason', '')} | {p.get('max_pan_speed', '')} | {p.get('warn', '')} |")
    if reqs:
        lines += ["", "## Re-render requests (rerender_requests.json)", ""]
        lines += [f"- **{r.get('cid') or r.get('file')}**: {r['why']}. {r.get('ask', '')}" for r in reqs]
    if spec_done:
        lines += ["", "Written into the spec: " + ", ".join(spec_done)]
    if dropped_co:
        lines += ["", "## Callouts left out of the vertical", ""]
        lines += [f"- {d['label']}: {d['why']}" for d in dropped_co]
    if dropped_el:
        lines += ["", "## Elements dropped to keep the screen simple", ""]
        lines += [f"- {d['kind']} '{d['what']}' at {d['rec_in']:.2f}s: {d['why']}" for d in dropped_el]
    lines += ["", "Pictures: `reframe_plan.jpg` (the window on the 16:9 frames, faces in yellow)"
              + (", `contact_sheet.jpg` (the rendered vertical, one tile per shot)" if a.render and rc == 0 else "")]
    (out_dir / "report.md").write_text("\n".join(lines) + "\n")
    shutil.rmtree(work, ignore_errors=True)
    print(f"[vertical] {', '.join(f'{k} {n}' for k, n in sorted(counts.items()))}; callouts kept {len(vcall)}, "
          f"dropped {len(dropped_co)}; elements dropped {len(dropped_el)} -> final/vertical/report.md")
    if rc:
        return rc
    return 3 if flagged else 0


if __name__ == "__main__":
    sys.exit(main())

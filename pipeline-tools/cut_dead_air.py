#!/usr/bin/env python3
"""cut_dead_air — cut the silences out of REAL footage (talking-head, phone walk-and-talk).

A wrapper on auto-editor (github.com/WyattBlue/auto-editor, the pip package in
~/.local/finish-env; it fetches its own static binary on first run). auto-editor decides
where the sound is; we keep the decision as data and render it ourselves:

  OUT.cuts.json   the keep ranges and an episode-style EDL (fps, size, duration, cuts[] with
                  id/src/in/len/start/frames, the same shape as final/edl_final.json), so
                  build-episode, color_match --film and anything else that reads our EDLs
                  can use the cut without re-deciding it.
  OUT.mp4         (with --render) the cut file: frame-exact trims, an 8 ms audio fade at
                  every join so cuts never click.
  --nle resolve|premiere|final-cut-pro|shotcut   also write auto-editor's timeline for an NLE.

Defaults keep speech natural: 0.25 s kept before each sound (the breath in) and 0.40 s
after (the tail of the word and the breath out), silences shorter than 0.6 s are left
alone (that's a pause, not dead air), and sound blips shorter than 0.25 s don't count.

    ~/.local/finish-env/bin/python pipeline-tools/cut_dead_air.py IN.mov OUT [--render]
        [--threshold 0.04] [--margin 0.25,0.40] [--min-silence 0.6] [--min-sound 0.25]
        [--nle resolve] [--preview]

Never on AI or scored film audio: it judges by loudness, and music under picture is never
"dead air". Use it on recordings, before the edit.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

AE = Path.home() / ".local/finish-env/bin/auto-editor"
# auto-editor exits 0 and writes NOTHING when -o has the wrong extension for the export
# (e.g. v3 to "x.json"), so every export gets the extension it expects.
EXT = {"v3": ".v3", "resolve": ".fcpxml", "final-cut-pro": ".fcpxml", "premiere": ".xml",
       "shotcut": ".mlt", "kdenlive": ".kdenlive"}


def probe(path: Path) -> dict:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                        "stream=codec_type,width,height,avg_frame_rate:format=duration", "-of", "json", str(path)],
                       capture_output=True, text=True)
    d = json.loads(r.stdout or "{}")
    v = next((s for s in d.get("streams", []) if s.get("codec_type") == "video"), {})
    a = any(s.get("codec_type") == "audio" for s in d.get("streams", []))
    fr = v.get("avg_frame_rate", "30/1")
    fps = float(Fraction(fr)) if fr and fr != "0/0" else 30.0
    return {"w": v.get("width"), "h": v.get("height"), "fps": fps, "audio": a,
            "dur": float(d.get("format", {}).get("duration", 0) or 0)}


def auto_editor(src: Path, out: Path, a, fps: int, export: str) -> Path:
    out = out.with_suffix(EXT[export])
    edit = f"audio:threshold={a.threshold},mincut={a.min_silence}s,minclip={a.min_sound}s"
    lo, _, hi = a.margin.partition(",")
    margin = f"{float(lo)}s,{float(hi or lo)}s"
    cmd = [str(AE), str(src), "--edit", edit, "--margin", margin, "-fps", str(fps),
           "--export", export, "-o", str(out), "--no-open", "--progress", "none"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    made = [out] if out.is_file() else []
    if r.returncode or not made:
        sys.exit(f"auto-editor failed ({r.returncode}): {(r.stderr or r.stdout)[-600:]}\n  cmd: {' '.join(cmd)}")
    return made[-1]


def keep_ranges(v3: dict) -> list[tuple[float, float, float]]:
    """[(src_in, src_out, rec_in)] in seconds from an auto-editor v3 timeline."""
    tb = float(Fraction(v3["timebase"]))
    clips = v3["v"][0] if v3.get("v") and v3["v"][0] else v3["a"][0]
    out = []
    for c in clips:
        speed = float(c.get("speed", 1.0))
        if abs(speed - 1.0) > 1e-6:
            sys.exit("timeline has speed changes; this wrapper only cuts (frozen rule 4)")
        s = c["offset"] / tb; d = c["dur"] / tb
        out.append((s, s + d, c["start"] / tb))
    return out


def render(src: Path, keeps, out: Path, info: dict, crf: int) -> None:
    parts, labels = [], []
    fade = 0.008
    for i, (a, b, _) in enumerate(keeps):
        parts.append(f"[0:v]trim=start={a:.5f}:end={b:.5f},setpts=PTS-STARTPTS[v{i}]")
        lab = f"[v{i}]"
        if info["audio"]:
            parts.append(f"[0:a]atrim=start={a:.5f}:end={b:.5f},asetpts=PTS-STARTPTS,"
                         f"afade=t=in:d={fade},afade=t=out:st={max(0.0, b - a - fade):.5f}:d={fade}[a{i}]")
            lab += f"[a{i}]"
        labels.append(lab)
    n = len(keeps)
    tail = f"concat=n={n}:v=1:a={1 if info['audio'] else 0}[v]" + ("[a]" if info["audio"] else "")
    with tempfile.TemporaryDirectory() as d:
        g = Path(d) / "graph.txt"; g.write_text(";".join(parts) + ";" + "".join(labels) + tail)
        cmd = ["ffmpeg", "-v", "error", "-y", "-i", str(src), "-filter_complex_script", str(g), "-map", "[v]"]
        if info["audio"]:
            cmd += ["-map", "[a]", "-c:a", "aac", "-b:a", "192k"]
        cmd += ["-c:v", "libx264", "-crf", str(crf), "-preset", "medium", "-pix_fmt", "yuv420p",
                "-r", f"{info['fps']:.5f}", "-movflags", "+faststart", str(out)]
        r = subprocess.run(cmd, capture_output=True, text=True)
        if r.returncode:
            sys.exit(f"render failed: {r.stderr[-600:]}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("src"); ap.add_argument("out", help="output stem/path (OUT.cuts.json, OUT.mp4)")
    ap.add_argument("--threshold", default="0.04", help="loudness threshold (0-1 or e.g. -30dB)")
    ap.add_argument("--margin", default="0.25,0.40", help="seconds kept before,after each sound")
    ap.add_argument("--min-silence", type=float, default=0.6, help="shorter silences are kept (pauses)")
    ap.add_argument("--min-sound", type=float, default=0.25, help="shorter sounds are ignored (clicks)")
    ap.add_argument("--render", action="store_true", help="also write OUT.mp4, the cut file")
    ap.add_argument("--nle", choices=["resolve", "premiere", "final-cut-pro", "shotcut", "kdenlive"])
    ap.add_argument("--preview", action="store_true", help="print the stats only")
    ap.add_argument("--crf", type=int, default=14)
    a = ap.parse_args()
    if not AE.exists():
        sys.exit(f"auto-editor missing at {AE}")
    src = Path(a.src).expanduser().resolve()
    info = probe(src)
    if not info["audio"]:
        sys.exit("no audio stream: nothing to judge silence by")
    stem = Path(a.out).expanduser().resolve()
    stem = stem.with_suffix("") if stem.suffix in (".mp4", ".mov", ".json") else stem
    stem.parent.mkdir(parents=True, exist_ok=True)
    fps = max(1, round(info["fps"]))

    with tempfile.TemporaryDirectory() as d:
        v3 = json.loads(auto_editor(src, Path(d) / "tl", a, fps, "v3").read_text())
    keeps = keep_ranges(v3)
    # auto-editor applies mincut before the margins, so margins can leave 1-2 frame gaps:
    # a jump cut that removes nothing. Any gap shorter than --min-silence is a pause; keep it.
    merged = []
    for s_in, s_out, _ in keeps:
        if merged and s_in - merged[-1][1] < a.min_silence:
            merged[-1][1] = s_out
        else:
            merged.append([s_in, s_out])
    rec, keeps = 0.0, []
    for s_in, s_out in merged:
        keeps.append((s_in, s_out, rec)); rec += s_out - s_in
    if not keeps:
        sys.exit("auto-editor kept nothing (all silent at this threshold)")
    kept = sum(b - a_ for a_, b, _ in keeps)
    cuts = []
    for i, (s_in, s_out, rec) in enumerate(keeps):
        cuts.append({"id": f"k{i:03d}", "src": str(src), "in": round(s_in, 4), "len": round(s_out - s_in, 4),
                     "frames": int(round((s_out - s_in) * fps)), "start": round(rec, 4), "section": "dead_air_cut"})
    doc = {"tool": "cut_dead_air (auto-editor)", "src": str(src), "fps": fps, "size": [info["w"], info["h"]],
           "duration": round(kept, 4), "source_duration": round(info["dur"], 4),
           "settings": {"threshold": a.threshold, "margin": a.margin, "min_silence": a.min_silence,
                        "min_sound": a.min_sound},
           "keep": [[round(x, 4), round(y, 4)] for x, y, _ in keeps], "cuts": cuts}
    removed = info["dur"] - kept
    gaps = [keeps[i + 1][0] - keeps[i][1] for i in range(len(keeps) - 1)]
    print(f"[dead_air] {src.name}: {info['dur']:.2f}s -> {kept:.2f}s (removed {removed:.2f}s, "
          f"{100 * removed / max(info['dur'], 1e-6):.1f}%) in {len(keeps)} pieces"
          + (f"; cut gaps {min(gaps):.2f}-{max(gaps):.2f}s" if gaps else ""))
    if a.preview:
        return 0
    cj = stem.with_name(stem.name + ".cuts.json"); cj.write_text(json.dumps(doc, indent=1))
    print(f"  timeline -> {cj}")
    if a.nle:
        nle = auto_editor(src, stem.with_name(stem.name + f"_{a.nle}.x"), a, fps, a.nle)
        print(f"  {a.nle} timeline -> {nle}")
    if a.render:
        mp4 = stem.with_suffix(".mp4")
        if mp4 == src:
            sys.exit("refusing to overwrite the input")
        render(src, keeps, mp4, info, a.crf)
        got = probe(mp4)["dur"]
        print(f"  cut file -> {mp4} ({got:.2f}s, timeline says {kept:.2f}s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

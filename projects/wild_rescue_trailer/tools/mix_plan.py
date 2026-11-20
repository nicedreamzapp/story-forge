#!/usr/bin/env python3
"""Writes sfx/mix_plan.json for bin/surround-mix (schema: tools/surround_mix.py docstring). Paths relative to sfx/.
Adapted from last_signal. Surround design: the wagon thunders past front -> right side -> rear with doppler; the train
whistle sweeps left -> right across the front (doppler); the ant swarm surrounds the room (spread + a slow circle);
dialogue sits in Center. Score split L/R into the front pair + a quieter rear pair. The DEAD STOP (Hank's line + Doug's
answer) clears score and effects except the canyon wind; the BLACK is 1.0 s of true silence, then the title hit.
Static gains only (bin/surround-mix --no-loudnorm). Usage: mix_plan.py <score number>"""
import json, sys
import numpy as np, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent; S = P / "sfx"
e = json.load(open(P / "final/edl_final.json")); cut = {c["id"]: c["start"] for c in e["cuts"]}
END = {c["id"]: c["start"] + c["len"] for c in e["cuts"]}
STOP0, STOP1, B, TT = cut["c05a_hank"], cut["c06a_ground"], cut["c08_black"], cut["c09_title"]
DUR = e["duration"]
score = sys.argv[1] if len(sys.argv) > 1 else "1"
vc = json.load(open(P / "voices/voice_check.json"))
def words(line): return vc["takes"][vc["best"][line]]["words"]
y, sr = sf.read(P / f"music/arranged/score_{score}_arranged.wav")
# static duck under Doug's whisper-quiet first line (it plays over the night score): -8 dB, 80 ms ramps
w0 = words("doug1"); t = np.arange(len(y)) / sr
d1s = cut["c01e_ditch"] + 0.04; d1e = d1s + (w0[-1]["e"] - w0[0]["s"] if w0 else 1.2) + 0.25; rmp = 0.08
g = 1 - (1 - 10 ** (-8 / 20)) * np.clip(np.minimum((t - d1s + rmp) / rmp, (d1e + rmp - t) / rmp), 0, 1)
y = y * g[:, None]
# the swell (written static gain curve, not a compressor): the reveal climbs -2 -> +1 dB, the ramp +1 -> +6 dB into the black
# (first mix 10:45: the ramp sat flat at ~-15 dB, quieter than the theme)
R0, R1, R2 = cut["c06a_ground"], cut["c07a_bridge"], B
sw = np.interp(t, [R0, R1, R2], [-2.0, 1.0, 6.0]) * ((t >= R0) & (t < R2))
y = y * (10 ** (sw / 20))[:, None]
sf.write(S / "score_L.wav", y[:, 0], sr, subtype="PCM_24"); sf.write(S / "score_R.wav", y[:, 1], sr, subtype="PCM_24")
def flen(f):
    i = sf.info(str(S / f)); return i.frames / i.samplerate
src = []
MASTER_DB = -3.0
def add(name, file, start, gain, stop_ok=False, **kw):
    d = {"name": name, "file": file, "start": round(start, 4), "gain_db": round(gain + MASTER_DB, 2)}; d.update(kw)
    if not d.get("dialog") and not d.pop("timeline", False):
        t0 = d.get("trim", [0])[0] if d.get("trim") else 0
        end = start + flen(file) - t0
        wins = [(B, TT)] + ([] if stop_ok else [(STOP0, STOP1)])
        for a, b in wins:
            if start < a < end:
                d["trim"] = [t0, round(t0 + (a - start), 4)]; d["fade_out"] = max(d.get("fade_out", 0.005), 0.04); end = a
    src.append(d)
V = "../voices/"
# ---- score
add("score_FL", "score_L.wav", 0, -4.0, timeline=True, position={"azimuth": -30, "distance": 1}, lfe=0.12)
add("score_FR", "score_R.wav", 0, -4.0, timeline=True, position={"azimuth": 30, "distance": 1}, lfe=0.12)
add("score_RL", "score_L.wav", 0, -11.0, timeline=True, position={"azimuth": -110, "distance": 1})
add("score_RR", "score_R.wav", 0, -11.0, timeline=True, position={"azimuth": 110, "distance": 1})
# ---- numpy sub layer
add("sub_theme", "sub_theme.wav", cut["c03a_burst"], -3.0, lfe=1.0, position={"azimuth": 0, "distance": 1, "spread": 1.0})
add("sub_rumble", "sub_rumble.wav", cut["c06a_ground"], -5.0, lfe=1.0, position={"azimuth": 0, "distance": 1, "spread": 1.0})
add("sub_hits", "sub_hits.wav", 0, -3.5, timeline=True, lfe=0.9, position={"azimuth": 0, "distance": 1, "spread": 0.6})
add("title_sub", "title_sub.wav", TT, -3.0, lfe=1.0, position={"azimuth": 0, "distance": 1, "spread": 1.0})
jobs = {j["name"]: j for j in json.load(open(S / "jobs.json"))}
def at(n): return cut[jobs[n]["cut"]]
def has(n): return (S / f"{n}.wav").exists() and n not in json.load(open(S / "screen.json")).get("drop", [])
def A(name, gain, file=None, start=None, **kw):
    f = file or f"{name}.wav"
    if has(Path(f).stem): add(name, f, at(name) if start is None else start, gain, **kw)
# ---- beds
A("night_bed", -14.0, start=0.0, position={"azimuth": 0, "distance": 1, "spread": 1.0}, trim=[0, cut["c02a_rails"]], fade_out=0.15, fade_in=0.8)
A("wind_bed", -16.0, start=cut["c04b_gap"], stop_ok=True, position={"azimuth": 0, "distance": 1, "spread": 1.0}, fade_in=0.4,
  trim=[0, cut["c06a_ground"] - cut["c04b_gap"] + 0.3], fade_out=0.4)
# ---- origin
A("forest_sniff", -10.0, position={"azimuth": 0, "distance": 1.5, "spread": 0.3})
A("lantern_tumble", -6.0, position={"azimuth": -15, "distance": 1.5, "spread": 0.2})
# ---- the call
A("rails_scream", -4.0, lfe=0.3, path=[{"t": 0, "azimuth": -60, "distance": 3}, {"t": 0.8, "azimuth": 40, "distance": 2}], doppler=True)
A("rabbit_thump", -3.0, lfe=0.3, position={"azimuth": 0, "distance": 1})
A("hawk_cry", -5.0, position={"azimuth": 10, "distance": 2, "spread": 0.3})
A("prairie_whistle", -6.0, position={"azimuth": -10, "distance": 1.5})
# ---- the theme: barn doors burst on the cut, the wagon thunders past front -> right -> rear
A("barn_burst", -3.0, start=cut["c03a_burst"] - 0.05, lfe=0.5, position={"azimuth": 0, "distance": 2, "spread": 0.5})
A("boom_theme", -4.0, start=cut["c03a_burst"], lfe=0.8, position={"azimuth": 0, "distance": 1, "spread": 0.8})
A("wagon_thunder", -2.0, lfe=0.5, doppler=True, doppler_scale=0.5,
  path=[{"t": 0, "azimuth": 0, "distance": 12}, {"t": 0.9, "azimuth": 25, "distance": 3}, {"t": 1.6, "azimuth": 90, "distance": 1.0},
        {"t": 2.4, "azimuth": 160, "distance": 5}, {"t": 3.2, "azimuth": 180, "distance": 14}])
A("wheel_roll", -4.0, lfe=0.3, path=[{"t": 0, "azimuth": -40, "distance": 2}, {"t": 0.9, "azimuth": 70, "distance": 1.2}])
A("team_gallop", -4.0, lfe=0.3, position={"azimuth": 0, "distance": 2, "spread": 0.5})
A("water_slosh", -5.0, path=[{"t": 0, "azimuth": 40, "distance": 3}, {"t": 1.2, "azimuth": -40, "distance": 3}])
# ---- stakes
A("train_chug", -5.0, lfe=0.3, position={"azimuth": 0, "distance": 4, "spread": 0.4})
A("canyon_wind", -7.0, stop_ok=True, position={"azimuth": 0, "distance": 1, "spread": 0.9})
# ---- reveal: the ants surround the room (a slow circle + spread)
A("ground_moves", -5.0, position={"azimuth": 0, "distance": 1, "spread": 0.8})
A("ant_swarm", -3.0, lfe=0.2, path=[{"t": 0, "azimuth": 0, "distance": 1.2, "spread": 0.7}, {"t": 1.0, "azimuth": 120, "distance": 1.2, "spread": 0.8},
                                     {"t": 2.0, "azimuth": 240, "distance": 1.2, "spread": 0.8}, {"t": 3.0, "azimuth": 360, "distance": 1.2, "spread": 0.8}])
A("ant_march", -6.0, position={"azimuth": 0, "distance": 1, "spread": 0.3})
# ---- ramp
A("riser", -9.0, start=cut["c07a_bridge"] - 1.0, position={"azimuth": 0, "distance": 1, "spread": 0.9}, fade_in=0.5)
A("bridge_lock", -4.0, position={"azimuth": 0, "distance": 1, "spread": 0.9})
A("elephant_trumpet", -3.0, position={"azimuth": -20, "distance": 2, "spread": 0.3})
A("train_whistle", -4.0, path=[{"t": 0, "azimuth": -70, "distance": 6}, {"t": 0.8, "azimuth": 0, "distance": 2}, {"t": 1.6, "azimuth": 70, "distance": 6}], doppler=True)
A("whistle_long", -10.0, start=cut["c07d_whistle"] + 0.6, doppler=True,
  path=[{"t": 0, "azimuth": -40, "distance": 5}, {"t": 1.5, "azimuth": 40, "distance": 3}, {"t": 3.0, "azimuth": 120, "distance": 10}])
A("cab_rattle", -6.0, position={"azimuth": 0, "distance": 1, "spread": 0.4})
A("ants_link", -4.0, position={"azimuth": 0, "distance": 1, "spread": 0.8})
A("wheels_edge", -3.0, lfe=0.4, position={"azimuth": 0, "distance": 1.5, "spread": 0.4})
A("whoosh_1", -5.0, start=cut["c07i_rush"] - 0.25, path=[{"t": 0, "azimuth": 0, "distance": 4}, {"t": 0.8, "azimuth": 0, "distance": 0.6}])
A("smash_hit", -2.0, start=B - 0.06, lfe=0.6, position={"azimuth": 0, "distance": 1, "spread": 0.8})
# ---- title + button
A("title_boom", -3.0, start=TT, lfe=0.8, position={"azimuth": 0, "distance": 1, "spread": 0.8})
A("salute_pop", -12.0, start=cut["c10a_ant_salute"] + 0.55, position={"azimuth": 0, "distance": 1})
# ---- voices: hard cuts land on the first word onset (frozen rule 32)
def onset(l): ws = words(l); return ws[0]["s"] if ws else 0
add("doug1", V + "doug1.wav", cut["c01e_ditch"] + 0.04 - onset("doug1"), -4.0, dialog=True)
# Hank's line is split onto his two mouth beats in R18 t1 (mouth_sync: 0.12-0.38 and 1.54-2.83 s of the clip, in-point 0.05):
# "Doug..." on the first open, "that's a big hole." on the second (frozen rule 9: density matched, never a closed mouth voiced)
hw = words("hank1"); hy, hsr = sf.read(P / "voices/hank1.wav")
cutp = int(((hw[0]["e"] + hw[1]["s"]) / 2) * hsr) if len(hw) > 1 else len(hy)
fd = int(0.02 * hsr); a_ = hy[:cutp].copy(); b_ = hy[cutp:].copy()
a_[-fd:] *= np.linspace(1, 0, fd); b_[:fd] *= np.linspace(0, 1, fd)
sf.write(P / "voices/hank1a.wav", a_, hsr, subtype="PCM_24"); sf.write(P / "voices/hank1b.wav", b_, hsr, subtype="PCM_24")
add("hank1", V + "hank1a.wav", cut["c05a_hank"] + (0.12 - 0.05) - hw[0]["s"], -1.0, dialog=True)
b_on = (hw[1]["s"] - cutp / hsr) if len(hw) > 1 else 0
add("hank1b", V + "hank1b.wav", cut["c05a_hank"] + (1.54 - 0.05) - b_on, -1.0, dialog=True)
add("doug2", V + "doug2.wav", cut["c05b_doug"] + 0.04 - onset("doug2"), -1.5, dialog=True)
plan = {"sample_rate": 48000, "duration": DUR, "tail": 0, "master": {"lufs_51": None, "lufs_stereo": None, "ceiling_db": -1.0}, "sources": src}
json.dump(plan, open(S / "mix_plan.json", "w"), indent=1)
print(len(src), "sources; doug1 at", round(cut["c01e_ditch"] + 0.04, 2), "hank1 at", round(cut["c05a_hank"] + 0.25, 2), "doug2 at", round(cut["c05b_doug"] + 0.04, 2))

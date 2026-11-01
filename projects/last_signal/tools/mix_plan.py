#!/usr/bin/env python3
"""Writes sfx/mix_plan.json for bin/surround-mix (schema: tools/surround_mix.py docstring). Paths relative to sfx/.
Surround design: the ship arrival sweeps front -> overhead -> rear with doppler and a heavy LFE send (plus our numpy
25-40 Hz swell, LFE 1.0); the planet voice is a full-room wash (spread 1.0 = all five speakers); the ship computer
and the captain's whisper are dialog (Center). The score is split L/R into front pair + a quieter rear pair for
envelopment. Dead stop (welcome -> ramp) and the black (1 s of silence, then the whisper) are enforced by clamping
every non-dialog source so nothing crosses into them. Static gains only (no loudnorm, --no-loudnorm)."""
import json, sys
import numpy as np, soundfile as sf
from pathlib import Path
P = Path(__file__).resolve().parent.parent; S = P / "sfx"
e = json.load(open(P / "final/edl_final.json")); cut = {c["id"]: c["start"] for c in e["cuts"]}
W, R, B, TT = cut["c09_welcome"], cut["c10_second_sun"], cut["c17_black"], cut["c18_title"]
DUR = e["duration"]
score = sys.argv[1] if len(sys.argv) > 1 else "1"
vc = json.load(open(P / "voices/voice_check.json"))
def words(name): return vc["takes"][vc["best"][name]]["words"]
# split the arranged score into L/R mono stems
y, sr = sf.read(P / f"music/arranged/score_{score}_arranged.wav")
# static duck under "Uncharted." (the only line that plays over score): -7 dB from 1.50 to 2.45 s, 60 ms ramps
t = np.arange(len(y)) / sr; t0, t1, rmp = cut["c02a_cockpit"], cut["c02a_cockpit"] + 0.95, 0.06
g = 1 - (1 - 10 ** (-7 / 20)) * np.clip(np.minimum((t - t0 + rmp) / rmp, (t1 + rmp - t) / rmp), 0, 1)
y = y * g[:, None]
sf.write(S / "score_L.wav", y[:, 0], sr, subtype="PCM_24"); sf.write(S / "score_R.wav", y[:, 1], sr, subtype="PCM_24")
def flen(f):
    i = sf.info(str(S / f) if not str(f).startswith("/") else f); return i.frames / i.samplerate
src = []
MASTER_DB = -3.0   # one static trim on every source: the first pass measured -10.8 LUFS stereo; this lands ~-14 (no loudnorm)
def add(name, file, start, gain, **kw):
    d = {"name": name, "file": file, "start": round(start, 4), "gain_db": round(gain + MASTER_DB, 2)}; d.update(kw)
    if not d.get("dialog") and not d.pop("timeline", False):   # full-length timeline tracks carry their own silences
        L = flen(file) - (d.get("trim", [0])[0] if d.get("trim") else 0)
        end = start + L
        for w0, w1 in ((W, R), (B, TT)):        # never cross into the dead stop or the black
            if start < w0 < end:
                t0 = d.get("trim", [0, None])[0]
                d["trim"] = [t0, round(t0 + (w0 - start), 4)]; d["fade_out"] = max(d.get("fade_out", 0.005), 0.03)
                end = w0
    src.append(d)
V = "../voices/"
# ---- score
add("score_FL", "score_L.wav", 0, -4.0, timeline=True, position={"azimuth": -30, "distance": 1}, lfe=0.15)
add("score_FR", "score_R.wav", 0, -4.0, timeline=True, position={"azimuth": 30, "distance": 1}, lfe=0.15)
add("score_RL", "score_L.wav", 0, -11.0, timeline=True, position={"azimuth": -110, "distance": 1})
add("score_RR", "score_R.wav", 0, -11.0, timeline=True, position={"azimuth": 110, "distance": 1})
# ---- the beep (centre-front, a little spread), and our sub layers
add("beep", "beep_track.wav", 0, -13.0, timeline=True, position={"azimuth": 0, "distance": 1, "spread": 0.25})
A = cut["c04_arrival"]
add("sub_arrival", "sub_arrival.wav", A - 0.3, -3.0, lfe=1.0, position={"azimuth": 0, "distance": 1, "spread": 1.0})
add("sub_hits", "sub_hits.wav", 0, -5.0, timeline=True, trim=[0, B], fade_out=0.03, lfe=0.9, position={"azimuth": 0, "distance": 1, "spread": 0.6})
add("title_sub", "title_sub.wav", TT, -2.0, lfe=1.0, position={"azimuth": 0, "distance": 1, "spread": 1.0})
# ---- picture-synced MMAudio (each starts on its cut)
jobs = {j["name"]: j for j in json.load(open(S / "jobs.json"))}
def at(n): return jobs[n]["film_start"]
add("arrival_rumble", "arrival_rumble.wav", at("arrival_rumble"), -1.0, lfe=0.7, doppler=True, doppler_scale=0.6,
    path=[{"t": 0, "azimuth": 0, "distance": 30}, {"t": 2.2, "azimuth": 15, "distance": 5}, {"t": 3.2, "azimuth": 90, "distance": 0.8},
          {"t": 4.4, "azimuth": 170, "distance": 8}, {"t": 6.0, "azimuth": 180, "distance": 30}])
add("asteroids_flyby", "asteroids_flyby.wav", at("asteroids_flyby"), -6.0, lfe=0.3, doppler=True,
    path=[{"t": 0, "azimuth": 0, "distance": 25}, {"t": 1.3, "azimuth": 10, "distance": 3}, {"t": 2.2, "azimuth": 120, "distance": 6}, {"t": 4.5, "azimuth": 170, "distance": 30}])
add("cockpit_alarm", "cockpit_alarm.wav", at("cockpit_alarm"), -14.0, position={"azimuth": 0, "distance": 1, "spread": 0.7})
add("dive_thunder", "dive_thunder.wav", at("dive_thunder"), -5.0, lfe=0.4, position={"azimuth": 0, "distance": 2, "spread": 0.5})
add("claws_impact", "claws_impact.wav", at("claws_impact"), -1.0, lfe=0.8, path=[{"t": 0, "azimuth": 0, "distance": 6}, {"t": 0.6, "azimuth": 0, "distance": 0.9}, {"t": 1.6, "azimuth": 0, "distance": 1.0}])
add("monolith_reveal", "monolith_reveal.wav", at("monolith_reveal"), -7.0, position={"azimuth": 0, "distance": 1, "spread": 0.6})
add("crew_walk", "crew_walk.wav", at("crew_walk"), 0.0, position={"azimuth": 0, "distance": 1.5})
add("handwriting_glow", "handwriting_glow.wav", at("handwriting_glow"), -9.0, position={"azimuth": 0, "distance": 1, "spread": 0.3})
add("lightwave_whoosh", "lightwave_whoosh.wav", at("lightwave_whoosh"), -3.0, lfe=0.4,
    path=[{"t": 0, "azimuth": 0, "distance": 4}, {"t": 0.9, "azimuth": 120, "distance": 3}, {"t": 1.8, "azimuth": 240, "distance": 3}, {"t": 2.6, "azimuth": 360, "distance": 4}])
add("second_sun", "second_sun.wav", at("second_sun"), -6.0, position={"azimuth": 0, "distance": 1, "spread": 0.5})
add("yanked", "yanked.wav", at("yanked"), -4.0, path=[{"t": 0, "azimuth": 0, "distance": 2}, {"t": 1.0, "azimuth": -150, "distance": 15}])
add("engines_explosion", "engines_explosion.wav", at("engines_explosion"), -2.0, lfe=0.7, position={"azimuth": 0, "distance": 1, "spread": 0.5})
add("creature_rise", "creature_rise.wav", at("creature_rise"), -3.0, lfe=0.8, position={"azimuth": 0, "distance": 3, "spread": 0.7})
add("glass_crack", "glass_crack.wav", at("glass_crack"), 0.0, position={"azimuth": 0, "distance": 1, "spread": 0.3})
add("ship_grab", "ship_grab.wav", at("ship_grab"), -2.0, lfe=0.6, path=[{"t": 0, "azimuth": -40, "distance": 4}, {"t": 2.5, "azimuth": 40, "distance": 4}])
# ---- designed hits (text-mode MMAudio)
add("riser_into_arrival", "riser_4s.wav", A - 4.0, -9.0, position={"azimuth": 0, "distance": 1, "spread": 0.8}, fade_in=0.5)
add("braam", "braam.wav", A, -2.0, lfe=0.6, position={"azimuth": 0, "distance": 1, "spread": 0.7})
add("boom_arrival", "boom_1.wav", A, -3.0, lfe=0.9, position={"azimuth": 0, "distance": 1, "spread": 0.8})
for c in e["cuts"]:
    if c["section"] == "ramp":
        add(f"horn_{c['id']}", "horn_hit.wav", c["start"], -3.0, trim=[0, 0.9], fade_out=0.2, position={"azimuth": 0, "distance": 1, "spread": 0.6})
add("scream", "scream.wav", cut["c16_05_scream"], -9.0, position={"azimuth": 0, "distance": 1.5, "spread": 0.5}, fade_out=0.2)   # the crewmate's scream under the strobe (R20 on screen 4x)
add("riser_into_black", "riser_4s.wav", B - 4.0, -8.0, position={"azimuth": 0, "distance": 1, "spread": 0.9}, fade_in=0.8)   # riser_6s came back as white-noise hiss (flatness 0.45): not used
add("final_hit", "final_hit.wav", TT, -1.0, lfe=0.8, position={"azimuth": 0, "distance": 1, "spread": 0.8})
add("boom_title", "boom_2.wav", TT, -3.0, lfe=0.9, position={"azimuth": 0, "distance": 1, "spread": 0.8})
# ---- voices: onsets on the words
wc = words("computer")[0]["s"] if words("computer") else 0
add("computer", V + "computer.wav", cut["c02a_cockpit"] + 0.12 - wc, -2.0, dialog=True)
wp = words("planet")[0]["s"] if words("planet") else 0
add("planet", V + "planet.wav", W + 0.55 - wp, -1.0, lfe=0.12, position={"azimuth": 0, "distance": 1, "spread": 1.0})
wk = words("captain")[0]["s"] if words("captain") else 0
add("captain", V + "captain.wav", B + 1.0 - wk, -1.0, dialog=True)
plan = {"sample_rate": 48000, "duration": DUR, "tail": 0, "master": {"lufs_51": None, "lufs_stereo": None, "ceiling_db": -1.0},
        "sources": src}
json.dump(plan, open(S / "mix_plan.json", "w"), indent=1)
print(len(src), "sources; computer at", round(cut["c02a_cockpit"] + 0.12, 2), "planet at", round(W + 0.55, 2), "captain at", round(B + 1.0, 2))

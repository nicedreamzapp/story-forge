#!/usr/bin/env python3
"""make_episode.py — one command for a painted Hank & Doug episode, driven by shots.json.
  python3 make_episode.py [shots.json] [--stage stills|voices|music|clips|finish|all]
Stages are resumable (existing outputs are skipped). Real times go to times.txt.
  stills : every shot's still in ONE krea_batch.py run (one model load)
  voices : character_voice.py per line (+ the wild_rescue voice_fx: Hank -1.5 st + 160 Hz shelf, Doug +2 dB at 3 kHz),
           joined per shot with head/tail gaps -> voice/<shot>.wav
  music  : instrumental bed from the local Song Forge (promo_music.py), only when jobs_running == 0
  clips  : make-ltx25 per shot (a2v with the shot wav for talking Hank/Doug shots, distilled i2v otherwise)
  finish : 1920x1080 upscale, our own dialogue on top (never LTX's), ambience from LTX on wide shots, music bed,
           concat -> film.mp4 + manifest.json for film_qc
"""
import json, os, re, subprocess, sys, time, urllib.request
from pathlib import Path

D = Path(__file__).resolve().parent
SF = Path.home() / "Desktop/PROJECTS/story-forge"
KREA = SF / "projects/wild_rescue_trailer/tools/v4/krea_batch.py"
LTX = SF / "bin/make-ltx25"
CV = Path.home() / "AI/videopipe/bin/character_voice.py"
CBPY = Path.home() / "chatterbox-env/bin/python"
FF = "/opt/homebrew/bin/ffmpeg"
argv = sys.argv[1:]
if "--stage" in argv: i = argv.index("--stage"); del argv[i:i + 2]
args = [a for a in argv if not a.startswith("--")]
SPEC = json.load(open(args[0] if args else D / "shots.json"))
STAGE = sys.argv[sys.argv.index("--stage") + 1] if "--stage" in sys.argv else "all"
for sub in ("stills", "voice", "clips", "music", "build"):
    (D / sub).mkdir(exist_ok=True)

def log(msg):
    line = f"{time.strftime('%H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(D / "times.txt", "a") as f: f.write(line + "\n")

def sh(cmd, **kw):
    return subprocess.run(cmd, check=True, **kw)

def dur(p):
    return float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                capture_output=True, text=True).stdout.strip())

def songforge_busy():
    try:
        return json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5)).get("jobs_running", 0) > 0
    except Exception:
        return False

def wait_songforge():
    while songforge_busy():
        log("Song Forge busy, waiting"); time.sleep(20)

def fill(text):
    for k, v in SPEC["chars"].items():
        text = re.sub(rf"\b{k}\b", v, text)
    return text

def stills():
    t = time.time()
    jobs = [{"out": str(D / "stills" / f"{s['id']}.png"), "w": 1344, "h": 768, "seed": 1101,
             "prompt": SPEC["style"] + " " + fill(s["still"]) + " Wide cinematic composition."} for s in SPEC["shots"]]
    json.dump(jobs, open(D / "stills/jobs.json", "w"), indent=1)
    wait_songforge()
    sh(["python3", str(KREA), str(D / "stills/jobs.json")], cwd=D / "stills")
    log(f"stills done in {time.time() - t:.0f}s")

FX = {"HANK": "asetrate=24000*0.917,aresample=24000,atempo=1.0905,lowshelf=f=160:g=3",
      "DOUG": "highshelf=f=3000:g=2"}

def voices():
    t = time.time()
    for s in SPEC["shots"]:
        out = D / "voice" / f"{s['id']}.wav"
        if out.exists() or not s["lines"]: continue
        parts = []
        for i, (who, line) in enumerate(s["lines"]):
            raw = D / "voice" / f"{s['id']}_{i}_{who}_raw.wav"
            fx = D / "voice" / f"{s['id']}_{i}_{who}.wav"
            if not raw.exists():
                sh([str(CBPY), str(CV), "--character", SPEC["voices"][who], "--line", line, "--out", str(raw)],
                   cwd=CV.parent, capture_output=True)
            af = "silenceremove=start_periods=1:start_threshold=-45dB,areverse,silenceremove=start_periods=1:start_threshold=-45dB,areverse"
            if who in FX: af += "," + FX[who]
            sh([FF, "-v", "error", "-y", "-i", str(raw), "-af", af + ",aresample=48000", "-ac", "1", str(fx)])
            parts.append(fx)
        # 0.3 s head, 0.4 s between speakers, 0.5 s tail
        inputs, filt = [], []
        sil = lambda d, n: f"anullsrc=r=48000:cl=mono,atrim=duration={d}[{n}]"
        chain = ["[h]"]
        filt.append(sil(0.3, "h"))
        for i, p in enumerate(parts):
            inputs += ["-i", str(p)]
            chain.append(f"[{i}:a]")
            if i < len(parts) - 1:
                filt.append(sil(0.4, f"g{i}")); chain.append(f"[g{i}]")
        filt.append(sil(0.5, "t")); chain.append("[t]")
        fc = ";".join(filt) + ";" + "".join(chain) + f"concat=n={len(chain)}:v=0:a=1[o]"
        sh([FF, "-v", "error", "-y", *inputs, "-filter_complex", fc, "-map", "[o]", "-ar", "48000", str(out)])
        log(f"voice {s['id']} {dur(out):.2f}s")
    log(f"voices done in {time.time() - t:.0f}s")

def shot_len(s):
    w = D / "voice" / f"{s['id']}.wav"
    if s["a2v"]: return max(dur(w), 97 / 24)
    return max(s["dur"], dur(w) if w.exists() else 0)

def music():
    t = time.time()
    if (D / "music/bed.wav").exists(): return
    if songforge_busy(): log("music skipped: Song Forge busy"); return
    total = sum(shot_len(s) for s in SPEC["shots"])
    r = subprocess.run([str(CBPY), str(SF / "pipeline-tools/promo_music.py"), str(D), "--seconds", str(int(total + 10)),
                        "--style", SPEC.get("music", "gentle warm acoustic folk, soft fingerpicked guitar, light strings, hopeful, storybook adventure, instrumental, no vocals"),
                        "--out", "music/bed.wav"], capture_output=True, text=True)
    log(f"music rc={r.returncode} in {time.time() - t:.0f}s :: {(r.stdout + r.stderr)[-300:]}")

def clips():
    for s in SPEC["shots"]:
        out = D / "clips" / f"{s['id']}.mp4"
        if out.exists(): continue
        wait_songforge()
        t = time.time()
        cmd = ["python3", str(LTX), "--i2v", str(D / "stills" / f"{s['id']}.png"), "--res", SPEC["res"],
               "--seed", "11", "--label", f"hdp_{s['id']}", "--gb", "105"]
        if s["a2v"]:
            cmd += ["--audio", str(D / "voice" / f"{s['id']}.wav")]
        else:
            cmd += ["--duration", f"{shot_len(s):.2f}"]
            if s.get("ambience"): cmd.append("--keep-audio")
        cmd.append(fill(s["motion"]))
        r = subprocess.run(cmd, capture_output=True, text=True)
        m = re.search(r"done in [\d.]+s → (\S+)", r.stdout)
        if not m:
            log(f"clip {s['id']} FAILED: {r.stderr[-600:]}"); continue
        os.replace(m.group(1), out)
        log(f"clip {s['id']} {dur(out):.2f}s in {time.time() - t:.0f}s ({'a2v' if s['a2v'] else 'i2v'})")

def finish():
    t = time.time()
    segs, manifest, clock = [], {"film": str(D / "film.mp4"), "shots": [], "lines": []}, 0.0
    for s in SPEC["shots"]:
        c = D / "clips" / f"{s['id']}.mp4"
        if not c.exists(): log(f"finish: missing clip {s['id']}"); continue
        L = shot_len(s)
        v = D / "voice" / f"{s['id']}.wav"
        seg = D / "build" / f"{s['id']}.mp4"
        ins = ["-i", str(c)]
        mix = []
        if v.exists(): ins += ["-i", str(v)]; mix.append(f"[1:a]volume=1.0[va]")
        amb = s.get("ambience") and not s["a2v"]
        if amb: mix.append("[0:a]volume=0.35,highpass=f=80[am]")
        labels = (["[va]"] if v.exists() else []) + (["[am]"] if amb else [])
        if not labels:
            mix.append(f"anullsrc=r=48000:cl=stereo,atrim=duration={L}[sil]"); labels = ["[sil]"]
        fc = ";".join(mix) + ";" + "".join(labels) + f"amix=inputs={len(labels)}:normalize=0:duration=longest,apad,atrim=duration={L:.3f},aresample=48000,aformat=channel_layouts=stereo[a]"
        fc += f";[0:v]tpad=stop_mode=clone:stop_duration=2,trim=duration={L:.3f},scale=1920:1080:flags=lanczos,fps=24,setsar=1[v]"
        sh([FF, "-v", "error", "-y", *ins, "-filter_complex", fc, "-map", "[v]", "-map", "[a]",
            "-c:v", "h264_videotoolbox", "-b:v", "12M", "-c:a", "aac", "-b:a", "192k", str(seg)])
        segs.append(seg)
        manifest["shots"].append({"id": s["id"], "start": round(clock, 2), "end": round(clock + L, 2),
                                  "description": fill(s["still"])[:300], "speaker": s["lines"][0][0] if s["lines"] and s["a2v"] else None})
        off = clock + 0.3
        for who, line in s["lines"]:
            manifest["lines"].append({"speaker": who, "text": line, "start": round(off, 2), "shot": s["id"]})
            off += 1.5
        clock += L
    lst = D / "build/list.txt"
    lst.write_text("".join(f"file '{p}'\n" for p in segs))
    body = D / "build/body.mp4"
    sh([FF, "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(body)])
    bed = D / "music/bed.wav"
    film = D / "film.mp4"
    if bed.exists():
        sh([FF, "-v", "error", "-y", "-i", str(body), "-i", str(bed), "-filter_complex",
            f"[1:a]volume=0.18,afade=t=in:d=1.5,afade=t=out:st={max(clock - 2.5, 0):.2f}:d=2.5,atrim=duration={clock:.3f}[m];[0:a][m]amix=inputs=2:normalize=0:duration=first[a]",
            "-map", "0:v", "-map", "[a]", "-c:v", "copy", "-c:a", "aac", "-b:a", "192k", str(film)])
    else:
        os.replace(body, film)
    json.dump(manifest, open(D / "manifest.json", "w"), indent=1)
    log(f"finish done in {time.time() - t:.0f}s -> {film} ({dur(film):.1f}s)")

STAGES = {"stills": stills, "voices": voices, "music": music, "clips": clips, "finish": finish}
for name in (STAGES if STAGE == "all" else [STAGE]):
    STAGES[name]()

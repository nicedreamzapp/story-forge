#!/usr/bin/env python3
"""Overnight judge-gated search for the Scene 2 wagon charge-out still.

Rolls candidates via the two viable recipes, judges every frame with
Qwen3-VL (in-process, loaded once), saves ONLY frames that pass all gates
to stills/s2_pass/. Safety: stops on Song Forge customer jobs, high swap,
low memory, or the attempt/time budget. Log: overnight_s2.log
"""
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
STILLS = HERE / "stills"
PASSDIR = STILLS / "s2_pass"
PASSDIR.mkdir(exist_ok=True)
LOG = open(HERE / "overnight_s2.log", "a")

MFLUX = Path.home() / "mflux-venv/bin/mflux-generate-flux2"
MODEL = "AITRADER/FLUX2-klein-9B-mlx-8bit"
HL = str(Path.home() / ".hankdoug_seeds/HANK_LORA.safetensors")
DL = str(Path.home() / ".hankdoug_seeds/DOUG_LORA.safetensors")

sys.path.insert(0, str(Path.home() / "Desktop/PROJECTS/story-forge/pipeline-tools"))
from film_qc import vl_ask, _state
_state["use_server"] = False


CANON = Path.home() / "Desktop/PROJECTS/story-forge/projects/circus_train/canon"

def make_compare(candidate, master, out):
    """Side-by-side sheet: locked master left, candidate right."""
    from PIL import Image, ImageDraw
    m = Image.open(master).convert("RGB")
    c = Image.open(candidate).convert("RGB")
    H = 480
    def fit(im):
        s = H / im.height
        return im.resize((int(im.width * s), H), Image.LANCZOS)
    m, c = fit(m), fit(c)
    sheet = Image.new("RGB", (m.width + c.width + 30, H + 40), (20, 20, 20))
    sheet.paste(m, (0, 40))
    sheet.paste(c, (m.width + 30, 40))
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "OFFICIAL CHARACTER (canon)", fill=(255, 255, 0))
    d.text((m.width + 40, 10), "CANDIDATE FRAME", fill=(0, 255, 255))
    sheet.save(out)
    return out

DOG_COMPARE_Q = ("The LEFT image is the official locked design of Doug the bloodhound. "
    "Look at the dog in the RIGHT image. Is it the SAME character drawn on-model: "
    "IDENTICAL ear shape (long, heavy, FLAT and smooth-hanging — not curly, not "
    "fluffy, not wavy), same dark-brown ear color, same orange-tan coat, same lanky "
    "build, same face style, no collar? Be strict about ear texture. Start YES or NO.")

BEAR_COMPARE_Q = ("The LEFT image is the official locked design of Hank the bear. "
    "Look at the bear in the RIGHT image. Is it the SAME character drawn on-model: "
    "same round head and small rounded ears, same light tan muzzle, same brown fuzzy "
    "coat with tan belly patch, same gentle face? Start YES or NO.")

MAX_ATTEMPTS = 40
DEADLINE = time.time() + 6 * 3600


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.write(line + "\n")
    LOG.flush()


def safe_to_continue():
    try:
        st = json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5))
        if int(st.get("jobs_running") or 0) > 0:
            log("Song Forge customer job running — pausing 5 min")
            time.sleep(300)
            return safe_to_continue()
    except Exception:
        pass
    out = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True).stdout
    m = re.search(r"used = ([\d.]+)M", out)
    if m and float(m.group(1)) > 45000:
        log(f"swap {m.group(1)}MB > 45GB — stopping for safety")
        return False
    out = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True).stdout
    m = re.search(r"free percentage:\s*(\d+)", out)
    if m and int(m.group(1)) < 15:
        log(f"free {m.group(1)}% < 15% — stopping for safety")
        return False
    return True


PROMPT_T2I = ("low angle three-quarter shot of a large rustic wooden fire-engine wagon "
              "charging toward the camera on a dirt forest road, hankbear a huge round "
              "brown bear with light tan muzzle and large tan belly patch gripping rope "
              "reins in the driver's seat, dougdog a TALL LANKY orange-tan bloodhound "
              "with very long heavy dark-brown floppy ears and droopy jowls, no collar, "
              "sitting upright on the bench a small distance from the bear, both large "
              "and clearly visible, two galloping horses at the lower left edge mostly "
              "out of view, a single long wooden hitch pole running from the wagon to "
              "the horses, ladder and water barrel strapped in the bed, dust clouds "
              "behind the wheels, mouths closed, heroic sense of speed, Pixar 3D "
              "animated movie style, golden afternoon light")

PROMPT_WELD = ("hankbear a huge round brown bear with light tan muzzle and tan belly "
               "patch holding rope reins, and a SEPARATE smaller animal, dougdog a tall "
               "lanky orange-tan bloodhound with very long heavy dark-brown floppy ears "
               "and droopy jowls, no collar, the bear and the dog seated apart from each "
               "other in the front of a large rustic wooden fire-engine wagon charging "
               "toward the camera on a dirt forest road, two galloping brown horses at "
               "the lower left pulling via a wooden hitch pole, ladder and water barrel "
               "in the bed, dust behind the wheels, mouths closed, Pixar 3D animated "
               "movie style, golden afternoon light")


def gen(out, seed, weld_strength=None):
    cmd = ["nice", "-n", "10", str(MFLUX), "-m", MODEL,
           "--lora-paths", HL, DL, "--lora-scales", "0.85", "1.0",
           "--guidance", "1.0", "--steps", "24", "--seed", str(seed),
           "--width", "832", "--height", "480", "--output", str(out)]
    if weld_strength:
        cmd += ["--image-path", str(STILLS / "s2_rough3.png"),
                "--image-strength", str(weld_strength), "--prompt", PROMPT_WELD]
    else:
        cmd += ["--prompt", PROMPT_T2I]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    return out.exists() and r.returncode == 0


GATES_TEXT = [
    ("anatomy", "This is a STYLIZED Pixar-style cartoon: round bodies, stubby limbs, "
                "oversized heads and simplified anatomy are INTENTIONAL design — do not "
                "penalize them. Only fail for CLEAR generation errors: extra or missing "
                "limbs, extra heads or eyes, two animals merged into one body, melted or "
                "warped faces, or duplicated extra wheels. Start PASS or FAIL."),
    ("natural", "Does the scene look like one naturally rendered animation frame — "
                "consistent light, believable contact, nothing pasted or floating? "
                "Start with PASS or FAIL."),
]


def judge(img):
    import tempfile
    for name, master, q in [("dog", CANON / "doug_canon.png", DOG_COMPARE_Q),
                            ("bear", CANON / "hank_canon.png", BEAR_COMPARE_Q)]:
        cmp_img = STILLS / f"_cmp_{name}.png"
        make_compare(img, master, cmp_img)
        a = vl_ask(str(cmp_img), q).strip()
        ok = re.match(r"^\W*YES", a, re.I)
        log(f"  gate {name}(vs canon): {'ok' if ok else 'FAIL'} — {a[:200].replace(chr(10),' ')}")
        if not ok:
            return False
    for name, q in GATES_TEXT:
        a = vl_ask(str(img), q).strip()
        ok = re.match(r"^\W*(YES|PASS)", a, re.I)
        log(f"  gate {name}: {'ok' if ok else 'FAIL'} — {a[:200].replace(chr(10),' ')}")
        if not ok:
            return False
    return True


def main():
    attempts, passed = 0, 0
    # re-judge kept fails first — already-rendered frames are free candidates
    faildir = STILLS / "s2_fail"
    if faildir.exists():
        for f in sorted(faildir.glob("*.png")):
            log(f"re-judging kept fail {f.name}")
            if judge(f):
                passed += 1
                f.rename(PASSDIR / f"s2_PASS_{passed:02d}_rejudged_{f.name}")
                log(f"  *** PASSED on re-judge")
            if passed >= 6:
                break
    plans = []
    seed = 7000
    while len(plans) < MAX_ATTEMPTS:
        plans.append(("t2i", seed, None))   # welds kept failing the dog gate — t2i only
        seed += 3
    for kind, s, strength in plans[:MAX_ATTEMPTS]:
        if time.time() > DEADLINE:
            log("time budget reached")
            break
        if not safe_to_continue():
            break
        attempts += 1
        out = STILLS / f"s2_try_{kind}_{s}.png"
        log(f"attempt {attempts}/{MAX_ATTEMPTS}: {kind} seed={s} strength={strength}")
        try:
            if not gen(out, s, strength):
                log("  generation failed")
                continue
        except Exception as e:
            log(f"  generation error: {e}")
            continue
        if judge(out):
            passed += 1
            dest = PASSDIR / f"s2_PASS_{passed:02d}_{kind}_{s}.png"
            out.rename(dest)
            log(f"  *** PASSED ALL GATES -> {dest.name}")
            if passed >= 6:
                log("6 passing candidates banked — done early")
                break
        else:
            faildir = STILLS / "s2_fail"
            faildir.mkdir(exist_ok=True)
            out.rename(faildir / out.name)
    log(f"DONE: {attempts} attempts, {passed} passed")


if __name__ == "__main__":
    main()

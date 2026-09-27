#!/usr/bin/env python3
"""Judge-gated still generation for Circus Train scenes 3-8 (+S2 top-up if empty).

Per scene: roll candidates (t2i, dual or single LoRA), judge every frame with
Qwen3-VL (loaded once), bank up to 2 passers per scene in stills/passes/<scene>/.
Safety: pauses for Song Forge customer jobs, stops on swap/memory limits.
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
LOG = open(HERE / "scenes_gen.log", "a")

MFLUX = Path.home() / "mflux-venv/bin/mflux-generate-flux2"
MODEL = "AITRADER/FLUX2-klein-9B-mlx-8bit"
HL = str(Path.home() / ".hankdoug_seeds/HANK_LORA.safetensors")
DL = str(Path.home() / ".hankdoug_seeds/DOUG_LORA_V2.safetensors")

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

DOG_COMPARE_Q = ("These are two renders of a cartoon character from an animation "
    "production. LEFT is the official design of Doug the bloodhound. RIGHT is a frame "
    "from the show. PAY CLOSEST ATTENTION TO THE EARS: the official ears hang straight "
    "down like heavy flat smooth leather straps, with clean simple outlines. Compare the "
    "RIGHT dog's ears: if they are puffy, fluffy, plush-textured, curly, wavy, ruffled, "
    "or wing outward from the head, answer NO. Also answer NO for: a collar, wrong coat "
    "color, or a clearly different face or body type. Normal variation in pose, angle, "
    "lighting and minor softness is acceptable. Would a viewer accept this as the same "
    "character? Start YES or NO.")

BEAR_COMPARE_Q = ("The LEFT image is the official locked design of Hank the bear. "
    "Look at the bear in the RIGHT image. Is it the SAME character drawn on-model: "
    "same round head and small rounded ears, same light tan muzzle, same brown fuzzy "
    "coat with tan belly patch, same gentle face? Start YES or NO.")

DOUG = ("dougdog a TALL LANKY orange-tan bloodhound dog with very long heavy "
        "dark-brown floppy ears and droopy jowls, no collar")
HANK = ("hankbear a huge round gentle brown bear with light tan muzzle and "
        "large tan belly patch")
STYLE = "Pixar 3D animated movie style"

DOG_GATE = ("Describe the dog. Is it a TALL LANKY bloodhound with VERY LONG heavy "
            "dark-brown floppy ears, droopy jowls, and NO collar? Start YES or NO.")
BEAR_GATE = ("Does the bear have a round head, small rounded ears, light tan muzzle, "
             "and look like a gentle round brown bear (not deformed, not dog-like)? "
             "Start YES or NO.")
ANATOMY_GATE = ("This is a STYLIZED Pixar-style cartoon: round bodies, stubby limbs, "
                "oversized heads and simplified anatomy are INTENTIONAL design — do not "
                "penalize them. Only fail for CLEAR generation errors: extra or missing "
                "limbs, extra heads or eyes, two animals merged into one body, melted or "
                "warped faces, or duplicated extra wheels. Start PASS or FAIL.")
NATURAL_GATE = ("Is this one naturally rendered animation frame — consistent lighting, "
                "believable ground contact, nothing floating or pasted? Start PASS or FAIL.")

SCENES = {
    "s2_rollout": {
        "loras": "both",
        "prompt": f"low angle three-quarter shot of a large rustic wooden fire-engine "
                  f"wagon charging toward the camera on a dirt forest road, {HANK} "
                  f"gripping rope reins in the driver's seat, {DOUG} sitting upright on "
                  f"the bench a small distance from the bear, both large and clearly "
                  f"visible, two galloping horses at the lower left edge mostly out of "
                  f"view, a single wooden hitch pole running from wagon to horses, ladder "
                  f"and water barrel strapped in the bed, dust clouds behind the wheels, "
                  f"mouths closed, heroic sense of speed, {STYLE}, golden afternoon light",
        "extra": [("wagon", "Is there a wooden wagon in motion with dust and at least "
                            "one horse pulling it? Start YES or NO.")],
    },
    "s3_arrival": {
        "loras": "both",
        "prompt": f"a stopped circus train of colorful wooden animal-cage train cars "
                  f"sitting on rails in bright hot midday sun, heat shimmer, worried "
                  f"animal faces peeking between the wooden slats, {HANK} and {DOUG} "
                  f"arriving in the foreground looking up at the train, standing apart "
                  f"from each other, mouths closed, {STYLE}, harsh noon light, wide shot",
        "extra": [("train", "Is there a stopped circus train with wooden cars and rails "
                            "clearly visible? Start YES or NO.")],
    },
    "s4_problem": {
        "loras": "doug",
        "prompt": f"{DOUG}, standing close to a heavy wooden circus train car door, "
                  f"inspecting a big jammed iron latch pin on the door, one paw raised "
                  f"toward the pin, a large gentle elephant eye visible through the gap "
                  f"between wooden slats, mouth closed, {STYLE}, harsh noon light, "
                  f"medium shot",
        "extra": [("pin", "Is the dog examining a latch on a wooden train car door? Start YES or NO.")],
        "skip_bear": True,
    },
    "s5_doug_moment": {
        "loras": "doug",
        "prompt": f"{DOUG}, pressing his nose gently to the crack of a heavy wooden "
                  f"circus train car door, ears hanging forward, focused and kind "
                  f"expression, mouth closed, warm dusty light rays, {STYLE}, "
                  f"medium close shot from the side",
        "extra": [("door", "Is the dog's nose near the crack or edge of a wooden door? "
                           "Start YES or NO.")],
        "skip_bear": True,
    },
    "s6_hank_moment": {
        "loras": "hank",
        "prompt": f"{HANK}, driving his shoulder hard into a heavy wooden circus train "
                  f"car door, pushing with all his strength, straining pose, wood "
                  f"starting to give with small splinters and dust, mouth closed, "
                  f"{STYLE}, harsh noon light, dynamic medium shot",
        "extra": [("push", "Is the bear pushing its shoulder into a wooden door with "
                           "visible effort? Start YES or NO.")],
        "skip_dog": True,
    },
    "s7_cooldown": {
        "loras": "both",
        "prompt": f"a joyful scene beside a circus train: a tall giraffe standing like "
                  f"a ladder, an elephant spraying a fan of water from its trunk, "
                  f"circus animals cooling off happily, a small green turtle floating "
                  f"on its back in a wooden water tank, {HANK} and {DOUG} standing "
                  f"together at one side watching proudly, standing apart from each "
                  f"other, water sparkle, {STYLE}, bright afternoon light, wide shot",
        "extra": [("water", "Is an elephant spraying water and a turtle floating in a tank? Start YES or NO.")],
    },
    "s8_pawbump": {
        "loras": "both",
        "prompt": f"{HANK} and {DOUG} facing each other and touching front paws in a "
                  f"triumphant paw bump, a clear gap of sky visible between their "
                  f"bodies, a small cheerful blue bird perched on top of the bear's "
                  f"head, golden sunset light, circus train and happy animals blurred "
                  f"in the background, mouths closed, {STYLE}, medium wide shot",
        "extra": [("bump", "Are the bear and dog raising front paws toward each other, with a small bird on the bear's head? Start YES or NO.")],
    },
}

MAX_PER_SCENE = 20
WANT_PER_SCENE = 2


def log(msg):
    line = f"[{time.strftime('%H:%M:%S')}] {msg}"
    print(line, flush=True)
    LOG.write(line + "\n")
    LOG.flush()


def safe():
    try:
        st = json.load(urllib.request.urlopen("http://127.0.0.1:8767/api/status", timeout=5))
        if int(st.get("jobs_running") or 0) > 0:
            log("forge customer job — pausing 5 min")
            time.sleep(300)
            return safe()
    except Exception:
        pass
    out = subprocess.run(["memory_pressure", "-Q"], capture_output=True, text=True).stdout
    m = re.search(r"free percentage:\s*(\d+)", out)
    if m and int(m.group(1)) < 12:
        log("memory pressure — stop")
        return False
    return True


def gen(scene, spec, seed, out):
    loras, scales = [], []
    if spec["loras"] in ("both", "hank"):
        loras.append(HL); scales.append("0.85")
    if spec["loras"] in ("both", "doug"):
        loras.append(DL); scales.append("1.0")
    cmd = ["nice", "-n", "10", str(MFLUX), "-m", MODEL,
           "--lora-paths", *loras, "--lora-scales", *scales,
           "--guidance", "1.0", "--steps", "24", "--seed", str(seed),
           "--width", "832", "--height", "480", "--output", str(out),
           "--prompt", spec["prompt"]]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    return out.exists() and r.returncode == 0


def judge(img, spec):
    pairs = []
    if not spec.get("skip_dog"):
        pairs.append(("dog", CANON / "doug_canon.png", DOG_COMPARE_Q))
    if not spec.get("skip_bear"):
        pairs.append(("bear", CANON / "hank_canon.png", BEAR_COMPARE_Q))
    for name, master, q in pairs:
        cmp_img = STILLS / f"_cmp_{name}.png"
        make_compare(img, master, cmp_img)
        a = vl_ask(str(cmp_img), q).strip()
        ok = re.match(r"^\W*YES", a, re.I)
        log(f"    {name}(vs canon): {'ok' if ok else 'FAIL'} — {a[:200].replace(chr(10),' ')}")
        if not ok:
            return False
    for name, q in [("anatomy", ANATOMY_GATE), ("natural", NATURAL_GATE)] + spec.get("extra", []):
        a = vl_ask(str(img), q).strip()
        ok = re.match(r"^\W*(YES|PASS)", a, re.I)
        log(f"    {name}: {'ok' if ok else 'FAIL'} — {a[:200].replace(chr(10),' ')}")
        if not ok:
            return False
    return True


def main():
    for scene, spec in SCENES.items():
        passdir = STILLS / "passes" / scene
        passdir.mkdir(parents=True, exist_ok=True)
        have = len(list(passdir.glob("*.png")))
        if have >= WANT_PER_SCENE:
            log(f"{scene}: already has {have} — skip")
            continue
        log(f"=== {scene} ===")
        seed = abs(hash(scene)) % 9000 + 20100
        for i in range(MAX_PER_SCENE):
            if not safe():
                return
            out = STILLS / f"{scene}_try{i}.png"
            log(f"  attempt {i+1}/{MAX_PER_SCENE} seed={seed + i * 7}")
            try:
                if not gen(scene, spec, seed + i * 7, out):
                    log("    gen failed")
                    continue
            except Exception as e:
                log(f"    gen error: {e}")
                continue
            if judge(out, spec):
                n = len(list(passdir.glob("*.png"))) + 1
                out.rename(passdir / f"{scene}_PASS_{n}.png")
                log(f"    *** PASS -> banked ({n}/{WANT_PER_SCENE})")
                if n >= WANT_PER_SCENE:
                    break
            else:
                out.unlink(missing_ok=True)
    log("SCENES DONE")


if __name__ == "__main__":
    main()

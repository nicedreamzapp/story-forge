#!/usr/bin/env python3
"""S2 via the proven S1 recipe: validated single-LoRA parts -> spaced composite
-> gentle weld -> full comparative judging. Loops strengths/seeds until a pass."""
import re, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
STILLS = HERE / "stills"
CANON = HERE / "canon"
LOG = open(HERE / "s2_weld_hunt.log", "a")
sys.path.insert(0, str(Path.home() / "Desktop/PROJECTS/story-forge/pipeline-tools"))
from film_qc import vl_ask, _state
_state["use_server"] = False
from PIL import Image, ImageDraw, ImageFilter

MFLUX = Path.home() / "mflux-venv/bin/mflux-generate-flux2"
MODEL = "AITRADER/FLUX2-klein-9B-mlx-8bit"
HL = str(Path.home() / ".hankdoug_seeds/HANK_LORA.safetensors")
DL = str(Path.home() / ".hankdoug_seeds/DOUG_LORA.safetensors")

def log(m):
    line = f"[{time.strftime('%H:%M:%S')}] {m}"
    print(line, flush=True); LOG.write(line + "\n"); LOG.flush()

def make_compare(candidate, master, out):
    m = Image.open(master).convert("RGB"); c = Image.open(candidate).convert("RGB")
    H = 480
    fit = lambda im: im.resize((int(im.width * H / im.height), H), Image.LANCZOS)
    m, c = fit(m), fit(c)
    sheet = Image.new("RGB", (m.width + c.width + 30, H + 40), (20, 20, 20))
    sheet.paste(m, (0, 40)); sheet.paste(c, (m.width + 30, 40))
    d = ImageDraw.Draw(sheet)
    d.text((10, 10), "OFFICIAL CHARACTER (canon)", fill=(255, 255, 0))
    d.text((m.width + 40, 10), "CANDIDATE FRAME", fill=(0, 255, 255))
    sheet.save(out)

DOG_Q = ("The LEFT image is the official locked design of Doug the bloodhound. Look at "
         "the dog in the RIGHT image. Is it the SAME character drawn on-model: IDENTICAL "
         "ear shape (long, heavy, FLAT and smooth-hanging — not curly, not fluffy, not "
         "wavy), same dark-brown ear color, same orange-tan coat, same lanky build, same "
         "face style, no collar? Be strict about ear texture. Start YES or NO.")
BEAR_Q = ("The LEFT image is the official locked design of Hank the bear. Look at the "
          "bear in the RIGHT image. Is it the SAME character: same round head, small "
          "rounded ears, light tan muzzle, brown fuzzy coat with tan belly patch, gentle "
          "face? Start YES or NO.")
ANAT_Q = ("This is a STYLIZED Pixar-style cartoon: round bodies, stubby limbs and "
          "simplified anatomy are intentional. Only fail for CLEAR errors: extra/missing "
          "limbs, extra heads/eyes, merged animals, melted faces, duplicated wheels. "
          "Start PASS or FAIL.")
NAT_Q = ("Is this one naturally rendered animation frame — consistent light, believable "
         "contact, nothing pasted or floating? Start PASS or FAIL.")

def judge(img):
    for name, q, master in [("dog", DOG_Q, CANON / "doug_canon.png"),
                            ("bear", BEAR_Q, CANON / "hank_canon.png")]:
        make_compare(img, master, "/tmp/_s2cmp.png")
        a = vl_ask("/tmp/_s2cmp.png", q).strip()
        ok = re.match(r"^\W*YES", a, re.I)
        log(f"  {name}(vs canon): {'ok' if ok else 'FAIL'} — {a[:150].replace(chr(10),' ')}")
        if not ok: return False
    for name, q in [("anatomy", ANAT_Q), ("natural", NAT_Q)]:
        a = vl_ask(str(img), q).strip()
        ok = re.match(r"^\W*(YES|PASS)", a, re.I)
        log(f"  {name}: {'ok' if ok else 'FAIL'} — {a[:150].replace(chr(10),' ')}")
        if not ok: return False
    return True

def build_rough():
    bg = Image.open(STILLS / "s2_bg.png").convert("RGBA")
    def prep(p, h):
        cut = remove(Image.open(p).convert("RGBA"))
        cut = cut.crop(cut.getbbox())
        s = h / cut.height
        return cut.resize((int(cut.width * s), h), Image.LANCZOS)
    hank = prep(STILLS / "s2_hank_pose.png", 165)
    doug = prep(STILLS / "s1_doug_pose.png", 118)   # S1's part — its Doug PASSED
    bg.alpha_composite(hank, (296, 112))            # front bench
    bg.alpha_composite(doug, (612, 150))            # rear rail — wide gap
    bg.convert("RGB").save(STILLS / "s2_rough_wide.png")

def weld(seed, strength, out):
    prompt = ("hankbear a huge round brown bear with light tan muzzle and tan belly patch "
              "holding rope reins at the front of the wagon, and far behind him at the "
              "back rail dougdog a tall lanky orange-tan bloodhound with very long heavy "
              "flat dark-brown floppy ears and droopy jowls, no collar, riding a large "
              "rustic wooden fire-engine wagon charging toward the camera on a dirt "
              "forest road, two galloping horses lower left, wooden hitch pole, ladder "
              "and barrel in the bed, dust behind the wheels, mouths closed, Pixar 3D "
              "animated movie style, golden afternoon light")
    r = subprocess.run(["nice", "-n", "10", str(MFLUX), "-m", MODEL,
                        "--lora-paths", HL, DL, "--lora-scales", "0.85", "1.0",
                        "--guidance", "1.0", "--steps", "24", "--seed", str(seed),
                        "--image-path", str(STILLS / "s2_rough_wide.png"),
                        "--image-strength", str(strength),
                        "--width", "832", "--height", "480",
                        "--output", str(out), "--prompt", prompt],
                       capture_output=True, text=True, timeout=900)
    return out.exists()

def main():
    log("using pre-built wide-gap rough")
    passdir = STILLS / "s2_pass"; passdir.mkdir(exist_ok=True)
    n = 0
    for strength in (0.28, 0.33, 0.24):
        for seed in (9001, 9007, 9013):
            log(f"weld strength={strength} seed={seed}")
            out = STILLS / f"s2_wweld_{seed}_{int(strength*100)}.png"
            if not weld(seed, strength, out):
                log("  gen failed"); continue
            if judge(out):
                n += 1
                out.rename(passdir / f"s2_PASS_weld_{n:02d}.png")
                log(f"  *** PASSED -> banked ({n})")
                if n >= 2: log("2 banked — done"); return
            else:
                out.unlink(missing_ok=True)
    log(f"hunt done, {n} passed")

main()

#!/usr/bin/env python3
"""
idea_factory.py — the LOCAL equivalent of the n8n "AI video factory" front-end.

The n8n guy uses ChatGPT to invent an idea + caption, then Veo3/FAL (cloud, paid)
to render it. This does the same job 100% local and free:

    local LLM (One AI router :4010)  ->  invent {title, caption, 3 wild scenes}
    -> write a valid Story Forge .sf  (Flux stills + LTX motion + ACE music, NO VO)
    -> log a row to ledger.csv        (the "Google Sheet")
    -> qadd into story-forge-queue    (renders -> YouTube unlisted -> texts Matt)

Narration-free by design: viral-short style (wild visual + motion + music + an
on-screen caption burned in post). Dodges the lip-sync wall and the narration
voice rule entirely. Add Allison/cloned-voice narration later as a toggle.

Usage:
    python3 idea_factory.py --theme "deep sea creatures throwing a rave" --scenes 3
    python3 idea_factory.py                       # auto-picks a wild theme
    python3 idea_factory.py --scenes 1 --render   # also render+caption now (test)
    python3 idea_factory.py --dry                 # generate + validate, don't queue
"""
import argparse, csv, json, os, re, subprocess, sys, time, urllib.request
from datetime import datetime
from pathlib import Path

HOME   = Path.home()
QUEUE  = HOME / "story-forge-queue"
INBOX  = QUEUE / "inbox"
LEDGER = QUEUE / "ledger.csv"
DRAFTS = QUEUE / "drafts"           # generated .sf scripts live here before queueing
ROUTER = "http://127.0.0.1:4010/v1/messages"
SF_BIN = HOME / "Desktop/PROJECTS/story-forge/bin/sf"
OUTDIR = HOME / "AI/videopipe/outputs"

# A wild-idea seed pool so the factory can run hands-off (the n8n guy's "auto idea").
SEED_THEMES = [
    "a yeti food-vlogging in a neon ramen shop",
    "deep-sea anglerfish throwing a glow-in-the-dark rave",
    "a raccoon barista pulling latte art at 3am",
    "sloths drag-racing tricked-out wheelchairs through a rainforest",
    "an octopus running a tiny watch-repair stall on the seafloor",
    "a grumpy owl hosting a midnight cooking show in a treehouse",
    "capybaras opening a rooftop hot-spring spa at sunset",
    "a pigeon detective working a noir case in a rainy alley",
]


def llm_json(prompt: str, max_tokens: int = 900, timeout: int = 180,
             temperature: float = 0.7) -> dict:
    """Call the One AI router and pull strict JSON back. Coder model nails JSON.
    Non-zero temperature stops the model collapsing onto a memorized idea when
    the theme is loosely constraining (greedy decoding regurgitates otherwise)."""
    body = json.dumps({
        "model": "auto",
        "max_tokens": max_tokens,
        "temperature": temperature,
        "messages": [{"role": "user", "content": prompt}],
    }).encode()
    req = urllib.request.Request(ROUTER, data=body, method="POST")
    req.add_header("content-type", "application/json")
    req.add_header("anthropic-version", "2023-06-01")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        resp = json.load(r)
    text = "".join(b.get("text", "") for b in resp.get("content", []) if isinstance(b, dict))
    # strip code fences, grab the first {...} object
    text = re.sub(r"```(?:json)?", "", text).strip()
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if not m:
        raise ValueError(f"no JSON in model reply:\n{text[:500]}")
    return json.loads(m.group(0))


def slugify(s: str) -> str:
    s = re.sub(r"[^a-z0-9]+", "_", s.lower()).strip("_")
    return ("vf_" + s)[:40]


STOPWORDS = {"the", "a", "an", "of", "at", "in", "on", "and", "with", "to", "for", "his", "her", "their", "its"}


def _theme_words(theme: str) -> set:
    return {w for w in re.findall(r"[a-z]+", theme.lower()) if len(w) > 3 and w not in STOPWORDS}


def _matches_theme(idea: dict, theme: str) -> bool:
    """Cheap guard against cache-bleed drift: at least one significant theme word
    must show up somewhere in the generated idea."""
    want = _theme_words(theme)
    if not want:
        return True
    blob = " ".join([idea.get("title", ""), idea.get("caption", ""),
                     " ".join(s.get("flux", "") for s in idea.get("scenes", []))]).lower()
    return any(w in blob for w in want)


def invent(theme: str, n_scenes: int, tries: int = 4) -> dict:
    last_err = None
    for attempt in range(tries):
        if attempt:
            time.sleep(2.0)   # let the backend KV/prompt cache clear between tries
        # nonce busts any backend prompt-cache that bleeds the prior theme in
        nonce = f"{int(time.time()*1000) % 1_000_000}-{attempt}"
        try:
            data = _invent_once(theme, n_scenes, nonce)
        except Exception as e:
            last_err = e
            print(f"[idea] gen attempt {attempt+1} failed ({e}); retrying", flush=True)
            continue
        if not _matches_theme(data, theme):
            last_err = ValueError(f"off-theme (got '{data.get('title')}' for '{theme}')")
            print(f"[idea] gen attempt {attempt+1} drifted off-theme; retrying", flush=True)
            continue
        return data
    raise RuntimeError(f"idea generation failed after {tries} tries: {last_err}")


def _invent_once(theme: str, n_scenes: int, nonce: str) -> dict:
    # NOTE: the theme is restated at the very END on purpose. The coder backend
    # weights the prompt tail hardest; a generic closing line ("output the JSON")
    # let it mode-collapse onto a recent idea. Theme-last keeps it on-subject.
    prompt = f"""You are a viral short-form video idea generator. Invent ONE wild,
visually striking vertical short with NO voiceover — it sells on bold visuals +
motion + music + one punchy on-screen caption. Return STRICT JSON only, no prose,
this exact shape:

{{
  "title": "short youtube title, <=60 chars",
  "caption": "one punchy on-screen line, <=70 chars, no emojis",
  "style": "a vivid visual style phrase appended to every image prompt (e.g. 'cinematic 3D pixar render, dramatic rim light, 8k')",
  "music": "a hyphenated music-bed descriptor, e.g. 'glitchy-deep-house-pulse' or 'warm-cinematic-underscore'",
  "scenes": [
    {{"flux": "a detailed image prompt for this beat", "motion": "a short camera/ambient motion description"}}
    // exactly {n_scenes} scene object(s)
  ]
}}

Make the scenes a tiny visual arc (establish -> twist -> payoff). Keep each flux
prompt concrete and renderable. (session {nonce})

The ONLY subject is: {theme}
Every title, caption, and scene must depict "{theme}" and nothing else — do not
drift to any other animal or subject. Now output ONLY the JSON for: {theme}"""
    data = llm_json(prompt)
    # normalize / guard
    data.setdefault("title", theme[:60])
    data.setdefault("caption", theme[:70])
    data.setdefault("style", "cinematic, dramatic light, highly detailed, 8k")
    data.setdefault("music", "warm-cinematic-underscore")
    scenes = data.get("scenes") or []
    if not scenes:
        raise ValueError("model returned no scenes")
    data["scenes"] = scenes[:n_scenes]
    return data


def to_sf(idea: dict, slug: str, scene_dur: float) -> str:
    style = idea["style"].replace('"', "'")
    music = re.sub(r"[^a-z0-9-]+", "-", idea["music"].lower()).strip("-") or "warm-cinematic-underscore"
    lines = [
        f'# {idea["title"]}  — generated by idea_factory.py (narration-free viral short)',
        f'# caption (burned in post): {idea["caption"]}',
        "",
        f'$style = "{style}"',
        "",
        f'film "{idea["title"]}" slug={slug} target=m5 format=reel',
        "",
        f'music bed: ace/{music} vol=0.32',
        "",
        "@transition xfade dur=0.4",
        "",
    ]
    for i, sc in enumerate(idea["scenes"]):
        flux = sc.get("flux", "").replace('"', "'")
        motion = sc.get("motion", "gentle push-in, soft ambient motion").replace('"', "'")
        lines += [
            f"scene beat_{i}:",
            "    still flux:",
            f'        prompt: "{{$style}}, {flux}"',
            "        seed: auto",
            "    motion ltx:",
            f'        prompt: "{motion}"',
            f"        duration: {scene_dur}",
            f"    music bed vol=0.32",
            "",
        ]
    return "\n".join(lines)


def log_ledger(row: dict):
    new = not LEDGER.exists()
    with LEDGER.open("a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["ts", "slug", "title", "caption", "music", "sf_path", "status"])
        if new:
            w.writeheader()
        w.writerow(row)


def _caption_png(caption: str, vid_w: int, vid_h: int, png: Path):
    """Render the on-screen caption as a transparent PNG (this Homebrew ffmpeg
    has no drawtext filter, so we composite a PIL image with `overlay` instead)."""
    from PIL import Image, ImageDraw, ImageFont
    font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
    if not Path(font_path).exists():
        font_path = "/System/Library/Fonts/Supplemental/Arial.ttf"
    fs = 52
    font = ImageFont.truetype(font_path, fs)
    img = Image.new("RGBA", (vid_w, vid_h), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)

    # word-wrap to ~88% of width
    maxw = int(vid_w * 0.88)
    words, lines, cur = caption.upper().split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if d.textlength(t, font=font) > maxw and cur:
            lines.append(cur); cur = w
        else:
            cur = t
    if cur:
        lines.append(cur)

    lh = fs + 14
    block_h = lh * len(lines)
    y0 = int(vid_h * 0.72)
    # translucent rounded backing box
    pad = 28
    box_w = max(d.textlength(l, font=font) for l in lines) + pad * 2
    bx0 = (vid_w - box_w) / 2
    d.rounded_rectangle([bx0, y0 - pad, bx0 + box_w, y0 + block_h + pad - 14],
                        radius=24, fill=(0, 0, 0, 150))
    for i, l in enumerate(lines):
        tw = d.textlength(l, font=font)
        x = (vid_w - tw) / 2
        y = y0 + i * lh
        d.text((x, y), l, font=font, fill=(255, 255, 255, 255),
               stroke_width=3, stroke_fill=(0, 0, 0, 255))
    img.save(png)


def burn_caption(mp4: Path, caption: str) -> Path:
    """PIL caption PNG -> ffmpeg overlay (drawtext-free, works on this build)."""
    out = mp4.with_name(mp4.stem + "_cap.mp4")
    dims = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                           "-show_entries", "stream=width,height", "-of", "csv=p=0", str(mp4)],
                          capture_output=True, text=True).stdout.strip()
    vw, vh = (int(x) for x in dims.split(","))
    png = mp4.with_suffix(".caption.png")
    _caption_png(caption, vw, vh, png)
    proc = subprocess.run(["ffmpeg", "-y", "-i", str(mp4), "-i", str(png),
                           "-filter_complex", "[0:v][1:v]overlay=0:0",
                           "-c:a", "copy", str(out)],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stderr[-1500:] + "\n")
        raise subprocess.CalledProcessError(proc.returncode, "ffmpeg overlay")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--theme", default=None, help="seed theme (default: rotate the pool)")
    ap.add_argument("--scenes", type=int, default=3)
    ap.add_argument("--scene-dur", type=float, default=4.0)
    ap.add_argument("--render", action="store_true", help="also render + burn caption now (test path)")
    ap.add_argument("--dry", action="store_true", help="generate + validate (sf --dry), do NOT queue")
    args = ap.parse_args()

    DRAFTS.mkdir(parents=True, exist_ok=True)
    INBOX.mkdir(parents=True, exist_ok=True)

    # rotate the seed pool deterministically off the ledger length (no Math.random needed)
    if args.theme:
        theme = args.theme
    else:
        n = sum(1 for _ in LEDGER.open()) if LEDGER.exists() else 0
        theme = SEED_THEMES[n % len(SEED_THEMES)]

    print(f"[idea] theme: {theme}", flush=True)
    idea = invent(theme, args.scenes)
    slug = slugify(idea["title"]) + f"_{int(time.time())%100000}"
    sf_text = to_sf(idea, slug, args.scene_dur)
    sf_path = DRAFTS / f"{slug}.sf"
    sf_path.write_text(sf_text)

    print(f"[idea] title:   {idea['title']}")
    print(f"[idea] caption: {idea['caption']}")
    print(f"[idea] music:   {idea['music']}")
    print(f"[idea] scenes:  {len(idea['scenes'])}")
    print(f"[idea] wrote:   {sf_path}")

    # always validate the script compiles
    dry = subprocess.run([str(SF_BIN), "render", str(sf_path), "--dry"],
                         capture_output=True, text=True)
    ok = dry.returncode == 0
    print(f"[idea] sf --dry: {'OK' if ok else 'FAILED'}")
    if not ok:
        sys.stderr.write(dry.stdout[-1500:] + "\n" + dry.stderr[-1500:] + "\n")

    status = "validated"
    if ok and args.render:
        print("[idea] rendering (lean)… this loads Flux+LTX, give it a few min", flush=True)
        rr = subprocess.run([str(SF_BIN), "render", str(sf_path), "--engine", "lean"],
                            capture_output=True, text=True)
        mp4 = OUTDIR / f"{slug}.mp4"
        if rr.returncode == 0 and mp4.exists():
            capped = burn_caption(mp4, idea["caption"])
            status = f"rendered:{capped}"
            print(f"[idea] RENDERED + captioned: {capped}")
        else:
            status = "render_failed"
            sys.stderr.write(rr.stdout[-2000:] + "\n" + rr.stderr[-2000:] + "\n")
    elif ok and not args.dry:
        # the autopilot drop: hand the script to the queue
        (INBOX / f"{slug}.sf").write_text(sf_text)
        status = "queued"
        print(f"[idea] queued -> {INBOX / (slug + '.sf')}")

    log_ledger({
        "ts": datetime.now().isoformat(timespec="seconds"),
        "slug": slug, "title": idea["title"], "caption": idea["caption"],
        "music": idea["music"], "sf_path": str(sf_path), "status": status,
    })
    print(f"[idea] ledger += {LEDGER}")
    print(f"[idea] done ({status})")


if __name__ == "__main__":
    main()

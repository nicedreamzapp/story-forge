"""videopipe.director — the Director: chat + storyboard front-end for the whole formula.

Flow it enforces (mirrors the Story Forge pipeline rules):
  concept (chat, talk-first)  ->  scene plan  ->  per-scene: still -> QC gate ->
  approve/lock -> draft animate -> final animate  ->  score (Song Forge, instrumental)
  ->  assemble  ->  film_qc verification.

State lives in projects/director/<pid>/project.json; all heavy work runs in
background threads, one GPU job at a time. Song Forge customer jobs always
outrank us: any GPU stage refuses to start while the forge reports jobs_running.
"""
from __future__ import annotations

import base64
import json
import re
import shutil
import subprocess
import threading
import time
import urllib.request
import urllib.error
import uuid
from pathlib import Path

from flask import jsonify, request, send_from_directory

import os
import sys

ROOT = Path(__file__).resolve().parent
PROJ_DIR = ROOT / "projects" / "director"


def _env_path(name, default):
    raw = os.environ.get(name)
    return Path(raw).expanduser() if raw else Path(default)


# Every external dependency is overridable, same convention as
# story_forge/config.py — a fresh clone runs with the in-repo tools.
FLUX = _env_path("SF_FLUX_SCRIPT", ROOT / "tools" / "flux_t2i.py")
FILM_QC = _env_path("SF_FILM_QC", ROOT / "pipeline-tools" / "film_qc.py")
QC_PYTHON = _env_path("SF_QC_PYTHON", sys.executable)   # needs mlx_vlm + mlx_whisper
COMFY_START = os.environ.get("SF_COMFY_START", "")      # optional autostart script

LLM_URL = os.environ.get("SF_LLM_URL",                  # any OpenAI-compatible local server
                         "http://127.0.0.1:9420/v1/chat/completions")
CHAT_MODEL = os.environ.get("SF_CHAT_MODEL", "mlx-community/gemma-3-12b-it-4bit")
PE_URL = os.environ.get("SF_PE_URL", "http://127.0.0.1:8181")      # vision judge (still QC gate)
FORGE_URL = os.environ.get("SF_FORGE_URL", "http://127.0.0.1:8767")  # ACE-Step music server
SELF_URL = os.environ.get("SF_SELF_URL", "http://127.0.0.1:17600")   # our own render endpoints

_LOCK = threading.RLock()
_GPU = threading.Semaphore(1)             # one heavy GPU job at a time, always

# ── memory governor ──────────────────────────────────────
# Story Forge runs SMART (Matt, 2026-07-22): every heavy stage states what it
# needs, frees what the machine can't afford to keep, and waits rather than
# shoving the box into swap thrash. One freeze is one too many.

_STILLS_PENDING = 0                       # stills jump the animate queue: they
_PENDING_CV = threading.Condition()       # reuse the resident FLUX weights and
                                          # finish in seconds, so batching them
                                          # avoids Flux<->Wan reload ping-pong


def _free_pct():
    try:
        out = subprocess.run(["memory_pressure", "-Q"], capture_output=True,
                             text=True, timeout=10).stdout
        m = re.search(r"free percentage:\s*(\d+)", out)
        return int(m.group(1)) if m else 100
    except Exception:
        return 100


def _wait_for_memory(min_free_pct, label, timeout=300):
    """Block until the machine can afford the next stage. The supervisor's
    idle-hog eviction runs every ~2min, so waiting usually IS the fix."""
    t0 = time.time()
    while time.time() - t0 < timeout:
        pct = _free_pct()
        if pct >= min_free_pct:
            return True
        time.sleep(15)
    print(f"[director] {label}: memory still tight after {timeout}s "
          f"(free {_free_pct()}%) — proceeding carefully", flush=True)
    return False


def _prepare_memory(stage):
    """Call while holding _GPU, before doing the stage's heavy work.
    still/animate ride ComfyUI (it swaps Flux/Wan internally); vl_qc must have
    ComfyUI GONE first — Wan weights + a 32B VL model can't share this box."""
    if stage == "vl_qc":
        _evict_idle_comfy()
        _wait_for_memory(35, stage)
    elif stage == "animate":
        _wait_for_memory(25, stage)
    else:  # still
        _wait_for_memory(15, stage)


# ───────────────────── small utils ─────────────────────

def _http_json(url, payload=None, timeout=120, method=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method or ("POST" if data else "GET"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())


def _slugify(s):
    s = re.sub(r"[^a-z0-9]+", "-", (s or "untitled").lower()).strip("-")
    return s[:40] or "untitled"


def _forge_busy():
    """Customer songs outrank everything we do. True = hands off the GPU."""
    try:
        st = _http_json(f"{FORGE_URL}/api/status", timeout=3)
        return int(st.get("jobs_running") or 0) > 0
    except Exception:
        return False  # forge down = nothing to preempt


# ───────────────────── project store ─────────────────────

def _pdir(pid):
    return PROJ_DIR / pid


def _load(pid):
    f = _pdir(pid) / "project.json"
    if not f.exists():
        return None
    return json.loads(f.read_text())


def _save(p):
    p["updated"] = time.time()
    d = _pdir(p["id"])
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "project.json.tmp"
    tmp.write_text(json.dumps(p, indent=1))
    tmp.rename(d / "project.json")


def _new_project():
    pid = time.strftime("%m%d") + "-" + uuid.uuid4().hex[:6]
    p = {
        "id": pid, "created": time.time(), "updated": time.time(),
        "stage": "concept",
        "concept": {"title": "", "slug": "", "style": "", "mood": "",
                    "characters": [], "scene_count": 0},
        "chat": [],
        "scenes": [],
        "song": {"status": "none", "file": None, "task_id": None, "style": "", "error": None},
        "film": {"status": "none", "file": None, "qc": {"status": "none", "passed": 0,
                                                        "failed": 0, "unchecked": 0,
                                                        "report": "", "error": None}},
    }
    _save(p)
    return p


# ── recipe bank — the system gets better with every approval ─────
# Every Matt-approved still and every film that passes film_qc banks its
# recipe (style, prompt, seed, motion). The chat director reads a digest of
# proven recipes, so wins compound instead of being re-derived per movie.

BANK_FILE = PROJ_DIR / "recipe_bank.json"


def _bank_add(kind, entry):
    with _LOCK:
        bank = []
        if BANK_FILE.exists():
            try:
                bank = json.loads(BANK_FILE.read_text())
            except Exception:
                bank = []
        entry.update({"kind": kind, "ts": time.time()})
        bank.append(entry)
        BANK_FILE.parent.mkdir(parents=True, exist_ok=True)
        BANK_FILE.write_text(json.dumps(bank[-500:], indent=1))


def _bank_digest(max_items=6):
    """Short 'what already worked' block for the chat director's context."""
    if not BANK_FILE.exists():
        return ""
    try:
        bank = json.loads(BANK_FILE.read_text())
    except Exception:
        return ""
    films = [b for b in bank if b["kind"] == "film_pass"][-3:]
    stills = [b for b in bank if b["kind"] == "still_approved"][-max_items:]
    if not films and not stills:
        return ""
    lines = ["PROVEN RECIPES (Matt approved these — reuse their exact phrasing when they fit):"]
    for f in films:
        lines.append(f"- full film passed QC: style=\"{f['style']}\" mood=\"{f.get('mood','')}\"")
    for s in stills:
        lines.append(f"- approved still: style=\"{s['style']}\" scene=\"{s['desc'][:70]}\""
                     + (f" motion=\"{s['motion'][:60]}\"" if s.get("motion") else ""))
    return "\n".join(lines)


def _blank_scene(idx, s=None):
    s = s or {}
    return {
        "idx": idx,
        "title": (s.get("title") or f"Scene {idx}").strip()[:80],
        "desc": (s.get("desc") or "").strip(),
        "motion": (s.get("motion") or "").strip(),
        "dialogue": (s.get("dialogue") or "").strip(),
        "locked": False,
        "still": {"file": None, "status": "none", "seed": 73 + idx * 17, "source": "flux",
                  "qc": {"status": "none", "notes": ""}},
        "draft": {"file": None, "status": "none", "error": None},
        "final": {"file": None, "status": "none", "error": None},
    }


# ───────────────────── the chat brain ─────────────────────

SYSTEM_PROMPT = """You are the Director of Story Forge, Matt's 100% local AI movie studio.
You plan movies with him in casual conversation, then his crew renders them scene by scene.

HOW YOU WORK (the studio's locked rules):
- Talk first, render second. Lock the concept before scenes: title, visual style, characters, mood, scene count.
- Ask AT MOST ONE short question per reply, and only if truly needed. If Matt gives you enough to run with, propose the full concept AND the full scene list in the same reply. Never interrogate him.
- Default movie length: 8 scenes (about 40 seconds of film). Matt can change it.
- The animator (Wan i2v) CANNOT do: physics, object collisions, lip sync, coordinated multi-character action. Motion prompts stay inside: ambient motion, camera moves (push-in, pull-back, pan, parallax, gentle orbit), walking, breathing, atmosphere, particles, mouth opening/closing while speaking.
- Every scene gets: a still description (what is in frame, present tense, concrete and visual), a motion prompt (camera + ambient movement), and at most ONE short dialogue line ("Name: line") or "" for a silent scene.
- Characters need a name, species, a visual "look" description (kept IDENTICAL across scenes for consistency), and a voice note (e.g. "warm gravelly male").
- The score comes later from Song Forge as an INSTRUMENTAL — capture the musical mood in concept.mood.

REPLY FORMAT — you MUST reply with ONLY a JSON object, no markdown, no fences:
{"reply": "what you say to Matt, short and casual",
 "concept": {"title": "...", "style": "...", "mood": "...", "scene_count": 8,
             "characters": [{"name": "...", "species": "...", "look": "...", "voice": "..."}]} or null,
 "scenes": [{"title": "...", "desc": "...", "motion": "...", "dialogue": "Name: ..." }] or null}

Include "concept" only when it changes. Include "scenes" only when creating or changing scenes, and ALWAYS return the FULL scene list (it replaces the old one). Keep "reply" to a few sentences."""


def _project_context(p):
    c = p["concept"]
    lines = [f"CURRENT PROJECT STATE (stage: {p['stage']}):",
             f"title={c['title'] or '(unset)'} | style={c['style'] or '(unset)'} | mood={c['mood'] or '(unset)'}",
             "characters: " + (", ".join(f"{ch['name']} ({ch['species']}, {ch.get('look','')})"
                                         for ch in c["characters"]) or "(none)")]
    if p["scenes"]:
        lines.append("scenes:")
        for s in p["scenes"]:
            lines.append(f"  {s['idx']}. {s['title']}: {s['desc'][:90]}"
                         + (f" [locked]" if s["locked"] else ""))
    digest = _bank_digest()
    if digest:
        lines.append("")
        lines.append(digest)
    return "\n".join(lines)


def _extract_json(text):
    text = re.sub(r"^```(json)?|```$", "", text.strip(), flags=re.M).strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{.*\}", text, re.S)
    if m:
        try:
            return json.loads(m.group(0))
        except Exception:
            pass
    return None


def _chat_llm(p, user_msg):
    # ONE system message only — the mlx server 404s on a second system role
    # (gemma chat template restriction, found 2026-07-22).
    msgs = [{"role": "system", "content": SYSTEM_PROMPT + "\n\n" + _project_context(p)}]
    for m in p["chat"][-16:]:
        msgs.append({"role": m["role"], "content": m["text"]})
    msgs.append({"role": "user", "content": user_msg})
    out = _http_json(LLM_URL, {
        "model": CHAT_MODEL, "messages": msgs,
        "max_tokens": 2000, "temperature": 0.7,
    }, timeout=180)
    return out["choices"][0]["message"]["content"]


def _apply_chat_result(p, parsed):
    c = parsed.get("concept")
    if isinstance(c, dict):
        con = p["concept"]
        for k in ("title", "style", "mood"):
            if c.get(k):
                con[k] = str(c[k]).strip()
        if c.get("scene_count"):
            try:
                con["scene_count"] = int(c["scene_count"])
            except Exception:
                pass
        if isinstance(c.get("characters"), list) and c["characters"]:
            con["characters"] = [
                {"name": str(ch.get("name", "")).strip(),
                 "species": str(ch.get("species", "")).strip(),
                 "look": str(ch.get("look", "")).strip(),
                 "voice": str(ch.get("voice", "")).strip()}
                for ch in c["characters"] if ch.get("name")]
        con["slug"] = _slugify(con["title"])

    scenes = parsed.get("scenes")
    if isinstance(scenes, list) and scenes:
        old = {s["idx"]: s for s in p["scenes"]}
        rebuilt = []
        for i, sc in enumerate(scenes, start=1):
            ns = _blank_scene(i, sc)
            prev = old.get(i)
            # keep rendered assets when the scene text didn't change (never
            # touch a locked scene's picture just because the list was resent)
            if prev and (prev["locked"] or
                         (prev["desc"] == ns["desc"] and prev["motion"] == ns["motion"])):
                for k in ("locked", "still", "draft", "final"):
                    ns[k] = prev[k]
                if prev["locked"]:
                    ns["title"], ns["desc"], ns["motion"] = prev["title"], prev["desc"], prev["motion"]
            rebuilt.append(ns)
        p["scenes"] = rebuilt
        p["stage"] = "production"
    elif p["concept"]["title"] and not p["scenes"]:
        p["stage"] = "concept"


# ───────────────────── stills + QC gate ─────────────────────

def _cast_line(p, desc):
    """Append the fixed 'look' of every character that appears in this scene —
    consistency is structural, not left to the LLM."""
    bits = []
    for ch in p["concept"]["characters"]:
        if ch["name"].lower() in desc.lower():
            bits.append(f"{ch['name']} is {ch['look']}" if ch.get("look")
                        else f"{ch['name']} the {ch['species']}")
    return (". " + ". ".join(bits)) if bits else ""


def _still_prompt(p, s):
    style = p["concept"]["style"]
    return f"{style}. {s['desc']}{_cast_line(p, s['desc'])}".strip(". ")


def _qc_still(p, s, png):
    """Input gate: show the still to Picture Eyes. Down = UNCHECKED, never a fake pass."""
    q = (f"You are a film QC judge. Scene intent: \"{s['desc']}\". "
         f"Characters expected on-model: "
         + ("; ".join(f"{ch['name']} = {ch['look'] or ch['species']}"
                      for ch in p["concept"]["characters"]) or "none")
         + ". Does the image match the intent, characters on-model, no deformities "
           "(extra limbs, warped faces, merged bodies)? "
           "Answer ONLY JSON: {\"pass\": true/false, \"notes\": \"one short sentence\"}")
    try:
        st = _http_json(f"{PE_URL}/status", timeout=3)
        if not st.get("loaded"):
            raise RuntimeError("PE not loaded")
        boundary = uuid.uuid4().hex
        img = Path(png).read_bytes()
        body = (
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"prompt\"\r\n\r\n{q}\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"max_tokens\"\r\n\r\n200\r\n"
            f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
            f"filename=\"s.png\"\r\nContent-Type: image/png\r\n\r\n"
        ).encode() + img + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            f"{PE_URL}/describe", data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
        with urllib.request.urlopen(req, timeout=300) as r:
            ans = r.read().decode()
        parsed = _extract_json(ans) or {}
        if isinstance(parsed.get("pass"), bool):
            return ("pass" if parsed["pass"] else "fail",
                    str(parsed.get("notes", ""))[:200])
        return ("unchecked", "vision judge gave no verdict")
    except Exception:
        return ("unchecked", "Picture Eyes offline — verify by eye")


def _ensure_comfy():
    """flux_t2i.py and the Wan renders all ride ComfyUI (:8188) — boot it if down."""
    for attempt in range(2):
        try:
            urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
            return True
        except Exception:
            pass
        if attempt == 0:
            if not COMFY_START:
                return False  # no autostart configured — user runs ComfyUI themselves
            (ROOT / "logs").mkdir(exist_ok=True)
            comfy_log = open(ROOT / "logs" / "comfyui.log", "a")
            subprocess.Popen(["bash", COMFY_START],
                             stdout=comfy_log, stderr=subprocess.STDOUT,
                             start_new_session=True)
            for _ in range(120):
                try:
                    urllib.request.urlopen("http://127.0.0.1:8188/system_stats", timeout=2)
                    return True
                except Exception:
                    time.sleep(1)
    return False


def _gen_still(pid, idx):
    global _STILLS_PENDING
    with _PENDING_CV:
        _STILLS_PENDING += 1
    try:
        _gen_still_inner(pid, idx)
    finally:
        with _PENDING_CV:
            _STILLS_PENDING -= 1
            _PENDING_CV.notify_all()


def _gen_still_inner(pid, idx):
    with _GPU:
        _prepare_memory("still")
        p = _load(pid)
        s = p["scenes"][idx - 1]
        prompt = _still_prompt(p, s)
        png = _pdir(pid) / f"still_{idx:02d}.png"
        try:
            if not _ensure_comfy():
                raise RuntimeError("ComfyUI would not start")
            subprocess.run(
                ["python3", str(FLUX), prompt, "--out", str(png),
                 "--w", "832", "--h", "480", "--seed", str(s["still"]["seed"])],
                check=True, capture_output=True, text=True, timeout=1800)
        except Exception as e:
            with _LOCK:
                p = _load(pid)
                st = p["scenes"][idx - 1]["still"]
                st["status"] = "error"
                _save(p)
            return
        with _LOCK:
            p = _load(pid)
            st = p["scenes"][idx - 1]["still"]
            st["file"] = png.name
            st["status"] = "done"
            st["qc"] = {"status": "running", "notes": ""}
            _save(p)
    verdict, notes = _qc_still(p, p["scenes"][idx - 1], png)
    with _LOCK:
        p = _load(pid)
        p["scenes"][idx - 1]["still"]["qc"] = {"status": verdict, "notes": notes}
        _save(p)


# ───────────────────── animation (Wan i2v via our own server) ─────────────────────

DRAFT_RES = "480x272"      # ~3 min: the cheap gate that kills bad staging early
FINAL_RES = "832x480"      # ~9 min


def _animate(pid, idx, mode):
    res = DRAFT_RES if mode == "draft" else FINAL_RES
    # let queued stills clear first — they reuse the resident FLUX weights and
    # take seconds; interleaving them with Wan renders reloads models for nothing
    with _PENDING_CV:
        _PENDING_CV.wait_for(lambda: _STILLS_PENDING == 0, timeout=1800)
    with _GPU:
        _prepare_memory("animate")
        p = _load(pid)
        s = p["scenes"][idx - 1]
        png = _pdir(pid) / s["still"]["file"]
        try:
            # 1. hand the still to ComfyUI through our own upload endpoint
            boundary = uuid.uuid4().hex
            img = png.read_bytes()
            body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; "
                    f"filename=\"{png.name}\"\r\nContent-Type: image/png\r\n\r\n"
                    ).encode() + img + f"\r\n--{boundary}--\r\n".encode()
            req = urllib.request.Request(
                f"{SELF_URL}/api/upload", data=body,
                headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
            with urllib.request.urlopen(req, timeout=180) as r:
                comfy_name = json.loads(r.read().decode())["name"]

            # 2. queue the i2v render (native 5s — never stretched)
            motion = s["motion"] or "gentle ambient motion, subtle camera push-in"
            job = _http_json(f"{SELF_URL}/api/render", {
                "prompt": motion, "image_name": comfy_name,
                "duration": 5, "quality": "fast", "resolution": res,
            }, timeout=60)
            if job.get("error"):
                raise RuntimeError(job["error"])
            jid = job["job_id"]

            # 3. wait for it
            mp4 = None
            deadline = time.time() + 3600
            last_pct = -1
            while time.time() < deadline:
                st = _http_json(f"{SELF_URL}/api/status/{jid}", timeout=10)
                if st.get("state") == "done":
                    mp4 = st.get("mp4")
                    break
                if st.get("state") in ("error", "cancelled"):
                    raise RuntimeError(st.get("error") or st.get("state"))
                pct = int(st.get("pct") or 0)
                if pct != last_pct:
                    last_pct = pct
                    with _LOCK:
                        q = _load(pid)
                        q["scenes"][idx - 1][mode].update(
                            {"pct": pct, "stage": st.get("stage") or ""})
                        _save(q)
                time.sleep(3)
            if not mp4:
                raise RuntimeError("render timed out")
            dest = _pdir(pid) / f"{mode}_{idx:02d}.mp4"
            shutil.copy(mp4, dest)
            with _LOCK:
                p = _load(pid)
                p["scenes"][idx - 1][mode] = {"file": dest.name, "status": "done", "error": None}
                _save(p)
        except Exception as e:
            with _LOCK:
                p = _load(pid)
                p["scenes"][idx - 1][mode] = {"file": None, "status": "error",
                                              "error": str(e)[:300]}
                _save(p)


# ───────────────────── score (Song Forge) ─────────────────────

def _make_song(pid):
    p = _load(pid)
    n = len(p["scenes"])
    film_len = max(20, int(n * 4.5) + 8)          # 5s clips, 0.5s crossfades, fade tail
    mood = p["concept"]["mood"] or "warm cinematic"
    style = f"instrumental {mood} film score, no vocals"
    try:
        job = _http_json(f"{FORGE_URL}/api/song", {
            "style": style, "lyrics": "[inst]",    # explicit — never let the forge write lyrics
            "title": f"{p['concept']['title']} (score)",
            "duration": float(min(240, film_len)),
        }, timeout=30)
        tid = job.get("task_id") or job.get("id")
        if not tid:
            raise RuntimeError(f"forge refused: {job}")
        with _LOCK:
            p = _load(pid)
            p["song"].update({"status": "running", "task_id": tid, "style": style, "error": None})
            _save(p)
        deadline = time.time() + 1800
        audio_url = None
        while time.time() < deadline:
            st = _http_json(f"{FORGE_URL}/api/song/{tid}", timeout=15)
            if st.get("status") == "done":
                audio_url = st.get("audio") or st.get("audio_url")
                break
            if st.get("status") == "error":
                raise RuntimeError(st.get("last_error") or "forge error")
            time.sleep(5)
        if not audio_url:
            raise RuntimeError("score timed out")
        # download IMMEDIATELY — the mini's sentry purges forge songs after 1h
        if audio_url.startswith("/"):
            audio_url = FORGE_URL + audio_url
        dest = _pdir(pid) / "score.wav"
        with urllib.request.urlopen(audio_url, timeout=300) as r:
            dest.write_bytes(r.read())
        with _LOCK:
            p = _load(pid)
            p["song"].update({"status": "done", "file": "score.wav"})
            _save(p)
    except Exception as e:
        with _LOCK:
            p = _load(pid)
            p["song"].update({"status": "error", "error": str(e)[:300]})
            _save(p)


# ───────────────────── assembly + film_qc ─────────────────────

def _clip_dur(f):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", str(f)], capture_output=True, text=True)
    return float(out.stdout.strip())


def _assemble(pid, mode):
    """Stitch scene clips (xfade) + lay the score under. mode: preview|final."""
    p = _load(pid)
    d = _pdir(pid)
    clips, manifest_scenes, clip_modes = [], [], []
    try:
        for s in p["scenes"]:
            pick = used = None
            if mode == "final":
                if s["final"]["status"] == "done":
                    pick, used = d / s["final"]["file"], "final"
            else:
                for k in ("final", "draft"):
                    if s[k]["status"] == "done":
                        pick, used = d / s[k]["file"], k
                        break
            if not pick:
                raise RuntimeError(f"scene {s['idx']} has no rendered clip"
                                   + ("" if mode == "final" else " (draft or final)"))
            clips.append(pick)
            clip_modes.append(used)

        xfade = 0.5
        durs = [_clip_dur(c) for c in clips]
        inputs, fc = [], []
        for c in clips:
            inputs += ["-i", str(c)]
        # conform every clip to one canvas first, then chain xfades
        for i in range(len(clips)):
            fc.append(f"[{i}:v]scale=1920:1080:force_original_aspect_ratio=increase,"
                      f"crop=1920:1080,fps=30,settb=AVTB[c{i}]")
        last, off = "[c0]", 0.0
        for i in range(1, len(clips)):
            off += durs[i - 1] - xfade
            fc.append(f"{last}[c{i}]xfade=transition=fade:duration={xfade}:offset={off:.3f}[v{i}]")
            last = f"[v{i}]"
        total = off + durs[-1] if len(clips) > 1 else durs[0]
        t0 = 0.0
        for s, du in zip(p["scenes"], durs):
            manifest_scenes.append({"name": s["title"], "start": round(t0, 2),
                                    "end": round(min(t0 + du, total), 2)})
            t0 += du - xfade
        fade_out = max(0, total - 1.5)
        fc.append(f"{last}fade=in:st=0:d=0.8,fade=out:st={fade_out:.2f}:d=1.5[vout]")

        out = d / f"{p['concept']['slug'] or 'film'}_{mode}.mp4"
        song = d / "score.wav"
        cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *inputs]
        if song.exists():
            cmd += ["-i", str(song)]
            fc.append(f"[{len(clips)}:a]atrim=0:{total:.2f},afade=in:st=0:d=0.8,"
                      f"afade=out:st={fade_out:.2f}:d=1.5,apad=whole_dur={total:.2f}[aout]")
            cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]", "-map", "[aout]",
                    "-c:a", "aac", "-b:a", "192k"]
        else:
            cmd += ["-filter_complex", ";".join(fc), "-map", "[vout]"]
        cmd += ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-preset", "medium",
                "-crf", "18", "-r", "30", "-t", f"{total:.2f}",
                "-movflags", "+faststart", str(out)]
        subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=1800)

        manifest = {"characters": {ch["name"].lower(): (ch["look"] or ch["species"])
                                   for ch in p["concept"]["characters"]},
                    "scenes": manifest_scenes, "lines": []}
        (d / "manifest.json").write_text(json.dumps(manifest, indent=1))
        with _LOCK:
            p = _load(pid)
            p["film"]["status"] = "done"
            p["film"]["file"] = out.name
            p["film"]["mode"] = mode
            p["film"]["clip_modes"] = clip_modes
            p["film"]["qc"] = {"status": "none", "passed": 0, "failed": 0,
                               "unchecked": 0, "report": "", "error": None}
            p["stage"] = "assembled"
            _save(p)
    except subprocess.CalledProcessError as e:
        with _LOCK:
            p = _load(pid)
            p["film"]["status"] = "error"
            p["film"]["qc"]["error"] = (e.stderr or str(e))[-300:]
            _save(p)
    except Exception as e:
        with _LOCK:
            p = _load(pid)
            p["film"]["status"] = "error"
            p["film"]["qc"]["error"] = str(e)[:300]
            _save(p)


def _evict_idle_comfy():
    """Free ComfyUI's memory before loading another big model. Only when its
    queue is empty — same policy as the m5 supervisor's idle-hog eviction.
    film_qc's in-process Qwen3-VL on top of resident Wan weights froze the whole
    Mac on 2026-07-22; never stack them again."""
    try:
        q = _http_json("http://127.0.0.1:8188/queue", timeout=3)
        if len(q.get("queue_running", [])) + len(q.get("queue_pending", [])) > 0:
            return
        subprocess.run(["pkill", "-f", "main.py --listen 127.0.0.1 --port 8188"],
                       capture_output=True)
        time.sleep(8)
    except Exception:
        pass  # ComfyUI not running = nothing to free


def _qc_once(pid):
    """One film_qc pass. Returns (status, counts, report_text, defects)."""
    p = _load(pid)
    d = _pdir(pid)
    film = d / p["film"]["file"]
    report = d / "film_qc.md"
    with _GPU:
        _prepare_memory("vl_qc")
        r = subprocess.run(
            [str(QC_PYTHON), str(FILM_QC), str(film), str(d / "manifest.json"),
             "--report", str(report)],
            capture_output=True, text=True, timeout=3600)
    text = report.read_text() if report.exists() else (r.stdout + r.stderr)[-2000:]
    counts = {"passed": len(re.findall(r"\[PASS\]", text)),
              "failed": len(re.findall(r"\[FAIL\]", text)),
              "unchecked": len(re.findall(r"\bUNCHECKED\b", text))}
    status = {0: "pass", 1: "fail"}.get(r.returncode, "unavailable")
    defects = re.findall(r"\[FAIL\]\s*([\w-]+)@([\d.]+)s", text)  # (check, t)
    return status, counts, text, [(c, float(t)) for c, t in defects]


def _classify_defects(pid, defects):
    """Split timestamped defects into transition ghosts (benign — the xfade
    blends two scenes, the judge sees 'two overlapping characters') vs defects
    inside a scene's core, mapped to that scene's index for auto re-roll."""
    man = json.loads((_pdir(pid) / "manifest.json").read_text())
    scenes = man["scenes"]
    zones = [(scenes[i + 1]["start"] - 0.2, scenes[i]["end"] + 0.2)
             for i in range(len(scenes) - 1)]
    benign, core = [], {}
    for check, t in defects:
        if any(a <= t <= b for a, b in zones):
            benign.append((check, t))
            continue
        for i, sc in enumerate(scenes):
            if sc["start"] <= t <= sc["end"]:
                core.setdefault(i + 1, []).append((check, t))
                break
    return benign, core


def _run_film_qc(pid, autofix=True, max_fix_rounds=2):
    """The closed loop: verify → re-roll only the scenes that failed →
    re-assemble → re-verify. Matt sees the final verdict plus what got fixed
    on the way, not the broken intermediates."""
    rounds = []
    try:
        for rnd in range(max_fix_rounds + 1):
            status, counts, text, defects = _qc_once(pid)
            benign, core = ([], {}) if status != "fail" else _classify_defects(pid, defects)
            effective = "pass" if (status == "fail" and defects and not core
                                   and len(benign) == counts["failed"]) else status
            rounds.append({"round": rnd + 1, "status": status, **counts,
                           "benign_transition": len(benign),
                           "rerolled": sorted(core.keys())})
            note = (f"{len(benign)} flagged frame(s) are crossfade ghosting "
                    f"(two scenes mid-blend) — benign" if benign else "")
            with _LOCK:
                p = _load(pid)
                p["film"]["qc"] = {"status": effective, **counts,
                                   "report": text[-4000:], "rounds": rounds,
                                   "note": note,
                                   "error": None if status in ("pass", "fail")
                                   else "QC could not run (exit 2) — NOT a pass"}
                _save(p)
            if effective != "fail" or not core or not autofix or rnd == max_fix_rounds:
                return
            if _forge_busy():
                with _LOCK:
                    p = _load(pid)
                    p["film"]["qc"]["note"] = ("auto-fix paused — Song Forge is "
                                               "rendering a customer song; re-run QC later")
                    _save(p)
                return
            # re-roll ONLY the failed scenes' animations (fresh noise seed),
            # from their locked stills — the still itself is never touched
            p = _load(pid)
            film_mode = p["film"].get("mode", "preview")
            clip_modes = p["film"].get("clip_modes", [])
            for idx in sorted(core.keys()):
                m = clip_modes[idx - 1] if idx - 1 < len(clip_modes) else "draft"
                with _LOCK:
                    q = _load(pid)
                    q["scenes"][idx - 1][m] = {"file": None, "status": "running",
                                               "error": None}
                    q["film"]["qc"]["note"] = (f"auto-fixing scene {idx} "
                                               f"(round {rnd + 1}): re-rolling {m}")
                    _save(q)
                _animate(pid, idx, m)
                q = _load(pid)
                if q["scenes"][idx - 1][m]["status"] != "done":
                    with _LOCK:
                        q["film"]["qc"]["note"] = (f"auto-fix stopped: scene {idx} "
                                                   f"re-render failed")
                        _save(q)
                    return
            _assemble(pid, film_mode)
            p = _load(pid)
            if p["film"]["status"] != "done":
                return
    except Exception as e:
        with _LOCK:
            p = _load(pid)
            p["film"]["qc"]["status"] = "unavailable"
            p["film"]["qc"]["error"] = str(e)[:300]
            _save(p)


# ───────────────────── routes ─────────────────────

def register(app, ui_dir):

    def _spawn(fn, *a):
        threading.Thread(target=fn, args=a, daemon=True).start()

    @app.route("/director")
    def director_page():
        return send_from_directory(ui_dir, "director.html")

    @app.route("/api/dir/projects")
    def dir_projects():
        out = []
        if PROJ_DIR.exists():
            for f in PROJ_DIR.glob("*/project.json"):
                try:
                    p = json.loads(f.read_text())
                    out.append({"id": p["id"], "title": p["concept"]["title"] or "(untitled)",
                                "updated": p.get("updated", 0)})
                except Exception:
                    pass
        out.sort(key=lambda x: -x["updated"])
        return jsonify(out)

    @app.route("/api/dir/project", methods=["POST"])
    def dir_new_project():
        return jsonify(_new_project())

    @app.route("/api/dir/project/<pid>")
    def dir_get_project(pid):
        p = _load(pid)
        if not p:
            return jsonify({"error": "no such project"}), 404
        return jsonify(p)

    @app.route("/api/dir/project/<pid>/chat", methods=["POST"])
    def dir_chat(pid):
        p = _load(pid)
        if not p:
            return jsonify({"error": "no such project"}), 404
        msg = (request.get_json(force=True).get("message") or "").strip()
        if not msg:
            return jsonify({"error": "empty message"}), 400
        try:
            raw = _chat_llm(p, msg)
        except Exception as e:
            return jsonify({"error": f"local LLM (:9420) unreachable: {e}"}), 502
        parsed = _extract_json(raw)
        reply = (parsed or {}).get("reply") or raw.strip()
        with _LOCK:
            p = _load(pid)
            p["chat"].append({"role": "user", "text": msg, "ts": time.time()})
            p["chat"].append({"role": "assistant", "text": reply, "ts": time.time()})
            if parsed:
                _apply_chat_result(p, parsed)
            _save(p)
        return jsonify(p)

    def _scene_or_404(pid, idx):
        p = _load(pid)
        if not p or idx < 1 or idx > len(p["scenes"]):
            return None, None
        return p, p["scenes"][idx - 1]

    @app.route("/api/dir/scene/<pid>/<int:idx>/still", methods=["POST"])
    def dir_still(pid, idx):
        p, s = _scene_or_404(pid, idx)
        if not s:
            return jsonify({"error": "no such scene"}), 404
        if s["locked"]:
            return jsonify({"error": "scene is locked"}), 409
        reroll = bool((request.get_json(silent=True) or {}).get("reroll"))
        with _LOCK:
            p = _load(pid)
            st = p["scenes"][idx - 1]["still"]
            if st["status"] == "running":
                return jsonify({"error": "already rendering"}), 409
            if reroll:
                st["seed"] += 1000
            st["status"] = "running"
            st["source"] = "flux"
            st["qc"] = {"status": "none", "notes": ""}
            _save(p)
        _spawn(_gen_still, pid, idx)
        return jsonify(_load(pid))

    @app.route("/api/dir/scene/<pid>/<int:idx>/upload", methods=["POST"])
    def dir_upload_still(pid, idx):
        p, s = _scene_or_404(pid, idx)
        if not s:
            return jsonify({"error": "no such scene"}), 404
        if s["locked"]:
            return jsonify({"error": "scene is locked"}), 409
        f = request.files.get("image")
        if not f:
            return jsonify({"error": "no image"}), 400
        png = _pdir(pid) / f"still_{idx:02d}.png"
        f.save(str(png))
        with _LOCK:
            p = _load(pid)
            p["scenes"][idx - 1]["still"].update(
                {"file": png.name, "status": "done", "source": "upload",
                 "qc": {"status": "running", "notes": ""}})
            _save(p)

        def qc_it():
            verdict, notes = _qc_still(p, p["scenes"][idx - 1], png)
            with _LOCK:
                q = _load(pid)
                q["scenes"][idx - 1]["still"]["qc"] = {"status": verdict, "notes": notes}
                _save(q)
        _spawn(qc_it)
        return jsonify(_load(pid))

    @app.route("/api/dir/scene/<pid>/<int:idx>/approve", methods=["POST"])
    def dir_approve(pid, idx):
        p, s = _scene_or_404(pid, idx)
        if not s:
            return jsonify({"error": "no such scene"}), 404
        if s["still"]["status"] != "done":
            return jsonify({"error": "no still to approve"}), 400
        with _LOCK:
            p = _load(pid)
            s = p["scenes"][idx - 1]
            s["locked"] = True
            _save(p)
        if s["still"].get("source") == "flux":
            _bank_add("still_approved", {
                "project": pid, "style": p["concept"]["style"],
                "desc": s["desc"], "motion": s["motion"],
                "seed": s["still"]["seed"],
                "prompt": _still_prompt(p, s)})
        return jsonify(_load(pid))

    @app.route("/api/dir/scene/<pid>/<int:idx>/unlock", methods=["POST"])
    def dir_unlock(pid, idx):
        p, s = _scene_or_404(pid, idx)
        if not s:
            return jsonify({"error": "no such scene"}), 404
        with _LOCK:
            p = _load(pid)
            p["scenes"][idx - 1]["locked"] = False
            _save(p)
        return jsonify(_load(pid))

    @app.route("/api/dir/scene/<pid>/<int:idx>/animate", methods=["POST"])
    def dir_animate(pid, idx):
        p, s = _scene_or_404(pid, idx)
        if not s:
            return jsonify({"error": "no such scene"}), 404
        if s["still"]["status"] != "done":
            return jsonify({"error": "render the still first"}), 400
        if _forge_busy():
            return jsonify({"error": "Song Forge is rendering a customer song — "
                                     "GPU is theirs, try again in a few minutes"}), 409
        mode = (request.get_json(silent=True) or {}).get("mode", "draft")
        if mode not in ("draft", "final"):
            return jsonify({"error": "mode must be draft|final"}), 400
        with _LOCK:
            p = _load(pid)
            if p["scenes"][idx - 1][mode]["status"] == "running":
                return jsonify({"error": "already rendering"}), 409
            p["scenes"][idx - 1][mode] = {"file": None, "status": "running", "error": None}
            _save(p)
        _spawn(_animate, pid, idx, mode)
        return jsonify(_load(pid))

    @app.route("/api/dir/project/<pid>/song", methods=["POST"])
    def dir_song(pid):
        p = _load(pid)
        if not p:
            return jsonify({"error": "no such project"}), 404
        if _forge_busy():
            return jsonify({"error": "Song Forge is rendering a customer song — "
                                     "try again in a few minutes"}), 409
        if p["song"]["status"] == "running":
            return jsonify({"error": "score already rendering"}), 409
        with _LOCK:
            p = _load(pid)
            p["song"].update({"status": "running", "error": None})
            _save(p)
        _spawn(_make_song, pid)
        return jsonify(_load(pid))

    @app.route("/api/dir/project/<pid>/assemble", methods=["POST"])
    def dir_assemble(pid):
        p = _load(pid)
        if not p:
            return jsonify({"error": "no such project"}), 404
        mode = (request.get_json(silent=True) or {}).get("mode", "preview")
        with _LOCK:
            p = _load(pid)
            p["film"]["status"] = "running"
            _save(p)
        _spawn(_assemble, pid, mode)
        return jsonify(_load(pid))

    @app.route("/api/dir/project/<pid>/qc", methods=["POST"])
    def dir_qc(pid):
        p = _load(pid)
        if not p:
            return jsonify({"error": "no such project"}), 404
        if p["film"]["status"] != "done":
            return jsonify({"error": "assemble the film first"}), 400
        autofix = bool((request.get_json(silent=True) or {}).get("autofix", True))
        with _LOCK:
            p = _load(pid)
            p["film"]["qc"]["status"] = "running"
            _save(p)
        _spawn(_run_film_qc, pid, autofix)
        return jsonify(_load(pid))

    @app.route("/api/dir/asset/<pid>/<path:name>")
    def dir_asset(pid, name):
        return send_from_directory(_pdir(pid), name)

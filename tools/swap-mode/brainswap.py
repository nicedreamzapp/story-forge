#!/usr/bin/env python3
"""brainswap: SWAP MODE for a local "brain" model next to Story Forge on the M5 (10/30 local ladder).

One model in memory at a time. The brain (any mlx_lm.server model) is warm while it plans and writes. The moment a
heavy Story Forge step starts (a forge_guard render lease, or a heavy render process), the idle brain is unloaded;
the brain's next request WAITS until the heavy step is gone and the room is back, then the brain reloads and the
request is answered. The agent keeps the whole conversation client side, so nothing is lost: a reload is a re-prefill.

Wiring (no change to any model's behavior):
  agent.py --http--> freebridge test instance (Anthropic->OpenAI) --> THIS (127.0.0.1:8795) --> mlx_lm.server :8794
  It stands in for the Liquid tap on :8795 while the ladder runs and answers the same /liquid/* API, so forge_guard's
  existing yield call (POST /liquid/stop?if_idle=1 when a lease is refused) reaches it. Its lease is named
  "liquid-lfm-<short>" so forge_guard counts it under the registered "liquid" label (mlx_lm.server) and may seat it on
  measured headroom like Liquid.
Every load / unload / wait is one line in swaps.jsonl; per-request stats in requests.jsonl (same fields as tap.py).
  GET  /liquid/status   POST /liquid/ensure   POST /liquid/stop[?if_idle=1]   GET /swap/stats
Env: BS_MODEL (HF id), BS_SHORT, BS_LEASE_GB, BS_NEED_GB, BS_MAX_TOKENS, BS_LOGDIR, BS_PY, BS_EXTRA."""
import json, os, re, signal, subprocess, threading, time, urllib.request, urllib.error
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler

MODEL = os.environ["BS_MODEL"]
SHORT = os.environ.get("BS_SHORT", "brain")
LEASE_NAME = "liquid-lfm-" + SHORT
LEASE_GB = float(os.environ.get("BS_LEASE_GB", "57"))
NEED_GB = float(os.environ.get("BS_NEED_GB", str(LEASE_GB + 8)))
MAX_TOKENS = os.environ.get("BS_MAX_TOKENS", "16384")
PY = os.path.expanduser(os.environ.get("BS_PY", "~/liquid-venv/bin/python"))
EXTRA = os.environ.get("BS_EXTRA", "").split()
LOGD = os.path.expanduser(os.environ.get("BS_LOGDIR", "~/.local/brainswap/" + SHORT))
os.makedirs(LOGD, exist_ok=True)
UP_PORT = 8794
UP = "http://127.0.0.1:%d" % UP_PORT
GUARD = "http://127.0.0.1:8790"
WAIT_MAX_S = float(os.environ.get("BS_WAIT_MAX_S", "5400"))   # a request waits up to 90 min for a render to finish
IDLE_S = float(os.environ.get("BS_IDLE_S", "2700"))           # safety unload if nobody calls for 45 min
YIELD_MIN_IDLE_S = 3
# 10/30: the Liquid tap's reasoning-loop cutter flagged legit JSON drafting as a loop (Qwen 04:38); off for the ladder
LOOP_CUT = os.environ.get("BS_LOOP_CUT", "0") == "1"
LOAD_TIMEOUT_S = 600
# What counts as a heavy Story Forge step (forge_guard lease names / hog labels). Small helpers (kokoro, whisper) don't.
HEAVY_LEASES = ("storyforge-", "ltx25-", "chatterbox", "film-qc", "design_check", "callout_check", "hive-ltx2",
                "ltx2-render", "storyforge")
HEAVY_HOGS = ("flux", "wan", "ltx25", "ltx2", "chatterbox", "film_qc", "qwen_vl", "storyforge")
STATE = {"in_flight": 0, "last_done": time.time(), "loading": False, "lease": None, "why_down": "", "proc": None,
         "swaps_out": 0, "swaps_in": 0, "swap_s": 0.0, "wait_s": 0.0}
LOCK = threading.Lock()
LOAD_LOCK = threading.Lock()
SWAPS, SLIM, FULL = (os.path.join(LOGD, n) for n in ("swaps.jsonl", "requests.jsonl", "requests-full.jsonl"))
MALFORMED = re.compile(r"<\|tool_call_start\|>|<\|tool_call_end\|>|<tool_call>|<function=", re.S)


def append(path, obj):
    with open(path, "a") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


def event(kind, **kw):
    append(SWAPS, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "event": kind, "model": MODEL, **kw})


def up():
    try:
        with urllib.request.urlopen(UP + "/v1/models", timeout=3) as r:
            return r.status == 200
    except Exception:
        return False


def headroom_gb():
    try:
        vm = subprocess.run(["vm_stat"], capture_output=True, text=True, timeout=5).stdout
        sw = subprocess.run(["sysctl", "-n", "vm.swapusage"], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return 0.0
    page = int((re.search(r"page size of (\d+)", vm) or [0, 16384])[1])
    pages = sum(int((re.search(r"%s:\s+(\d+)" % k, vm) or [0, 0])[1])
                for k in ("Pages free", "Pages inactive", "Pages speculative", "Pages purgeable"))
    m = re.search(r"used\s*=\s*([0-9.]+)M", sw)
    return pages * page / 2**30 - (float(m.group(1)) / 1024 if m else 0.0)


def guard(method, path, body=None, timeout=10):
    req = urllib.request.Request(GUARD + path, method=method, data=json.dumps(body).encode() if body is not None else None,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, json.loads(r.read().decode() or "{}")
    except urllib.error.HTTPError as e:
        try:
            return e.code, json.loads(e.read().decode() or "{}")
        except Exception:
            return e.code, {}
    except Exception:
        return 0, None


HEAVY_PROC = re.compile(os.environ.get("BS_HEAVY_PROC",
    r"bin/make-promo|bin/make-ltx25|bin/forge-shot|ltx-2-mlx|mflux-generate|chatterbox|"
    r"(film_qc|design_check|callout_check|promo_voice|promo_gates|promo_footage|words_align)\.py"))
SKIP_FIRST = {"grep", "rg", "cat", "tail", "head", "sed", "less", "awk", "vim", "nano", "ls", "wc", "find", "pgrep", "ps"}


def heavy_procs():
    """Story Forge render processes running right now (the real programs, not a grep/tail that names them)."""
    try:
        ps = subprocess.run(["ps", "-axo", "pid=,command="], capture_output=True, text=True, timeout=5).stdout
    except Exception:
        return []
    out = []
    for line in ps.splitlines():
        pid, _, cmd = line.strip().partition(" ")
        if int(pid or 0) == os.getpid() or "brainswap" in cmd or "mlx_lm.server" in cmd:
            continue
        toks = cmd.split()
        first = os.path.basename(toks[0]) if toks else ""
        if first in SKIP_FIRST or (first in ("sh", "bash", "zsh", "nohup") and len(toks) > 1 and toks[1] == "-c"):
            continue
        m = HEAVY_PROC.search(cmd)
        if m:
            out.append("%s(pid %s)" % (m.group(0).split("/")[-1], pid))
    return out


def heavy_now():
    """Names of heavy Story Forge steps holding or using memory right now (never the brain itself)."""
    procs = heavy_procs()
    code, st = guard("GET", "/api/state", timeout=8)
    if code != 200 or not st:
        return procs
    out = procs + [l["name"] for l in st.get("leases", [])
           if l["name"].startswith(HEAVY_LEASES) and not l["name"].startswith("liquid-lfm")]
    out += ["%s(pid %s)" % (h.get("label"), h.get("pid")) for h in st.get("hogs", [])
            if h.get("label") in HEAVY_HOGS and float(h.get("rss_gb") or h.get("gb") or 0) >= 1.5]
    return out


def _start_locked():
    log = open(os.path.join(LOGD, "server.log"), "a")
    srv = os.environ.get("BS_SERVER_SCRIPT")   # 10/30: the checkpointing launcher for hybrid models (Qwen 3.8)
    cmd = ([PY, os.path.expanduser(srv)] if srv else [PY, "-m", "mlx_lm.server"]) + ["--model", MODEL, "--host", "127.0.0.1", "--port", str(UP_PORT),
           "--temp", "0", "--max-tokens", MAX_TOKENS,
           # 10/30: the default 10-entry prompt cache grew Qwen from 57 to 65 GB in 2 min; one agent = one live cache
           "--prompt-cache-size", os.environ.get("BS_CACHE_N", "2"),
           "--prompt-cache-bytes", str(int(float(os.environ.get("BS_CACHE_GB", "24")) * 2**30)), *EXTRA]
    STATE["proc"] = subprocess.Popen(cmd, stdout=log, stderr=subprocess.STDOUT, start_new_session=True,
                                     env={**os.environ, "HF_HUB_OFFLINE": "1"})


def _warm():
    """mlx_lm.server loads weights on the first request: a 1-token request makes 'up' mean 'loaded'."""
    b = json.dumps({"model": MODEL, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 1}).encode()
    urllib.request.urlopen(urllib.request.Request(UP + "/v1/chat/completions", b, {"Content-Type": "application/json"}),
                           timeout=LOAD_TIMEOUT_S).read()


def _reap_dead():
    """The server died under us (forge_guard SIGTERM, crash): drop its lease, or our own dead lease blocks the reload
    (10/30 04:12, the first Qwen run waited forever on its own 57 GB lease)."""
    p = STATE["proc"]
    if p is not None and p.poll() is not None:
        event("server_died", returncode=p.returncode, lease=STATE["lease"])
        if STATE["lease"]:
            guard("DELETE", "/api/reserve?id=%s" % STATE["lease"])
        STATE["lease"], STATE["proc"], STATE["why_down"] = None, None, "died rc=%s" % p.returncode


def ensure(asked_by="request"):
    _reap_dead()
    if up() and STATE["proc"] is not None:
        return True, ""
    with LOAD_LOCK:
        _reap_dead()
        if up() and STATE["proc"] is not None:
            return True, ""
        t0 = time.time()
        waited_for, last_note = set(), 0
        while True:
            h = heavy_now()
            room = headroom_gb()
            if not h and room >= NEED_GB:
                code, d = guard("POST", "/api/reserve", {"name": LEASE_NAME, "gb": LEASE_GB, "ttl": 1800})
                if code in (200, 0):
                    STATE["lease"] = (d or {}).get("id") if code == 200 else None
                    break
                h = ["forge_guard: %s" % (d or {}).get("reason", "refused")]
            waited_for.update(x.split(":")[0] for x in h)
            if time.time() - last_note > 60:
                last_note = time.time()
                event("waiting", for_=sorted(waited_for), room_gb=round(room, 1), waited_s=round(time.time() - t0))
            if time.time() - t0 > WAIT_MAX_S:
                event("wait_timeout", for_=sorted(waited_for))
                return False, "the brain model waited %d min for a render to finish and gave up" % (WAIT_MAX_S // 60)
            time.sleep(3)
        wait_s = time.time() - t0
        STATE["loading"] = True
        t1 = time.time()
        try:
            _start_locked()
            while time.time() - t1 < LOAD_TIMEOUT_S and not up():
                if STATE["proc"].poll() is not None:
                    break
                time.sleep(0.5)
            _warm()
        except Exception as e:
            event("load_failed", error=str(e)[:200])
            _stop_locked("load failed")
            return False, "the brain model failed to load: %s" % e
        finally:
            STATE["loading"] = False
        load_s = time.time() - t1
        with LOCK:
            STATE["swaps_in"] += 1
            STATE["swap_s"] += load_s
            STATE["wait_s"] += wait_s
            STATE["last_done"] = time.time()
        event("load", load_s=round(load_s, 1), waited_s=round(wait_s, 1), waited_for=sorted(waited_for),
              asked_by=asked_by, room_gb=round(headroom_gb(), 1))
        return True, ""


def _stop_locked(why):
    t0 = time.time()
    p = STATE["proc"]
    if p is not None and p.poll() is None:
        try:
            os.killpg(p.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        for _ in range(60):
            if p.poll() is not None:
                break
            time.sleep(0.5)
        if p.poll() is None:
            os.killpg(p.pid, signal.SIGKILL)
            p.wait()
    subprocess.run(["pkill", "-TERM", "-f", "mlx_lm.server.*--port %d" % UP_PORT])
    if STATE["lease"]:
        guard("DELETE", "/api/reserve?id=%s" % STATE["lease"])
    unload_s = time.time() - t0
    STATE["lease"], STATE["proc"], STATE["why_down"] = None, None, why
    return unload_s


def stop(why, if_idle=False):
    with LOAD_LOCK:
        with LOCK:
            quiet = time.time() - STATE["last_done"]
            if if_idle and (STATE["in_flight"] or quiet < YIELD_MIN_IDLE_S):
                return False, "busy"
        if STATE["proc"] is None and not up():
            return True, "already down"
        unload_s = _stop_locked(why)
        with LOCK:
            STATE["swaps_out"] += 1
            STATE["swap_s"] += unload_s
        event("unload", why=why, unload_s=round(unload_s, 1), room_gb=round(headroom_gb(), 1))
        return True, "stopped"


def keeper():
    beat = 0
    while True:
        time.sleep(2)
        try:
            if STATE["loading"] or STATE["proc"] is None:
                continue
            with LOCK:
                idle = STATE["in_flight"] == 0
                quiet = time.time() - STATE["last_done"]
            if idle and quiet >= YIELD_MIN_IDLE_S:
                h = heavy_now()
                if h:
                    stop("swap out for " + ", ".join(h)[:200], if_idle=True)
                    continue
            if idle and quiet > IDLE_S:
                stop("idle %d min" % (IDLE_S // 60), if_idle=True)
            beat += 2
            if beat >= 300 and STATE["lease"]:
                beat = 0
                guard("POST", "/api/heartbeat", {"id": STATE["lease"], "ttl": 1800})
        except Exception as e:
            event("keeper_error", error=str(e)[:200])


def looping(chunks):
    words = "".join(chunks[-400:]).split()[-200:]
    if len(words) < 150:
        return False
    grams = [" ".join(words[i:i + 4]).lower() for i in range(len(words) - 3)]
    return len(set(grams)) / len(grams) < 0.7


class H(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, *a):
        pass

    def _send(self, code, body, ctype="application/json"):
        b = body if isinstance(body, bytes) else json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def do_GET(self):
        if self.path.startswith("/liquid/status") or self.path.startswith("/swap/stats"):
            with LOCK:
                st = {"model": MODEL, "up": up(), "loading": STATE["loading"], "in_flight": STATE["in_flight"],
                      "idle_s": round(time.time() - STATE["last_done"]), "lease": STATE["lease"],
                      "why_down": STATE["why_down"], "swaps_out": STATE["swaps_out"], "swaps_in": STATE["swaps_in"],
                      "swap_s": round(STATE["swap_s"], 1), "wait_s": round(STATE["wait_s"], 1)}
            return self._send(200, st)
        if self.path.startswith("/v1/models") and not up():
            return self._send(200, {"object": "list", "data": [{"id": MODEL, "object": "model", "loaded": False}]})
        try:
            with urllib.request.urlopen(UP + self.path, timeout=10) as r:
                return self._send(r.status, r.read(), r.headers.get("Content-Type", "application/json"))
        except Exception as e:
            return self._send(502, {"error": {"message": "brain server not up: %s" % type(e).__name__}})

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length") or 0))
        if self.path.startswith("/liquid/ensure"):
            ok, why = ensure("ensure")
            return self._send(200, {"ok": True}) if ok else self._send(503, {"ok": False, "error": {"message": why}})
        if self.path.startswith("/liquid/stop"):
            ok, why = stop("asked over http" + (" (forge_guard yield)" if "if_idle=1" in self.path else ""),
                           if_idle="if_idle=1" in self.path)
            return self._send(200 if ok else 409, {"stopped": ok, "reason": why})
        # strict one-at-a-time: a heavy step is running, so the brain steps out before it answers and waits for it
        h = heavy_now()
        if h and STATE["proc"] is not None:
            stop("swap out before answering, for " + ", ".join(h)[:200])
        with LOCK:
            STATE["in_flight"] += 1
        try:
            ok, why = ensure()
            if not ok:
                return self._send(503, {"error": {"message": why, "type": "brain_not_loaded"}})
            return self._post(raw)
        finally:
            with LOCK:
                STATE["in_flight"] -= 1
                STATE["last_done"] = time.time()

    def _post(self, raw):
        try:
            body = json.loads(raw)
        except Exception:
            return self._send(400, {"error": {"message": "bad json"}})
        body["model"] = MODEL
        if not self.path.startswith("/v1/chat/completions") or body.get("stream"):
            req = urllib.request.Request(UP + self.path, data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=1800) as r:
                    return self._send(r.status, r.read(), r.headers.get("Content-Type", "application/json"))
            except urllib.error.HTTPError as e:
                return self._send(e.code, e.read())
        body["stream"] = True
        body["stream_options"] = {"include_usage": True}
        t0 = time.time(); t1 = None; tlast = t0
        content, reasoning, calls, usage, fin, rid = [], [], {}, {}, None, None
        n_content = n_reason = 0
        loop_cut = False
        req = urllib.request.Request(UP + "/v1/chat/completions", data=json.dumps(body).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=1800) as r:
                for line in r:
                    line = line.decode("utf-8", "replace").strip()
                    if not line.startswith("data:"):
                        continue
                    d = line[5:].strip()
                    if d == "[DONE]":
                        break
                    try:
                        j = json.loads(d)
                    except Exception:
                        continue
                    rid = j.get("id") or rid
                    if j.get("usage"):
                        usage = j["usage"]
                    for ch in j.get("choices") or []:
                        dl = ch.get("delta") or {}
                        if dl.get("content") or dl.get("reasoning") or dl.get("tool_calls"):
                            t1 = t1 or time.time(); tlast = time.time()
                        if dl.get("content"):
                            content.append(dl["content"]); n_content += 1
                        if dl.get("reasoning"):
                            reasoning.append(dl["reasoning"]); n_reason += 1
                            if LOOP_CUT and n_reason >= 600 and n_reason % 64 == 0 and not calls and looping(reasoning):
                                loop_cut = True
                        for tc in dl.get("tool_calls") or []:
                            i = tc.get("index", len(calls))
                            cur = calls.setdefault(i, {"id": tc.get("id"), "type": "function",
                                                       "function": {"name": "", "arguments": ""}})
                            f = tc.get("function") or {}
                            cur["id"] = cur["id"] or tc.get("id")
                            cur["function"]["name"] += f.get("name") or ""
                            cur["function"]["arguments"] += f.get("arguments") or ""
                        fin = ch.get("finish_reason") or fin
                    if loop_cut:
                        fin = "length"
                        break
        except urllib.error.HTTPError as e:
            err = e.read()
            append(SLIM, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "error": e.code, "body": err[:300].decode("utf-8", "replace")})
            return self._send(e.code, err)
        except Exception as e:
            append(SLIM, {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "error": type(e).__name__, "body": str(e)[:300]})
            return self._send(502, {"error": {"message": "brain server failed: %s" % type(e).__name__}})
        t2 = time.time()
        text, rtext = "".join(content), "".join(reasoning)
        tcs = [calls[k] for k in sorted(calls)]
        for i, tc in enumerate(tcs):
            tc["id"] = tc.get("id") or "call_%d_%d" % (int(t0), i)
        msg = {"role": "assistant", "content": text or None}
        if rtext:
            msg["reasoning"] = rtext
        if tcs:
            msg["tool_calls"] = tcs
        pt, ct = usage.get("prompt_tokens", 0), usage.get("completion_tokens", n_content + n_reason)
        ttft = (t1 or t2) - t0
        stat = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "prompt_tokens": pt, "completion_tokens": ct,
                "ttft_s": round(ttft, 3), "total_s": round(t2 - t0, 3),
                "gen_tps": round((ct - 1) / (tlast - t1), 1) if t1 and tlast > t1 and ct > 1 else None,
                "tool_calls": len(tcs), "tool_names": [c["function"]["name"] for c in tcs], "finish": fin,
                "n_messages": len(body.get("messages") or []), "malformed_in_text": bool(text and MALFORMED.search(text)),
                "loop_cut": loop_cut}
        append(SLIM, stat)
        last = (body.get("messages") or [{}])[-1]
        append(FULL, {**stat, "last_in": str(last.get("content"))[:3000], "content": text,
                      "reasoning": rtext if len(rtext) <= 6000 else rtext[:3000] + "\n[...]\n" + rtext[-3000:],
                      "tool_calls_raw": tcs})
        self._send(200, {"id": rid or "chatcmpl-brain", "object": "chat.completion", "created": int(t0), "model": MODEL,
                         "choices": [{"index": 0, "message": msg, "finish_reason": fin or ("tool_calls" if tcs else "stop")}],
                         "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct}})


def _on_term(signum, frame):
    """A killed tap must never leave its lease behind (10/26 + 10/30: a stale liquid-lfm lease blocked every reload)."""
    try:
        _stop_locked("tap stopping (signal %d)" % signum)
        event("tap_stop")
    finally:
        os._exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGINT, _on_term)
    # a lease this tap name left behind (crash) is released before we start
    _c, _st = guard("GET", "/api/state")
    for _l in (_st or {}).get("leases", []):
        if _l["name"] == LEASE_NAME:
            guard("DELETE", "/api/reserve?id=%s" % _l["id"])
    event("tap_start", lease_gb=LEASE_GB, need_gb=NEED_GB)
    threading.Thread(target=keeper, daemon=True).start()
    ThreadingHTTPServer(("127.0.0.1", 8795), H).serve_forever()

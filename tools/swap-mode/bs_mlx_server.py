#!/usr/bin/env python3
"""mlx_lm.server with a PROMPT-END CHECKPOINT and a cache that survives swaps (10/30 ladder, Qwen 3.8 rerun).

Why: Qwen 3.5/3.8 are hybrid models (linear-attention layers + full attention). Their cache can't be trimmed, so
mlx_lm reuses a cached entry only when its tokens are an exact prefix of the new prompt. The server stores
prompt + GENERATED tokens, and the next agent prompt re-renders that assistant turn differently (thinking dropped,
tool call re-serialized), so every step missed and re-read the whole ~50k-token context (85 s per step on 10/30).

Fix (no change to what the model sees or does):
  1. Before generating, prefill all but the last K prompt tokens, snapshot the cache, and store the snapshot under
     those tokens. The next request starts with exactly those tokens, so it reuses the snapshot and only prefills
     the new tail (the assistant turn + the tool result).
  2. On SIGTERM (swap-mode unload) the newest snapshot is written to BS_CKPT_FILE (safetensors); on the next start
     it's loaded back into the prompt cache, so a reload after a render doesn't start cold.
Usage: python bs_mlx_server.py <mlx_lm.server args>   env: BS_CKPT_FILE, BS_CKPT_TAIL (default 12)
"""
import copy, json, os, signal, sys, threading, time
import mlx.core as mx
import mlx_lm.server as S
from mlx_lm.models import cache as C

K = int(os.environ.get("BS_CKPT_TAIL", "12"))
CKPT_FILE = os.environ.get("BS_CKPT_FILE", "")
STATE = {"lru": None, "model_key": None, "tokens": None, "last": None, "pending": None}
LOCK = threading.Lock()


def log(msg):
    print("[ckpt] " + msg, file=sys.stderr, flush=True)


# 1) remember the full prompt tokens + the LRU instance of the request being served; seed a restored checkpoint
_orig_fetch = C.LRUPromptCache.fetch_nearest_cache


def fetch(self, model, tokens):
    with LOCK:
        STATE["lru"], STATE["model_key"], STATE["tokens"] = self, model, list(tokens)
        pend = STATE.pop("pending", None)
    if pend is not None:
        ptoks, pcache = pend
        self.insert_cache(model, ptoks, pcache, cache_type="user")
        log("restored checkpoint from disk: %d tokens" % len(ptoks))
    cache, rest = _orig_fetch(self, model, tokens)
    log("prompt %d tokens, reused %d, prefill %d" % (len(tokens), len(tokens) - len(rest), len(rest)))
    return cache, rest


C.LRUPromptCache.fetch_nearest_cache = fetch

# 2) prefill to the prompt end minus K, snapshot, store, then generate as usual
_orig_sg = S.stream_generate


def stream_generate(*args, **kw):
    cache = kw.get("prompt_cache")
    rest = list(kw.get("prompt") or [])
    full = STATE.get("tokens")
    if (cache is not None and full and len(rest) > K + 32 and not C.can_trim_prompt_cache(cache)
            and full[len(full) - len(rest):] == rest):
        pre, tail = rest[:-K], rest[-K:]
        model = kw["model"]
        step = 2048
        t0 = time.time()
        st = kw.get("stream")
        with mx.stream(st) if st is not None else mx.stream(mx.default_stream(mx.default_device())):
            for i in range(0, len(pre), step):
                model(mx.array(pre[i:i + step])[None], cache=cache)
                mx.eval([c.state for c in cache])
        snap = copy.deepcopy(cache)
        key = full[:len(full) - K]
        with LOCK:
            STATE["lru"].insert_cache(STATE["model_key"], key, snap, cache_type="user")
            STATE["last"] = (key, snap)
        log("checkpoint at %d tokens (prefilled %d in %.1fs)" % (len(key), len(pre), time.time() - t0))
        kw["prompt"] = tail
    return _orig_sg(*args, **kw)


S.stream_generate = stream_generate

# 3) single-request path only (the checkpoint hook lives there)
for _name in dir(S):
    _cls = getattr(S, _name)
    if isinstance(_cls, type) and hasattr(_cls, "_is_batchable"):
        _cls._is_batchable = lambda self, args: False


# 4) the cache survives a swap
def _save_and_exit(signum, frame):
    try:
        with LOCK:
            last = STATE.get("last")
        if CKPT_FILE and last is not None:
            t0 = time.time()
            key, snap = last
            C.save_prompt_cache(CKPT_FILE, snap, {"tokens": json.dumps(key)})
            log("saved checkpoint (%d tokens) in %.1fs" % (len(key), time.time() - t0))
    except Exception as e:
        log("save failed: %s" % e)
    os._exit(0)


if CKPT_FILE and os.path.exists(CKPT_FILE):
    try:
        t0 = time.time()
        pc, meta = C.load_prompt_cache(CKPT_FILE, return_metadata=True)
        STATE["pending"] = (json.loads(meta["tokens"]), pc)
        STATE["last"] = (json.loads(meta["tokens"]), pc)
        log("loaded checkpoint file (%s tokens) in %.1fs" % (len(json.loads(meta["tokens"])), time.time() - t0))
    except Exception as e:
        log("load failed: %s" % e)

signal.signal(signal.SIGTERM, _save_and_exit)
sys.argv[0] = "mlx_lm.server"
S.main()

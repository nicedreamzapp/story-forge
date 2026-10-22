#!/usr/bin/env python3
"""browser_acquire_driver — the half of bin/browser-acquire that runs ON THE MINI.

bin/browser-acquire (on the M5) copies this file and the reference images to the mini,
then runs:    cd ~/sf-acquire && python3 browser_acquire_driver.py job.json
It drives Matt's logged-in Brave through the browser broker (hidden lease tab, never
focus, never bb-show) and writes each take into job["outdir"] on the mini. Every take
prints one JSON line on stdout:  {"ok": true, "n": 1, "file": ..., "src": ..., "secs": ...}
or {"ok": false, "n": 1, "error": ...}. The M5 side copies the files back.

Backends (selectors probed against the live DOM 2026-10-22):
  chatgpt-image  NOT FOR PHOTOREAL PRODUCT SHOTS (Matt 2026-10-22: "horrible"; it invents parts/legs).
                 chatgpt.com: ProseMirror composer, hidden file inputs, send button,
                 result = <img alt^="Generated image"> fetched in-page with credentials.
  chatgpt-edit   same page, ONE CAD still, and the prompt asks for an EDIT of that exact image
                 (materials + light only, no part added/removed/moved). The default for products.
  grok-image     grok.com/imagine: upload ONE CAD still -> post page -> Image mode edit prompt -> new <img>.
  gemini-image   gemini.google.com: "Upload & tools" reveals a hidden image/* input; edit prompt; the new
                 <img> inside the last model-response (googleusercontent; fetched directly if CORS blocks).
  grok-video     grok.com/imagine: upload a still -> /imagine/post/<id>, "Make Video" menu
                 -> "Add Prompt" (first frame = the still), resolution/duration radios,
                 "Make video" submit, result = a new <video> under /generated/ fetched in-page.
                 With no ref it types the prompt in Video mode on /imagine (text-to-video).
"""
import base64, json, os, sys, time

sys.path.insert(0, os.path.expanduser("~/Scripts"))
from broker_client import lease  # noqa: E402

OWNER = "story-forge-acquire"


def log(**kw):
    print(json.dumps(kw), flush=True)


def note(msg):
    print(json.dumps({"note": msg}), flush=True)


class Page:
    def __init__(self, tab):
        self.t = tab

    def js(self, expr):
        return self.t.eval(expr)

    def wait(self, expr, timeout, every=2.0, what=""):
        end = time.time() + timeout
        while time.time() < end:
            try:
                v = self.js(expr)
            except Exception:
                v = None
            if v:
                return v
            time.sleep(every)
        raise TimeoutError(f"timed out after {timeout}s waiting for {what or expr[:80]}")

    def upload(self, selector, files):
        doc = self.t.send("DOM.getDocument", depth=-1, pierce=True)
        nid = self.t.send("DOM.querySelector", nodeId=doc["root"]["nodeId"], selector=selector)["nodeId"]
        if not nid:
            raise RuntimeError(f"no file input matches {selector}")
        self.t.send("DOM.setFileInputFiles", nodeId=nid, files=files)

    def type_into(self, selector, text):
        ok = self.js("(()=>{const e=[...document.querySelectorAll(%s)].filter(x=>x.getBoundingClientRect().width>0).pop();"
                     "if(!e)return false;e.focus();return true})()" % json.dumps(selector))
        if not ok:
            raise RuntimeError(f"no visible composer matches {selector}")
        self.t.send("Input.insertText", text=text)

    def pointer_open(self, selector):
        """Radix menus open on pointerdown, not click."""
        return self.js("(()=>{const b=document.querySelector(%s);if(!b)return false;"
                       "b.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0,pointerType:'mouse'}));return true})()"
                       % json.dumps(selector))

    def menu_pick(self, role, text):
        return self.js("(()=>{const m=[...document.querySelectorAll('[role=%s]')].filter(e=>e.innerText.trim()===%s).pop();"
                       "if(!m)return false;m.click();return true})()" % (role, json.dumps(text)))

    def escape(self):
        self.js("document.dispatchEvent(new KeyboardEvent('keydown',{key:'Escape',bubbles:true}))")

    def fetch_b64(self, url):
        """Download inside the page so the site's own cookies apply. Returns bytes."""
        b64 = self.js("""(async()=>{const r=await fetch(%s,{credentials:'include'});if(!r.ok)return 'ERR'+r.status;
            const b=new Uint8Array(await r.arrayBuffer());let s='';for(let i=0;i<b.length;i+=0x8000)
            s+=String.fromCharCode.apply(null,b.subarray(i,i+0x8000));return btoa(s)})()""" % json.dumps(url))
        if b64 and not b64.startswith("ERR"):
            return base64.b64decode(b64)
        if url.startswith("http"):
            # CORS-blocked CDN (Gemini's googleusercontent images): fetch outside the page with the
            # browser's own cookies for that host and its redirect targets (a bare GET is a 403).
            from urllib.parse import urlparse
            from urllib.request import Request, urlopen
            host = urlparse(url).netloc
            ck = self.t.send("Network.getCookies", urls=[url, f"https://{host}/", "https://www.google.com/",
                                                          "https://lh3.google.com/", "https://gemini.google.com/"])
            jar = "; ".join(f"{c['name']}={c['value']}" for c in ck.get("cookies", []))
            ua = self.js("navigator.userAgent") or "Mozilla/5.0"
            req = Request(url, headers={"User-Agent": ua, "Cookie": jar, "Referer": self.js("location.href") or ""})
            with urlopen(req, timeout=60) as r:
                return r.read()
        raise RuntimeError(f"download failed {b64} for {url[:100]}")

    def shot(self, path):
        r = self.t.send("Page.captureScreenshot", format="png")
        open(path, "wb").write(base64.b64decode(r["data"]))


# ---------------------------------------------------------------- chatgpt-image
CG_IMGS = ("JSON.stringify([...document.querySelectorAll('img')].filter(i=>/^Generated image/i.test(i.alt||'')"
           "&&i.complete&&i.naturalWidth>256).map(i=>i.src))")
CG_BUSY = ("!!document.querySelector('[data-testid=stop-button],button[aria-label*=\"Stop\"]')")


def chatgpt_image(p, job, n, out):
    p.t.goto("https://chatgpt.com/", wait=8)
    p.wait("!!document.querySelector('.ProseMirror')", 40, what="chatgpt composer")
    if job.get("refs"):
        sel = "input[type=file][accept*='image']:not([capture])"
        if not p.js("!!document.querySelector(%s)" % json.dumps(sel)):
            sel = "input[type=file]"
        p.upload(sel, job["refs"])
        # an attachment thumbnail appears and the send button stays disabled until the upload lands
        time.sleep(4)
    lead = "" if job["backend"] == "chatgpt-edit" else "Create an image. "
    p.type_into(".ProseMirror[contenteditable=true]", lead + job["prompt"])
    time.sleep(1.5)
    send = ("button[data-testid=send-button]:not([disabled]),button[aria-label='Send prompt']:not([disabled]),"
            "button[aria-label=Send]:not([disabled]),form button[type=submit]:not([disabled])")
    p.wait("!!document.querySelector(%s)" % json.dumps(send), 90, what="send button enabled (upload)")
    p.js("document.querySelector(%s).click()" % json.dumps(send))
    t0 = time.time()
    p.wait("location.pathname.startsWith('/c/')", 60, what="chat to start")
    # generated image: present, loaded, src stable, nothing streaming
    last, stable = None, 0
    while time.time() - t0 < job.get("timeout", 420):
        srcs = json.loads(p.js(CG_IMGS) or "[]")
        busy = p.js(CG_BUSY)
        cur = srcs[-1] if srcs else None
        if cur and cur == last and not busy:
            stable += 1
            if stable >= 3:
                break
        else:
            stable = 0
        last = cur
        time.sleep(5)
    else:
        p.shot(out + f".timeout_{n}.png")
        txt = p.js("(document.querySelector('[data-message-author-role=assistant]:last-of-type')||{}).innerText||''")
        raise TimeoutError(f"no generated image after {job.get('timeout', 420)}s; assistant said: {str(txt)[:300]}")
    data = p.fetch_b64(last)
    ext = ".png" if data[:4] == b"\x89PNG" else (".webp" if data[8:12] == b"WEBP" else ".jpg")
    path = f"{out}_{n}{ext}"
    open(path, "wb").write(data)
    return path, last, round(time.time() - t0), p.js("location.href")


def big_imgs(p, scope="document"):
    return json.loads(p.js("JSON.stringify([...%s.querySelectorAll('img')].filter(i=>i.complete&&i.naturalWidth>=400)"
                           ".map(i=>i.currentSrc||i.src))" % scope) or "[]")


def wait_new_image(p, before, job, n, out, scope="document", busy_js="false"):
    """Wait until an image that wasn't on the page before submit appears and stops changing."""
    t0, last, stable = time.time(), None, 0
    while time.time() - t0 < job.get("timeout", 420):
        new = [s for s in big_imgs(p, scope) if s not in before and not s.startswith("data:")]
        real = [s for s in new if s.startswith("http")]
        cur = (real or new)[-1] if new else None
        if cur and cur == last and not p.js(busy_js):
            stable += 1
            if stable >= 2:
                return cur, round(time.time() - t0)
        else:
            stable = 0
        last = cur
        time.sleep(5)
    p.shot(out + f".timeout_{n}.png")
    raise TimeoutError(f"no new image after {job.get('timeout', 420)}s")


def img_canvas(p, src):
    """Read a same-origin/blob <img> through a canvas at its natural size (PNG)."""
    d = p.js("""(()=>{const i=[...document.querySelectorAll('img')].find(x=>(x.currentSrc||x.src)===%s);if(!i)return null;
        const c=document.createElement('canvas');c.width=i.naturalWidth;c.height=i.naturalHeight;
        c.getContext('2d').drawImage(i,0,0);try{return c.toDataURL('image/png')}catch(e){return null}})()""" % json.dumps(src))
    return base64.b64decode(d.split(",", 1)[1]) if d and d.startswith("data:image") else None


def img_capture(p, src):
    """Last resort: screenshot the <img> element scaled up to its natural resolution."""
    r = json.loads(p.js("""(()=>{const i=[...document.querySelectorAll('img')].find(x=>(x.currentSrc||x.src)===%s);
        if(!i)return 'null';i.scrollIntoView({block:'center'});const b=i.getBoundingClientRect();
        return JSON.stringify({x:b.x+scrollX,y:b.y+scrollY,w:b.width,h:b.height,nw:i.naturalWidth})})()""" % json.dumps(src)) or "null")
    if not r or not r["w"]:
        return None
    scale = max(1.0, r["nw"] / r["w"])
    shot = p.t.send("Page.captureScreenshot", format="png", captureBeyondViewport=True,
                    clip={"x": r["x"], "y": r["y"], "width": r["w"], "height": r["h"], "scale": scale})
    note(f"image saved by element capture at {scale:.2f}x (download blocked)")
    return base64.b64decode(shot["data"])


def save_image(p, src, out, n):
    try:
        data = p.fetch_b64(src)
    except Exception as e:
        data = img_canvas(p, src) or img_capture(p, src)
        if not data:
            raise RuntimeError(f"could not save the image ({e})")
    ext = ".png" if data[:4] == b"\x89PNG" else (".webp" if data[8:12] == b"WEBP" else ".jpg")
    path = f"{out}_{n}{ext}"
    open(path, "wb").write(data)
    return path


# ---------------------------------------------------------------- grok-image
def grok_image(p, job, n, out):
    """Upload ONE CAD still -> its /imagine/post page -> type the edit in Image mode -> submit."""
    p.t.goto("https://grok.com/imagine", wait=8)
    p.wait("!!document.querySelector('[contenteditable=true]')", 40, what="grok composer")
    p.upload("input[type=file]", job["refs"][:1])
    p.wait("location.pathname.startsWith('/imagine/post/')", 90, what="grok to accept the still")
    time.sleep(4)
    p.js("[...document.querySelectorAll('button[aria-label=Image]')].forEach(b=>b.getAttribute('aria-pressed')!=='true'&&b.click())")
    time.sleep(1)
    before = set(big_imgs(p))
    p.type_into("[contenteditable=true]", job["prompt"])
    time.sleep(1.0)
    sub = ("[...document.querySelectorAll('button[aria-label=Edit],button[aria-label=Submit],button[type=submit]')]"
           ".filter(b=>!b.disabled&&b.getBoundingClientRect().width>0)")
    if not p.js("(()=>{const b=%s.pop();if(!b)return false;b.click();return true})()" % sub):
        raise RuntimeError("grok-image: edit/submit button not found/enabled")
    src, secs = wait_new_image(p, before, job, n, out)
    if p.js(UPSELL):
        raise RuntimeError("grok-image: upsell dialog (paid-only option)")
    return save_image(p, src, out, n), src, secs, p.js("location.href")


# ---------------------------------------------------------------- gemini-image
GEM_BUSY = "!!document.querySelector('button[aria-label*=\"Stop\"],.loading-indicator,mat-progress-bar')"


def gemini_image(p, job, n, out):
    """Gemini (Nano Banana) edit: 'Upload & tools' exposes a hidden image/* input; send; wait for the reply image."""
    p.t.goto("https://gemini.google.com/app", wait=8)
    p.wait("!!document.querySelector('.ql-editor[contenteditable=true]')", 40, what="gemini composer")
    p.js("document.querySelector('button[aria-label=\"Upload & tools\"]')?.click()")
    time.sleep(1.5)
    p.upload("input[type=file][accept='image/*']", job["refs"][:1])
    time.sleep(5)
    p.escape()
    before = set(big_imgs(p))
    p.type_into(".ql-editor[contenteditable=true]", job["prompt"])
    time.sleep(1.5)
    send = ("[...document.querySelectorAll('button')].filter(b=>/send message/i.test(b.getAttribute('aria-label')||'')"
            "&&b.getAttribute('aria-disabled')!=='true'&&!b.disabled)")
    p.wait("%s.length>0" % send, 90, what="gemini send enabled (upload)")
    p.js("%s[0].click()" % send)
    # only images inside model responses count, never the uploaded thumbnail
    src, secs = wait_new_image(p, before, job, n, out, busy_js=GEM_BUSY,
                               scope="(document.querySelector('model-response:last-of-type')||document.createElement('div'))")
    return save_image(p, src, out, n), src, secs, p.js("location.href")


# ---------------------------------------------------------------- grok-video
GV_SRCS =("JSON.stringify([...document.querySelectorAll('video')].map(v=>v.currentSrc||v.src||'')"
           ".filter(s=>/\\/generated\\//.test(s)))")


UPSELL = ("(()=>{const d=[...document.querySelectorAll('[role=dialog]')].find(x=>/Unlock|Upgrade|Get Plus|Claim offer/i.test(x.innerText));"
          "if(!d)return false;const c=[...d.querySelectorAll('button')].find(b=>/close/i.test(b.getAttribute('aria-label')||''))"
          "||[...d.querySelectorAll('button')].find(b=>!b.innerText.trim());if(c)c.click();return true})()")


def grok_set(p, label, value):
    """Pick a radio in a composer menu. Paid-only options pop an upsell; close it and keep the default."""
    if not value:
        return True
    # the composer renders a hidden twin of each option button; read and open the visible one
    vis = "[...document.querySelectorAll('button[aria-label=\"%s\"]')].find(x=>x.innerText.trim())" % label
    cur = (p.js("(%s||{innerText:''}).innerText.trim()" % vis) or "").strip()
    if cur == value:
        return True
    p.js("(()=>{const b=%s;if(b)b.dispatchEvent(new PointerEvent('pointerdown',{bubbles:true,button:0,pointerType:'mouse'}))})()" % vis)
    time.sleep(1.2)
    picked = p.menu_pick("menuitemradio", value)
    time.sleep(1.5)
    if p.js(UPSELL):
        note(f"grok: {label} {value} needs a paid plan; kept the free default")
        time.sleep(1.0)
        return False
    if not picked:
        note(f"grok: {label} option {value!r} not offered; kept the default")
    return picked


def grok_video(p, job, n, out):
    p.t.goto("https://grok.com/imagine", wait=8)
    p.wait("!!document.querySelector('[contenteditable=true]')", 40, what="grok composer")
    if job.get("refs"):
        p.upload("input[type=file]", job["refs"][:1])
        p.wait("location.pathname.startsWith('/imagine/post/')", 90, what="grok to accept the still")
        p.wait("!!document.querySelector('button[aria-label=\"Make Video\"]')", 40, what="Make Video menu")
        time.sleep(2)
        p.pointer_open('button[aria-label="Make Video"]')
        time.sleep(1.2)
        if not p.menu_pick("menuitem", "Add Prompt"):
            raise RuntimeError("grok: 'Add Prompt' menu item not found")
        p.wait("!!document.querySelector('button[aria-label=\"Make video\"]')", 20, what="video composer")
    else:
        p.js("document.querySelector('button[aria-label=Video]')?.click()")
        time.sleep(1.5)
    grok_set(p, "Video resolution", job.get("resolution"))
    grok_set(p, "Video duration", f"{int(job['duration'])}s" if job.get("duration") else None)
    if job.get("refs") and not p.js("!!document.querySelector('button[aria-label=\"Make video\"]')"):
        raise RuntimeError("grok: video composer closed while setting options")
    before = set(json.loads(p.js(GV_SRCS) or "[]"))
    p.type_into("[contenteditable=true]", job["prompt"])
    time.sleep(1.0)
    submit = 'button[aria-label="Make video"]:not([disabled])' if job.get("refs") else 'button[type=submit]:not([disabled]),button[aria-label="Submit"]:not([disabled])'
    if not p.js("(()=>{const b=document.querySelector(%s);if(!b)return false;b.click();return true})()" % json.dumps(submit)):
        raise RuntimeError("grok: submit button not found/enabled")
    t0 = time.time()
    while time.time() - t0 < job.get("timeout", 600):
        new = [s for s in json.loads(p.js(GV_SRCS) or "[]") if s not in before]
        if new:
            src = new[-1]
            time.sleep(3)
            data = p.fetch_b64(src)
            if len(data) > 50_000 and b"ftyp" in data[:64]:
                path = f"{out}_{n}.mp4"
                open(path, "wb").write(data)
                return path, src, round(time.time() - t0), p.js("location.href")
        time.sleep(6)
    p.shot(out + f".timeout_{n}.png")
    raise TimeoutError(f"no new video after {job.get('timeout', 600)}s")


BACKENDS = {"chatgpt-image": chatgpt_image, "chatgpt-edit": chatgpt_image, "grok-image": grok_image,
            "gemini-image": gemini_image, "grok-video": grok_video}


def main():
    job = json.load(open(sys.argv[1]))
    fn = BACKENDS[job["backend"]]
    if not job.get("refs"):
        sys.exit("browser_acquire_driver: refs are required (frozen rule 28: the CAD stills go up with every prompt)")
    os.makedirs(job["outdir"], exist_ok=True)
    out = os.path.join(job["outdir"], job["id"])
    start = int(job.get("start", 1))
    with lease(f"{OWNER}-{job['backend']}", url="about:blank", purpose=f"story-forge {job['backend']} {job['id']}", ttl=900) as tab:
        tab.send("Emulation.setDeviceMetricsOverride", width=1400, height=900, deviceScaleFactor=1, mobile=False)
        tab.send("DOM.enable")
        tab.send("Runtime.enable")
        p = Page(tab)
        for n in range(start, start + int(job.get("count", 3))):
            try:
                path, src, secs, page = fn(p, job, n, out)
                log(ok=True, n=n, file=path, src=src, secs=secs, page=page)
            except Exception as e:  # one failed take must not lose the others
                try:
                    p.shot(f"{out}.fail_{n}.png")
                except Exception:
                    pass
                log(ok=False, n=n, error=f"{type(e).__name__}: {e}", shot=f"{out}.fail_{n}.png")


if __name__ == "__main__":
    main()

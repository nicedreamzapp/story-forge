"""Build the staged Story Forge + Software index pages from the live copies in live/.
Run: python3 build_pages.py   (re-run after pulling fresh live copies right before deploy)"""
from pathlib import Path
HERE = Path(__file__).parent
VID = "HSgm6hOsLTs"
YT = f"https://youtu.be/{VID}"
GH = "https://github.com/nicedreamzapp/story-forge/tree/main/projects/last_signal"

CSS = """<style id="last-signal-pass">
.dt-sw #last-signal { scroll-margin-top: 24px; }
.dt-sw .ls-box { padding: 32px 36px; }
.dt-sw .ls-box p:first-of-type::first-letter { font-size: inherit; float: none; line-height: inherit; margin: 0; color: inherit; font-weight: inherit; }
.dt-sw .ls-embed { position: relative; width: 100%; max-width: 860px; margin: 0 auto 26px; aspect-ratio: 16 / 9; border-radius: 12px; overflow: hidden; border: 1px solid var(--border); background: #000; }
.dt-sw .ls-embed iframe { position: absolute; inset: 0; width: 100%; height: 100%; border: 0; }
.dt-sw .ls-hook { font-size: 1.12rem; color: var(--fg); text-align: center; max-width: 680px; margin: 0 auto 16px; line-height: 1.55; font-weight: 500; }
.dt-sw .ls-chips { display: flex; flex-wrap: wrap; gap: 8px; justify-content: center; margin: 0 0 28px; }
.dt-sw .ls-chips .chip { font-size: 0.8rem; padding: 4px 12px; }
.dt-sw .ls-label { color: var(--gold); text-transform: uppercase; letter-spacing: 0.16em; font-size: 0.72rem; font-weight: 700; margin: 0 0 10px; }
.dt-sw .ls-hw { background: var(--bg-card-2); border: 1px solid var(--border); border-left: 4px solid var(--gold); border-radius: 10px; padding: 16px 20px; margin: 0 0 28px; }
.dt-sw .ls-hw .ls-hw-main { color: var(--fg); font-weight: 700; font-size: 1.02rem; margin: 0 0 4px; }
.dt-sw .ls-hw .ls-hw-sub { color: var(--muted); font-size: 0.9rem; margin: 0; line-height: 1.5; }
.dt-sw .ls-steps { list-style: none; padding: 0; margin: 0 0 18px; display: grid; gap: 6px; }
.dt-sw .ls-steps li { display: grid; grid-template-columns: 30px minmax(0, 1fr) auto; gap: 12px; align-items: center; background: var(--bg-card-2); border: 1px solid var(--border); border-radius: 9px; padding: 9px 14px; }
.dt-sw .ls-steps .n { width: 24px; height: 24px; border-radius: 50%; background: rgba(63,185,80,0.12); color: var(--gold); border: 1px solid rgba(63,185,80,0.35); display: grid; place-items: center; font-size: 0.72rem; font-weight: 700; }
.dt-sw .ls-steps .what { color: var(--fg-dim); font-size: 0.92rem; line-height: 1.4; min-width: 0; }
.dt-sw .ls-steps .what b { color: var(--fg); font-weight: 700; margin-right: 6px; }
.dt-sw .ls-steps .t { justify-self: end; white-space: nowrap; font-size: 0.76rem; color: var(--fg-dim); background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.1); border-radius: 999px; padding: 2px 10px; font-variant-numeric: tabular-nums; }
.dt-sw .ls-steps li.stall { border-color: rgba(210,153,34,0.35); }
.dt-sw .ls-steps li.stall .n { background: rgba(210,153,34,0.12); color: #d29922; border-color: rgba(210,153,34,0.4); }
.dt-sw .ls-steps li.done { border-color: rgba(63,185,80,0.4); }
.dt-sw .ls-more { margin: 0 0 28px; }
.dt-sw .ls-more summary { padding: 14px 20px; font-size: 0.95rem; }
.dt-sw .ls-more .readme-body { padding: 20px 26px; }
.dt-sw .ls-more .readme-body p { font-size: 0.92rem; margin: 0 0 10px; line-height: 1.55; }
.dt-sw .ls-notes { background: rgba(210,153,34,0.06); border: 1px solid rgba(210,153,34,0.3); border-radius: 10px; padding: 14px 20px; margin: 0 0 26px; }
.dt-sw .ls-notes .ls-label { color: #d29922; }
.dt-sw .ls-notes p { color: var(--fg-dim); font-size: 0.92rem; margin: 0 0 6px; line-height: 1.5; }
.dt-sw .ls-notes p:last-child { margin: 0; }
.dt-sw .ls-notes b { color: var(--fg); }
.dt-sw .ls-box .btn-row { justify-content: center; }
.dt-sw .ls-box .btn { padding: 11px 22px; font-size: 0.92rem; }
@media (max-width: 600px) {
  .dt-sw .ls-box { padding: 20px 16px; }
  .dt-sw .ls-steps li { grid-template-columns: 26px minmax(0, 1fr); gap: 4px 10px; padding: 9px 12px; align-items: start; }
  .dt-sw .ls-steps .t { grid-column: 2; justify-self: start; }
  .dt-sw .ls-more summary { padding: 13px 16px; }
  .dt-sw .ls-more .readme-body { padding: 16px 16px; }
  .dt-sw .ls-box .btn { width: 100%; justify-content: center; }
}
</style>
"""

STEPS = [
    ("", "Story", "premise and script v3 locked, about 40 cuts", "2:00 to 2:52 AM"),
    ("", "Shot list", "every shot planned before a render", "3:08 to 3:20 AM"),
    ("", "The ship", "Blender 5.1.1, Cycles on Metal", "3:20 to 4:27 AM"),
    ("stall", "Stall", "memory guard refused a 48 GB image model", "16 min"),
    ("", "Stills", "Z-Image-Turbo 6B, bf16", "4:50 to 5:45 AM"),
    ("", "Previs", "LTX-2.5 distilled, MLX bf16, 20 drafts", "5:46 to 6:14 AM"),
    ("", "Quality pass", "LTX-2.5 hq two stage, MLX bf16, 832x480", "6:15 to ~11:30 AM"),
    ("", "Clip gate", "Qwen3-VL-32B local vision judge", "25 min"),
    ("", "Score", "ACE-Step 1.5 through Song Forge", "3 candidates"),
    ("", "Synth", "our own numpy sub bass, beeps and kicks", "by script"),
    ("", "Sound effects", "MMAudio large 44k v2, picture synced", "4 min"),
    ("", "Voices", "ChatterBox, 9 takes of 3 lines", "1.5 min"),
    ("", "Mix", "our own 5.1 panner", "5.1 + stereo"),
    ("", "Upscale", "SeedVR2-3B fp16, 720p then 4K", "12:34 to 3:56 PM"),
    ("", "Grade", "our own LUTs, grain, 2.39:1, FFmpeg", "by script"),
    ("", "QC", "Qwen3-VL-32B + Whisper, two rounds", "51 of 53 pass"),
    ("done", "Ready", "finished trailer", "5:38 PM"),
]

LONG = [
    ("Story", "Premise and trailer script written in chat, cut faster to v3 (about 40 cuts) and locked before anything rendered."),
    ("The ship", "A procedural city sized ship in Blender 5.1.1, Cycles on Metal: 7 hero stills and 2 camera animations."),
    ("Stills", "Z-Image-Turbo 6B in bf16 made the character canon and every start frame. The creature began as a MattPaint painting and went in through img2img to become photoreal. The Blender ship frames got a light img2img polish."),
    ("Previs", "LTX-2.5 distilled made a quick draft of every shot (20 drafts, about 106 s each). A rough cut then decided which shots and seconds earned a real render."),
    ("Quality pass", "LTX-2.5 hq two stage rendered 35 takes of only the shots that made the cut, about 9.5 min a take."),
    ("Score and synth", "ACE-Step 1.5 made 3 instrumental candidates, each cut to the trailer's beat map by script. Our own numpy synth added the sub bass swell under the arrival, the heartbeat radio beep, a sub kick on every ramp cut and the title drop."),
    ("Sound effects", "MMAudio large 44k v2 made 25 effects in one load, 15 of them generated from the clips so they sync to picture."),
    ("Voices", "ChatterBox made 9 takes of the 3 lines. The planet is pitched down and layered, the captain whispered."),
    ("Mix", "Our own 5.1 panner: the ship sweeps front to rear, the planet comes from every speaker, LFE on the rumble. E-AC3 5.1 plus stereo."),
    ("Upscale", "SeedVR2-3B fp16 restored the held shots at 720p (866 frames, about 12.7 s a frame), then they were resized to 4K."),
    ("Grade", "Bloom on the engines, our own LUTs (cold space teal, teal orange blockbuster), light grain, 2.39:1 scope, FFmpeg for every cut."),
    ("QC", "A local vision model (Qwen3-VL-32B) plus Whisper checked the finished cut: 51 of 53 checks passed, and the 2 flags are the stone monster itself. A face check caught the captain drifting, so 4 shots got a face lock back to her canon face."),
]

def section():
    steps = "\n".join(
        f'      <li{" class=%s" % chr(34)+c+chr(34) if c else ""}><span class="n">{i}</span><span class="what"><b>{s}</b>{w}</span><span class="t">{t}</span></li>'
        for i, (c, s, w, t) in enumerate(STEPS, 1))
    longp = "\n".join(f"        <p><strong>{h}.</strong> {b}</p>" for h, b in LONG)
    return f'''  <section id="last-signal">
  <div class="section-eyebrow">Newest film, October 31 2026</div>
  <h2 class="section-title">THE LAST SIGNAL: a sci fi trailer made 100% local on one M5 Max 128GB.</h2>
  <div class="intro ls-box">
    <div class="ls-embed"><iframe src="https://www.youtube-nocookie.com/embed/{VID}" title="THE LAST SIGNAL, a Story Forge trailer" allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture" allowfullscreen loading="lazy"></iframe></div>
    <div class="ls-hook">A cargo ship follows a signal nobody has charted, and the planet at the end of it already knows the captain's name.</div>
    <div class="ls-chips"><span class="chip">46.6 s</span><span class="chip">50 cuts</span><span class="chip">4K deliverable</span><span class="chip">5.1 surround</span><span class="chip white">One day, story to trailer</span></div>

    <div class="ls-hw">
      <div class="ls-label">Hardware</div>
      <p class="ls-hw-main">MacBook Pro · Apple M5 Max · 128GB unified memory</p>
      <p class="ls-hw-sub">No cloud renders, no API calls, no subscriptions. One model in memory at a time: load, batch every job, unload, next stage.</p>
    </div>

    <div class="ls-label">The pipeline, real clock times from 10/31</div>
    <ol class="ls-steps">
{steps}
    </ol>
    <details class="readme-wrap ls-more">
      <summary>How each step worked</summary>
      <div class="readme-body">
{longp}
      </div>
    </details>

    <div class="ls-notes">
      <div class="ls-label">Honest notes</div>
      <p><b>4K deliverable, not native 4K detail.</b> Held shots were restored at 720p, then resized.</p>
      <p><b>About 2 of the 14.5 hours were stalls.</b> 16 min on the memory guard, 29 min getting the upscaler running, and 78 min when one shot came back smeared twice and had to be split.</p>
    </div>

    <div class="btn-row">
      <a class="btn btn-gold" href="{GH}" rel="noopener">⭐ Plan, scripts and time ledger on GitHub</a>
      <a class="btn btn-outline" href="{YT}" rel="noopener">▶ Watch on YouTube</a>
    </div>
  </div>
</section>

'''

CARD = f'''    <div style="background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.12);border-radius:12px;overflow:hidden;">
      <div style="aspect-ratio:16/9;"><iframe src="https://www.youtube-nocookie.com/embed/{VID}" title="THE LAST SIGNAL" style="width:100%;height:100%;border:0;" allowfullscreen loading="lazy"></iframe></div>
      <div style="padding:14px 16px;"><h3 style="margin:0 0 6px;color:var(--fg,#fff);">THE LAST SIGNAL</h3><p style="margin:0;opacity:0.75;font-size:0.93rem;">October 31 2026 sci fi trailer. Blender ship, LTX-2.5 motion, 5.1 surround, made in one day on one M5 Max 128GB. <a href="#last-signal">The pipeline</a></p></div>
    </div>
'''

INDEX_CARD = f'''    <div class="card">
      <a class="card-link" href="/software/story-forge/#last-signal" aria-label="THE LAST SIGNAL, the trailer and its pipeline"></a>
      <div class="head"><span class="emoji">🛸</span><h3>THE LAST SIGNAL</h3></div>
      <p>A sci fi trailer made 100% local on one M5 Max 128GB in one day, with the full Story Forge pipeline and real clock times.</p>
      <div class="links">
        <a class="link primary" href="/software/story-forge/#last-signal">Trailer + pipeline →</a>
        <a class="link" href="{YT}" rel="noopener">▶ Watch</a>
      </div>
    </div>

'''

def one(s, old, new):
    assert s.count(old) == 1, (old[:60], s.count(old))
    return s.replace(old, new)

sf = (HERE / "live/story-forge.index.html").read_text()
sf = one(sf, "</style>\n</head>", "</style>\n" + CSS + "</head>")
sf = one(sf, '  <section>\n  <div class="section-eyebrow">Newest film, October 2026</div>',
         section() + '  <section>\n  <div class="section-eyebrow">October 2026 progress film</div>')
grid = '<div style="display:grid;grid-template-columns:repeat(auto-fill,minmax(300px,1fr));gap:22px;margin:0 0 48px;">\n'
sf = one(sf, grid, grid + CARD)
(HERE / "staged/story-forge.index.html").write_text(sf)

ix = (HERE / "live/software.index.html").read_text()
sf_card_end = '        <a class="link" href="https://youtu.be/_bFQTl7_vF4" rel="noopener">▶ First film</a>\n      </div>\n    </div>\n\n'
ix = one(ix, sf_card_end, sf_card_end + INDEX_CARD)
(HERE / "staged/software.index.html").write_text(ix)
print("built", len(sf), len(ix))

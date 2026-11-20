import sys, asyncio
from pathlib import Path
from playwright.async_api import async_playwright
HERE = Path(__file__).parent
PAGES = {"story-forge": ("staged/story-forge.index.html", "https://nicedreamzwholesale.com/software/story-forge/", "#last-signal"),
         "software": ("staged/software.index.html", "https://nicedreamzwholesale.com/software/", "a[href='/software/story-forge/#last-signal'].card-link")}
WIDTHS = [int(w) for w in (sys.argv[1:] or ["1049", "440"])]
CHECK = """(sel) => {
  const out = {vw: innerWidth, sw: document.documentElement.scrollWidth, bad: []};
  const root = sel.startsWith('#') ? document.querySelector(sel) : document.querySelector(sel).closest('.grid');
  const rr = root.getBoundingClientRect();
  root.querySelectorAll('*').forEach(e => { const r = e.getBoundingClientRect(); if (r.width && (r.right > rr.right + 1 || r.left < rr.left - 1 || e.scrollWidth > e.clientWidth + 1 && getComputedStyle(e).overflowX === 'visible' && e.clientWidth)) out.bad.push(e.tagName + '.' + e.className + ' ' + Math.round(r.left) + '-' + Math.round(r.right) + ' vs ' + Math.round(rr.left) + '-' + Math.round(rr.right)); });
  out.bad = out.bad.slice(0, 15); return out; }"""
async def main():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, executable_path='/Users/dtribe/Library/Caches/ms-playwright/chromium_headless_shell-1248/chrome-headless-shell-mac-arm64/chrome-headless-shell')
        for name, (f, base, sel) in PAGES.items():
            html = (HERE / f).read_text().replace("<head>", f'<head><base href="{base}">', 1)
            for w in WIDTHS:
                ctx = await b.new_context(viewport={"width": w, "height": 900}, device_scale_factor=1)
                pg = await ctx.new_page()
                await pg.set_content(html, wait_until="load", timeout=60000)
                await pg.wait_for_timeout(2500)
                print(name, w, await pg.evaluate(CHECK, sel))
                el = pg.locator(sel).first
                tgt = el if sel.startswith('#') else el.locator("xpath=..")
                if name == "software":
                    await tgt.scroll_into_view_if_needed()
                    box = await pg.evaluate("(s)=>{const g=document.querySelector(s).closest('.grid').getBoundingClientRect();return [g.top+scrollY,g.height]}", sel)
                    await pg.screenshot(path=str(HERE / f"previews/{name}_{w}.png"), full_page=True,
                                        clip={"x": 0, "y": max(0, box[0] - 120), "width": w, "height": min(1400, box[1] + 120)})
                else:
                    await tgt.screenshot(path=str(HERE / f"previews/{name}_{w}.png"))
                    if w == WIDTHS[0]:
                        await pg.click("#last-signal details summary"); await pg.wait_for_timeout(300)
                        await pg.locator("#last-signal details").screenshot(path=str(HERE / f"previews/{name}_{w}_details.png"))
                    films = pg.locator("section:has(h2:text('The Finished Films'))")
                    await films.screenshot(path=str(HERE / f"previews/{name}_{w}_films.png"))
                await ctx.close()
        await b.close()
asyncio.run(main())

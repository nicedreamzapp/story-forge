import sys, time, json, os, gc
sys.path.insert(0, os.path.expanduser("~/SongForgeM5"))
from mem_client import reserve
P = os.path.expanduser("~/Desktop/PROJECTS/story-forge")
D = P + "/projects/things_we_remember"
OUT = D + "/director_test"
rd = lambda p: open(p).read()
log = open(OUT + "/run.log", "a")
def L(*a):
    s = " ".join(str(x) for x in a); print(s, flush=True); log.write(s + "\n"); log.flush()

t0 = time.time(); L("start", time.strftime("%H:%M:%S"), "waiting for lease")
with reserve("qwen-director-test", 75, timeout=1800, ttl=2400):
    L("lease granted after", round(time.time() - t0), "s")
    import mlx.core as mx
    from mlx_vlm import load, generate
    from mlx_vlm.prompt_utils import apply_chat_template
    from mlx_vlm.utils import load_config
    MID = "mlx-community/Qwen3.6-35B-A3B-bf16"
    t1 = time.time(); model, proc = load(MID); cfg = load_config(MID)
    load_s = time.time() - t1; L("load_s", round(load_s, 1))
    SAMP = dict(temperature=1.0, top_p=0.95, top_k=20)

    def chat(prompt, images=None, max_tokens=1000):
        n = len(images) if images else 0
        p = apply_chat_template(proc, cfg, prompt, num_images=n)
        return generate(model, proc, p, image=images, max_tokens=max_tokens, verbose=False, **SAMP)

    # Task A
    prompt = f"""You are the film director and shot-list writer for a feature built from 5-minute parts. Write PART_01 of THE THINGS WE REMEMBER: the first 5 minutes, exactly as PARTS_MAP.md describes Part 1 (scenes 1, 2, 3 of the outline, ending on the hook). Output a FULL shot list in the same table format as the TEASER_45 example, extended with these columns: #, time, scene, shot (camera + action), reads (what the audience should read), sentiment (the emotion beat), dialogue (speaker + exact line, or none), sound/music, eng (V video model / C code-animated still, as in the example). Follow the script-writing rules. Cover the full 300 seconds, with timestamps that add up, and finish with the hook shot. Output only the shot list with a one-line title and the look note.

=== OUTLINE.md ===
{rd(D+'/OUTLINE.md')}

=== PARTS_MAP.md ===
{rd(D+'/PARTS_MAP.md')}

=== TEASER_45.md (format example) ===
{rd(D+'/TEASER_45.md')}

=== script-writing.md (rules) ===
{rd(P+'/_shared/script-writing.md')}
"""
    t2 = time.time(); r = chat(prompt, None, 12000); a_s = time.time() - t2
    open(OUT + "/PART_01_qwen.md", "w").write(r.text)
    L("A: s", round(a_s, 1), "prompt_tok", r.prompt_tokens, "gen_tok", r.generation_tokens, "gen_tps", round(r.generation_tps, 1), "prefill_tps", round(r.prompt_tps, 1), "finish", r.finish_reason)

    # Task B
    S = D + "/stills/"
    items = [
     ("s01_a.png", "ACCEPTED (teaser shot 1, approved)", "Sun through the kitchen window, dust drifting, first raindrops; warm home"),
     ("s07_a.png", "ACCEPTED (teaser shot 7 lip-sync, approved)", "Lily (7, blonde braids, pale yellow dress) at the dinner table looks calmly at the empty chair: she sees him"),
     ("s08_a.png", "ACCEPTED (teaser shot 8, approved)", "Dark child's bedroom: second bed, a small boy under the blanket facing the wall, only his hair visible; a child that isn't hers"),
     ("s11_bl.png", "ACCEPTED (teaser shot 11, approved; face deliberately soft)", "Claire at the dark kitchen window; in the reflection behind her, a soft, gentle man out of focus"),
     ("t13_a.png", "ACCEPTED (trailer HQ shot t13, kept)", "Claire alone at the kitchen table at night with an old cassette recorder, frozen"),
     ("s03_b.png", "FLAGGED (film_qc artifact x4: the man in the photo has a blank, featureless face; kept on purpose)", "Claire's hands hold an old photo; a man stands behind her parents, face in shadow"),
     ("s05_a.png", "FLAGGED (take rejected: figure walked into light, head-turn beat did not read)", "Glass slips from a hand; in the dark doorway behind, a figure's head turns toward the floor BEFORE it hits"),
     ("s06_a.png", "FLAGGED (take rejected: fork never moved / a family hand lifted it)", "Dinner table, five plates, push in on the empty chair; the fork on the plate slides by itself"),
     ("t01_a.png", "REJECTED (HQ video take: car reverses toward camera)", "Station wagon pulls slowly up a wet gravel driveway toward an old white farmhouse in soft rain, lamp glowing in one window"),
     ("t04_a.png", "REJECTED (HQ video take: push ends in a soft blur)", "Ruth (70s, silver curled hair, lavender cardigan) seen from behind at a rain-streaked living room window; slow push in"),
    ]
    rows = []; sc = 0; bt = time.time()
    for f, gt, desc in items:
        q = (f"You are the QC judge for a film. This is a frame from a shot. Shot description: \"{desc}\".\n"
             "Judge the image strictly: does it match the description and is it free of generation artifacts (blank or featureless faces, melted hands, wrong anatomy, wrong objects, unwanted text)? "
             "Reply in exactly this form: PASS or FAIL, then a dash, then ONE short sentence of reason.")
        rr = chat(q, [S + f], 120)
        v = rr.text.strip().replace("\n", " ")
        verdict = "PASS" if v.upper().lstrip("*# ").startswith("PASS") else ("FAIL" if "FAIL" in v.upper()[:12] else "?")
        truth_pass = gt.startswith("ACCEPTED")
        ok = (verdict == "PASS") == truth_pass
        sc += ok
        rows.append((f, gt, verdict, v.replace("|", "/"), ok))
        L("B", f, verdict, ok)
    b_s = time.time() - bt
    with open(OUT + "/judging.md", "w") as fh:
        fh.write("# Qwen3.6-35B-A3B-bf16 as QC judge (single still + shot description, thinking off, T1.0/top_p .95/top_k 20)\n\n")
        fh.write("| image | ground truth | Qwen verdict | reason | match |\n|---|---|---|---|---|\n")
        for f, gt, v, rs, ok in rows: fh.write(f"| {f} | {gt} | {v} | {rs} | {'yes' if ok else 'no'} |\n")
        fh.write(f"\nScore: {sc}/10 matches ground truth. Judging time {b_s:.0f}s.\n")
        fh.write("\nCaveat: stills cannot show video-only defects (motion, fork, car direction, blur at end of push); the ground truth for those flags comes from the rendered video takes.\n")
    L("B score", sc, "time", round(b_s))
    L("TOTAL", round(time.time() - t0))
    del model, proc; gc.collect(); mx.clear_cache()
L("unloaded+released")

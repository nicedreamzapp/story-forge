import json, time, urllib.request, sys
SF="http://127.0.0.1:8767"
OUT="/Users/dtribe/Desktop/PROJECTS/story-forge/projects/cemani_movie/out/music/"
MOTIF="a simple memorable 4-note melodic motif on clean electric guitar"
CUES=[
 ("m1_build_sparse", 75, f"instrumental, cinematic indie maker documentary, 92 BPM, {MOTIF}, muted electric guitar plucks, low warm analog synth pad, soft kick on 1 and 3, sparse, hi-hats build in near the end, then drums and bass synth enter doubling the motif, hopeful"),
 ("m2_full_groove", 45, f"instrumental, upbeat indie documentary groove, 96 BPM, {MOTIF} as the hook, kick snare hats, claps on 2 and 4, two interlocking electric guitars, bass synth, warm, confident, outdoors"),
 ("m3_low_pad", 40, f"instrumental, somber ambient, 70 BPM, single low analog synth pad and slow soft pulse, {MOTIF} played slow and unresolved, sparse, lots of space, melancholy, minimal"),
 ("m4_iteration_build", 85, f"instrumental, cinematic electronic build, 104 BPM, ticking woodblock and rim percussion loop, pulsing bass, plucked synth arpeggio, {MOTIF}, steady building tension, engineering montage, mid energy"),
 ("m5_peak", 50, f"instrumental, triumphant indie electronic peak, 104 BPM, full drums, bass, two electric guitars, synth pad, {MOTIF} as the lead line, big uplifting drop, energetic"),
 ("m6_warm_close", 45, f"instrumental, warm gentle closing theme, 92 BPM, {MOTIF} in full on clean electric guitar, soft synth pad, light drums that fade out, last note rings out, hopeful ending"),
]
def call(p,b=None):
    r=urllib.request.Request(SF+p,data=json.dumps(b).encode() if b else None,headers={"Content-Type":"application/json"},method="POST" if b else "GET")
    return json.load(urllib.request.urlopen(r,timeout=60))
only=sys.argv[1:] 
for name,secs,style in CUES:
    if only and name not in only: continue
    while int(call("/api/status").get("jobs_running") or 0)>0 and False: time.sleep(5)
    t0=time.time()
    j=call("/api/song",{"style":style,"lyrics":"[inst]","title":f"cemani {name}","duration":secs,"planner":"off","private":True,"video_only":True})
    jid=j.get("id") or (j.get("ids") or [None])[0]
    print(name,"job",jid,flush=True)
    info={}
    while time.time()-t0<900:
        time.sleep(4)
        try: info=call(f"/api/song/{jid}")
        except Exception: continue
        if info.get("status") in ("done","error"): break
    url=info.get("audio") or info.get("download") or info.get("url")
    if info.get("status")!="done" or not url: print(name,"FAILED",info.get("status"),flush=True); continue
    if url.startswith("/"): url=SF+url
    data=urllib.request.urlopen(urllib.request.Request(url,headers={"User-Agent":"curl"}),timeout=120).read()
    ext=".mp3" if data[:3]==b"ID3" or data[:2]==b"\xff\xfb" else ".wav"
    open(OUT+name+ext,"wb").write(data)
    json.dump({"style":style,"seconds":secs,"job":jid},open(OUT+name+".json","w"))
    print(name,"saved",ext,f"{time.time()-t0:.0f}s",flush=True)

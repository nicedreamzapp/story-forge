import json
tl=json.load(open("final/timeline.json"));ev=json.load(open("final/blackout_events.json"));S={s["name"]:s for s in tl["segments"]}
txt={"news":("anchor","Every major AI service is down. Worldwide."),"narr":("builder","Fixing the bug. Running the tests."),"rt1":("builder","Flashlight."),"rt2":("builder","Radio."),"rt3":("builder","Door open."),"stranger":("stranger","Yours still works?"),"matt":("builder","It never needed the internet.")}
lines=[{"t":e["t"],"speaker":txt[e["voice"]][0],"text":txt[e["voice"]][1],"offscreen":e["voice"]!="matt"} for e in ev if "voice" in e]
scenes=[{"name":s["name"],"start":s["start"],"end":s["end"],"note":""} for s in tl["segments"]]
ab=[[S[k]["start"]-0.1,S[k]["end"]+0.1] for k in ("card1","card3","card6","gap")]+[[S["sf"]["start"]-0.1,S["sf"]["start"]+0.7]]
json.dump({"characters":{"builder":"a bald middle-aged bearded man with clear glasses, lit by warm laptop glow, in a dark cabin","stranger":"backlit tall man silhouette in a doorway, face not visible, never speaks on camera","anchor":"off-screen news voice, never on screen"},"lines":lines,"scenes":scenes,"spec":{"width":1920,"height":1080,"fps":24,"lufs":-14,"allow_black":ab}},open("qc_manifest.json","w"),indent=1)

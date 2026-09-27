#!/usr/bin/env python3
"""Disclosure music video — full batch build.
Per shot: Flux still (768x512) -> LTX i2v animate (768x512, multi-scale).
Resumable: skips any shot whose clip already exists. Logs timing per shot.
Clips land in ~/AI/videopipe/outputs/disc_shotNN_ltxL_*.mp4
"""
import subprocess, sys, time, glob
from pathlib import Path

HOME = Path.home()
FLUX = str(HOME / "Scripts/flux_t2i.py")
LTX  = str(HOME / "Desktop/PROJECTS/story-forge/bin/make-ltx-lightricks")
VENV = str(HOME / "Desktop/PROJECTS/AI/ComfyUI/venv/bin/python")
OUT  = HOME / "AI/videopipe/outputs"
STILLS = Path("/tmp/disc_stills"); STILLS.mkdir(exist_ok=True)

GRADE = "cinematic teal and amber color grade, 35mm film grain, anamorphic, photoreal, volumetric haze, night"
VHS   = "1980s VHS broadcast look, scanlines, slight chroma bleed, vintage tube-TV color, photoreal"

# (label, flux_prompt, motion_prompt)
SHOTS = [
  # --- INTRO 0:00-0:45 : cold open, build the mystery ---
  ("02","extreme close-up of a Black man's eyes looking upward, faint starlight reflected in them, "+GRADE,"slow push-in on the eyes, a glimmer of light growing in the reflection"),
  ("03","a vast deep night sky full of stars over a silent city horizon, one faint pulsing light among the stars, "+GRADE,"slow drift across the star field, the faint light pulsing gently"),
  ("04","an empty suburban street at night under a single streetlight, a lone figure standing in the middle looking up, "+GRADE,"slow push-in down the empty street toward the figure"),
  ("05","a dark room lit only by a wall of old stacked tube televisions glowing with static, "+VHS,"the static flickering, faint glow pulsing across the room"),
  ("06","a stack of redacted classified government documents on a desk under a single lamp, black censor bars, "+GRADE,"slow push-in over the documents, lamp flickering"),
  ("07","macro close-up of an old brass key on a chain resting on dark paper, "+GRADE,"slow rotate, light glinting off the key"),
  ("08","a hand sliding a thin paper envelope across a dim hotel table at night, "+GRADE,"the envelope sliding slowly forward, shadows shifting"),
  ("09","a sweeping city skyline at night, a faint unnatural glow rising on the horizon, "+GRADE,"slow rise revealing the glowing horizon, clouds drifting"),
  # --- VERSE 1 0:45-1:05 : classified, the courier, the elders ---
  ("10","a Black man in a trench coat standing tense in a dim 1970s hotel hallway, looking back over his shoulder, "+GRADE,"slow push-in down the hallway toward him, light flickering"),
  ("11","close-up of weathered hands unfolding thin classified pages under lamplight, "+GRADE,"the pages slowly unfolding, lamp glow shifting"),
  ("12","an elderly Black woman on a wooden porch at dusk, looking up at the sky with quiet knowing, warm light, "+GRADE,"gentle push-in on her face as she looks up, breeze moving her shawl"),
  ("13","a vintage radio glowing on a shelf in a dark room, warm dial light, "+GRADE,"slow push-in on the glowing dial, faint flicker"),
  # --- HOOK 1:06-1:24 : the lift, people looking up ---
  ("14","a crowd of diverse people in a city street all slowly turning to look up at the sky, "+GRADE,"slow crane upward over the crowd as they look up together"),
  ("15","several faces tilted upward in awe, lit from above by a soft growing sky-glow, "+GRADE,"slow push-in across the awed upturned faces"),
  ("16","a night sky beginning to shimmer and ripple with soft light, clouds parting, "+GRADE,"the sky rippling open, light spreading slowly"),
  ("17","wide shot of a city bathed in a soft glowing sky, silhouettes on rooftops looking up, "+GRADE,"slow aerial drift over the glowing city"),
  # --- VERSE 2 1:25-1:41 : the broadcast, the weatherwoman, angel on a beam ---
  ("18","a 1980s television news studio, a weather reporter at a glowing weather map frozen mid-broadcast, transfixed, "+VHS,"slow push-in on the frozen reporter, studio lights flickering"),
  ("19","tight close-up of a weather reporter's face transfixed, pale light washing over her, "+VHS,"slow push-in, the light intensifying on her face"),
  ("20","a beam of pale light descending into a dark studio, a luminous angelic silhouette within the beam, "+GRADE,"the beam slowly intensifying, the silhouette resolving"),
  ("21","a row of vintage TVs in a dark store window all showing the same eerie broadcast, people watching from the street, "+VHS,"slow dolly past the glowing store window of TVs"),
  # --- BRIDGE / HOOK 2  1:41-2:36 : escalation, the country wakes ---
  ("22","an aerial night view of a sprawling neighborhood, lights flicking on house by house, "+GRADE,"slow aerial drift as more lights flick on across the dark neighborhood"),
  ("23","people pouring out of their homes into the street at night, all looking up, "+GRADE,"slow push-in through the gathering crowd toward the sky"),
  ("24","an enormous night sky tearing open with cascading light over a city, "+GRADE,"the sky slowly tearing open, light cascading down"),
  ("25","a vast luminous craft silhouetted high above the clouds, distant and awe-inspiring, "+GRADE,"the craft slowly emerging from the clouds, light glowing"),
  ("26","an elderly Black woman looking up with tears and a smile, light on her face, "+GRADE,"gentle push-in on her face, light growing brighter"),
  ("27","a lone Black man in a trench coat stepping forward into a shaft of descending light, seen from behind, "+GRADE,"slow push-in as he steps into the light"),
  ("28","two children pointing up at a glowing sky from a backyard at night, "+GRADE,"slow push-in on the children pointing upward"),
  ("29","a highway at night with cars stopped, people standing outside their cars looking up, "+GRADE,"slow aerial rise over the stopped highway and the upturned crowd"),
  ("30","a single brilliant beam of light standing over a city skyline at night, "+GRADE,"slow push-in toward the beam over the city"),
  ("31","a breathtaking cosmic vista, stars and nebulae, something vast and luminous approaching, "+GRADE,"slow drift through the cosmic vista toward the approaching light"),
  ("32","a sea of upturned faces in a city square bathed in golden descending light, "+GRADE,"slow crane up over the glowing crowd"),
  # --- OUTRO 2:36-3:00 : the reveal, sky was always full ---
  ("33","the lone Black man from the rooftop now bathed in brilliant light, looking up, seen from behind, "+GRADE,"slow push-in on him as the light envelops him"),
  ("34","a wide pull-back revealing an entire night sky filled with countless luminous lights over a city, "+GRADE,"slow pull-back revealing the full glowing sky"),
  ("35","a vast cosmic reveal, the whole sky alive with light as if it was always full, silhouetted figures below, "+GRADE,"slow majestic rise revealing the sky full of light"),
  ("36","silhouettes of people standing together against an enormous glowing sky, hopeful, "+GRADE,"slow push-in on the silhouettes against the radiant sky, fading"),
]

def have_clip(label):
    return bool(glob.glob(str(OUT / f"disc_shot{label}_ltxL_*.mp4")))

def run(cmd, timeout):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

total = len(SHOTS); t_all = time.time(); done = 0; failed = []
print(f"=== Disclosure build: {total} shots (shot01 already done) ===", flush=True)
for i,(label,flux,motion) in enumerate(SHOTS,1):
    if have_clip(label):
        print(f"[{i}/{total}] shot{label}: already exists, skip", flush=True); done+=1; continue
    t0=time.time()
    still=str(STILLS/f"shot{label}.png")
    print(f"[{i}/{total}] shot{label}: flux still...", flush=True)
    try:
        r=run(["python3",FLUX,flux,"--w","768","--h","512","--out",still],600)
        if r.returncode!=0 or not Path(still).exists():
            print(f"   FLUX FAIL shot{label}: {r.stderr[-200:]}", flush=True); failed.append(label); continue
        print(f"   flux ok; ltx animate...", flush=True)
        r=run([VENV,LTX,"--i2v",still,"--duration","5","--res","768x512","--label",f"disc_shot{label}",motion],1800)
        if r.returncode!=0 or not have_clip(label):
            print(f"   LTX FAIL shot{label}: {r.stderr[-200:]}", flush=True); failed.append(label); continue
        done+=1
        print(f"   shot{label} DONE in {int(time.time()-t0)}s  ({done}/{total})", flush=True)
    except subprocess.TimeoutExpired:
        print(f"   TIMEOUT shot{label}", flush=True); failed.append(label)
print(f"=== BUILD COMPLETE: {done}/{total} clips in {int((time.time()-t_all)/60)} min. failed: {failed} ===", flush=True)

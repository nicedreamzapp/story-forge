# ANTARCTICA: The Continent We Just Met
*Story Forge documentary — built 2026-06-11. Every claim verified against sources (see FACTS.md).*

## Premise & meaning
For two centuries we knew Antarctica as a white blank. In the last ten years —
radar, satellites, drilling robots — we finally met the actual continent:
buried mountain ranges, canyons deeper than any on the surface, hundreds of
living lakes, forests in the rock, and a glacier writing us a warning.
Meaning: the age of exploration didn't end — it just went under the ice.
Tone: WONDER first, warning honest but not doom. We end on awe.

## Style (every Flux prompt ends with this)
STYLE: "cinematic documentary photograph, National Geographic style, epic
scale, dramatic natural light, ultra detailed, shot on large-format cinema
camera, atmospheric haze"
For data/under-ice reveals add: "scientific visualization, satellite relief
render" — these are VISUALIZATIONS of real data, framed as such by narration.

## Four acts (~5.5 min)
1. THE VEIL — the Antarctica we know (storms, ice, scale), then Bedmap3
   strips the ice: 82M measurements, the true landscape, the Wilkes Land
   canyon under 4,757 m of ice.
2. THE LIVING DARK — 85 new subglacial lakes (CryoSat, 2025), networks that
   fill and drain; Lake Mercer/Whillans microbes living on iron + sulfur;
   the 2021 Filchner-Ronne accident: sponges on a boulder, 260 km from
   daylight.
3. DEEP TIME — the 90-million-year rainforest core near Pine Island (2020);
   Gamburtsev ghost mountains (500M years old, never eroded); the fossil
   river valleys that drained toward Australia; Beyond EPICA's 2,800 m core
   = 1.2 million years of unbroken climate memory (Jan 2025).
4. THE EDGE — Thwaites; Icefin's 700 m descent to the grounding line (first
   video ever); the surprise: fracture beats melt; 14 km of retreat in two
   decades. Close: we finally met the continent — we'd never really seen it.

## Audio
- Narrator: Piper libritts_r speaker 0 (proven). Documentary cadence —
  shorter sentences than the fable, let pictures breathe.
- VO scheduling: PER-LINE pinned to target shots from the start
  (fix_sync.py pattern, ✓ table required before delivery).
- Score: ONE musical identity across 4 cues — glacial ambient orchestra,
  same motif language in every cue prompt ("slow rising four-note motif"),
  so the film ties together. Cues: veil/mystery → wonder/discovery →
  deep-time awe → urgent-then-resolved finale.

## Production rules in force
- Known-safe settings only: Flux 1152x768, LTX 768x512 multi-scale, 6 s MAX
  per clip (8 s melts — proven last night).
- One model at a time; watchdogged subprocesses; resume manifests; QC every
  still and sampled clips by eye; caffeinate running.
- No talking humans on screen (no lip-sync); scientists appear in wides/
  silhouettes/hands-only.
- Science honesty: narration distinguishes "what we measured" from "what we
  render" — reveals are introduced as "strip the ice away and..." so
  visualizations aren't passed off as photographs.

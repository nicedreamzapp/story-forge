# 06_assemble — stage note (2026-11-17, builder: Fable)
The cut is not an EDL of clips: script v2 is ONE unbroken travelling shot, so the picture is rendered by tools/finish.py as a pure
function of time (seek(t)) over the stills and clips, with paintlib.py's code layers (unpainted linen state, ripple + reveal, whip-pan
joins, old paint + crack heal, leading edge, lantern cutout on a parabola, title stroke reveal). Camera moves are float-coordinate affine
sampling (frozen rule 12), never zoompan. The Remotion finish was not used: the layers needed per-pixel mattes that numpy/cv2 do directly.
Audio: tools/mix.py (static gain, cue map in stages/05_sound/score_pick.md), then pipeline-tools/final_audio_gate.py --in-place.
final/timeline.json lists every beat, its source still/clip and the code layers; final/mix_cues.json lists every placed sound.
Coverage (frozen rule 29): every motion beat has the still + a code camera path, the LTX-2.5 previs clip, and (where time allowed) a K6
Pro clip; stills have 1-2 seeds; theme has 2 vocal takes; voices have alternates in voices/alt/. All listed in manifest.json.

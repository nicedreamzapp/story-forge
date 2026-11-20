# Score pick: HANK & DOUG'S WILD RESCUE (2026-11-01)

Commissioned 10:12 AM from the local Song Forge (ACE-Step), `"lyrics": "[instrumental]"`, private + video_only, 55 s each,
all asking for the v3 beat map (mysterious low night opening, urgent pizzicato build, a heroic brass THEME hit, an
adventurous gallop, a tension build, a sudden stop, a swelling ramp to a final hit, a light playful pizzicato/glockenspiel sting).

| Candidate | File | Notes (measured; I cannot hear) |
|---|---|---|
| 1 | music/candidates/score_1.wav | How to Train Your Dragon style. Opens fast (-22 dB by 1 s), biggest onset 15.8 s. Arranged fitness -4.79 |
| 2 | music/candidates/score_2.wav | classic western adventure, galloping. A real quiet opening (-40 to -33 dB for the first 2 s), biggest onset 22.9 s, dense stretch 28-40 s. Arranged fitness -2.96 (best) |
| 3 | music/candidates/score_3.wav | Pixar/Silvestri fanfare. Opening not quiet (-37 to -28 dB), biggest onset at 50.8 s (the end). Arranged fitness -7.20 |

Each candidate was cut to the beat map by tools/score_arrange.py (reused from last_signal; best window per section, no
material reused, no dropouts inside call/theme/ramp, 12 ms joins on the cut frames, silence for the dead stop and the
black): music/arranged/score_N_arranged.wav + arrangement.json.

## Builder's pick (delegated): candidate 2
Best fit to the beat map: the quietest opening for the night forest under Doug's whisper-low line, and its theme window
starts at 22.85 s, right on its biggest onset (22.89 s), so the brass hit lands on the wagon-burst cut. Its ramp window
(40.0 s) is its densest stretch. Designed layers on top (barn burst, theme boom, our numpy sub, title boom) carry the hits.

## Matt picked
Not yet. All 3 were texted to Matt at 10:43 AM from the mini (one plain text "Hank & Doug music: 3 versions coming,
reply 1, 2 or 3", then HankDoug_music_1/2/3.mp4 over the 480p cut; chat.db rows 42784, 42786, 42788, 42790, all
is_delivered=1; mini copies deleted). **Matt's reply overrides the builder's pick.** Swapping the score is a remix
only: `echo N > music/score_pick.txt`, `tools/mix_plan.py N`, then `tools/deliver.py` (no picture work).

## His words
(no reply yet)

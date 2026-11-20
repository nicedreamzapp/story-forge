# WILD RESCUE score candidates (rebuild, 2026-11-01 evening)

Made with ACE-Step 1.5 through the mini's Song Forge API (127.0.0.1:8767), lyrics "[instrumental]", planner off, private + video_only,
duration 45 s, 48 kHz stereo. jobs_running/queue_depth checked = 0 right before each request; requests 90 s apart. All 3 jobs DELETEd from
Song Forge after copying (API answered 404 afterwards); the mini's temp copies removed. Seed: the Song Forge API takes no seed and returns none
(ACE-Step picks it internally), so each candidate is recorded by its job id. Not sent to anyone; kept for the finish.
ACE-Step does not follow second-by-second section timing exactly; tools/score_arrange.py is expected to place the hit/stop/stinger on the cut.

## score_cand1.wav (45.0 s, job 3c65ecf7e23b4188b29c1305d851638e, made 16:43 PM, 35 s)

Celtic-horn/taiko heroic. Loudness curve follows the brief best: quiet open, builds from ~0:10, holds hot -12 to -15 dB through the ramp, then drops at 0:34 (-24 dB) and tails out ~0:43. Closest to the dead-stop shape.

Prompt: instrumental, no vocals, no choir, no singing, animated family adventure movie trailer score, 45 seconds, 0:00 mysterious night forest intrigue, low strings and a lone woodwind, soft pulse; 0:06 urgency, fast ticking pizzicato ostinato and snare rolls; 0:10 big heroic full orchestra brass theme hit with galloping rhythm and timpani; 0:16 dark dread, low brass and tremolo strings; 0:23 wonder, shimmering celesta and high strings; 0:27 relentless rising ramp, brass and strings climbing with pounding drums; 0:35 dead stop silence; 0:36 one massive title slam hit with boom; 0:39 a warm playful little pizzicato and glockenspiel button, Celtic-tinged heroic horns and big taiko, epic and joyful, How to Train Your Dragon style

## score_cand2.wav (45.0 s, job eac157b057544fb598d39c1e21164758, made 16:45 PM, 40 s)

Western frontier (horns, gallop, banjo color). Quieter and more even (mean -17.5 dB), no clear dead stop at 0:35 (one dip at 0:38); best as a bed that the arranger cuts to shape.

Prompt: instrumental, no vocals, no choir, no singing, animated family adventure movie trailer score, 45 seconds, 0:00 mysterious night forest intrigue, low strings and a lone woodwind, soft pulse; 0:06 urgency, fast ticking pizzicato ostinato and snare rolls; 0:10 big heroic full orchestra brass theme hit with galloping rhythm and timpani; 0:16 dark dread, low brass and tremolo strings; 0:23 wonder, shimmering celesta and high strings; 0:27 relentless rising ramp, brass and strings climbing with pounding drums; 0:35 dead stop silence; 0:36 one massive title slam hit with boom; 0:39 a warm playful little pizzicato and glockenspiel button, classic western frontier adventure, galloping rhythm, bold trumpets and French horns, banjo color, Rango and Spirit style

## score_cand3.wav (45.0 s, job ea0a7efbc5df47fb9ba13ff7c9ce2cb7, made 16:47 PM, 55 s)

Warm Pixar/Silvestri orchestra. Hot open, steady -12 to -16 dB through 0:35, then fades to silence by 0:38 (ends early; no button after the stinger). Brightest, fullest sound.

Prompt: instrumental, no vocals, no choir, no singing, animated family adventure movie trailer score, 45 seconds, 0:00 mysterious night forest intrigue, low strings and a lone woodwind, soft pulse; 0:06 urgency, fast ticking pizzicato ostinato and snare rolls; 0:10 big heroic full orchestra brass theme hit with galloping rhythm and timpani; 0:16 dark dread, low brass and tremolo strings; 0:23 wonder, shimmering celesta and high strings; 0:27 relentless rising ramp, brass and strings climbing with pounding drums; 0:35 dead stop silence; 0:36 one massive title slam hit with boom; 0:39 a warm playful little pizzicato and glockenspiel button, warm Pixar DreamWorks trailer orchestra, heroic brass fanfare, warm strings, playful woodwinds, Alan Silvestri style

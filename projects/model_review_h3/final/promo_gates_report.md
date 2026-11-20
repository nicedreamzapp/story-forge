# Promo gates: model_review_h3

Film: `final/model_review_h3.mp4`, 105.60 s. PASS 9, FAIL 0, WARN 1, UNCHECKED 0.

| gate | verdict | detail |
|---|---|---|
| words (final mix vs script) | WARN | whole-film pass 278/279 (expected 'it's' heard 'it'); every line heard word for word in its own window of the final mix. Listen for it in the full watch. |
| word timing vs plan | PASS | median offset 55 ms over 277 words |
| loudness | PASS | integrated -16.0 LUFS (target -16.0+/-1.0), true peak -1.5 dBFS (max -1.0), LRA 3.1 |
| voice over music | PASS | voice stem -13.3 LUFS, ducked music -27.8 LUFS: 14.5 dB apart (want >= 10) |
| slam after last word | PASS | last heard word ends 99.34s, slam 99.60s (+260 ms) |
| last words heard | PASS | want 'first then build' in the last seconds; heard 'we'll port it. That's how we pick our tools. Read the license first, then build.' |
| sting rings | PASS | RMS -17.6 dBFS in the 2 s after the slam |
| end card on screen | PASS | 93% dark, 5.0% bright type at 101.10s |
| design (shots in the cut) | PASS | all 26 used shots passed design_check |
| reading time (on-screen text) | PASS | all 3 text blocks readable (titles/callouts chars/15 + 1.5 s, subtitles <= 17 cps; tightest: endcard 'github.com/nicedreamzapp/story' 4.82s vs 3.90s) |
| frame strips | REVIEW | 15 strips in final/strips/ (look at every one; then watch the whole cut and write stages/09_gates/known_defects.md) |

Whisper heard (final mix):

> This morning our model watcher texted me. A new video model had just landed on Hugging Face and it looked promising. On paper it's a dream. Two Minimax H3 models blended across 50 blocks, 33 billion parameters in all. Plus two distillation adapters folded in for renders in 4 to 8 steps. And it squeezed from over 61 gigs down to about 19. And H3 ranked number one in our own local video research. But every new model starts at step one, which is the license. The actual license file, not the tag on the page? Every merge inherits its base model's license, so we followed it all the way back to Minimax H3. And there it is. Excluded territories means the European Union, the United Kingdom, Korea, and the United States. Outputs included. We're in California, so it's out. And putting an MLX port on Hugging Face would count as distributing it, so that's a no. It also only ships in 8-bit and only runs in ComfyUI. We run everything at full precision. So what do we use instead? We use Kandinsky 6 Pro. It has an MIT license, 29 billion parameters, and takes about 12 minutes per 3 second clip on the M5 Max. On its very first clip, I said that's the best I've ever seen. And we use LTX for quick previews and lip sync. Now every new model goes through the same seven steps. License, Fit, Compare, Test, Convert, Verdict, and a review video like this one. If the license on Minimax H3 ever changes, and their team said maybe, no promises, we'll port it. That's how we pick our tools. Read the license first, then build.

# Premise: how we pick our tools (the Minimax-H3 hybrid review, 2026-11-03)

## Who it is for
Builders running local video models, and anyone following how Story Forge chooses its tools.

## The problem
A new model looks perfect on paper (H3 merge, fast distilled steps, 19 GB int8), and H3 ranked #1 in our
own research. The easy move is to download it and start rendering.

## What the product changes
The new-model vetting production (`_shared/new-model-vetting.md`): license first, read the file not the tag,
follow base_model back. H3's license excludes the US (outputs included), so it stops at step 1. We keep
Kandinsky 6 Pro (MIT) and LTX-2.5, and every new model now goes through 7 steps.

## The one thing to remember
Read the license first, then build.

## Sentiment per line (what the viewer should feel)

| Line | Text | Sentiment |
|---|---|---|
| 1 | watcher texted me, new model on HF | a ping of curiosity: something new just landed |
| 2 | on paper a dream, two H3 blended, 33B | rising excitement, "oh, that's clever" |
| 3 | LoRAs, 4-8 steps, 61 to 19 GB | excitement peaks: fast AND small |
| 4 | H3 ranked #1 in our research | "this could be the one" |
| 5 | step one, the license, the file not the tag | a calm brake: the builder's habit kicks in |
| 6 | a merge inherits its base license | curiosity, following the trail |
| 7 | the Excluded Territories clause | the reveal: "there it is" |
| 8 | California, out; uploading = distributing | clear, settled decision, no drama |
| 9 | int8 only, ComfyUI only | confirmation, it did not fit anyway |
| 10 | Kandinsky 6 Pro, MIT, 29B, 12 min | relief and pride in what we have |
| 11 | best I've ever seen; LTX-2.5 | warmth, Matt's genuine reaction |
| 12 | seven steps every model goes through | "oh, that's a smart system" |
| 13 | if MiniMax relicenses, we'll port it | open door, goodwill toward MiniMax |
| 14 | read the license first, then build | a confident landing, the takeaway |

## Facts and sources (use only these)
- Model card + license text: verified 2026-11-03, `_shared/new-model-vetting.md` log.
- Kandinsky 6 Pro numbers and Matt's quote: `VIDEO-MODEL-2026-11-01.md`.
- H3 #1 in our consensus: `MODEL-CONSENSUS-2026-11.md`.

## Matt's idea, in his words
"bake that into all things for the future when we look over new models and make this production" (step 7 =
this review video).

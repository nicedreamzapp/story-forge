---
stage: 06_edit
outputs:
  - vo/words.json
  - cues.json
  - edl.json
gate: none
---
# 06_edit — cut to the words

One job: an EDL whose cuts, titles and overlays land on the narration's words, ending on the end card.

## Commands (inside `bin/make-promo`)
1. `~/chatterbox-env/bin/python pipeline-tools/words_align.py projects/<film> --gap <promo.gap> --lead <promo.lead>`
2. `cues.json`: the agent picks the words (`cut`, `xfade`, `title`, `callout`, `overlay`). `promo_draft.py --cues`
   drafts one if missing (a title on the brand word, cuts ~2.4 s apart on long words, plus
   `promo.json "extra_cues"`), marked `"draft": true`.
3. `python3 pipeline-tools/edit_to_words.py projects/<film>` → `edl.json` (+ `edl.txt`). With
   `promo.json endcard.dur > 0` the picture stops at the slam = last word END + `slam_after` and the
   end card holds for `dur`.
4. `python3 pipeline-tools/cue_check.py projects/<film>` must pass (every cue within 100 ms of its word,
   no shot under 0.8 s, nothing stretched, the slam after the last word).

## Done when
cue_check passes and the agent looked at `edl.txt`.

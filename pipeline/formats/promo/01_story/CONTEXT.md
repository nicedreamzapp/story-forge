---
stage: 01_story
outputs:
  - script.md
  - promo.json
  - stages/01_story/premise.md
gate: approved
---
# 01_story — the story, written for the viewer

One job: an approved narration script where every line says what the viewer should feel, and the
project's `promo.json` (voice, music, end card, Blender shots, YouTube text). No render yet.

## Reads
- Matt's idea and any existing VO; `../../../../_shared/script-writing.md`; the `screenwriting`
  skills (`sw-premise-theme` first); `../../../../LESSONS.json` filtered by the product's keywords.

## Writes
- `script.md`: numbered narration lines (`N. [picture note] spoken text`). Line N is voiced as
  `vo/final/part<N-1>.wav`. Optional indented sub-lines: `say: ...` (what the TTS reads when it
  differs, e.g. numbers) and `alt: ...` (a re-wording the voice stage may fall back to).
- `promo.json` (schema in `../SCHEMAS.md`; the template carries every field with the Sitka defaults).
- `stages/01_story/premise.md`: the premise, then a sentiment per line.

## Process
1. Premise: who it is for, the problem, what the product changes, the one thing to remember.
2. A sentiment per line. Write for the viewer; the judge's limits shape staging, never the story (RULES.md 32).
3. Every claim must be SHOWABLE with the real product (the design facts, 03). Numbers appear on screen
   only when the narrator says them.
4. The last line is the invitation; the end card (`promo.json endcard`) slams AFTER its last word.

## Done when
The files are real (no TEMPLATE marker) and `stages/01_story/APPROVED.md` holds Matt's words.
`bin/make-promo` builds a draft cut before that, and says the approval is open.

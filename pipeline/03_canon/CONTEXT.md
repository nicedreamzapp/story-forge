---
stage: 03_canon
outputs:
  - canon/
gate: approved
---
# 03_canon — lock the cast and the sets

One job: make ONE master image per character and per recurring set. Every later view
derives from these (frozen rule 10, RULES.md 6 and 8).

## Inputs
- Working (this film): `beats.json` (who and where appears), `stages/01_story/script.md`
- Reference (every film): `../../RULES.md` "How characters are made"
- Reference (every film): `../../bin/character_voice.py` casting (voice must match the
  character's gender, age and species; casting happens here, voicing in 05)

Do NOT load: `clips/`, sound files, other films' canon.

## Process
1. Generate candidates per character and set; keep the winner in `canon/`.
2. Delete every losing candidate the same session (frozen rule 13).
3. Need new angles later? Train or reuse the character LoRA now.

## Outputs
- `projects/<film>/canon/` (one master per character and set)

## Human check
Matt looks at every master and says yes. A drifted colour or texture is a no.
Write `APPROVED.md` listing each master he approved.

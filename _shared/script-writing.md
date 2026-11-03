## SCRIPT-WRITING SKILLS — use them BEFORE any render (installed 2026-09-07)

The `screenwriting` plugin is installed at user scope (12 skills, from
https://github.com/jtydhr88/screenwriting-skills — 19 books plus the Chekhov and Ozu
corpora). It is the WRITING half of Story Forge; the pipeline below is the RENDER half.
Nothing in it touches the pipeline, and it never overrides a rule in this file.

**Standing direction: every new film starts in the script, not the queue.** Before a
bible is written or a single still is generated, invoke the skills that fit the story and
use them to settle premise, structure, character conflict, and the dialogue — then carry
the result into `*.bible.sf` and the scene beats.

| Skill | Use it for |
|---|---|
| `sw-premise-theme` | the controlling idea — settle this FIRST, before anything else |
| `sw-story-structure` | act structure and beats → becomes the scene list |
| `sw-character-conflict` | who wants what, and what stands in the way |
| `sw-dialogue` | every spoken line, before it is voiced |
| `sw-scene-craft` | what each scene turns on — feeds the shot coverage plan |
| `sw-format-adaptation` | adapting an existing story or a formatted script |
| `sw-american-case-studies` / `sw-japanese-screenwriting` / `sw-korean-french-screenwriting` | worked examples when a film needs a reference |
| `chekhov-dramaturgy` / `ozu-screenplay-style` | quiet, character-driven, low-plot pieces |
| `sw-industry-business` | only for the business side; not part of the build |

**The bridge (ours, not theirs).** These skills output ordinary screenplay thinking —
beats, scenes, slug lines, dialogue. They do NOT emit `.sf`. The translation is our job
and it runs one way:

    premise → beats → scenes → *.bible.sf + .sf scene blocks → coverage plan → render

Write the drama first in plain screenplay terms, THEN convert each scene into `.sf`,
applying the givens below (multi-shot coverage, prompted mouth motion, density-matched
dialogue). Never let a screenwriting skill's formatting advice change `.sf` syntax, the
film bible spec, or any frozen rule — the craft is theirs, the language and the pipeline
stay ours.

**Story test before the render queue (2026-09-30).** Write, from the SHOT LIST ALONE (no
narration), the paragraph a first-time viewer would say the film is about. If it doesn't
match the premise, the shots are missing a beat — The Oldest Tree never showed the
grandfather wandering off, so the whole plot had to be guessed. Every plot turn needs a
shot that SHOWS it, and flashbacks need a spoken time marker ("Five hundred years ago").

**Sentiment, and who the script is for (2026-10-22, Fable review + Sitka promo).** Scripts
were being written for the VL judge, not the viewer, and no spec ever said what the viewer
should feel. Every beat (every narration line in a promo) carries a SENTIMENT line: what the
viewer feels there ("curiosity, then 'oh, that's clever'"). The judge's limits never override
the viewer's story: write the story for the viewer, then make each shot judgeable (a visible
state, RULES.md 1–2), not the other way round. If a beat cannot be made judgeable, it is
staged differently or checked by eye and marked UNCHECKED; it is not cut from the story.

**Dialogue caveat specific to this pipeline:** lines still get density-matched to the
mouth motion we prompt for (rule 9 / rule 3 below). A beautifully written speech that a
shot's mouth motion cannot carry gets rewritten shorter — the mouth wins, always.

**Model the viewer: pacing per shot (2026-11-02, from ClaudeAnimationBase's ANIMATION_GUIDE §4 and
lemo-opuscar's DIRECTOR §7, both MIT).** The viewer sees each shot once, at full speed, for the first
time. We know what happens because we wrote it; they don't. So for every shot:
- **List the reads.** In the shot list, write in order what the viewer has to understand in that shot
  (`reads: 1. the door is locked  2. Doug notices  3. Hank's grin`). Each read needs time for the eye to
  find it, to understand it, and to register before the next starts. Small, distant, fast or subtle reads
  take longer. A shot with many reads cannot be short; the reads set the length, the last shot included.
- **One read at a time.** Never start a read while the last one is still landing. Two things at once = the
  viewer sees one. Cause, then reaction, in sequence, never on top of each other. One subject plus its
  ambience ("the hand stays still while light spreads") is one read; two events joined by "while", "as",
  "meanwhile" or "at the same time" are two, so split them across beats or shots.
- **Fast actions, slow meanings.** A move can be quick when it is anticipated; what it MEANS needs a held
  beat after it. Hold after every fast action before the next read. Lead the eye to a read first (a look, a
  camera move, light) and give it time to get there.
- **Text is a read too.** Every title, callout, card and subtitle stays fully visible for chars/15 s
  (CJK 4.5 per second) + 1.5 s; `pipeline-tools/text_readtime_check.py` enforces it.

**Emotion transitions: faces act, they never snap.** When a face changes emotion inside a shot, prompt the
change as a sequence, never a swap (the recipe ClaudeAnimationBase's `emotions()` builds in code):
1. **Anticipation**: a small opposite move first (a dip of the head, a breath in) so the eye is ready.
2. **Squint / blink**: the eyes close a little for a split second at the change.
3. **The take**: the new emotion arrives with a body reaction (head pulls back, shoulders lift).
4. **Overshoot**: the new expression goes a touch past its mark (brows a little too high, grin too wide).
5. **Settle** into the held new emotion, and hold it long enough to read.
Prompt wording: "eyes narrow for a beat, then widen in surprise, brows overshooting high, then settle into a
wide grin", never "smiling, then suddenly furious". `spec_lint.py` prints an advisory (⚠, never a block) on
any shot field that stacks simultaneous reads or changes emotion with no transition beat.

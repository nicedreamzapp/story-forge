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

**Dialogue caveat specific to this pipeline:** lines still get density-matched to the
mouth motion we prompt for (rule 9 / rule 3 below). A beautifully written speech that a
shot's mouth motion cannot carry gets rewritten shorter — the mouth wins, always.

# Film template

The stamp for a new film. `bin/film-status projects/<film> --init` copies `stages/` into
the film without overwriting anything already there. Every file starts with a TEMPLATE
marker line; film-status treats a file that still has it as not written yet.

Also stamped (2026-11-24): `MATERIAL.md` (step one: Matt's real footage, screenshots and photos, gathered before
the script), `LOOK.md` (this film's own look from Matt's references; there is no shared house style) and
`ALLOW.md` (motifs Matt asked for that the cliche gate would otherwise block). `pipeline-tools/cliche_gate.py`
fails the film until LOOK.md is written and the shot list is clean.

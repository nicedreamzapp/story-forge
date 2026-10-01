# Film template

The stamp for a new film. `bin/film-status projects/<film> --init` copies `stages/` into
the film without overwriting anything already there. Every file starts with a TEMPLATE
marker line; film-status treats a file that still has it as not written yet.

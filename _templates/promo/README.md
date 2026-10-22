# Promo template

The stamp for a new promo. `bin/film-status projects/<film> --init --format promo` copies
everything here except this README into the film without overwriting anything already
there, and writes `projects/<film>/FORMAT`. Every file starts with a TEMPLATE marker line;
film-status treats a file that still has it as not written yet, and the JSON tools refuse
it (it is not valid JSON until the marker is gone). Schemas: `pipeline/formats/promo/SCHEMAS.md`.
Then: put the CAD GLBs and an HDRI in `assets/` (never committed), fill the files, and run
`bin/make-promo projects/<film>`. The worked example is `projects/sitka_demo/`.

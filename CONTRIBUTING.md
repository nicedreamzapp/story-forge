# Contributing

Thanks for taking a look. Story Forge was built on one Mac and still has some paths hard-coded to
it, so a bug report from a different machine is useful even if you never send code.

## Reporting a problem

Open an [issue](https://github.com/nicedreamzapp/story-forge/issues/new/choose). The things that
make it quick to fix:

- your Mac (chip and RAM) and macOS version, and your Python version
- what `./bin/sf doctor` prints
- the command you ran (`sf render`, `forge`, `make-promo` and so on) and the `.sf` script or
  project folder you ran it on
- the last lines of the output, and which model or ComfyUI workflow was loaded

## Running it locally

```bash
git clone https://github.com/nicedreamzapp/story-forge && cd story-forge
./bin/sf doctor                                         # what's missing
./bin/sf render story_forge/examples/test_tiny.sf --dry # parse only, no ComfyUI needed
./bin/sf render story_forge/examples/test_tiny.sf
```

A full render needs ComfyUI running with Flux and Wan or LTX loaded, plus ffmpeg. The gated
director pipeline (`./bin/forge`) needs more; see the README and [docs/install.md](docs/install.md).

## Tests

The `.sf` parser, packs and scaffolding have unit tests that need no GPU:

```bash
python3 -m pytest -q story_forge/tests
```

The 5 tests in `test_keyframes.py` are known to fail, because the keyframe wiring was removed from
`run.py` (see [docs/troubleshooting.md](docs/troubleshooting.md)). For changes to rendering or the gates, say
which project or script you rendered and what the gate reports said.

## Pull requests

Small and focused is easiest to review. For big changes, open an issue first so we can talk it
through.

Everyone taking part is expected to follow the [code of conduct](CODE_OF_CONDUCT.md).

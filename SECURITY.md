# Security policy

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report them privately through GitHub: go to the **Security** tab of this repo and click **Report a vulnerability** ([direct link](https://github.com/nicedreamzapp/story-forge/security/advisories/new)). Only the maintainer sees the report.

Helpful details: what you found, how to reproduce it, which commit, your Mac and macOS version, and which script or tool in `bin/` or `pipeline-tools/` is involved.

I aim to reply within 3 days and to ship a fix or a clear plan within 30 days, depending on severity. You will be credited in the advisory unless you ask not to be.

## Supported versions

Fixes go into the latest version on `main`. Please update before reporting if you are on an older version.

## What matters most here

The parts where a mistake could hurt someone:

- `server.py`, the Flask web UI on `127.0.0.1:17600`, including `/api/upload`, which saves images from the browser and passes them to ComfyUI
- `bin/imessage-video-bot`, which reads the local Messages database and turns incoming messages into render prompts
- `bin/browser-acquire` and `bin/browser_acquire_driver.py`, which copy files to a second Mac over ssh and drive a logged-in browser there
- the tools in `bin/` and `pipeline-tools/` that run ffmpeg and model scripts on paths taken from `.sf` scripts and project folders

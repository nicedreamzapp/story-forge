import {Config} from '@remotion/cli/config';

// Story Forge promo renderer. Props come from pipeline-tools/render_edl.py --renderer remotion.
Config.setVideoImageFormat('jpeg');
Config.setJpegQuality(92);
Config.setOverwriteOutput(true);

// 2026-10-22: the default chrome-headless-shell never fires requestAnimationFrame on this
// M5 (macOS / Darwin 27), so every render hung on "Waiting for root component to load".
// Chrome for Testing (new headless) works. Keep this unless a test render proves otherwise.
Config.setChromeMode('chrome-for-testing');

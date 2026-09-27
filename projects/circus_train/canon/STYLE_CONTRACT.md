# Style contract

Paste this paragraph verbatim into every image and animate prompt for this project. It was measured from the frames below — frames that already passed both gates and made the cut — not written from imagination.

## The contract

Fifty-millimetre framing on a shallow plane of focus: the subject and the ground it stands on stay sharp while everything behind falls into gentle bokeh. Warm low-angle sunlight enters from one side, soft-edged and naturally diffused, with light haze carrying depth through the air. Golden yellow, warm brown, soft green and pale orange dominate, with muted red accents. Blacks stay lifted, highlights run slightly hot, overall contrast is low. Surfaces read smooth and painterly with almost no grain. Late-afternoon golden hour, clear to lightly hazy.

## Known outlier

`ellie_eye` is an INTERIOR frame: soft even light, no golden hour, no haze, 50-85mm. It is the one frame of the eight that does not fit the paragraph above. Interior beats should keep the lens, palette and lifted blacks and drop the low-angle sun.

## Read from

- LOCKED_ellie_eye.png
- LOCKED_r1_monkeys_out.png
- LOCKED_r3_giraffe_out.png
- LOCKED_r4_parrots_sky.png
- LOCKED_s1.png
- LOCKED_s2_call.png
- LOCKED_s2b_smoke.png
- LOCKED_s3b_wagonpass.png

## Provenance

Frames read locally by Qwen3-VL (film_qc.vl_ask) 2026-08-01. The paragraph was written by hand from those readings after gemma :9420 spent its token budget reasoning and returned no answer three times; `merge_readings()` is the deterministic fallback for future runs. Raw readings below are the model's, verbatim.

## Raw readings

```
--- ellie_eye
LENS: ~50-85mm equivalent, shallow depth of field (foreground slats in focus, background blurred).
LIGHT: Key light from front-left, soft and diffused, likely a single source (possibly practical or window light).
PALETTE: Dark brown (wood), off-white (skin), amber (iris), black (pupil and shadows).
CONTRAST: Blacks slightly lifted, highlights not clipped; mid-tone emphasis.
TEXTURE: Smooth, digital render with minimal grain; soft focus on non-focused areas; no visible atmospheric haze.
TIME: Indeterminate, but soft, even lighting suggests overcast daylight or interior diffused light.

--- r1_monkeys_out
LENS: ~50mm equivalent, shallow depth of field (foreground monkeys sharp, background softly blurred).

LIGHT: Low-angle, warm, directional key light from upper left (sunrise/sunset), soft with gentle diffusion, likely natural sunlight.

PALETTE: Golden yellow, warm brown, soft green, muted red (hats).

CONTRAST: Blacks are lifted, highlights are slightly clipped but not harsh—overall soft contrast.

TEXTURE: Smooth, painterly softness; minimal grain; light atmospheric haze; gentle bokeh in background.

TIME: Early morning or late afternoon (golden hour), clear or lightly hazy weather.

--- r3_giraffe_out
LENS: ~50mm equivalent, shallow depth of field (foreground giraffe and wagon in focus, background softly blurred).

LIGHT: Low-angle, warm, directional light from the upper right (sunset/sunrise), soft diffusion, likely natural sunlight with atmospheric scattering.

PALETTE: Golden yellow, warm brown, soft green, pale orange.

CONTRAST: Blacks are lifted (no deep shadows), highlights are slightly clipped (bright sky areas), overall low-contrast with a soft, painterly feel.

TEXTURE: Smooth, digital render with minimal grain; soft focus on distant elements; light atmospheric haze enhancing depth.

TIME: Late afternoon or early evening (golden hour), clear or lightly hazy skies, calm weather.

--- r4_parrots_sky
LENS: ~50mm equivalent, shallow depth of field (foreground parrots sharp, background slightly soft).
LIGHT: Low-angle, warm, directional light from lower right; soft diffusion, likely sunset; key light source is the sun near horizon.
PALETTE: Deep red, vibrant blue, golden yellow, dark gray (smoke).
CONTRAST: Blacks slightly lifted (smoke retains detail), highlights not clipped (sky retains texture).
TEXTURE: Smooth, digital render; minimal grain; soft atmospheric haze; slight bloom around light edges.
TIME: Late afternoon to early evening (sunset); clear to partly cloudy skies, warm ambient light.

--- s1
LENS: ~50mm equivalent, shallow depth of field (foreground subjects in focus, background softly blurred).

LIGHT: Soft, warm, directional light from upper left (approx. 45°), likely golden hour sun; key light source is natural sunlight, diffused by atmosphere.

PALETTE: Golden yellow, soft green, warm brown, muted blue-gray (in water and sky).

CONTRAST: Blacks are lifted (no deep shadows), highlights are slightly clipped but not harsh; overall low-contrast, painterly tonal range.

TEXTURE: Smooth, digital render with minimal grain; soft focus on distant elements; light atmospheric haze enhancing depth; grass and fur show fine, stylized detail.

TIME: Late afternoon (golden hour), clear or lightly hazy weather, calm conditions.

--- s2_call
LENS: ~50mm equivalent, shallow depth of field (foreground rails and train front in focus, background softly blurred).

LIGHT: Low-angle, warm, directional light from the upper right (sunset direction), soft to medium hardness, key light source is the setting sun.

PALETTE: Burnt orange, deep red, dark charcoal gray, muted beige.

CONTRAST: Blacks are slightly lifted (visible shadow detail), highlights are slightly clipped on the train’s headlamp and smoke edges.

TEXTURE: Smooth, digital render-like; minimal grain, soft focus on distant elements, light atmospheric haze diffusing light and softening edges.

TIME: Late afternoon to early evening (golden hour), clear to lightly hazy skies, dry desert conditions.

--- s2b_smoke
LENS: ~50-70mm equivalent, shallow depth of field (bokeh in smoke and background).
LIGHT: Key light from upper right, soft and diffused, likely sunset/sunrise; warm, golden tone; source appears to be natural sky light.
PALETTE: Sepia-brown, dark grey, rust-red, warm orange.
CONTRAST: Blacks slightly lifted, highlights not clipped; mid-tones rich, subtle gradation.
TEXTURE: Smooth, low grain; soft focus on smoke; slight atmospheric haze; metallic surfaces show fine detail without noise.
TIME: Late afternoon or early evening (golden hour); overcast or hazy sky, diffused sunlight.

--- s3b_wagonpass
LENS: ~50mm equivalent, shallow depth of field (foreground horse in focus, background softly blurred).

LIGHT: High-angle, slightly side-lit from upper left; soft, diffused key light, likely from a hazy sun; no harsh shadows, suggesting overcast or golden hour diffusion.

PALETTE: Warm earthy browns, golden yellows, soft greens, and pale sky blues.

CONTRAST: Blacks are lifted (no deep shadows), highlights are slightly clipped on the horse’s coat and dust cloud, but not overly so.

TEXTURE: Smooth, painterly softness; minimal grain; visible atmospheric haze in the dust cloud and distant landscape; air feels dry and dusty.

TIME: Late afternoon (golden hour), clear or lightly hazy skies, warm light.
```

## LIGHTING — a given on every still and shot (Matt, 2026-11-02)

Source: the one-page "Lighting Guide to Master in AI Filmmaking" (credit: shailesh, beginnersblog.org), saved locally at
`_shared/refs/lighting-guide-ai-filmmaking.jpg` (M5 only, kept out of the public repo). Read the image when a lighting call is not covered below.

Every still prompt and every i2v prompt names its light on purpose, the same way rule 5 makes every move motivated.
A shot whose lighting is not stated is a flag, never a default.

### The core principles
1. **Key direction.** Place the key 30 to 60 degrees off the camera axis, slightly above eye line.
2. **Shoot the shadow side.** Put the camera on the side away from the key for shape and depth (the "far side" look). Facing the key flattens the face.
3. **Motivate it.** Every light must feel like it comes from something in the scene: window, lamp, monitor, TV, neon, candle, street light. Name the source in the prompt.
4. **Soft unless there is a reason.** Big, close sources wrap and flatter. Hard light is a choice (drama, noon sun, stylized scenes).
5. **Light the background.** The room should say something about the scene. A practical lamp or a gradient on the wall separates the subject.
6. **Shape and contrast.** Cut and guide the eye; do not light everything evenly.
7. **Texture and atmosphere.** Haze or backlit dust shows the light and adds depth.
8. **Negative fill.** Remove bounce (a dark wall or flag on the shadow side) to deepen shadows and sculpt the face.
9. **Build in layers.** Expose for the room first, then bring the key up.
10. **Grow your kit slowly.** One good key beats five lights.

### The foundation (three roles, not a formula)
- **Key:** main light; sets direction and mood; usually one side, slightly above eye level.
- **Fill:** lifts the shadows gently; often just bounce, often skipped.
- **Back / hair:** separates the subject from the background.
Literal three-point lighting often looks flat. One soft key + practicals + negative fill usually reads more cinematic.

### The one-light blueprint (default for a character close-up)
Soft key 30 to 60 degrees off axis on the subject's far side, camera on the shadow side, a practical lamp in the
background on the same side as the key (motivated), black flag or dark wall on the camera side for negative fill.
Aim for a Rembrandt triangle (a small patch of light on the far cheek).

### Cheap ways to soften
Bounce off a wall · shoot through a bedsheet or sheer curtain · diffusion fabric · a larger softbox · move the source closer.

### Outdoors (work with the sun)
| Condition | Light quality | Expect |
|---|---|---|
| Golden hour | low, warm sun | even, flattering, detailed skies |
| Midday | overhead sun | harsh shadows and dark eye sockets |
| Overcast | diffused | soft, even, but flat |
Backlight with low sun, still shoot the shadow side; at midday use open shade, overhead diffusion, or flip the subject so the sun is behind.

### Layered workflow (the order to describe a scene's light)
1. Set the camera for the look you want. 2. Light the background first. 3. Expose for the bright areas or windows.
4. Set the subject. 5. Raise the key slowly. 6. Add fill or negative fill only if needed. 7. Add separation only if the subject blends in.
If a key light is in full power, the room is probably underlit or the light is too far away.

### Shaping tools (words to use in prompts)
Softbox (bigger, softer) · lantern (soft ambient spread) · barn doors (keep light off walls) · grid (narrow beam) ·
flag (block light, create negative fill) · scrim (cut intensity without changing softness) · bounce / reflector (soft fill) ·
gobo / projector (window, branch or blind patterns) · haze (makes beams visible) · practicals (lamps in frame).

### Troubleshooting
| Symptom | Fix |
|---|---|
| Face looks flat | move the key 30 to 60 degrees off axis, shoot the shadow side, add negative fill |
| Harsh shadows | bigger or closer source, diffuse it, or bounce it |
| Subject pasted onto a dark background | light the background, add a practical or a back light |
| Window blows out | expose for the window, bring the key up to match |
| Background looks flat | add a practical, a gradient or gobo pattern |
| Light feels fake | motivate it from a visible source, match its color |
| Everything evenly bright | turn off fill, add negative fill, light in pools |
| Dark eye sockets | lower the key toward eye level, add a small bounce under |
| Subject blends into the background | back or hair light, or separate by color and brightness |
| Skin looks too red | cooler white balance or a less warm source |

### How this lands in our pipeline
- The still stage (Flux / LoRA stills) writes key side, softness, motivating source, background practical and negative fill into every prompt.
- The i2v stage (K6 default) keeps the light consistent across coverage: the key stays on the same side of the set for every setup of a scene.
- Coverage from new angles moves the camera, not the sun: keep the motivated source fixed and re-derive which side is the shadow side.

# v3 1-step distill — checkpoint eval

Metric: per-frame LPIPS, student 1-step render vs teacher 4-step render (same still/prompt/seed). Eval set: first 8 prompts.
**Measured 1-step wall @ 192×192: 0.2181** (raw lightx2v 1-step vs 4-step teacher, same res; literature ref 1.09). Lower is better.

| checkpoint | mean LPIPS | beats wall? |
|---|---|---|
| student_step_0050.safetensors | 0.1043 | ✅ |
| student_step_0100.safetensors | 0.0950 | ✅ |
| student_step_0150.safetensors | 0.0701 | ✅ |
| student_step_0200.safetensors | 0.0614 | ✅ |
| student_step_0250.safetensors | 0.0535 | ✅ |
| student_step_0300.safetensors | 0.0521 | ✅ |

**Best: student_step_0300.safetensors @ LPIPS 0.0521** (beats the wall), vs measured wall 0.2181.

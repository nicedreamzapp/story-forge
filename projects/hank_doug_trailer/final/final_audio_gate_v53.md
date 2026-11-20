{
 "ran": "2026-11-18T19:21:50",
 "file": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v53.mp4",
 "target_lufs": -14.0,
 "tp_max": -1.0,
 "tol": 0.5,
 "audio_index": 0,
 "steps": [
  {
   "attempt": 1,
   "method": "static gain +0.10 dB + 4x-oversampled peak limiter at -1.5 dBTP (peaks would reach +0.0)",
   "measured_in": {
    "input_i": -14.1,
    "input_tp": -0.09,
    "input_lra": 9.7,
    "input_thresh": -25.47,
    "target_offset": -0.34
   },
   "after": {
    "I": -14.3,
    "TP": -1.1,
    "LRA": 9.3
   }
  }
 ],
 "video_s": 64.333,
 "audio_in_s": [
  64.32
 ],
 "before": {
  "I": -14.1,
  "TP": -0.1,
  "LRA": 9.3
 },
 "audio_out_s": 64.32,
 "video_out_s": 64.333,
 "after": {
  "I": -14.3,
  "TP": -1.1,
  "LRA": 9.3
 },
 "verdict": "FIXED",
 "output": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v53.mp4",
 "output_bytes": 64645656,
 "why": "-14.1 LUFS / -0.1 dBTP -> -14.3 LUFS / -1.1 dBTP (static gain +0.10 dB + 4x-oversampled peak limiter at -1.5 dBTP (peaks would reach +0.0)); audio 64.32s covers picture 64.33s"
}
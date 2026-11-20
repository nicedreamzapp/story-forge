{
 "ran": "2026-11-18T13:16:42",
 "file": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v51.mp4",
 "target_lufs": -14.5,
 "tp_max": -1.9,
 "tol": 0.5,
 "audio_index": 0,
 "steps": [
  {
   "attempt": 1,
   "method": "static gain -0.15 dB + 4x-oversampled peak limiter at -2.4 dBTP (peaks would reach -0.3)",
   "measured_in": {
    "input_i": -14.35,
    "input_tp": -0.15,
    "input_lra": 10.8,
    "input_thresh": -25.57,
    "target_offset": 0.7
   },
   "after": {
    "I": -15.2,
    "TP": -2.1,
    "LRA": 10.3
   }
  },
  {
   "attempt": 2,
   "method": "static gain +0.55 dB + 4x-oversampled peak limiter at -2.9 dBTP (peaks would reach +0.4)",
   "measured_in": {
    "input_i": -14.35,
    "input_tp": -0.15,
    "input_lra": 10.8,
    "input_thresh": -25.57,
    "target_offset": 0.7
   },
   "after": {
    "I": -15.0,
    "TP": -2.5,
    "LRA": 9.4
   }
  }
 ],
 "video_s": 57.25,
 "audio_in_s": [
  57.408
 ],
 "before": {
  "I": -14.2,
  "TP": -0.1,
  "LRA": 11.6
 },
 "audio_out_s": 57.408,
 "video_out_s": 57.25,
 "after": {
  "I": -15.0,
  "TP": -2.5,
  "LRA": 9.4
 },
 "verdict": "FIXED",
 "output": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v51.mp4",
 "output_bytes": 64932391,
 "why": "-14.2 LUFS / -0.1 dBTP -> -15.0 LUFS / -2.5 dBTP (static gain +0.55 dB + 4x-oversampled peak limiter at -2.9 dBTP (peaks would reach +0.4)); audio 57.41s covers picture 57.25s"
}
{
 "ran": "2026-11-18T12:45:25",
 "file": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v5.mp4",
 "target_lufs": -14.5,
 "tp_max": -1.9,
 "tol": 0.5,
 "audio_index": 0,
 "steps": [
  {
   "attempt": 1,
   "method": "static gain -0.24 dB + 4x-oversampled peak limiter at -2.4 dBTP (peaks would reach +0.7)",
   "measured_in": {
    "input_i": -14.26,
    "input_tp": 0.92,
    "input_lra": 10.6,
    "input_thresh": -25.44,
    "target_offset": 0.64
   },
   "after": {
    "I": -15.2,
    "TP": -2.2,
    "LRA": 10.0
   }
  },
  {
   "attempt": 2,
   "method": "static gain +0.46 dB + 4x-oversampled peak limiter at -2.9 dBTP (peaks would reach +1.4)",
   "measured_in": {
    "input_i": -14.26,
    "input_tp": 0.92,
    "input_lra": 10.6,
    "input_thresh": -25.44,
    "target_offset": 0.64
   },
   "after": {
    "I": -15.0,
    "TP": -2.5,
    "LRA": 9.0
   }
  }
 ],
 "video_s": 57.25,
 "audio_in_s": [
  57.408
 ],
 "before": {
  "I": -14.1,
  "TP": 0.9,
  "LRA": 11.2
 },
 "audio_out_s": 57.408,
 "video_out_s": 57.25,
 "after": {
  "I": -15.0,
  "TP": -2.5,
  "LRA": 9.0
 },
 "verdict": "FIXED",
 "output": "/Users/dtribe/Desktop/PROJECTS/story-forge/projects/hank_doug_trailer/final/hank_doug_wild_rescue_trailer_v5.mp4",
 "output_bytes": 66134415,
 "why": "-14.1 LUFS / 0.9 dBTP -> -15.0 LUFS / -2.5 dBTP (static gain +0.46 dB + 4x-oversampled peak limiter at -2.9 dBTP (peaks would reach +1.4)); audio 57.41s covers picture 57.25s"
}
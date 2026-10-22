// Mirrors pipeline/formats/promo/SCHEMAS.md (edl.json, callouts.json, vo/words.json).
export type Shot = {
  cid: string;
  file: string;
  kind?: 'video' | 'image';
  src_in: number;
  src_out: number;
  rec_in: number;
  rec_out: number;
  line: number;
  transition: 'cut' | 'xfade';
  xfade: number;
  head?: number;
  tail?: number;
  anchor_word?: number;
  speed?: number;
  move?: string;
};
export type AudioClip = {file: string; rec_in: number; kind: string; line?: number};
export type Title = {text: string; rec_in: number; rec_out: number; line?: number; word?: string};
export type Overlay = {
  file: string;
  rec_in: number;
  rec_out: number;
  x: number; // center, normalized
  y: number;
  w: number; // width, normalized; height keeps the clip's aspect
  opacity: number;
  cue_word?: string;
  src_in?: number;
};
export type Edl = {
  fps: number;
  w: number;
  h: number;
  dur: number;
  shots: Shot[];
  audio: AudioClip[];
  titles?: Title[];
  overlays?: Overlay[];
  endcard?: {rec_in: number; rec_out: number; title: string; tagline?: string; url?: string} | null;
};
export type Keyframe = [number, number, number];
export type Callout = {
  id: string;
  label: string;
  rec_in: number;
  rec_out: number;
  tip: [number, number] | Keyframe[];
  text_at: [number, number];
  cid?: string;
  part?: string;
};
export type Word = {i: number; line: number; word: string; start: number; end: number};
export type Words = {
  gap: number;
  lines: {line: number; wav: string; start: number; end: number; text: string}[];
  words: Word[];
};
export type PromoProps = {
  edl: Edl;
  callouts: Callout[] | {callouts: Callout[]};
  words: Words;
  base: string; // path under public/, e.g. "media/<film>/"
  voGainDb?: number;
  music?: {file: string; gain_db: number} | null;
  lowerThird?: boolean;
  fit?: 'crop' | 'pad';
  audioFile?: string | null; // a finished mix (promo_mix.py) replaces the per-line VO + music
  bug?: string | null;
};

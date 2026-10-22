import React from 'react';
import {CalculateMetadataFunction, Composition} from 'remotion';
import {Promo} from './Promo';
import {PromoProps} from './types';

// Placeholder props so `remotion studio` opens; real props come from render_edl.py --props.
const defaults: PromoProps = {
  edl: {fps: 30, w: 1920, h: 1080, dur: 2, shots: [], audio: [], titles: [{text: 'PROMO', rec_in: 0.2, rec_out: 1.9}]},
  callouts: [],
  words: {gap: 0.35, lines: [], words: []},
  base: 'media/',
  lowerThird: false,
};

const calc: CalculateMetadataFunction<PromoProps> = ({props}) => ({
  fps: props.edl.fps,
  width: props.edl.w,
  height: props.edl.h,
  durationInFrames: Math.max(1, Math.round(props.edl.dur * props.edl.fps)),
});

export const RemotionRoot: React.FC = () => (
  <Composition
    id="Promo"
    component={Promo}
    width={1920}
    height={1080}
    fps={30}
    durationInFrames={60}
    defaultProps={defaults}
    calculateMetadata={calc}
  />
);

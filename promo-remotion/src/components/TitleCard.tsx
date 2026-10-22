import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const AMBER = '#fbbf24';
const FONT = '"Avenir Next", "SF Pro Display", "Helvetica Neue", sans-serif';

// Kinetic title: letters spring in one after another (scale + opacity), an amber bar wipes
// under them, everything fades out over the last 9 frames.
export const TitleCard: React.FC<{text: string}> = ({text}) => {
  const frame = useCurrentFrame();
  const {fps, durationInFrames} = useVideoConfig();
  const out = interpolate(frame, [durationInFrames - 9, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
  const bar = spring({frame: frame - 6, fps, config: {damping: 20, stiffness: 90}});
  const letters = text.split('');
  return (
    <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', opacity: out}}>
      <div style={{display: 'flex', flexDirection: 'column', alignItems: 'center'}}>
        <div style={{display: 'flex', gap: text.length <= 8 ? 28 : 6}}>
          {letters.map((ch, i) => {
            const s = spring({frame: frame - i * 2, fps, config: {damping: 11, stiffness: 170}});
            return (
              <span
                key={i}
                style={{
                  display: 'inline-block',
                  fontFamily: FONT,
                  fontWeight: 800,
                  fontSize: 200,
                  color: 'white',
                  transform: `scale(${interpolate(s, [0, 1], [1.6, 1])})`,
                  opacity: Math.min(1, s * 1.5),
                  textShadow: '0 8px 30px rgba(0,0,0,0.55)',
                }}
              >
                {ch === ' ' ? ' ' : ch}
              </span>
            );
          })}
        </div>
        <div style={{height: 10, width: `${bar * 100}%`, background: AMBER, borderRadius: 5, marginTop: 8}} />
      </div>
    </AbsoluteFill>
  );
};

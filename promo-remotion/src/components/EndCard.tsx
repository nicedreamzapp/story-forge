import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';

const AMBER = '#fbbf24';
const TEAL = '#2dd4bf';
const FONT = '"Avenir Next", "SF Pro Display", "Helvetica Neue", sans-serif';

// The end card (Sitka recipe): it starts AFTER the last word, on the music's downbeat. A white
// flash, the brand SLAMS in (scale 1.35 -> 1), the amber bar wipes, the tagline rises in, the
// URL follows; the sting rings out underneath.
export const EndCard: React.FC<{title: string; tagline?: string; url?: string}> = ({title, tagline, url}) => {
  const f = useCurrentFrame();
  const {fps} = useVideoConfig();
  const slam = spring({frame: f, fps, config: {damping: 14, stiffness: 220}});
  const bar = spring({frame: f - 3, fps, config: {damping: 20, stiffness: 90}});
  const tag = spring({frame: f - Math.round(0.45 * fps), fps, config: {damping: 18}});
  const link = spring({frame: f - Math.round(0.85 * fps), fps, config: {damping: 18}});
  const flash = interpolate(f, [0, Math.round(0.25 * fps)], [0.92, 0], {extrapolateRight: 'clamp'});
  return (
    <AbsoluteFill style={{background: 'radial-gradient(ellipse at 50% 60%, #16202a 0%, #06080c 70%)'}}>
      <AbsoluteFill style={{justifyContent: 'center', alignItems: 'center', flexDirection: 'column', top: -60}}>
        <div style={{fontFamily: FONT, fontWeight: 800, fontSize: 230, color: 'white', letterSpacing: title.length <= 8 ? 40 : 4,
          transform: `scale(${interpolate(slam, [0, 1], [1.35, 1])})`, textShadow: '0 10px 40px rgba(0,0,0,0.6)'}}>
          {title}
        </div>
        <div style={{height: 10, width: `${bar * 42}%`, background: AMBER, borderRadius: 5, marginTop: 10}} />
        {tagline ? (
          <div style={{fontFamily: FONT, fontWeight: 600, fontSize: 58, color: 'white', marginTop: 70, opacity: tag,
            transform: `translateY(${(1 - tag) * 18}px)`}}>{tagline}</div>
        ) : null}
        {url ? (
          <div style={{fontFamily: FONT, fontWeight: 600, fontSize: 38, color: TEAL, marginTop: 34, opacity: link}}>{url}</div>
        ) : null}
      </AbsoluteFill>
      <AbsoluteFill style={{backgroundColor: 'white', opacity: flash}} />
    </AbsoluteFill>
  );
};

// The corner logo bug, on screen until the end card.
export const Bug: React.FC<{text: string}> = ({text}) => (
  <AbsoluteFill>
    <div style={{position: 'absolute', top: '3.2%', right: '3.5%', fontFamily: FONT, fontWeight: 800, fontSize: 36,
      letterSpacing: text.length <= 8 ? 8 : 1, color: 'rgba(255,255,255,0.7)'}}>{text}</div>
  </AbsoluteFill>
);

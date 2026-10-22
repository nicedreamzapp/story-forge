import React from 'react';
import {AbsoluteFill, interpolate, spring, useCurrentFrame, useVideoConfig} from 'remotion';
import {Callout, Keyframe} from '../types';

const TEAL = '#2dd4bf';
const FONT = '"Avenir Next", "SF Pro Display", "Helvetica Neue", sans-serif';

// Tip position at final-timeline time t: a fixed [x, y] or linear interpolation of [t, x, y] keyframes.
export const tipAt = (tip: Callout['tip'], t: number): [number, number] => {
  if (Array.isArray(tip[0])) {
    const ks = [...(tip as Keyframe[])].sort((a, b) => a[0] - b[0]);
    const ts = ks.map((k) => k[0]);
    if (ks.length === 1) return [ks[0][1], ks[0][2]];
    const x = interpolate(t, ts, ks.map((k) => k[1]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    const y = interpolate(t, ts, ks.map((k) => k[2]), {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});
    return [x, y];
  }
  return tip as [number, number];
};

const quadLength = (x0: number, y0: number, cx: number, cy: number, x1: number, y1: number) => {
  let len = 0;
  let px = x0;
  let py = y0;
  for (let i = 1; i <= 32; i++) {
    const u = i / 32;
    const x = (1 - u) * (1 - u) * x0 + 2 * (1 - u) * u * cx + u * u * x1;
    const y = (1 - u) * (1 - u) * y0 + 2 * (1 - u) * u * cy + u * u * y1;
    len += Math.hypot(x - px, y - py);
    px = x;
    py = y;
  }
  return len;
};

// Label pill springs in, then an arrow draws itself (SVG stroke-dashoffset, spring-driven)
// from the pill to the part; the tip follows the keyframes every frame; a dot pops at the tip.
export const CalloutArrow: React.FC<{callout: Callout}> = ({callout}) => {
  const frame = useCurrentFrame();
  const {fps, width: W, height: H, durationInFrames} = useVideoConfig();
  const t = callout.rec_in + frame / fps;
  const [tx, ty] = tipAt(callout.tip, t);
  const ex = tx * W;
  const ey = ty * H;
  const bx = callout.text_at[0] * W;
  const by = callout.text_at[1] * H;

  const pill = spring({frame, fps, config: {damping: 12, stiffness: 160}});
  const draw = spring({frame: frame - 4, fps, config: {damping: 18, stiffness: 120}});
  const dot = spring({frame: frame - 14, fps, config: {damping: 9, stiffness: 200}});
  const out = interpolate(frame, [durationInFrames - 8, durationInFrames], [1, 0], {extrapolateLeft: 'clamp', extrapolateRight: 'clamp'});

  // start the arrow at the pill's lower/upper edge, curve it gently toward the tip
  const sx = bx;
  const sy = ey > by ? by + 34 : by - 34;
  const cx = (sx + ex) / 2 + (ey - sy) * 0.18;
  const cy = (sy + ey) / 2 - (ex - sx) * 0.18;
  const len = quadLength(sx, sy, cx, cy, ex, ey);
  const d = `M ${sx} ${sy} Q ${cx} ${cy} ${ex} ${ey}`;

  return (
    <AbsoluteFill style={{opacity: out}}>
      <svg width={W} height={H} style={{position: 'absolute', inset: 0}}>
        <path d={d} fill="none" stroke="rgba(0,0,0,0.45)" strokeWidth={9} strokeLinecap="round"
          strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
        <path d={d} fill="none" stroke="white" strokeWidth={5} strokeLinecap="round"
          strokeDasharray={len} strokeDashoffset={len * (1 - draw)} />
        <circle cx={ex} cy={ey} r={22 * dot} fill="rgba(255,255,255,0.35)" />
        <circle cx={ex} cy={ey} r={11 * dot} fill={TEAL} stroke="white" strokeWidth={3 * dot} />
      </svg>
      <div
        style={{
          position: 'absolute',
          left: bx,
          top: by,
          transform: `translate(-50%, -50%) scale(${0.6 + 0.4 * pill})`,
          opacity: Math.min(1, pill * 1.4),
          padding: '14px 30px',
          borderRadius: 999,
          background: 'rgba(12,18,28,0.82)',
          border: `3px solid ${TEAL}`,
          color: 'white',
          fontFamily: FONT,
          fontWeight: 600,
          fontSize: 44,
          whiteSpace: 'nowrap',
          boxShadow: '0 8px 30px rgba(0,0,0,0.35)',
        }}
      >
        {callout.label}
      </div>
    </AbsoluteFill>
  );
};

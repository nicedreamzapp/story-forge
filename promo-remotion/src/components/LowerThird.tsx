import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig} from 'remotion';
import {Words} from '../types';

const TEAL = '#2dd4bf';
const FONT = '"Avenir Next", "SF Pro Display", "Helvetica Neue", sans-serif';

// Word-synced lower third: the current narration line, the spoken word lit in teal
// the frame its onset arrives (times from vo/words.json, final timeline).
export const LowerThird: React.FC<{words: Words}> = ({words}) => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const t = frame / fps;
  const line = words.lines.find((l) => t >= l.start - 0.1 && t <= l.end + 0.1);
  if (!line) return null;
  const ws = words.words.filter((w) => w.line === line.line);
  return (
    <AbsoluteFill style={{justifyContent: 'flex-end', alignItems: 'center', paddingBottom: 70}}>
      <div style={{maxWidth: 1500, padding: '16px 34px', borderRadius: 18, background: 'rgba(8,12,20,0.66)',
        fontFamily: FONT, fontWeight: 600, fontSize: 46, lineHeight: 1.3, textAlign: 'center'}}>
        {ws.map((w, k) => {
          const lit = t >= w.start;
          const next = k + 1 < ws.length ? ws[k + 1].start : w.end + 0.15;
          const now = t >= w.start && t < next;
          return (
            <span key={w.i} style={{color: now ? TEAL : lit ? 'white' : 'rgba(255,255,255,0.45)'}}>{w.word} </span>
          );
        })}
      </div>
    </AbsoluteFill>
  );
};

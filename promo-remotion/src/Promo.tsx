import React from 'react';
import {AbsoluteFill, Audio, Img, interpolate, OffthreadVideo, Sequence, staticFile, useCurrentFrame} from 'remotion';
import {CalloutArrow} from './components/CalloutArrow';
import {LowerThird} from './components/LowerThird';
import {TitleCard} from './components/TitleCard';
import {Bug, EndCard} from './components/EndCard';
import {Callout, PromoProps, Shot} from './types';

const dbToGain = (db: number) => Math.pow(10, db / 20);

// One shot. Hard cut = it simply starts on its frame. Xfade = it starts `head` early and
// fades in over 2*head frames, so it is 50% on screen at rec_in (the word onset).
// Never a speed change (frozen rule 4); stills get a slow, sub-pixel push (no shaking).
const ShotLayer: React.FC<{shot: Shot; fps: number; base: string; fit: 'crop' | 'pad'; headF: number; durF: number}> = ({
  shot, fps, base, fit, headF, durF,
}) => {
  const f = useCurrentFrame();
  const opacity = shot.transition === 'xfade' && headF > 0 ? interpolate(f, [0, 2 * headF], [0, 1], {extrapolateRight: 'clamp'}) : 1;
  const style: React.CSSProperties = {width: '100%', height: '100%', objectFit: fit === 'pad' ? 'contain' : 'cover'};
  if (shot.kind === 'image') {
    const z = interpolate(f, [0, durF], [1, 1.07]);
    return (
      <AbsoluteFill style={{opacity, backgroundColor: 'black'}}>
        <Img src={staticFile(base + shot.file)} style={{...style, transform: `scale(${z})`}} />
      </AbsoluteFill>
    );
  }
  const trimBefore = Math.max(0, Math.round((shot.src_in - (shot.head ?? 0)) * fps));
  return (
    <AbsoluteFill style={{opacity, backgroundColor: 'black'}}>
      <OffthreadVideo src={staticFile(base + shot.file)} trimBefore={trimBefore} trimAfter={trimBefore + durF} muted style={style} />
    </AbsoluteFill>
  );
};

export const Promo: React.FC<PromoProps> = (props) => {
  const {edl, base, words} = props;
  const fps = edl.fps;
  const callouts: Callout[] = Array.isArray(props.callouts) ? props.callouts : props.callouts?.callouts ?? [];
  const fit = props.fit ?? 'crop';
  return (
    <AbsoluteFill style={{backgroundColor: 'black'}}>
      {edl.shots.map((s, i) => {
        const inF = Math.round(s.rec_in * fps);
        const outF = Math.round(s.rec_out * fps);
        const headF = Math.round((s.head ?? 0) * fps);
        const tailF = Math.round((s.tail ?? 0) * fps);
        const durF = outF - inF + headF + tailF;
        return (
          <Sequence key={`shot${i}`} from={inF - headF} durationInFrames={durF} layout="none">
            <AbsoluteFill>
              <ShotLayer shot={s} fps={fps} base={base} fit={fit} headF={headF} durF={durF} />
            </AbsoluteFill>
          </Sequence>
        );
      })}
      {props.audioFile ? <Audio src={staticFile(base + props.audioFile)} /> : null}
      {(props.audioFile ? [] : edl.audio).map((a, i) => (
        <Sequence key={`a${i}`} from={Math.round(a.rec_in * fps)} layout="none">
          <Audio src={staticFile(base + a.file)} volume={dbToGain(props.voGainDb ?? 0)} />
        </Sequence>
      ))}
      {props.music && !props.audioFile ? <Audio src={staticFile(base + props.music.file)} volume={dbToGain(props.music.gain_db)} /> : null}
      {(edl.overlays ?? []).map((o, i) => {
        const inF = Math.round(o.rec_in * fps);
        const durF = Math.max(1, Math.round(o.rec_out * fps) - inF);
        const wPx = o.w * edl.w;
        return (
          <Sequence key={`ov${i}`} from={inF} durationInFrames={durF} layout="none">
            <AbsoluteFill>
              <OffthreadVideo
                src={staticFile(base + o.file)}
                transparent
                muted
                trimBefore={Math.round((o.src_in ?? 0) * fps)}
                style={{position: 'absolute', width: wPx, left: o.x * edl.w - wPx / 2, top: o.y * edl.h,
                  transform: 'translateY(-50%)', opacity: o.opacity}}
              />
            </AbsoluteFill>
          </Sequence>
        );
      })}
      {props.lowerThird ? <LowerThird words={words} /> : null}
      {props.bug ? (
        <Sequence from={0} durationInFrames={Math.max(1, Math.round((edl.endcard ? edl.endcard.rec_in : edl.dur) * fps))} layout="none">
          <Bug text={props.bug} />
        </Sequence>
      ) : null}
      {callouts.map((c) => (
        <Sequence key={c.id} from={Math.round(c.rec_in * fps)} durationInFrames={Math.max(1, Math.round((c.rec_out - c.rec_in) * fps))}>
          <CalloutArrow callout={c} />
        </Sequence>
      ))}
      {(edl.titles ?? []).map((t, i) => (
        <Sequence key={`t${i}`} from={Math.round(t.rec_in * fps)} durationInFrames={Math.max(1, Math.round((t.rec_out - t.rec_in) * fps))}>
          <TitleCard text={t.text} />
        </Sequence>
      ))}
      {edl.endcard ? (
        <Sequence from={Math.round(edl.endcard.rec_in * fps)} durationInFrames={Math.max(1, Math.round((edl.endcard.rec_out - edl.endcard.rec_in) * fps))}>
          <EndCard title={edl.endcard.title} tagline={edl.endcard.tagline} url={edl.endcard.url} />
        </Sequence>
      ) : null}
    </AbsoluteFill>
  );
};

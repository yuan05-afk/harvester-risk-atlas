// Real footage of the app on a floating plane. The camera is a framing rectangle in SOURCE pixels (1920x1080 capture)
// keyframed over time; the plane itself can slide, tilt and scale in the haze. Fast moves get a directional smear
// (an SVG horizontal/vertical blur sized by velocity): the film's one blur grammar.
import React from 'react';
import { Img, OffthreadVideo, Sequence, staticFile } from 'remotion';
import { FPS } from '../timing';
import { keys, velocity } from '../lib/motion';
import type { Ease } from '../lib/motion';
import { FLOAT_SHADOW } from '../lib/theme';

export type Rect = { x: number; y: number; w: number };
type K = Array<[number, number, Ease?]>;

/** Splits rect keyframes [[t, rect, ease]] into per-component tracks. */
export function rectTracks(k: Array<[number, Rect, Ease?]>) {
  return {
    x: k.map(([t, r, e]) => [t, r.x, e]) as K,
    y: k.map(([t, r, e]) => [t, r.y, e]) as K,
    w: k.map(([t, r, e]) => [t, r.w, e]) as K,
  };
}

export const Screen: React.FC<{
  t: number;
  src: string;
  /** Show this still (public/stills/<name>.png) instead of the video. */
  still?: string;
  /** Film second at which the clip's first used frame plays. */
  at: number;
  /** Seconds into the source clip to start from. */
  from: number;
  /** Seconds of film time the clip is shown. */
  dur: number;
  rate?: number;
  /** Camera framing over film time. */
  cam: Array<[number, Rect, Ease?]>;
  /** Plane geometry over film time (centre x/y in px, width px, rotateY deg). */
  px: K;
  py: K;
  pw: K;
  rot?: K;
  aspect?: number;
  radius?: number;
  opacity?: number;
  /** Drawn over the footage in SOURCE pixels (multiply by s), so callouts stay pinned to the UI as the camera moves. */
  overlay?: (s: number) => React.ReactNode;
  /** Folder under public/ holding the clip (version 2 uses footage2). */
  folder?: string;
}> = ({ t, src, still, at, from, dur, rate = 1, cam, px, py, pw, rot = [[0, 0]], aspect = 16 / 9, radius = 22, opacity = 1, overlay, folder = 'footage' }) => {
  const tr = rectTracks(cam);
  const W = keys(t, pw);
  const H = W / aspect;
  const cx = keys(t, px);
  const cy = keys(t, py);
  const rx = keys(t, tr.x);
  const ry = keys(t, tr.y);
  const rw = keys(t, tr.w);
  const s = W / rw;
  // Smear from plane motion plus camera pan, in screen pixels per frame.
  const vx = (velocity(t, px) + velocity(t, tr.x) * s) / FPS;
  const vy = (velocity(t, py) + velocity(t, tr.y) * s) / FPS;
  // A dead zone keeps slow pans and settles sharp; only whips smear.
  const bx = Math.min(40, Math.max(0, Math.abs(vx) - 8) * 0.55);
  const by = Math.min(40, Math.max(0, Math.abs(vy) - 8) * 0.55);
  const id = `smear-${(still ?? src).replace(/\W/g, '')}-${Math.round(at * 100)}`;
  return (
    <div
      style={{
        position: 'absolute',
        left: cx - W / 2,
        top: cy - H / 2,
        width: W,
        height: H,
        borderRadius: radius,
        overflow: 'hidden',
        boxShadow: FLOAT_SHADOW,
        background: '#fff',
        opacity,
        transform: `perspective(2400px) rotateY(${keys(t, rot)}deg)`,
        filter: bx > 0.4 || by > 0.4 ? `url(#${id})` : undefined,
      }}
    >
      <svg width="0" height="0" style={{ position: 'absolute' }}>
        <filter id={id} x="-10%" y="-10%" width="120%" height="120%">
          <feGaussianBlur stdDeviation={`${bx.toFixed(2)} ${by.toFixed(2)}`} />
        </filter>
      </svg>
      <div style={{ position: 'absolute', left: -rx * s, top: -ry * s, width: 1920 * s, height: 1080 * s }}>
        {still ? (
          <Img src={staticFile(`stills/${still}.png`)} style={{ width: '100%', height: '100%' }} />
        ) : (
        <Sequence from={Math.round(at * FPS)} durationInFrames={Math.round(dur * FPS)} layout="none">
          <OffthreadVideo
            src={staticFile(`${folder}/${src}.mp4`)}
            startFrom={Math.round(from * FPS)}
            playbackRate={rate}
            muted
            style={{ width: '100%', height: '100%' }}
          />
        </Sequence>
        )}
        {overlay?.(s)}
      </div>
    </div>
  );
};

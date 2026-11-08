// Motion primitives. Every value is a pure function of time (seconds), so any frame renders identically.
// Grammar (motionmaxxing craft laws): landings decelerate (most travel in the first few frames, long tail, no bounce),
// exits accelerate, median move ~0.33 s, one spring at most, almost nothing fades between scenes.

export type Ease = (x: number) => number;

const clamp01 = (x: number) => Math.min(1, Math.max(0, x));

/** Landing: most of the travel up front, then a long settle. */
export const land: Ease = (x) => (x >= 1 ? 1 : 1 - Math.pow(2, -10 * x));
/** Softer landing for large objects and the camera. */
export const settle: Ease = (x) => 1 - Math.pow(1 - x, 4);
/** Leaving: starts slow, accelerates out. */
export const leave: Ease = (x) => x * x * x;
/** Camera moves between two framings. */
export const glide: Ease = (x) => (x < 0.5 ? 8 * x * x * x * x : 1 - Math.pow(-2 * x + 2, 4) / 2);
export const linear: Ease = (x) => x;

/** Value of a tween over [t0, t1] at time t, held at the ends. */
export function tween(t: number, t0: number, t1: number, from: number, to: number, ease: Ease = land) {
  const p = clamp01((t - t0) / Math.max(1e-6, t1 - t0));
  return from + (to - from) * ease(p);
}

/** 0..1 progress over [t0, t1]. */
export const progress = (t: number, t0: number, t1: number, ease: Ease = linear) => ease(clamp01((t - t0) / Math.max(1e-6, t1 - t0)));

/** Piecewise keyframes: [[time, value, easeIntoThisKey?], ...]. */
export function keys(t: number, k: Array<[number, number, Ease?]>) {
  if (t <= k[0][0]) return k[0][1];
  for (let i = 1; i < k.length; i++) {
    if (t <= k[i][0]) return tween(t, k[i - 1][0], k[i][0], k[i - 1][1], k[i][1], k[i][2] ?? glide);
  }
  return k[k.length - 1][1];
}

/** Velocity (units per second) of a keyframe track at t, for directional motion blur. */
export function velocity(t: number, k: Array<[number, number, Ease?]>, dt = 1 / 120) {
  return (keys(t + dt, k) - keys(t - dt, k)) / (2 * dt);
}

/** Deterministic 0..1 noise (for drift, never Math.random). */
export function noise(seed: number) {
  const s = Math.sin(seed * 12.9898) * 43758.5453;
  return s - Math.floor(s);
}

/** Slow hand-held drift so no held frame is dead. */
export function drift(t: number, amp: number, seed = 1) {
  return {
    x: amp * Math.sin(t * 0.37 + seed) + amp * 0.4 * Math.sin(t * 0.91 + seed * 2.1),
    y: amp * 0.6 * Math.cos(t * 0.29 + seed * 1.3) + amp * 0.3 * Math.sin(t * 0.73 + seed),
  };
}

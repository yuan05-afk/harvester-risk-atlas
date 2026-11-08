// Kinetic type: whole words arrive out of blur at speech rhythm (each lands 0-2 frames before it is heard), leave by
// accelerating up and out of focus. One italic serif accent (Fraunces) and at most one sappan word per line.
import React from 'react';
import { C, SANS, SERIF } from '../lib/theme';
import { land, leave, progress } from '../lib/motion';

export type Word = { w: string; at: number; serif?: boolean; blue?: boolean; c?: string };

export const Words: React.FC<{
  t: number;
  words: Word[];
  x: number;
  y: number;
  size: number;
  exit?: number;
  align?: 'center' | 'left';
  color?: string;
  weight?: number;
  maxWidth?: number;
}> = ({ t, words, x, y, size, exit, align = 'center', color = C.ink, weight = 600, maxWidth = 1500 }) => {
  if (t < words[0].at - 0.2) return null;
  if (exit !== undefined && t > exit + 0.6) return null;
  return (
    <div
      style={{
        position: 'absolute',
        left: align === 'center' ? x - maxWidth / 2 : x,
        top: y,
        width: maxWidth,
        textAlign: align,
        fontFamily: SANS,
        fontWeight: weight,
        fontSize: size,
        lineHeight: 1.12,
        letterSpacing: -size * 0.025,
        color,
        transform: 'translateY(-50%)',
      }}
    >
      {words.map((wd, i) => {
        const pin = progress(t, wd.at - 0.03, wd.at + 0.42, land);
        const pout = exit !== undefined ? progress(t, exit + i * 0.02, exit + 0.32 + i * 0.02, leave) : 0;
        const blur = (1 - pin) * 16 + pout * 12;
        const opacity = pin * (1 - pout);
        const dy = (1 - pin) * size * 0.32 - pout * size * 0.3;
        const scale = 1 + (1 - pin) * 0.12;
        return (
          <span
            key={i}
            style={{
              display: 'inline-block',
              marginRight: size * 0.24,
              opacity,
              filter: blur > 0.05 ? `blur(${blur.toFixed(2)}px)` : undefined,
              transform: `translateY(${dy.toFixed(2)}px) scale(${scale.toFixed(4)})`,
              fontFamily: wd.serif ? SERIF : SANS,
              fontStyle: wd.serif ? 'italic' : 'normal',
              fontWeight: wd.serif ? 400 : weight,
              fontSize: wd.serif ? size * 1.12 : size,
              letterSpacing: wd.serif ? -size * 0.01 : undefined,
              color: wd.c ?? (wd.blue ? C.accent : color),
            }}
          >
            {wd.w}
          </span>
        );
      })}
    </div>
  );
};

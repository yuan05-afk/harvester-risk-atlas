// The ground: a cool grey-green field-atlas haze (mangrove and sappan light, a whisper of turmeric) with fine paper
// grain, drifting slowly so a held frame is never dead. `dark` (0..1) pulls it into the night of the opening.
import React from 'react';
import { AbsoluteFill } from 'remotion';
import { C } from '../lib/theme';

export const Haze: React.FC<{ t: number; dark?: number }> = ({ t, dark = 0 }) => {
  const a = Math.sin(t * 0.11) * 6;
  const b = Math.cos(t * 0.07) * 5;
  return (
    <AbsoluteFill style={{ background: C.haze1, overflow: 'hidden' }}>
      <AbsoluteFill
        style={{
          background: `radial-gradient(60% 70% at ${20 + a}% ${16 + b}%, #FFFFFF 0%, rgba(255,255,255,0) 62%),
            radial-gradient(55% 60% at ${84 - a}% ${26 + b}%, ${C.haze3} 0%, rgba(241,225,232,0) 70%),
            radial-gradient(70% 80% at ${58 + b}% ${98 - a}%, ${C.haze2} 0%, rgba(221,233,225,0) 70%),
            radial-gradient(28% 30% at ${12 - b}% ${86 + a * 0.5}%, ${C.haze4} 0%, rgba(244,234,208,0) 70%),
            linear-gradient(160deg, #F6F8F6 0%, #E9EEEA 100%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: dark,
          background: `radial-gradient(70% 60% at ${50 + a}% 112%, rgba(124,26,75,0.42) 0%, rgba(124,26,75,0) 62%),
            radial-gradient(50% 50% at ${18 - b}% ${8 + a}%, rgba(46,95,62,0.30) 0%, rgba(46,95,62,0) 65%),
            radial-gradient(60% 60% at 50% 40%, #1A2024 0%, ${C.night} 100%)`,
        }}
      />
      <AbsoluteFill
        style={{
          opacity: 0.2 - dark * 0.08,
          mixBlendMode: dark > 0.5 ? 'screen' : 'multiply',
          backgroundImage: `url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='240' height='240'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0.40  0 0 0 0 0.46  0 0 0 0 0.42  0 0 0 0.55 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>")`,
          backgroundPosition: `${(t * 7) % 240}px ${(t * 3) % 240}px`,
        }}
      />
    </AbsoluteFill>
  );
};

// The YouTube thumbnail (1280x720), in the film's grammar: the flat ground, the question in large ink type and
// tongkat ali's photo. It must still read at 320 px wide.
//   npx remotion still src/index.ts Thumb out/youtube-thumbnail.png
import React from 'react';
import { AbsoluteFill, Img, staticFile } from 'remotion';
import '@fontsource-variable/atkinson-hyperlegible-next';
import '@fontsource-variable/fraunces';
import { C, SANS, SERIF } from './lib/theme';
import { PAPER } from './kit';

export const Thumb: React.FC = () => (
  <AbsoluteFill style={{ background: PAPER, fontFamily: SANS }}>
    <div style={{ position: 'absolute', left: 64, top: 64, width: 700 }}>
      <div style={{ fontSize: 26, fontWeight: 700, letterSpacing: 2, color: C.tertiary }}>HARVESTER RISK ATLAS · PHILIPPINES</div>
      <div style={{ marginTop: 26, fontFamily: SERIF, fontWeight: 650, fontSize: 104, lineHeight: 0.98, letterSpacing: -3, color: C.ink }}>
        Which wild medicinal plants need help <span style={{ color: C.accent }}>first?</span>
      </div>
      <div style={{ marginTop: 34, display: 'flex', gap: 14 }}>
        {['29 plants ranked', '2,000 runs', '12 months'].map((w) => (
          <span key={w} style={{ fontSize: 26, fontWeight: 700, color: C.ink, background: '#FCFCFD', border: '1px solid #D8DCE1', borderRadius: 4, padding: '8px 14px' }}>
            {w}
          </span>
        ))}
      </div>
    </div>
    <div style={{ position: 'absolute', right: 56, top: 56, width: 400, height: 608, borderRadius: 4, overflow: 'hidden', boxShadow: '0 2px 3px rgba(21,24,28,0.08), 0 16px 30px rgba(21,24,28,0.14)' }}>
      <Img src={staticFile('photos/eurycoma-longifolia.jpg')} style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
      <div style={{ position: 'absolute', left: 18, bottom: 18, background: '#FCFCFD', borderRadius: 4, padding: '10px 14px', fontFamily: SANS }}>
        <div style={{ fontFamily: SERIF, fontWeight: 650, fontSize: 34, color: C.ink, lineHeight: 1 }}>Tongkat ali</div>
        <div style={{ fontSize: 20, fontWeight: 700, color: C.accent, marginTop: 4 }}>Endangered · 5 records</div>
      </div>
    </div>
    <div style={{ position: 'absolute', left: 64, bottom: 40, fontSize: 22, fontWeight: 600, color: C.tertiary }}>EthnoHack 2026 · Track 3: Biodiversity & Sustainability</div>
  </AbsoluteFill>
);

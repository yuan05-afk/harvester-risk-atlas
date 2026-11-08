"""Vocal chain for the cloned narration: it arrives dull and boxy (most energy at 300-1000 Hz, little above 6 kHz).

    python tools/voice_chain.py public/audio/vo-take1.mp3 audio/vo-clean.wav

No time-stretch (stretching smeared the voice). Steps: rumble cut, warmth, de-box, presence, air shelf, a harmonic
exciter for the missing top end, de-esser, gentle compression, a light final limiter. Prints the band balance before
and after so the change is measured, not guessed."""
import subprocess
import sys

import numpy as np

src, out = sys.argv[1], sys.argv[2]
CHAIN = ','.join([
    'highpass=f=75:poles=2',
    'equalizer=f=170:t=q:w=1.0:g=0.5',      # a little chest
    'equalizer=f=420:t=q:w=1.1:g=-4.0',     # boxiness
    'equalizer=f=850:t=q:w=1.4:g=-1.5',     # honk
    'equalizer=f=3000:t=q:w=1.1:g=3.5',     # presence: consonants, intelligibility
    'highshelf=f=7000:g=3.5',               # air
    'aexciter=amount=1.1:drive=4.5:blend=0:freq=5000:ceil=15000',
    'deesser=i=0.45:m=0.5:f=0.5',
    'acompressor=threshold=-24dB:ratio=2.6:attack=6:release=140:knee=6:makeup=2.5',
    'alimiter=limit=0.89:attack=4:release=60',
])
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', src, '-af', CHAIN, '-ar', '48000', '-ac', '1', out], check=True)


def bands(path):
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-ac', '1', '-ar', '44100', '-f', 'f32le', '-'], capture_output=True, check=True).stdout
    y = np.frombuffer(raw, np.float32)
    n = 1 << 15
    acc = None
    for k in range(10):  # average ten windows across the take
        seg = y[44100 * (8 + k * 15): 44100 * (8 + k * 15) + n]
        if len(seg) < n:
            break
        s = np.abs(np.fft.rfft(seg * np.hanning(n))) ** 2
        acc = s if acc is None else acc + s
    f = np.fft.rfftfreq(n, 1 / 44100)
    tot = acc.sum()
    return [10 * np.log10(acc[(f >= a) & (f < b)].sum() / tot + 1e-12) for a, b in BANDS]


BANDS = [(100, 300), (300, 1000), (1000, 3000), (3000, 6000), (6000, 10000), (10000, 16000)]
for (a, b), x, y in zip(BANDS, bands(src), bands(out)):
    print(f'{a:>5}-{b:<5} Hz  before {x:6.1f} dB  after {y:6.1f} dB')

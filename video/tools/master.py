"""Builds the narration master from the one ElevenLabs take, cleaned by tools/voice_chain.py (audio/vo-clean.wav).

    python tools/master.py

1. No time-stretch: the voice keeps its own pace (stretching smeared it).
2. At each beat boundary (the silence after a named word) inserts a short designed pause for the picture.
3. Normalises to -16 LUFS with a -1.5 dBTP limiter, then adds a room-tone floor.
The film's length follows from the voice: lead + speech + pauses + end hold.
Writes public/audio/vo-master.wav and src/timeline.generated.json (every word's start/end in film seconds and the
boundary times). Cuts only ever land inside measured silences."""
import json
import subprocess

import numpy as np

TEMPO = 1.0
LEAD = 0.8  # picture before the first word
END_HOLD = 3.0
SR = 48000

# (word that ends the beat, occurrence of that word, extra seconds of picture after it)
BEATS = [
    ('left.', 1, 0.6),         # the hook lands
    ('start?', 1, 0.6),        # the question hangs
    ('it.', 1, 0.8),           # five records on the map
    ('are.', 1, 0.8),          # the app
    ('number.', 1, 0.5),       # the range
    ('find.', 1, 1.6),         # atlas: the map flies to its hexagons
    ('fifth.', 1, 1.2),        # profile
    ('brief.', 1, 1.2),        # field brief
    ('updates.', 1, 1.4),      # the slider re-ranks
    ('looking.', 1, 1.4),      # the year plays on the Seasons page
    ('next.', 1, 1.2),         # the cross-check on the page
    ('searched.', 1, 0.4),     # the searched cells
    ('searched.', 2, 0.8),     # two thirds under-searched
    ('moves.', 1, 0.6),        # results
    ('field.', 1, 0.6),        # limits
]

words = json.load(open('audio/vo3-brian.words.json', encoding='utf-8'))
sil = json.load(open('audio/vo3-brian.silences.json', encoding='utf-8'))

raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', 'audio/vo-clean.wav', '-ac', '1', '-ar', str(SR), '-f', 'f32le', '-'],
                     capture_output=True, check=True).stdout
y = np.frombuffer(raw, np.float32).copy()
k = 1 / TEMPO
for w in words:
    w['start'] *= k
    w['end'] *= k
for s in sil:
    s['start'] *= k
    s['end'] *= k


def find_word(token, n):
    hits = [i for i, w in enumerate(words) if w['word'].lower() == token.lower()]
    if len(hits) < n:
        raise SystemExit(f'no occurrence {n} of {token!r}: {len(hits)} found')
    return hits[n - 1]


def silence_after(t):
    """The measured silence that starts closest to t (ASR word ends can run into the pause)."""
    best = min(sil, key=lambda s: abs(s['start'] - t) if s['end'] > t - 0.05 else 1e9)
    if abs(best['start'] - t) > 0.6:
        # The voice runs straight on: cut at the end of the word itself (a gap between words, not mid-word).
        sil.append({'start': t, 'end': t + 0.04})
        return sil[-1]
    return best


# Designed inserts at beat boundaries.
inserts = {}  # silence index -> extra seconds
beat_words = []
for token, n, extra in BEATS:
    i = find_word(token, n)
    s = silence_after(words[i]['end'])
    inserts[sil.index(s)] = inserts.get(sil.index(s), 0) + extra
    beat_words.append((token, n, i))

# The take ends with ~0.3 s of its own tail; the end hold is counted from the last sample.
speech = len(y) / SR
FILM = round(LEAD + speech + sum(inserts.values()) + END_HOLD, 3)
print(f'speech {speech:.2f}s, beat inserts {sum(inserts.values()):.2f}s, end hold {END_HOLD}s -> film {FILM:.2f}s')

# Assemble: cut each chosen silence at its midpoint and insert zeros there.
cuts = sorted((((sil[j]['start'] + sil[j]['end']) / 2), v) for j, v in inserts.items())
parts, shift_at, pos = [np.zeros(int(LEAD * SR), np.float32)], [], 0
shift = LEAD
for t, extra in cuts:
    c = int(t * SR)
    parts.append(y[pos:c])
    parts.append(np.zeros(int(round(extra * SR)), np.float32))
    shift_at.append((t, extra))
    pos = c
parts.append(y[pos:])
out = np.concatenate(parts)
target = int(FILM * SR)
out = np.concatenate([out, np.zeros(max(0, target - len(out)), np.float32)])[:target]


def film_time(t):
    return LEAD + t + sum(e for c, e in shift_at if c <= t)


for w in words:
    w['start'] = round(film_time(w['start']), 3)
    w['end'] = round(film_time(w['end']), 3)

tmp = 'audio/vo-master.raw.wav'
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-f', 'f32le', '-ar', str(SR), '-ac', '1', '-i', '-', tmp], input=out.tobytes(), check=True)
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', tmp, '-af', 'loudnorm=I=-16:TP=-1.5:LRA=11,alimiter=limit=0.84',
                '-ar', str(SR), '-ac', '2', '-t', str(FILM), 'public/audio/vo-master.wav'], check=True)

boundaries = {f'{tok}#{n}': words[i]['end'] for tok, n, i in beat_words}
json.dump({'film': FILM, 'lead': LEAD, 'tempo': TEMPO, 'words': words, 'beats': boundaries},
          open('src/timeline.generated.json', 'w', encoding='utf-8'), indent=1)
print('last word ends', words[-1]['end'], '; master', FILM, 's')
for k_, v in boundaries.items():
    print(f'  {k_:12s} {v:7.2f}')

# Room tone: a pink-noise floor about -77 dB in the pauses, so the gaps breathe instead of dropping to digital zero.
subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', 'public/audio/vo-master.wav', '-f', 'lavfi', '-i',
                'anoisesrc=color=pink:amplitude=0.0016:seed=7:sample_rate=48000,lowpass=f=5000,highpass=f=80,aformat=channel_layouts=stereo',
                '-filter_complex', '[0:a][1:a]amix=inputs=2:duration=first:normalize=0', '-t', str(FILM), '-ar', str(SR),
                'public/audio/vo-master-rt.wav'], check=True)
print('wrote public/audio/vo-master-rt.wav (the film plays this)')

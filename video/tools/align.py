"""Word timestamps for the narration (faster-whisper), plus measured silences from the waveform.

    python tools/align.py public/audio/vo-take1.mp3 audio/vo-take1

Writes <out>.words.json ([{word, start, end}]) and <out>.silences.json ([{start, end}], gaps >= 0.25 s below -40 dB).
Cuts and inserted pauses use the silences, never the ASR word edges."""
import json
import subprocess
import sys

import numpy as np
from faster_whisper import WhisperModel

src, out = sys.argv[1], sys.argv[2]
pcm = subprocess.run(['ffmpeg', '-v', 'error', '-i', src, '-ac', '1', '-ar', '16000', '-f', 's16le', '-'], capture_output=True, check=True).stdout
audio = np.frombuffer(pcm, np.int16).astype(np.float32) / 32768

model = WhisperModel('small.en', device='cpu', compute_type='int8')
segments, _ = model.transcribe(audio, word_timestamps=True, beam_size=5, vad_filter=False)
words = [{'word': w.word.strip(), 'start': round(w.start, 3), 'end': round(w.end, 3)} for s in segments for w in s.words]
json.dump(words, open(out + '.words.json', 'w', encoding='utf-8'), indent=0)

# Silences: 20 ms RMS frames below -40 dBFS, merged into runs of at least 0.25 s.
hop = 320
rms = np.sqrt(np.convolve(audio ** 2, np.ones(hop) / hop, mode='same')[::hop] + 1e-12)
quiet = 20 * np.log10(rms) < -40
sil, start = [], None
for i, q in enumerate(quiet):
    if q and start is None:
        start = i
    if (not q or i == len(quiet) - 1) and start is not None:
        if (i - start) * hop / 16000 >= 0.25:
            sil.append({'start': round(start * hop / 16000, 3), 'end': round(i * hop / 16000, 3)})
        start = None
json.dump(sil, open(out + '.silences.json', 'w', encoding='utf-8'), indent=0)
print(len(words), 'words;', len(sil), 'silences; total', round(len(audio) / 16000, 2), 's')
print(' '.join(w['word'] for w in words))

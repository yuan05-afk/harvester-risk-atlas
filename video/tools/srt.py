"""YouTube subtitles: the script's exact words (audio tags removed), timed by the master's word timestamps.
Usage: python tools/srt.py vo.txt src/words.json 0 out/harvester-risk-atlas-pitch.en.srt"""
import json
import re
import sys

script_path, words_path, lead, out = sys.argv[1], sys.argv[2], float(sys.argv[3]), sys.argv[4]
script = re.sub(r'\[[^\]]*\]', ' ', open(script_path, encoding='utf-8').read()).replace('...', '…').split()
heard = json.load(open(words_path, encoding='utf-8'))
norm = lambda w: re.sub(r'[^a-z0-9]', '', w.lower())

# Align script words to heard words in order; a script word with no match takes its neighbour's time.
times, j = [], 0
for w in script:
    k = next((k for k in range(j, min(j + 4, len(heard))) if norm(heard[k]['word']) == norm(w) or (norm(w)[:4] and norm(heard[k]['word'])[:4] == norm(w)[:4])), None)
    if k is None:
        times.append(None)
        continue
    times.append((heard[k]['start'], heard[k]['end']))
    j = k + 1
for i, t in enumerate(times):
    if t is None:
        prev = next((times[p] for p in range(i - 1, -1, -1) if times[p]), (0, 0))
        times[i] = (prev[1], prev[1] + 0.3)

# Cues: break after sentence ends, after commas once long enough, or at 84 characters; two lines of up to 42.
cues, cur = [], []
for i, w in enumerate(script):
    cur.append(i)
    text = ' '.join(script[k] for k in cur)
    nxt = script[i + 1] if i + 1 < len(script) else ''
    if not nxt or w.endswith(('.', '?')) or (w.endswith(':') and len(text) > 20) or (w.endswith(',') and len(text) > 40) or len(text + ' ' + nxt) > 84:
        cues.append(cur)
        cur = []


def wrap(text, width=42):
    if len(text) <= width:
        return text
    cut = text.rfind(' ', 0, len(text) // 2 + 8)
    return text[:cut] + '\n' + text[cut + 1:]


def ts(s):
    ms = int(round(s * 1000))
    return f'{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}'


with open(out, 'w', encoding='utf-8') as f:
    for n, cue in enumerate(cues, 1):
        start = times[cue[0]][0] + lead
        end = times[cue[-1]][1] + lead + 0.25
        if n < len(cues):
            end = min(end, times[cues[n][0]][0] + lead - 0.02)
        f.write(f"{n}\n{ts(start)} --> {ts(end)}\n{wrap(' '.join(script[k] for k in cue))}\n\n")
print(len(cues), 'cues')

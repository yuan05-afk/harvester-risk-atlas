"""Checks every cue('word', n) in src/Film.tsx against the master's transcript, before a render fails on one."""
import json
import re

W = json.load(open('src/words.json', encoding='utf-8'))
norm = lambda s: re.sub(r'[^a-z0-9]', '', s.lower())
src = open('src/Film.tsx', encoding='utf-8').read()
bad = 0
for m in re.finditer(r"cue\(['\"](.+?)['\"](?:,\s*(\d+))?\)", src):
    w, n = m.group(1).replace("\\'", "'"), int(m.group(2) or 1)
    hits = [x['start'] for x in W if norm(x['word']) == norm(w)]
    if len(hits) < n:
        bad += 1
        print('MISSING', repr(w), n, 'found', len(hits))
        continue
    i = [k for k, x in enumerate(W) if norm(x['word']) == norm(w)][n - 1]
    ctx = ' '.join(x['word'] for x in W[max(0, i - 3): i + 3])
    print(f"{hits[n - 1]:7.2f}  {w!r:14} #{n}  ...{ctx}...")
print('cues ok' if not bad else f'{bad} missing')

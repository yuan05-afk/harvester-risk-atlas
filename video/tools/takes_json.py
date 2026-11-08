"""Merges the latest capture reports (capture60/_report-*.json) into src/takes.json: frames, click frames, marks and the
boxes of marked elements (viewport px), which the film uses to place its drawn ink marks.

    python tools/takes_json.py
"""
import glob
import json
import os

takes = json.load(open('src/takes.json', encoding='utf-8'))
for f in sorted(glob.glob('capture60/_report-*.json'), key=os.path.getmtime):
    for name, r in json.load(open(f, encoding='utf-8')).items():
        t = {'frames': r['frames'], 'clicks': [], 'marks': {}, 'boxes': {}}
        for m in r['marks']:
            if 'click' in m:
                t['clicks'].append(m['f'])
            else:
                t['marks'][m['mark']] = m['f']
                if 'box' in m:
                    t['boxes'][m['mark']] = m['box']
        takes[name] = t
json.dump(takes, open('src/takes.json', 'w', encoding='utf-8'), indent=1)
for k, v in takes.items():
    print(f"{k:9s} {v['frames'] / 60:6.2f}s clicks {[round(c / 60, 2) for c in v['clicks']]} marks {v['marks']}")

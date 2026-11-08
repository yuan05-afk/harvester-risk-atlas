# Harvester Risk Atlas pitch film: note

`out/harvester-risk-atlas-pitch.mp4`: 1920×1080, 30 fps, H.264 yuv420p + AAC, **4:00.000** (7,200 frames). Remotion composition `Film` (`src/Film.tsx`). Captions for YouTube: `harvester-risk-atlas-pitch.en.srt`. Upload copy: [`YOUTUBE.md`](YOUTUBE.md).

## The idea

A judge should leave able to say: *wild medicinal plants are disappearing and nobody counts the harvest; this free map ranks which ones need help first, shows why in plain words, and is honest about how sure it is.*

The film follows AIDA and also EthnoHack's Problem → Data → Method → Prototype → Results → Impact. It is one continuous take. Nothing cuts to a new slide; each beat grows out of the one before, an idea taken from OneTake and built in our own code:

| Time | Beat | What it buys | Carried into the next beat |
|---|---|---|---|
| 0:00 | **Attention**: hook, at night | the viewer feels the scale: 4 billion people, plants taken from the wild | "counting" → the night lifts into the first counter |
| 0:18 | The problem in numbers | 30,000 species; only 7 of every 100 checked; 175 ha of tree cover lost a day; 1,186 listed; harvest **not measured** | the question "where do you even start?" |
| 0:49 | Tongkat ali | one real plant: roots dug, Endangered, **5** reliable records (five hexagons drop) | the five hexagons rise to the centre … |
| 1:04 | **Interest**: the answer | … and become the app's own opening animation; the name lands | the overview stays as the plane leaves |
| 1:19 | How it works | three plain questions, six sources, 9,660 → 4,789 records, rarity only where botanists searched, 2,000 re-runs → **a range, not one number** | the range resolves into the demo |
| 1:56 | **Desire**: the live app | overview → atlas → plant → field brief → weights → all plants, with a page rail on top | "so what did we find?" |
| 2:49 | What we found | the five plants, their rank ranges; two already DENR-listed | the checks page |
| 3:07 | Can you trust it? | real checks: "change the math, the order barely moves"; ±5 places | honest limits |
| 3:20 | Limits and next | not medical advice or a permit; harvest data from books awaits expert eyes; next: Filipino ethnobotanists | the name |
| 3:45 | **Action** | name, question, link, "help us protect the plants that heal us"; slow push to the end | — |

## Real versus designed

**Real**
- Every app shot is live footage of the production build (`web/` at commit `a999f3c`, served locally because the public URL was briefly unreachable from this machine). It was recorded in real time by `tools/capture.mjs`: headless Chrome at 2× pixel density (3840×2160), with a drawn cursor because headless frames have none. The clicks are real: a plant row, the Field brief link and the Harvest harm slider. The tooltips and the re-ranking are the app's own.
- All numbers on screen come from the project's data or a cited source:
  - **The atlas's own data:** 29 of 51 plants, 9,660 → 4,789 records, 332 of 1,267 well-searched cells, 2,000 draws, ranks and ranges from `web/public/data/species.json`, ρ values from `validation.json`.
  - **Computed from files in the repo:** 1,186 threatened plants (from `data/raw/denr`) and 175 ha a day (from `data/raw/gfw`).
  - **Cited in the narration and on YouTube:** 30,000 species, 60–90% wild-harvested, 7% assessed, 1 in 5 threatened (IUCN/TRAFFIC 2018), and 4 billion people (Kew 2020).
- The plant photos are iNaturalist images already used and credited in the app.

**Designed (illustrations, not data)**
- **The opening and the counters:** the night ground, the counters, the 100-square grid, and the three-row "where it grows / how threatened / how much is harvested" ledger.
- **Method diagrams:** the hexagon field for "roadsides vs deep forest". It illustrates the idea; it is not the real effort map. The rank strip for "2,000 re-runs" draws illustrative jitter, but its resolved range (1st–5th, median 2nd) is tongkat ali's real interval.
- **Overlays:** the page rail, the label pills and the end card.

## Voice

- **The take:** one take of the team's own cloned voice ("Yato"), ElevenLabs `eleven_v4`, 3,169 credits, script `vo.txt`. No other takes were generated.
- **The master** (`tools/master.py`):
  - The take is slowed to 90% with rubberband, keeping pitch and formants.
  - Designed pauses are added at 13 beat boundaries, and the remainder is spread evenly over 41 natural pauses, giving exactly 240.000 s.
  - It is normalised to −16 LUFS, and a pink-noise room tone at about −77 dB keeps the gaps from dropping to digital zero.
  - Every cut sits inside a measured silence.
- **Verified:** the master was re-transcribed (`tools/align.py`, faster-whisper `small.en`) and matches the script word for word, apart from the recogniser's spelling of names ("Tonkat Ali", "Kalinag"). Picture cues use the master's own word times (`src/words.json`). One recogniser error was found and handled: it placed "One" 2.9 s early on the take, while the master shows the pause is correctly before "One click".
- **No music**, as the team asked.

## Checks on the delivered file

Run on the final render (filled in below from the actual output).

## Rebuild

```bash
npm ci
python tools/align.py public/audio/vo-take1.mp3 audio/vo-take1     # take: words + silences
python tools/master.py                                               # master + room tone (exactly 240 s)
python tools/align.py public/audio/vo-master.wav audio/vo-master && cp audio/vo-master.words.json src/words.json
# footage: serve web/dist (cd ../web && npm run build && npx vite preview --port 4173), then
BASE_URL=http://localhost:4173 node tools/capture.mjs intro overview atlas profile brief weights plants checks
node tools/concat-lists.mjs   # then encode each capture/_<clip>.txt to public/footage/<clip>.mp4 (see the ffmpeg line in this note's history)
python tools/check_cues.py
npx remotion render src/index.ts Film out/harvester-risk-atlas-pitch.mp4 --codec=h264 --crf=16 --pixel-format=yuv420p
python tools/srt.py vo.txt src/words.json 0 harvester-risk-atlas-pitch.en.srt
```

Encode command used per clip: `ffmpeg -f concat -safe 0 -i capture/_<clip>.txt -t <capture/<clip>/_end.txt seconds> -vf "fps=30,scale=3840:2160:flags=lanczos,format=yuv420p" -c:v libx264 -crf 17 public/footage/<clip>.mp4`.

Fonts: Atkinson Hyperlegible Next and Fraunces (SIL OFL), the app's own. OneTake (PolyForm Noncommercial) was **not** installed or copied; only its principle, that every beat is carried into the next, was applied in this project's own code.

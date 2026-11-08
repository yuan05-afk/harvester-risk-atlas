# Harvester Risk Atlas pitch film: note (version 4)

`out/harvester-risk-atlas-pitch-yt.mp4` is the upload: 1920×1080, **60 fps**, H.264 yuv420p (standard range) + AAC, **2:48** (167.6 s). It fits the organisers' 2–3 minute demo guideline. Remotion composition `Film` (`src/Film.tsx`, pieces in `src/kit.tsx`). Captions: `harvester-risk-atlas-pitch.en.srt` (54 cues, the script's exact words). Upload copy and chapters: [`YOUTUBE.md`](YOUTUBE.md). Earlier versions are kept by the team in `video versions/` and `demo pitch versions/`.

## What changed in version 4, and why

| Feedback on version 3 | Version 4 |
|---|---|
| Intro too dark; gradients look generated | One flat cool-grey ground (the app's `--paper`) from the first frame to the last. No gradients, no glow, no night opening. |
| Too much italic | Type is upright: Atkinson for words, Fraunces for numbers and names. Italic is kept only for Latin plant names, as botany requires. |
| "175 ha" | "175 hectares of tree cover lost, every day". |
| Tongkat ali to the app was not smooth | One map carries the opening: the Philippines' real outline appears with the problem, tongkat ali's five real cells drop onto it, and the map shrinks into the app's own map as the app rises from the same spot. |
| Cards with a coloured line on top | Gone. The three questions, the problem and the five plants are ruled ledgers on one white sheet, with a small ink square for each component. |
| The ×2,000 animation was messy and did not explain the runs | A histogram builds from tongkat ali's **real** ranks across the 2,000 runs (1st 900 times, 2nd 336, 3rd 385, 4th 227, 5th 134, 6th 11, 7th 3; `uncertainty.rank_summary` with the published seed), with a run counter, then a bracket: "Ranked 2nd, could be anywhere from 1st to 5th". |
| Pauses too long | Designed pauses 0.4–1.6 s, only where the picture needs time (a map flying, a page loading). |
| Focus on what matters | One drawn mark at a time: an ellipse around Play, an underline under the rank and under Co's Flora's row, and a plain caption under the footage. |
| New voice | ElevenLabs **Brian** (premade, "Deep, Resonant and Comforting") on **eleven_v4**, one generation only (2,380 credits on the team's new account). Light polish: high-pass, gentle de-ess and compression, limiter. |
| More innovation | New beat (1:26–1:50): the **Seasons** page plays makahiya's year month by month on the map, then the calendar of every plant with its hover label. |

## Real versus designed

**Real**
- **App footage:** the production build (`web/`), recorded frame by frame at 60 fps (`tools/vcap.mjs`, takes in `tools/takes.mjs`). Clicks are real: Tongkat Ali in the list, Full profile, Field brief, the Harvest harm slider, Seasons in the menu, Play the year.
- **Maps:** the Philippines' outline and H3 cells come from the app's own `web/public/data/geo` (`tools/geo.py`): survey effort per country-view cell (share of its areas with 100+ plant records), tongkat ali's five cells, and the islands Co's Digital Flora documents it on (Mindoro, Homonhon, Bucas Grande; dashed rings at the islands, not record points).
- **Numbers:** 175 hectares a day (Global Forest Watch), 5 reliable records, 332 of 1,267 well-searched areas, the 2,000-run histogram, 50 of 51 names in WFO, 66% (2,992 of 4,542 neighbouring areas), the five plants and their rank ranges, all from the pipeline's outputs.

**Designed (illustrations, not data)**
- the ring of six neighbours for "66%";
- captions, underlines and the closing card.

## Rebuild

```bash
npm ci
python tools/align.py public/audio/vo3-brian.mp3 audio/vo3-brian
ffmpeg -i public/audio/vo3-brian.mp3 -af "highpass=f=60:poles=2,deesser=i=0.2:m=0.5:f=0.5,acompressor=threshold=-24dB:ratio=1.8:attack=10:release=160:knee=6:makeup=1.2,alimiter=limit=0.89:attack=4:release=60" -ar 48000 -ac 1 audio/vo-clean.wav
python tools/master.py                                     # master + room tone; film length follows the voice
python tools/align.py public/audio/vo-master-rt.wav audio/vo-master && cp audio/vo-master.words.json src/words.json
../.venv/Scripts/python.exe tools/geo.py                   # map shapes (needs h3)
# footage: serve web/dist on :4173, then
node tools/vcap.mjs overview atlas profile brief weights seasons check
python tools/takes_json.py                                 # frames, clicks and element boxes -> src/takes.json
# encode each: ffmpeg -framerate 60 -i capture60/<take>/%05d.jpg -c:v libx264 -crf 16 -pix_fmt yuv420p public/footage/<take>.mp4
python tools/check_cues.py && npx tsc --noEmit
npx remotion render src/index.ts Film out/harvester-risk-atlas-pitch-v4.mp4 --codec=h264 --crf=17
python tools/srt.py vo3.txt src/words.json 0 harvester-risk-atlas-pitch.en.srt
```

Fonts: Atkinson Hyperlegible Next and Fraunces (SIL OFL), the app's own. No music.

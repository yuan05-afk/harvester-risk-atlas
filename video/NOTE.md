# Harvester Risk Atlas pitch film: note (version 3)

`out/harvester-risk-atlas-pitch-yt.mp4` is the upload: 1920×1080, **60 fps**, H.264 yuv420p (standard range) + AAC, **2:19.2** (8,352 frames), −14.8 LUFS. It fits the organisers' 2–3 minute demo guideline. Remotion composition `Film` (`src/Film.tsx`). Captions: `harvester-risk-atlas-pitch.en.srt` (46 cues, the script's exact words). Upload copy and chapters: [`YOUTUBE.md`](YOUTUBE.md). Version 1 (4:00, the team's own cloned voice) is kept by the team in `demo pitch versions/`.

## What changed in version 3, and why

| Feedback | Version 3 |
|---|---|
| Recordings not smooth, lag | Every app shot is recorded **frame by frame at a true 60 fps**: Chrome headless shell under begin-frame control with a virtual clock, advanced exactly 1/60 s per frame (`tools/vcap.mjs`). Animations, the map fly-to, scrolls and the re-ranking are captured at their real pace whatever the machine's speed. |
| Cursor looked like an AI | A person's hand (`tools/vcap.mjs`, `path()`): curved minimum-jerk moves with a small overshoot and settle, a faint tremor, a short pause before each press, the pointer hand over links, and wheel scrolling. Positions are dispatched to the page every frame, so hovers and clicks are the page's real responses. |
| Pauses too long | Designed pauses cut to 0.6–2.2 s at picture beats only, and no padding to a fixed length. |
| Transitions | The demo is one journey: each take starts on the frame after the previous take's click, so the real click is the cut (atlas → plant → field brief → weights). |
| Voice "like a broken mic" | New voice: ElevenLabs **Jennica**, a professional narrator, on `eleven_turbo_v2_5`. One take, 1,964 credits of the 2,022 left. No time-stretch, with a light polish: high-pass, de-box, presence, de-ess, gentle compression, limiter. |
| Real innovation, verified | New beat (1:18–1:53): names checked in **World Flora Online** (50 of 51 matched, all accepted); plants compared with **Co's Digital Flora of the Philippines**, with the real plant-page section on screen; **where to look next** (Mindoro, Homonhon, Bucas Grande for tongkat ali); **66%** of the land next to known records barely searched. |

## Real versus designed

**Real**
- **App footage:** every app shot is the production build (`web/`), recorded locally at 2880×1620. The clicks are real: the Tongkat Ali row, Full profile, Field brief and the Harvest harm slider.
- **Cross-check figures:** from `data/processed/v2/name_check.csv` and `scripts/survey_gaps.py`. 50 of 51 names matched; 2,992 of 4,542 neighbouring cells under-searched; CDFP's tongkat ali entry (native, DAO Endangered; Bucas Grande, Dinagat, Homonhon, Surigao, Mindoro).
- **Ranking figures:** as in version 2, from the atlas's data and validation.

**Designed (illustrations, not data)**
- the night ground, counters, the "not measured" ledger, the hexagon field for "where botanists searched well", and the rank strip (its resolved 1st–5th range is tongkat ali's real interval);
- the ring of six neighbours for "66%";
- the label pills, page rail and end card.

## Checks on the delivered file

- **Format:** ffprobe gives 1920×1080, 60 fps, 8,352 frames, 139.20 s, yuv420p (tv range), with AAC audio.
- **Loudness:** −14.8 LUFS integrated, LRA 3.8 LU, true peak −3.0 dBFS.
- **MotionMaxxing `look.py`:**
  - **G0 render exists and G2 no empty frame:** PASS.
  - **G3 (end hold):** flagged at 3.9 s. The closing card (name, link, "help us protect the plants that heal us") stays readable after the last word while the camera pushes in slowly; the push is below look.py's 96×54-thumbnail threshold. "Final shot 38%" is the same measurement limit: the film's beats change by blur and planes, not hard cuts, so its cut detector sees one long shot.
  - **Mean luma change:** below the human band, as expected of a voice-led explainer with reading holds.
- **By eye:** stills every few seconds (`look/sheet-g.png`, `look/final2/sheet.jpg`), with defects found and fixed before the final render. Cue words that also occur earlier in the narration ("measures", "Every", "Five", "sure", "searched", "Help") were bound to the wrong occurrence; `tools/check_cues.py` now prints every cue with its context.

## Rebuild

```bash
npm ci
python tools/align.py public/audio/vo2-take1.mp3 audio/vo2-take1
ffmpeg -i public/audio/vo2-take1.mp3 -af "highpass=f=70:poles=2,equalizer=f=320:t=q:w=1.1:g=-1.5,equalizer=f=3400:t=q:w=1.1:g=1.5,deesser=i=0.3:m=0.5:f=0.5,acompressor=threshold=-22dB:ratio=2:attack=8:release=150:knee=6:makeup=1.5,alimiter=limit=0.89:attack=4:release=60" -ar 48000 -ac 1 audio/vo-clean.wav
python tools/master.py                                     # master + room tone; film length follows the voice
python tools/align.py public/audio/vo-master.wav audio/vo-master && cp audio/vo-master.words.json src/words.json
# footage: serve web/dist on :4173, then
node tools/vcap.mjs intro overview atlas profile brief weights check    # 60 fps frames -> capture60/
# encode each: ffmpeg -framerate 60 -i capture60/<take>/%05d.jpg -c:v libx264 -crf 16 -pix_fmt yuv420p public/footage/<take>.mp4
python tools/check_cues.py && npx tsc --noEmit
npx remotion render src/index.ts Film out/harvester-risk-atlas-pitch.mp4 --codec=h264 --crf=17
python tools/srt.py vo2.txt src/words.json 0 harvester-risk-atlas-pitch.en.srt
```

Fonts: Atkinson Hyperlegible Next and Fraunces (SIL OFL), the app's own. OneTake (PolyForm Noncommercial) was not installed or copied; only its principle, that every beat is carried into the next, was applied in this project's own code. No music.

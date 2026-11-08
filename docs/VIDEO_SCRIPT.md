# Pitch video script — Harvester Risk Atlas

> **The recorded film supersedes this draft.** The final 4:00 film is built in [`../video/`](../video/). Its narration is [`../video/vo.txt`](../video/vo.txt), voiced in one take in Yuan's own voice. [`../video/NOTE.md`](../video/NOTE.md) has the beat-by-beat direction, what is real and what is designed, and the checks. [`../video/YOUTUBE.md`](../video/YOUTUBE.md) has the upload copy and chapters. The draft below is kept for reference.

EthnoHack 2026 limit: **10 minutes maximum**. This script runs about **8 minutes**, leaving two minutes in hand. Upload to YouTube or Vimeo (public or unlisted) and paste the link into Devpost.

Director and editor: Alicia Jhyle Vilale. The script follows the slide deck (`submission/Harvester-Risk-Atlas-slides.pdf`) in AIDA order: **Attention** (slides 1–3), **Interest** (4–5), **Desire** (6–9) and **Action** (10). Each heading names the EthnoHack points it covers: problem, motivation, approach, technology, data, results, demo, impact and future.

## Script

### 0:00 · Hook (slide 1) · problem, about 25 s

"Up to four billion people rely on herbal medicine. Most medicinal plants in trade are taken from the wild, and almost no one is counting what is left. This is Harvester Risk Atlas, for EthnoHack Track 3. It shows which wild medicinal plants of the Philippines need help first, where they grow, and how sure we are."

### 0:25 · The global problem (slide 2) · problem, motivation, about 45 s

"About thirty thousand plant species have documented medicinal uses. Of those in international trade, sixty to ninety percent are collected from the wild. Only seven percent have ever been assessed for extinction risk, and one in five of those is already threatened. Meanwhile the trade tripled in value in under twenty years. When roots or bark are taken, the plant often dies, and with it goes a remedy families have used for generations."

### 1:10 · The Philippines (slide 3) · problem, motivation, about 45 s

"In the Philippines, the forests these plants need are shrinking. From 2001 to 2023 the country lost about 175 hectares of tree cover every day, roughly 245 football pitches. The government lists 1,186 threatened plants, but nobody measures harvest. Take tongkat ali: its roots are dug up and sold, it is officially Endangered, and open databases hold only five reliable records of it in the whole country. So where should rangers and harvesters look first?"

[Optional: add a sentence on why this matters to you.]

### 1:55 · Our answer (slide 4) · approach, about 40 s

"Our answer is a free map that ranks which plants need help first, and says why in plain words. For each native medicinal plant we ask three questions. How hard is it to find? Does harvesting kill it? Is its home disappearing? Each counts equally. Climate change is shown, but not scored, because projected warming is the same for every plant."

### 2:35 · How it works (slide 5) · data, approach, about 50 s

"We use six open sources: GBIF records, Kew's plant checklist, protected areas, forest loss, climate, and Stuart's *Philippine Medicinal Plants*. Nine checks clean 9,660 records down to 4,789 reliable ones. Because busy roadsides get recorded more than remote forest, we measure rarity only in 332 well-searched areas. Twenty-nine native plants are scored. Then we re-run the ranking 2,000 times with slightly different weights and evidence, so every plant gets a rank range, not just one number."

### 3:25 · Demo (slide 6, then the live app) · demo, technology, about 2 min 15 s

Open https://harvester-risk-atlas.vercel.app in a clean browser window.

1. **Overview:** "The hotspot map shows where plants that need attention cluster."
2. **Atlas → tongkat ali:** "Plants appear only as broad hexagons, never exact spots, so the map can't lead collectors to them."
3. **Plant profile:** "Three reasons in plain words. It ranks second of twenty-nine, and could be anywhere from first to fifth. The harvest traits say they are still being checked."
4. **Field brief:** "One printable page for rangers and harvesters, with what they can do."
5. **How it works → weight explorer:** "If you think harvest harm matters more, move the slider. The ranking updates live."

Over the last step: "The pipeline is Python with pandas, GeoPandas and H3, and it rebuilds every number offline. The app is React and TypeScript with MapLibre. A test keeps the browser maths identical to the Python index, and automated checks run on every change."

### 5:40 · Results (slide 7) · results, about 40 s

"Five plants need attention now: kalingag, found only in the Philippines; tongkat ali; bitaog; tibig; and amuyon. For all five, rarity is the biggest reason. Two of them are on the government's threatened list, even though we never used that list as an input."

### 6:20 · Can you trust it? (slide 8) · results, validation, about 40 s

"There is no answer key for harvest risk, so we tried to break our own ranking. Combine the reasons another way: nearly the same order. Change what counts as well-searched: the same order. Leave rarity out and the order shifts most, so rarity matters most. And the threatened plants rank higher than chance: a weak signal, because there are only four."

### 7:00 · Honest limits (slide 9) · limitations, about 35 s

"This is not medical advice, a harvest permit or a Red List assessment. Records follow people, harvest harm comes from books, and tongkat ali rests on only five records. The harvest traits come from cited sources, but none is expert-checked yet. Every plant page says so."

### 7:35 · Call to action (slide 10) · impact, future, about 25 s

"DENR, local governments and harvester groups can use it today to decide where to look first. Next, we want expert checks with Filipino ethnobotanists and harvester communities, range models, and trade data. Open the atlas, and help us make it certain."

## Recording notes

- Record at 1920 × 1080 or 1280 × 720 and keep the browser zoom at 100%.
- Both team members should appear or speak if possible.
- Hold each big number on screen for at least two seconds; these are the moments judges remember.
- Read numbers from the live app on the day; if the data is rebuilt, update this script.
- Keep account settings, tokens and notifications off screen.
- Keep the development dates consistent with [`ORIGINALITY.md`](ORIGINALITY.md).

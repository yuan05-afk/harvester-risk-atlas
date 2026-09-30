# Judging — EthnoHACK 2026 Track 3

**Biodiversity & Sustainability** · one-pager for judges

**Live demo:** https://harvester-risk-atlas.streamlit.app/  
**Repo:** GitHub — currently **private** (make public before Devpost close, or share judge access).

> Not medical advice. Not a harvest permit. IUCN categories are never invented.

---

## Problem

Philippine / SEA medicinal plants face overlapping pressures: sparse occurrence data, climate stress, wild collection, and uneven protected-area coverage. Field teams lack a single transparent score that separates *relative pressure* from Red List status.

## Harvest Pressure Index (HPI v1.1)

```
HPI = 0.30·R + 0.25·C + 0.25·H + 0.20·P
```

| Symbol | Component | Source cue |
|--------|-----------|------------|
| R | Rarity | GBIF n (inverted) + endemism cue |
| C | Climate stress | WorldClim 2.1 bio1 / bio12 / bio15 (SEA clip) |
| H | Harvest proxy | Local density + recent frac + literature flag |
| P | PA gap | WDPCA PH overlap + distance |

Each ∈ [0,1]. Confidence penalizes imputed inputs. IUCN is a **dossier field only** — not an HPI input. Full methods: [`METHODS.md`](METHODS.md).

## Workflow

1. **Map** — species centroids, HPI band color, size ∝ score  
2. **Dossier** — R/C/H/P bars + waterfall, data gaps, archetype, decade hist  
3. **Field brief** — HTML / PDF stewardship sheet (research/education only)

Also: **Compare** two species · **Methods** cohort HPI + archetypes.

## Data & licenses

| Source | Role | Notes |
|--------|------|-------|
| GBIF | Occurrences | Cite datasets when publishing |
| WorldClim 2.1 | Climate | SEA clips shipped; Fick & Hijmans 2017 |
| WDPCA PH (HDX) | Protected areas | Protected Planet / WDPA family |
| IUCN API v4 | Red List (optional) | Token → live category; else `not_queried` |
| Seed CSV | Vernaculars | Curated; cultural context only |

Code: MIT. Upstream data keep their own terms.

## AI / OSS disclosure

- Code & docs drafted with AI assistance (Grok / Cursor); reviewed — no invented IUCN statuses.  
- Libraries: `requirements.txt` (their licenses).  
- Optional LLM name helper behind `ENABLE_LLM_NAMES=1` (off by default).

## What to click (Demo mode)

1. Open the live demo. Home states the problem, the index, and the path. A short preface plays once — **Skip** if you want the page immediately. If it does not appear (this session already played it, or the phone reports reduced motion), sidebar → **Replay intro**. `?demo=1` skips the preface and opens the map.  
2. **Open the map**, then sidebar → toggle **Demo mode** (locks *Arcangelisia flava* / abutra + talk track).  
3. **Map** (~15s) — color = HPI band; abutra is moderate with a harvest-proxy signal.  
4. **Continue** → **Dossier** (~25s) — components, gaps (IUCN not linked), archetype, decade hist.  
5. **Field brief** (~15s) — download HTML or PDF. Stewardship only.  
6. Optional: **Compare**, **Methods**.

Spoken script: [`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md) · Checklist: [`SUBMISSION_CHECKLIST.md`](SUBMISSION_CHECKLIST.md).

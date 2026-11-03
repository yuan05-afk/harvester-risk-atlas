# Submission checklist — Harvester Risk Atlas

EthnoHack 2026, Track 3: Biodiversity & Sustainability. Checked against the EthnoHack overview, rules, resources and updates pages and the organisers' final reminder on **3 November 2026**.

**Deadline:** **8 November 2026, 10:00 Athens time (EET, UTC+2)**: 16:00 in Manila (UTC+8) and 08:00 UTC. The Devpost form shows 17:00 GMT+8, but the organisers' final reminder gives 10:00 Athens time, so treat **16:00 Manila** as the deadline. Judging ends 15 November 2026.

**Hacking period:** started 2 November 2026, 13:00 Athens time (19:00 Manila).

Devpost copy, field by field: [`../submission/devpost.md`](../submission/devpost.md). Slides: `submission/Harvester-Risk-Atlas-slides.pdf`. Gallery: `submission/gallery/`.

## Team size

**Now met:** the Devpost project lists two members, Yuan Andrei C. Mariano (@yuan05-afk) and Alicia Jhyle Vilale (@asvilale). One check is still open: Alicia Jhyle Vilale must have registered for EthnoHack by 31 October, 23:00. Each member's real contribution should be stated in the Devpost Team section and in `ORIGINALITY.md`.

Original note, kept for reference:

The rules require **2 to 5 team members** ("Team Requirements: 2-5 Team members"; the Devpost sidebar says "Team required: 2 to 5 members"). **A solo entry does not meet the eligibility rules.** The disqualification clause covers submissions that fail the requirements.

Do this first:

1. Find at least one teammate. The hackathon Discord (https://discord.gg/GrQRGfk9YK) is the place to look. Domain expertise in botany, ethnobotany or pharmacognosy would also strengthen scientific relevance, and a teammate could take on verifying the harvest traits.
2. The teammate must have **registered for EthnoHack by 31 October, 23:00**: later registrations are not eligible for judging or prizes. Choose someone who is already among the registered participants.
3. Invite them through **Manage team** on the Devpost draft and confirm they accept.
4. List their real contribution in the Devpost Team section and in `ORIGINALITY.md`. Do not credit work they did not do.
5. If no teammate can be found, email the hackathon manager (the "Questions? Email the hackathon manager" link on the overview page) to ask whether a solo entry can be judged, before 8 November.

## Rules compliance

| Rule | Status | Evidence |
|---|---|---|
| Team of 2–5, all listed on Devpost | Met (2 members) | Devpost Manage team; registration date of the second member to confirm |
| Legal age, not a company entry | Owner to confirm | — |
| Addresses an official track | Met | Track 3: Biodiversity & Sustainability |
| Meaningful use of data and computation | Met | Python pipeline, Monte Carlo uncertainty, web atlas |
| Devpost project page with required sections | Drafted | `submission/devpost.md`: title, track, description, problem, approach, technologies, data, results, team (placeholder), impact and future |
| Public source repository | Met | https://github.com/yuan05-afk/harvester-risk-atlas (public) |
| README, installation and reproduction | Met | `README.md`; `python -m harvester_risk_atlas all --offline` |
| Data-processing scripts and model code | Met | `src/harvester_risk_atlas/`, `notebooks/01_eda_hpi.ipynb` |
| Dataset references and licences | Met | `README.md`, `docs/METHODS.md` §9, `docs/ORIGINALITY.md`, How it works page |
| Pitch video ≤ 10 min | **To record** | Script: [`VIDEO_SCRIPT.md`](VIDEO_SCRIPT.md), about 8 min |
| Slide deck ≤ 10 slides | Met | `submission/Harvester-Risk-Atlas-slides.pdf`, 10 slides |
| Originality: work created during the hackathon; own vs pre-existing parts identified | Met per owner's confirmation | `docs/ORIGINALITY.md` records development on 2–3 Nov 2026 and lists every third-party component. Some source-data retrieval and access dates in the data files fall before 2 November. If a judge asks, explain them as data provenance; `ORIGINALITY.md` already covers this |
| Licences respected | Met, with care | WDPCA and some GBIF datasets are non-commercial; the project is non-commercial. Stuart text is cited, not redistributed |
| Indigenous and traditional knowledge handled with care | Met | Published, cited compendium only; no community or personal data; locations generalised |
| AI use disclosed | Met | `README.md`, `ORIGINALITY.md`, Devpost "Responsible research". Harvest traits were AI-drafted and are marked unverified |
| No unvalidated findings presented as medical fact | Met | No health claims; disclaimer on every page, the slides and Devpost |
| Uncertainty and limitations communicated | Met | Rank intervals, tiers, `METHODS.md` §7, slide 9 |

## Organisers' final checklist

From the "Final reminder" sent to participants.

| Item | Where | Status |
|---|---|---|
| Project title | Devpost Step 1 | Drafted: "Harvester Risk Atlas" |
| Selected challenge track | Devpost | Pick Track 3: Biodiversity & Sustainability |
| Team members | Devpost Manage team | Done: 2 members |
| Problem statement | Devpost "Inspiration" | Drafted, with sourced numbers |
| Description of the solution | "What it does", "How we built it" | Drafted |
| Technologies and tools | "Built with" tags, "How we built it" | Drafted (25 tags) |
| Data sources and attribution | "How we built it", "Responsible research", README | Drafted |
| Results or prototype | "Results", live app, gallery | Drafted |
| GitHub repository | "Try it out" links | Public |
| Pitch video ≤ 10 min | "Video demo link" | **To record** |
| Slide deck ≤ 10 slides | Additional info upload (one file: the PDF) | Done: 10 slides |
| Limitations, assumptions, future work | "Responsible research", "Assumptions", "What's next"; README | Drafted |
| README explains how it works | `README.md` | Done |
| No unvalidated results presented as medical evidence | Disclaimer on every page, README, Devpost, slides | Done |

## Before submitting

- [x] Teammate added and accepted on Devpost.
- [ ] Second member's EthnoHack registration confirmed as on or before 31 October.
- [x] Roles filled in: `submission/devpost.md` Team section and `ORIGINALITY.md`.
- [ ] Video recorded, under 10 minutes, uploaded, link pasted.
- [ ] Slides PDF uploaded under Additional info.
- [ ] Gallery images uploaded with captions.
- [ ] Walk the demo path in a private window: Overview → Atlas → plant profile → field brief → How it works.
- [ ] Run the checks and record the actual results: `python -m pytest -q`; in `web/`: `npm test`, `npm run build`, `npm run e2e`.
- [ ] Every link opens in a private (signed-out) browser window: live app, GitHub, slides PDF, video.
- [ ] Submit **before 16:00 Manila on 8 November** (10:00 Athens), well ahead of the last minutes.
- [ ] Open the public project page and check that it renders.

These boxes are pending checks, not claims of completed work. Deployment notes: [`../DEPLOY.md`](../DEPLOY.md).

# WB Election 2026: SIR 2026 — Deleted Voter Impact Simulator

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

An interactive browser-based simulator that estimates how the West Bengal Assembly Election 2026 results might have differed if voters deleted during the Special Intensive Revision (SIR) 2026 had been allowed to vote.

**[Open Simulator →]([WB Election 2026: SIR 2026 — Deleted Voter Impact Simulator](https://voice-cfg.github.io/WB_Election_SIR_2026_Impact_Sim/))** *(Use Large Screen)*

---

## What This Tool Does

The Election Commission of India (ECI) deleted approximately **90 lakh (9 million)** voters from West Bengal's electoral rolls during the SIR 2026 process.

**Why does the simulator only use ~26.5 lakh, not 90 lakh?**

Of the 90.6 lakh total deletions, roughly **57 lakh (≈63%) are ASDD deletions** — voters removed because they were found to be **Absentee, Shifted, Dead, or Duplicate**. These are standard roll-cleaning removals that happen every revision cycle. A dead or duplicate voter would not have voted regardless, so including them in a "what if they voted" simulation would be misleading.

| Category | Deleted | % of total | Simulated? |
|---|---|---|---|
| ASDD (Absentee / Shifted / Dead / Duplicate) | ~57.1 lakh | ~63% | **No** — would not vote |
| Under Adjudication (contested deletions) | ~26.0 lakh | ~29% | Partially (see below) |
| Final SIR list (Feb 28 draft) | ~5.4 lakh | ~6% | Partially (see below) |
| **Total** | **90.6 lakh** | 100% | — |

The **~26.5 lakh** this simulator uses is the confirmed net reduction in registered voters between the January 2026 draft roll and the election-day final roll, derived from official constituency-wise data (OpenCity). This covers the post-draft phase and is the only figure available with full constituency-level breakdown. The pre-draft ASDD deletions are not available in constituency-wise machine-readable form.

This tool focuses on the **~26.5 lakh (2.65 million) net deletions** that are confirmed from official data (the post-draft phase, Jan 2026 to election day), constituency by constituency across all 294 assembly seats.

The simulator lets you adjust:
- **Voter turnout** — what % of deleted voters would have shown up to vote
- **Vote split by religion** — how Muslim, Hindu, and Other-religion deleted voters would have distributed their votes across TMC, BJP, CPIM, INC, and Others
- **Per-constituency overrides** — including adjusting the religion composition of deleted voters for each constituency individually

It then recomputes vote totals and identifies which seats would have flipped, narrowed, or widened.

---

## Disclaimer

**This is a simulation tool for educational and research purposes only. It carries no warranty of any kind.**

- **No claim is made** that deleted voters were wrongly removed, that removal was targeted by religion, or that any party or authority acted improperly. The tool models a hypothetical scenario, not a factual one.
- **The results are estimates**, not predictions. Every output depends on assumptions (turnout rate, vote split) chosen by the user. Different assumptions produce different results.
- **Religion-wise voter data is not published by the ECI.** All religion proportions used here are derived from third-party academic and journalistic sources (see Data Sources below) and are approximations.
- **The simulation cannot prove intent or causation.** It only shows arithmetic: given certain assumptions, what would the vote totals look like.
- The tool is provided as-is. The authors accept no responsibility for any use or interpretation of its outputs.

---

## Data Sources

### 1. Electoral Roll Counts — OpenCity / ECI
- **Source:** [OpenCity — West Bengal and Kolkata SIR Electoral Rolls 2026](https://data.opencity.in/dataset/west-bengal-and-kolkata-sir-electoral-rolls-2026)
- Two CSV files: draft roll as of 1 Jan 2026 (7.08 crore voters) and final roll on nomination day (6.83 crore voters)
- The difference per constituency = net deletion count used in this simulator (~25.7–26.5 lakh across 294 constituencies)
- **Reliability: High** — derived directly from official ECI-sourced data published by OpenCity

### 2. Religion Proportions by Constituency — Raphael Susewind (Oxford)
- **Source:** [india-religion-politics / wbrolls2021](https://github.com/raphael-susewind/india-religion-politics/tree/master/wbrolls2021)
- Name-based probabilistic religion classification of the 2021 West Bengal voter rolls, aggregated from booth level to constituency level using elector-weighted averages
- Covers 272 of 294 constituencies; 22 hill/tribal constituencies (Darjeeling, Jalpaiguri, Kalimpong, parts of Malda) use district-level weighted averages as fallback
- **Reliability: Medium** — published academic methodology, but based on 2021 rolls and name-pattern inference, not direct religion data

> ⚠️ **Important — Constituency Religion Data Is Estimated**
>
> The Hindu%, Muslim%, and Other% figures shown for each constituency in the "Religion Mix" column are **estimates derived from name-pattern analysis of 2021 voter rolls**. They are not official ECI figures (ECI does not publish religion-wise voter data). There is a **high chance these proportions are inaccurate** for individual constituencies, especially in areas with mixed or tribal populations, or where the 2021 demographic composition has shifted.
>
> **If you believe the religion mix is wrong for a specific constituency**, click on that constituency row to open its detail panel and adjust the **Hindu% / Muslim%** sliders under "Deleted Voter Religion Mix". The simulation will immediately recalculate using your corrected values.

### 3. State-level Deletion Breakdown — Private Research Organisation (via The Week)
- **Source:** The Week, ["More Muslim voters deleted than Hindus in West Bengal's SIR list?"](https://www.theweek.in/news/india/2026/04/14/more-muslim-voters-deleted-than-hindus-in-west-bengals-sir-list.html), 14 April 2026
- Figures cited: 57.47 lakh Hindu (63.4%), 31.10 lakh Muslim (34.3%) of 90.62 lakh total deletions
- **The research organisation is unnamed and has not published its methodology. These figures cannot be independently verified.**
- **Reliability: Low–Medium** — widely reported in media but primary source is not public

### 4. Constituency-level Confirmed Data — The Wire & SABAR Institute
- **Source:** [The Wire — "What the Voter Purges in Three Constituencies Reveals About West Bengal's SIR"](https://m.thewire.in/article/rights/what-the-voter-purges-in-three-constituencies-reveals-about-west-bengals-sir)
- Confirmed religion-wise deletion figures for Nandigram, Bhabanipur, Mothabari, Nakashipara, and Habra from investigative reporting
- **Reliability: High** — from primary source documents; noted in the data as `confirmed_data`

### 5. Election Results — ECI Results Website
- **Source:** `https://results.eci.gov.in/ResultAcGenMay2026/`
- Full candidate-wise results for all 294 constituencies scraped using `wb_eci_scraper_v5.py`
- **Reliability: High** — official ECI source

---

## Key Limitations

| Limitation | Detail |
|---|---|
| Only post-draft deletions simulated | The ~26.5L figure covers Jan 2026 draft → election day only. The remaining ~64L (ASDD phase) are not in this tool as no constituency-wise breakdown exists. |
| Religion data is estimated, not measured | ECI does not publish religion-wise voter data. All religion figures are third-party approximations. |
| Vote split is user assumption | There is no data on how deleted voters would have voted. The defaults are illustrative, not evidence-based. |
| 2021 religion data applied to 2026 | Susewind's dataset is from 2021 rolls; demographic composition may have shifted. |
| 13 constituencies have no religion data | Hill/tribal constituencies in Darjeeling, Jalpaiguri, Kalimpong: all their deleted voters are treated as "Other religion" in the simulation. |
| No post-SC reinstatements | Some voters under adjudication were restored by Supreme Court order; this is not reflected in the data. |

---

## Usage

Because the simulator fetches JSON files via `fetch()`, it must be served over HTTP — it will not auto-load if opened directly as a local file. Options:

**GitHub Pages (recommended):** Enable GitHub Pages on the repository. Open `https://<username>.github.io/<repo>/sim.html`.

**Local web server:**
```bash
cd eci_data_wb
python3 -m http.server 8000
# then open http://localhost:8000/sim.html
```

**Manual file picker:** If auto-load fails, the page shows a file picker. Select `wb_election_results.json` and `wb_sir_religion_deletions.json` manually.

---

## Files

| File | Description |
|---|---|
| `sim.html` | Interactive simulator (open this in a browser) |
| `wb_election_results.json` | ECI election results for all 294 constituencies |
| `wb_sir_religion_deletions.json` | Net deletion counts and religion estimates per constituency |
| `wb_eci_scraper_v5.py` | Script that scraped election results from ECI website |
| `wb_sir_religion_deletions.py` | Script that computed religion-wise deletion estimates |
| `METHODOLOGY.md` | Detailed methodology, formulas, and source documentation |

---

## Reproducing the Data

```bash
pip install curl_cffi beautifulsoup4 lxml

# Scrape election results (optional — JSON already included)
python wb_eci_scraper_v5.py

# Recompute religion-wise deletion estimates (optional — JSON already included)
python wb_sir_religion_deletions.py
```

---

*Data current as of May 2026. Election results from West Bengal Assembly Election, May 2026.*

---

## Acknowledgements

- **[Raphael Susewind](https://github.com/raphael-susewind)** (Oxford) — for the open religion classification of West Bengal voter rolls
- **[OpenCity](https://data.opencity.in)** — for publishing machine-readable SIR electoral roll data
- **[Claude Code](https://claude.ai/code)** (Anthropic) — this simulator, all data processing scripts, and this documentation were built with the assistance of Claude AI

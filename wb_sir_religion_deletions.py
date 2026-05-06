"""
WB SIR 2026 Deleted Voter List — Religion-wise Constituency Analysis

DATA SOURCES:
  1. OpenCity — SIR Draft roll (01-Jan-2026) and Final roll (election day)
     https://data.opencity.in/dataset/west-bengal-and-kolkata-sir-electoral-rolls-2026
     → Gives constituency-wise net voter change during SIR 2026
     → Draft (7.08 crore) → Final (6.83 crore) = 25.7 lakh net change
     NOTE: The full "90 lakh deleted" figure reported in news is measured
     from the pre-SIR 2024 roll (7.6 crore) to the final roll (6.7 crore).
     No machine-readable 2024 baseline is publicly available, so we use
     a scaled estimate for the 90L figure (see below).

  2. Raphael Susewind (india-religion-politics) — wbrolls2021.csv
     https://github.com/raphael-susewind/india-religion-politics
     → Booth-level name-based religion estimates from 2021 voter rolls
     → Aggregated to constituency level for Hindu / Muslim / Other %

  3. The Week (April 2026) — Category-wise state-level religion breakdown
     Source: private research organisation cited in The Week, Apr 14 2026
     Total deletions (state-level): 90,62,188
       ASDD (Absent/Shifted/Dead/Duplicate): Hindu 43,81,378 | Muslim 13,31,325
       Final SIR list (Feb 28):              Hindu  5,28,820 | Muslim     13,363
       Under Adjudication:                   Hindu  8,37,116 | Muslim  17,65,475
     → Overall:  Hindu ~57.5L (63.4%)  |  Muslim ~31.1L (34.3%)

  4. Confirmed constituency data (SABAR Institute / The Wire / The Week)
     → Nandigram, Bhabanipur, Mothabari, Nakashipara, Habra

TWO DELETION FIGURES PER CONSTITUENCY:
  a) net_deleted   — actual roll change from OpenCity (Draft Jan-2026 → Final)
                     25.7 lakh statewide. Captures post-draft adjudication phase.
  b) scaled_deleted — constituency share of the reported 90L total.
                     Allocated proportional to each AC's share of net deletions.
                     Matches the figure cited in Mamata's statement and news.

OUTPUT: wb_sir_religion_deletions.json
"""

import json
import csv
import io
from curl_cffi import requests as curl_requests

# ── URLs ─────────────────────────────────────────────────────────────────────

DRAFT_CSV_URL    = ("https://data.opencity.in/dataset/f534b035-5e5f-4b2d-bd48-b0549a7d222b"
                    "/resource/c7cb58ef-4267-4386-8ab5-5a014078999c/download/wb-sir-draft-rolls-2026.csv")
FINAL_CSV_URL    = ("https://data.opencity.in/dataset/f534b035-5e5f-4b2d-bd48-b0549a7d222b"
                    "/resource/f7c67499-5830-4991-b724-3e796b634ef9/download/wb_acwise_elector_2026.csv")
RELIGION_CSV_URL = ("https://raw.githubusercontent.com/raphael-susewind/"
                    "india-religion-politics/master/wbrolls2021/wbrolls2021.csv")

OUTPUT_FILE = "wb_sir_religion_deletions.json"

# ── State-level religion breakdown from The Week / private research org ───────
# Source: The Week, Apr 14 2026. Private org; no public methodology.
STATE_TOTAL_REPORTED = 9_062_188   # 90.62 lakh (The Week)
STATE_RELIGION = {
    # category       : {hindu, muslim}
    "asdd"           : {"hindu": 4_381_378, "muslim": 1_331_325},  # Absent/Shifted/Dead/Dup
    "final_sir_list" : {"hindu":   528_820, "muslim":    13_363},  # Feb 28 final list
    "under_adjudication": {"hindu": 837_116, "muslim": 1_765_475},
}
# Derived totals
STATE_HINDU_TOTAL  = sum(v["hindu"]  for v in STATE_RELIGION.values())  # ~57.5L
STATE_MUSLIM_TOTAL = sum(v["muslim"] for v in STATE_RELIGION.values())  # ~31.1L
STATE_HINDU_PCT    = STATE_HINDU_TOTAL  / STATE_TOTAL_REPORTED * 100    # 63.42%
STATE_MUSLIM_PCT   = STATE_MUSLIM_TOTAL / STATE_TOTAL_REPORTED * 100    # 34.32%

# ── Confirmed constituency data from SABAR Institute / The Wire / The Week ────
CONFIRMED = {
    "nandigram"   : {"muslim": 3270, "non_muslim": 191,  "total": 3461,
                     "source": "SABAR Institute, via The Week Apr 2026"},
    "bhabanipur"  : {"muslim": 1554, "non_muslim": 2321, "total": 3875,
                     "source": "SABAR Institute, via The Week Apr 2026"},
    "mothabari"   : {"muslim_pct": 67.3, "total_confirmed": 46274,
                     "source": "The Wire Apr 2026 (Under Adjudication category)"},
    "nakashipara" : {"muslim_pct": 81.16, "total_confirmed": 23666,
                     "source": "The Wire Apr 2026 (Under Adjudication category)"},
    "habra"       : {"muslim_pct": 34.0, "total_confirmed": 43117,
                     "source": "The Wire Apr 2026"},
}


def fetch_csv(session, url, label):
    print(f"  Downloading {label}...")
    r = session.get(url, timeout=60)
    r.raise_for_status()
    return r.text


def parse_draft(text):
    text = text.lstrip("﻿")
    reader = csv.DictReader(io.StringIO(text))
    data = {}
    for row in reader:
        if not row["AC NO"].strip():
            continue
        ac = int(row["AC NO"])
        data[ac] = {
            "ac_no":       ac,
            "ac_name":     row["AC name"].strip(),
            "district":    row["Name of District"].strip(),
            "draft_total": int(row["Total electors"]),
        }
    return data


def parse_final(text):
    reader = csv.DictReader(io.StringIO(text))
    data = {}
    for row in reader:
        if not row["AC No."].strip():
            continue
        ac = int(row["AC No."])
        data[ac] = int(row["Total"])
    return data


def parse_religion(text):
    """
    Aggregates Susewind's booth-level religion % to constituency level,
    weighted by electors_21.
    Returns {ac_id: {muslim_pct, hindu_pct, other_pct, source}}
    """
    reader = csv.DictReader(io.StringIO(text))
    agg = {}

    for row in reader:
        if not row["ac_id_09"].strip():
            continue
        ac       = int(row["ac_id_09"])
        electors = float(row["electors_21"] or 0)
        if electors <= 0:
            continue

        muslim = float(row.get("muslim_percent_21") or 0)
        hindu  = float(row.get("hindu_percent_21")  or 0)
        other  = max(0.0, 100.0 - muslim - hindu)

        if ac not in agg:
            agg[ac] = {"muslim_wsum": 0, "hindu_wsum": 0, "other_wsum": 0, "total_electors": 0}
        agg[ac]["muslim_wsum"]    += muslim * electors
        agg[ac]["hindu_wsum"]     += hindu  * electors
        agg[ac]["other_wsum"]     += other  * electors
        agg[ac]["total_electors"] += electors

    result = {}
    for ac, v in agg.items():
        te = v["total_electors"]
        if te > 0:
            result[ac] = {
                "muslim_pct": round(v["muslim_wsum"] / te, 2),
                "hindu_pct":  round(v["hindu_wsum"]  / te, 2),
                "other_pct":  round(v["other_wsum"]  / te, 2),
                "source":     "Susewind 2021 voter roll name-based analysis",
            }
    return result


def district_fallbacks(draft, religion):
    """District-average religion proportions for the 22 ACs missing from Susewind."""
    d_agg = {}
    for ac_no, info in draft.items():
        if ac_no not in religion:
            continue
        rel    = religion[ac_no]
        voters = info["draft_total"]
        d      = info["district"]
        if d not in d_agg:
            d_agg[d] = {"muslim_wsum": 0, "hindu_wsum": 0, "other_wsum": 0, "total_electors": 0}
        d_agg[d]["muslim_wsum"]    += rel["muslim_pct"] * voters
        d_agg[d]["hindu_wsum"]     += rel["hindu_pct"]  * voters
        d_agg[d]["other_wsum"]     += rel["other_pct"]  * voters
        d_agg[d]["total_electors"] += voters

    fallback = {}
    for d, v in d_agg.items():
        te = v["total_electors"]
        if te > 0:
            fallback[d] = {
                "muslim_pct": round(v["muslim_wsum"] / te, 2),
                "hindu_pct":  round(v["hindu_wsum"]  / te, 2),
                "other_pct":  round(v["other_wsum"]  / te, 2),
                "source":     f"District-level fallback (Susewind 2021, AC not in dataset)",
            }
    return fallback


def lookup_confirmed(ac_name):
    key = ac_name.lower().strip()
    if key in CONFIRMED:
        return CONFIRMED[key]
    for k, v in CONFIRMED.items():
        if k in key or key in k:
            return v
    return None


def build_results(draft, final, religion, total_net_deleted):
    fallback = district_fallbacks(draft, religion)
    results  = {}

    for ac_no in sorted(draft.keys()):
        info        = draft[ac_no]
        draft_total = info["draft_total"]
        final_total = final.get(ac_no, 0)
        net_deleted = max(0, draft_total - final_total)

        # Scale to the 90L reported figure (proportional to this AC's share of net deletions)
        share          = net_deleted / total_net_deleted if total_net_deleted > 0 else 0
        scaled_deleted = round(share * STATE_TOTAL_REPORTED)

        # Religion proportions
        if ac_no in religion:
            rel = religion[ac_no]
        else:
            rel = fallback.get(info["district"],
                               {"muslim_pct": 0, "hindu_pct": 0, "other_pct": 0,
                                "source": "No data"})

        m_pct = rel["muslim_pct"] / 100
        h_pct = rel["hindu_pct"]  / 100
        o_pct = rel["other_pct"]  / 100

        # Estimates based on constituency religion proportions (Susewind)
        susewind_est = {
            "muslim": round(scaled_deleted * m_pct),
            "hindu":  round(scaled_deleted * h_pct),
            "other":  round(scaled_deleted * o_pct),
            "note": "Susewind 2021 religion % × scaled 90L deletion share",
        }

        # Estimates based on state-level religion proportions (The Week)
        statelevel_est = {
            "muslim": round(scaled_deleted * STATE_MUSLIM_PCT / 100),
            "hindu":  round(scaled_deleted * STATE_HINDU_PCT  / 100),
            "other":  round(scaled_deleted * (100 - STATE_HINDU_PCT - STATE_MUSLIM_PCT) / 100),
            "note": "State-level Hindu 63.4% / Muslim 34.3% from The Week (private research org)",
        }

        confirmed = lookup_confirmed(info["ac_name"])

        entry = {
            "ac_no":        ac_no,
            "ac_name":      info["ac_name"],
            "district":     info["district"],
            "draft_voters": draft_total,
            "final_voters": final_total,

            "net_deleted":    net_deleted,
            "scaled_deleted": scaled_deleted,

            "religion_proportions": {
                "muslim_pct": rel["muslim_pct"],
                "hindu_pct":  rel["hindu_pct"],
                "other_pct":  rel["other_pct"],
                "source":     rel.get("source", ""),
            },
            "estimated_deleted_susewind":   susewind_est,
            "estimated_deleted_statelevel": statelevel_est,
        }

        if confirmed:
            cd = {"source": confirmed["source"]}
            if "muslim" in confirmed:
                cd["muslim_deleted"]     = confirmed["muslim"]
                cd["non_muslim_deleted"] = confirmed["non_muslim"]
                cd["total_confirmed"]    = confirmed["total"]
            elif "muslim_pct" in confirmed:
                tc = confirmed.get("total_confirmed", scaled_deleted)
                cd["muslim_deleted"]     = round(tc * confirmed["muslim_pct"] / 100)
                cd["non_muslim_deleted"] = round(tc * (100 - confirmed["muslim_pct"]) / 100)
                cd["total_confirmed"]    = tc
            entry["confirmed_data"] = cd

        results[str(ac_no)] = entry

    return results


def summarise(results, total_net_deleted):
    net_total    = sum(v["net_deleted"]    for v in results.values())
    scaled_total = sum(v["scaled_deleted"] for v in results.values())

    sus_muslim   = sum(v["estimated_deleted_susewind"]["muslim"]   for v in results.values())
    sus_hindu    = sum(v["estimated_deleted_susewind"]["hindu"]     for v in results.values())
    sl_muslim    = sum(v["estimated_deleted_statelevel"]["muslim"]  for v in results.values())
    sl_hindu     = sum(v["estimated_deleted_statelevel"]["hindu"]   for v in results.values())

    district_totals = {}
    for v in results.values():
        d = v["district"]
        district_totals.setdefault(d, {
            "net_deleted": 0, "scaled_deleted": 0,
            "est_muslim_susewind": 0, "est_hindu_susewind": 0,
            "est_muslim_statelevel": 0, "est_hindu_statelevel": 0,
        })
        district_totals[d]["net_deleted"]           += v["net_deleted"]
        district_totals[d]["scaled_deleted"]         += v["scaled_deleted"]
        district_totals[d]["est_muslim_susewind"]    += v["estimated_deleted_susewind"]["muslim"]
        district_totals[d]["est_hindu_susewind"]     += v["estimated_deleted_susewind"]["hindu"]
        district_totals[d]["est_muslim_statelevel"]  += v["estimated_deleted_statelevel"]["muslim"]
        district_totals[d]["est_hindu_statelevel"]   += v["estimated_deleted_statelevel"]["hindu"]

    return {
        "methodology_note": (
            "net_deleted = actual roll change Jan-2026 draft → election-day final (OpenCity). "
            "scaled_deleted = proportional share of the 90.6L total reported in news "
            "(The Week Apr 2026, private research org). "
            "Religion estimates: (a) Susewind = constituency-specific proportions; "
            "(b) statelevel = uniform 63.4% Hindu / 34.3% Muslim applied to all ACs."
        ),
        "state_level_news_figures": {
            "total_deleted_reported":   STATE_TOTAL_REPORTED,
            "hindu_deleted":            STATE_HINDU_TOTAL,
            "muslim_deleted":           STATE_MUSLIM_TOTAL,
            "hindu_pct":                round(STATE_HINDU_PCT, 2),
            "muslim_pct":               round(STATE_MUSLIM_PCT, 2),
            "breakdown_by_category": {
                "asdd":              STATE_RELIGION["asdd"],
                "final_sir_list":    STATE_RELIGION["final_sir_list"],
                "under_adjudication": STATE_RELIGION["under_adjudication"],
            },
            "source": "Private research organisation cited in The Week, Apr 14 2026; no public methodology",
        },
        "openCity_net_totals": {
            "total_net_deleted": net_total,
            "note": "Difference between Jan-2026 draft roll and election-day final roll (OpenCity CSVs)",
        },
        "total_constituencies": len(results),
        "estimated_statewide": {
            "scaled_total":    scaled_total,
            "hindu_susewind":  sus_hindu,
            "muslim_susewind": sus_muslim,
            "hindu_statelevel":  sl_hindu,
            "muslim_statelevel": sl_muslim,
        },
        "district_totals": district_totals,
    }


def main():
    print("=" * 65)
    print("WB SIR 2026 — Religion-wise Deleted Voter Analysis (v2)")
    print("=" * 65)

    session = curl_requests.Session(impersonate="chrome124")

    print("\n[1/3] Fetching electoral roll data from OpenCity...")
    draft_text    = fetch_csv(session, DRAFT_CSV_URL,    "SIR Draft rolls (Jan 2026 baseline)")
    final_text    = fetch_csv(session, FINAL_CSV_URL,    "Final rolls (election-day)")

    print("\n[2/3] Fetching religion data (Susewind 2021 voter roll analysis)...")
    religion_text = fetch_csv(session, RELIGION_CSV_URL, "Religion proportions by booth")

    print("\n[3/3] Computing constituency-wise deletions & estimates...")
    draft    = parse_draft(draft_text)
    final    = parse_final(final_text)
    religion = parse_religion(religion_text)

    total_net = sum(max(0, draft[ac]["draft_total"] - final.get(ac, 0)) for ac in draft)
    print(f"  Net deleted (OpenCity diff): {total_net:,} ({total_net/1e5:.1f} lakh)")
    print(f"  Scaled-to 90L total:         {STATE_TOTAL_REPORTED:,} ({STATE_TOTAL_REPORTED/1e5:.1f} lakh)")
    print(f"  Scaling factor:              {STATE_TOTAL_REPORTED/total_net:.1f}×")

    results  = build_results(draft, final, religion, total_net)
    summary  = summarise(results, total_net)
    output   = {"summary": summary, "constituencies": results}

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # ── Print report ──────────────────────────────────────────────────────────
    print(f"\n{'=' * 65}")
    print(f"Saved → {OUTPUT_FILE}")

    print(f"\n{'─'*65}")
    print(f"STATE-LEVEL (news-reported 90L figure — The Week, private org):")
    snf = summary["state_level_news_figures"]
    print(f"  Total deleted:    {snf['total_deleted_reported']:>12,}  ({snf['total_deleted_reported']/1e5:.1f} lakh)")
    print(f"  Hindu deleted:    {snf['hindu_deleted']:>12,}  ({snf['hindu_pct']:.1f}%)")
    print(f"  Muslim deleted:   {snf['muslim_deleted']:>12,}  ({snf['muslim_pct']:.1f}%)")
    print(f"\n  By deletion category:")
    for cat, v in snf["breakdown_by_category"].items():
        h, m = v["hindu"], v["muslim"]
        total_cat = h + m
        print(f"  {cat:<22}: Hindu {h:>9,} ({h/total_cat*100:.0f}%)  |  Muslim {m:>9,} ({m/total_cat*100:.0f}%)")
    print(f"\n  Source: {snf['source']}")

    print(f"\n{'─'*65}")
    print(f"TOP 20 CONSTITUENCIES BY SCALED DELETIONS (90L proportional estimate):")
    top = sorted(results.values(), key=lambda x: x["scaled_deleted"], reverse=True)[:20]
    print(f"  {'AC':>3}  {'Constituency':<25} {'Scaled':>8}  {'Est.Hindu':>10}  {'Est.Muslim':>10}  {'Confirmed':>9}")
    print(f"  {'---':>3}  {'-'*25} {'--------':>8}  {'----------':>10}  {'----------':>10}  {'---------':>9}")
    for v in top:
        sus  = v["estimated_deleted_susewind"]
        conf = "YES *" if "confirmed_data" in v else ""
        print(f"  {v['ac_no']:>3}  {v['ac_name']:<25} {v['scaled_deleted']:>8,}  "
              f"{sus['hindu']:>10,}  {sus['muslim']:>10,}  {conf:>9}")
    print(f"  (* = confirmed religion breakdown from news investigation)")

    print(f"\n{'─'*65}")
    print(f"TOP 15 DISTRICTS BY SCALED DELETIONS:")
    top_d = sorted(summary["district_totals"].items(), key=lambda x: -x[1]["scaled_deleted"])[:15]
    print(f"  {'District':<25} {'Scaled':>8}  {'Est.Hindu':>10}  {'Est.Muslim':>10}")
    print(f"  {'-'*25} {'--------':>8}  {'----------':>10}  {'----------':>10}")
    for d, v in top_d:
        print(f"  {d:<25} {v['scaled_deleted']:>8,}  "
              f"{v['est_hindu_susewind']:>10,}  {v['est_muslim_susewind']:>10,}")

    print(f"\n{'─'*65}")
    print(f"KEY NOTES:")
    print(f"  1. ECI publishes NO official religion-wise voter statistics.")
    print(f"  2. The '90L' figure & Hindu/Muslim split came from an unnamed private")
    print(f"     research org cited in The Week (Apr 14 2026). No public methodology.")
    print(f"  3. Mamata Banerjee claimed '60L Hindu, 30L Muslim' — close to the data")
    print(f"     (actual ~57.5L Hindu, ~31.1L Muslim per the private org).")
    print(f"  4. The Under-Adjudication category was 67.8% Muslim (contested deletions).")
    print(f"     ASDD (routine) was 76.6% Hindu (absentee/dead/shifted).")
    print(f"  5. Constituency-level religion figures are ESTIMATES only.")


if __name__ == "__main__":
    main()

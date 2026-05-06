"""
ECI West Bengal Scraper v5 — curl_cffi (Chrome TLS fingerprint spoof)
This bypasses Cloudflare by impersonating a real Chrome TLS handshake.

Install:
  pip install curl_cffi beautifulsoup4 lxml

Run:
  python wb_eci_scraper_v5.py
"""

import json
import time
import re
from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests

BASE_URL = "https://results.eci.gov.in/ResultAcGenMay2026/ConstituencywiseS25{}.htm"
TOTAL_CONSTITUENCIES = 294
OUTPUT_FILE = "wb_election_results.json"
DELAY = 0.6


def clean(text):
    return re.sub(r"\s+", " ", text or "").strip()

def to_int(s):
    s = re.sub(r"[^\d]", "", s or "")
    return int(s) if s else 0

def to_float(s):
    s = re.sub(r"[^\d.]", "", s or "")
    try: return float(s)
    except: return 0.0


def parse_page(html, num):
    soup = BeautifulSoup(html, "lxml")
    body = soup.get_text().lower()

    if "access denied" in body or "cloudflare" in body or "forbidden" in body:
        return {"constituency_number": num, "error": "Blocked: " + body[:80].strip()}

    result = {
        "constituency_number": num,
        "constituency_name": "",
        "total_votes": 0,
        "winning": {"candidate_name": "", "party": "", "votes": 0, "margin": 0},
        "candidates": {},
    }

    # Constituency name
    for sel in ["div.cand-name", "h2", "h3", "h1", ".title"]:
        tag = soup.select_one(sel)
        if tag:
            n = clean(tag.get_text())
            if n and len(n) < 120:
                result["constituency_name"] = n
                break
    if not result["constituency_name"] and soup.title:
        result["constituency_name"] = clean(soup.title.get_text())

    # Find results table
    col_map = {}
    candidate_table = None
    for table in soup.find_all("table"):
        ths = table.find_all("th") or (table.find("tr").find_all("td") if table.find("tr") else [])
        headers = [clean(th.get_text()).lower() for th in ths]
        joined = " ".join(headers)
        if "candidate" in joined or ("party" in joined and "vote" in joined):
            candidate_table = table
            for i, h in enumerate(headers):
                if ("candidate" in h or "name" in h) and "name" not in col_map: col_map["name"] = i
                if "party" in h and "party" not in col_map: col_map["party"] = i
                if "evm" in h: col_map["evm_votes"] = i
                if "postal" in h: col_map["postal_votes"] = i
                if "total" in h and "vote" in h: col_map["total_votes"] = i
                if ("%" in h or "percent" in h) and "percentage" not in col_map: col_map["percentage"] = i
            if "total_votes" not in col_map:
                for i, h in enumerate(headers):
                    if "vote" in h: col_map["total_votes"] = i; break
            break

    total_sum = 0
    if candidate_table:
        for idx, row in enumerate(candidate_table.find_all("tr")[1:]):
            cells = [clean(td.get_text()) for td in row.find_all("td")]
            if not cells or all(c == "" for c in cells): continue

            def get(k): i = col_map.get(k); return cells[i] if i is not None and i < len(cells) else ""

            name = get("name")
            if not name or name.lower() in ["total valid votes", "total", "invalid", "rejected"]: continue

            party   = get("party")
            votes   = to_int(get("total_votes"))
            evm     = to_int(get("evm_votes"))
            postal  = to_int(get("postal_votes"))
            pct     = to_float(get("percentage"))
            total_sum += votes

            result["candidates"][f"candidate_{idx+1}"] = {
                "name": name, "party": party,
                "evm_votes": evm, "postal_votes": postal,
                "votes": votes, "percentage": pct,
            }

    # Winner & margin
    ranked = sorted(result["candidates"].values(), key=lambda c: c["votes"], reverse=True)
    if ranked:
        w = ranked[0]
        result["winning"] = {
            "candidate_name": w["name"], "party": w["party"], "votes": w["votes"],
            "margin": w["votes"] - ranked[1]["votes"] if len(ranked) >= 2 else 0,
        }

    # Explicit total votes row
    tt = soup.find(string=re.compile(r"total\s+(valid\s+)?votes", re.I))
    if tt:
        tr = tt.find_parent("tr")
        if tr:
            for td in reversed(tr.find_all("td")):
                v = to_int(td.get_text())
                if v > 0: total_sum = v; break

    result["total_votes"] = total_sum
    return result


def save(results):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)


def scrape_all():
    results = {}
    session = curl_requests.Session(impersonate="chrome124")
    session.headers.update({
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-IN,en;q=0.9",
        "Accept-Encoding": "gzip, deflate, br",
        "Referer": "https://results.eci.gov.in/ResultAcGenMay2026/index.htm",
    })

    # Warm up
    print("Warming up...")
    try:
        session.get("https://results.eci.gov.in/ResultAcGenMay2026/index.htm", timeout=15)
        time.sleep(1.5)
    except Exception as e:
        print(f"  Warm-up warning: {e}")

    for i in range(1, TOTAL_CONSTITUENCIES + 1):
        url = BASE_URL.format(i)
        print(f"[{i:>3}/{TOTAL_CONSTITUENCIES}] {url}")

        for attempt in range(3):
            try:
                resp = session.get(url, timeout=15)
                resp.raise_for_status()
                data = parse_page(resp.text, i)

                if "error" in data:
                    if attempt < 2:
                        print(f"         ⚠ {data['error'][:60]} — retrying in 3s...")
                        time.sleep(3); continue
                    print(f"         ✗ Blocked after 3 attempts")

                name   = data.get("constituency_name") or f"Constituency_{i}"
                cands  = len(data.get("candidates", {}))
                tvotes = data.get("total_votes", 0)
                winner = data.get("winning", {}).get("candidate_name", "?")
                wparty = data.get("winning", {}).get("party", "?")
                print(f"         ✓ {name} | {cands} candidates | {tvotes:,} votes | {winner} ({wparty})")
                results[str(i)] = data
                break

            except Exception as e:
                print(f"         ✗ Attempt {attempt+1}: {e}")
                if attempt == 2: results[str(i)] = {"constituency_number": i, "error": str(e)}
                else: time.sleep(2)

        if i % 10 == 0:
            save(results)
            print(f"  💾 Saved progress ({i}/{TOTAL_CONSTITUENCIES})")

        time.sleep(DELAY)

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("ECI West Bengal Scraper v5 (curl_cffi / Chrome TLS spoof)")
    print(f"Scraping {TOTAL_CONSTITUENCIES} constituencies...")
    print("=" * 60)

    results = scrape_all()
    save(results)

    ok = sum(1 for v in results.values() if "error" not in v)
    print("=" * 60)
    print(f"Done! {ok}/{TOTAL_CONSTITUENCIES} succeeded → {OUTPUT_FILE}")

    parties = {}
    for v in results.values():
        p = v.get("winning", {}).get("party", "")
        if p: parties[p] = parties.get(p, 0) + 1

    if parties:
        print("\nParty-wise Seat Tally:")
        for party, seats in sorted(parties.items(), key=lambda x: -x[1]):
            print(f"  {party:35s} {seats:3d} seats")

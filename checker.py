#!/usr/bin/env python3
"""
William Browning — Application Checker v2
Page change detection: takes snapshots of careers pages and alerts when they change significantly.
Runs daily at 8am via GitHub Actions.
"""

import json
import os
import datetime
import time
import hashlib
import re

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    PLAYWRIGHT = True
except ImportError:
    PLAYWRIGHT = False

# ── FIRMS ─────────────────────────────────────────────────────────────────────

FIRMS = [
    {"name": "Schroders", "role": "Graduate Investment Analyst", "prob": "High",
     "url": "https://www.schroders.com/en-gb/uk/individual/careers/early-careers/"},
    {"name": "Rathbones", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.rathbones.com/careers"},
    {"name": "Brooks Macdonald", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.brooksmacdonald.com/careers"},
    {"name": "Canaccord Genuity Wealth", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.canaccordgenuitywealth.com/careers"},
    {"name": "Quilter Cheviot", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.quiltercheviot.com/about-us/careers/"},
    {"name": "Investec Wealth", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.investec.com/en_gb/welcome-to-investec/careers.html"},
    {"name": "M&G Investments", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.mandg.com/careers/early-careers"},
    {"name": "Legal & General IM", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.lgim.com/uk/en/capabilities/careers/"},
    {"name": "Rothschild Wealth", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.rothschildandco.com/en/careers/"},
    {"name": "Charles Stanley", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.charles-stanley.co.uk/careers"},
    {"name": "Smith & Williamson", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.smithandwilliamson.com/careers"},
    {"name": "Waverton Investment Management", "role": "Graduate / Analyst", "prob": "High",
     "url": "https://www.waverton.co.uk/about/careers"},
    {"name": "Fidelity International", "role": "Graduate Programme", "prob": "Good",
     "url": "https://careers.fidelityinternational.com/early-careers/"},
    {"name": "Baillie Gifford", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.bailliegifford.com/en/uk/about-us/careers/vacancies/"},
    {"name": "BlackRock", "role": "Client & Product Graduate Rotational", "prob": "Good",
     "url": "https://careers.blackrock.com/students-and-graduates-emea"},
    {"name": "Capital Group", "role": "Graduate Analyst", "prob": "Good",
     "url": "https://www.capitalgroup.com/us/en/careers/students.html"},
    {"name": "Invesco", "role": "Graduate Programme", "prob": "Good",
     "url": "https://careers.invesco.com/early-careers"},
    {"name": "Columbia Threadneedle", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.columbiathreadneedle.co.uk/careers/"},
    {"name": "UBS Wealth Management", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.ubs.com/global/en/careers/graduates.html"},
    {"name": "Ninety One", "role": "Graduate Programme", "prob": "Good",
     "url": "https://ninetyone.com/en/united-kingdom/careers"},
    {"name": "Hargreaves Lansdown", "role": "Graduate Programme", "prob": "Good",
     "url": "https://careers.hl.co.uk/early-careers"},
    {"name": "Newton Investment Management", "role": "Graduate / Analyst", "prob": "Good",
     "url": "https://www.newtonim.com/en-gb/about/careers/"},
    {"name": "Cazenove Capital", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.cazenovecapital.com/en-gb/careers/"},
    {"name": "Janus Henderson", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.janushenderson.com/en-gb/careers/early-careers/"},
    {"name": "abrdn", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.abrdn.com/careers/early-careers"},
    {"name": "Man Group", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.man.com/careers/graduates"},
    {"name": "Jupiter Asset Management", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.jupiteram.com/uk/en/about-us/careers/"},
    {"name": "Artemis", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.artemisfunds.com/en/gbr/individual/about/careers"},
    {"name": "Polar Capital", "role": "Analyst / Graduate", "prob": "Moderate",
     "url": "https://www.polarcapital.co.uk/about/careers"},
    {"name": "Liontrust", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.liontrust.co.uk/about-us/careers"},
    {"name": "Lazard Asset Management", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.lazardassetmanagement.com/uk/en_gb/about/careers"},
    {"name": "Federated Hermes", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.federatedhermes.com/us/about/careers.do"},
    {"name": "Pictet Asset Management", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.group.pictet/careers"},
    {"name": "Brevan Howard", "role": "Analyst Programme", "prob": "Stretch",
     "url": "https://www.brevanhoward.com/careers"},
    {"name": "TT International", "role": "Analyst / Graduate", "prob": "Stretch",
     "url": "https://www.ttim.com/careers"},
    {"name": "Rothschild & Co Advisory", "role": "Graduate Analyst", "prob": "Stretch",
     "url": "https://www.rothschildandco.com/en/careers/"},
    {"name": "Schroders Off-Cycle", "role": "Off-Cycle Internship", "prob": "Good",
     "url": "https://www.schroders.com/en-gb/uk/individual/careers/early-careers/"},
    {"name": "BlackRock Off-Cycle", "role": "Client & Product Off-Cycle", "prob": "Good",
     "url": "https://careers.blackrock.com/students-and-graduates-emea"},
]

# ── CONFIRMED OPEN KEYWORDS (very specific — only appear on live application pages) ──

CONFIRMED_OPEN = [
    "apply for 2027",
    "applications open for 2027",
    "graduate programme 2027",
    "summer analyst 2027",
    "summer internship 2027",
    "off-cycle 2027",
    "closing date",
    "application deadline",
    "apply by",
    "applications close",
    "now accepting applications",
    "applications are now open",
    "apply now for",
    "start date: september 2027",
    "start date: august 2027",
    "intake 2027",
    "cohort 2027",
]

CONFIRMED_CLOSED = [
    "applications are now closed",
    "applications closed",
    "this programme is now closed",
    "recruitment closed",
    "no current openings",
    "no current vacancies",
    "check back",
    "register your interest for 2027",
    "register interest",
    "be notified when",
    "join our talent community to be notified",
]

SNAPSHOTS_FILE = "snapshots.json"
RESULTS_FILE = "results.json"
CHANGES_THRESHOLD = 0.15  # 15% change in content = significant

# ── HELPERS ───────────────────────────────────────────────────────────────────

def load_snapshots():
    if os.path.exists(SNAPSHOTS_FILE):
        try:
            with open(SNAPSHOTS_FILE) as f:
                return json.load(f)
        except:
            pass
    return {}

def save_snapshots(snaps):
    with open(SNAPSHOTS_FILE, "w") as f:
        json.dump(snaps, f, indent=2)

def clean_text(text):
    """Remove dynamic elements like dates, prices, numbers that change daily."""
    text = re.sub(r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}', '', text)
    text = re.sub(r'\d{4}-\d{2}-\d{2}', '', text)
    text = re.sub(r'\b\d+\b', '', text)
    text = re.sub(r'\s+', ' ', text).strip()
    return text.lower()

def content_hash(text):
    return hashlib.md5(clean_text(text).encode()).hexdigest()

def similarity(old_text, new_text):
    """Returns 0-1 where 1 = identical, 0 = completely different."""
    old = set(clean_text(old_text).split())
    new = set(clean_text(new_text).split())
    if not old and not new:
        return 1.0
    if not old or not new:
        return 0.0
    intersection = old & new
    union = old | new
    return len(intersection) / len(union)

def check_keywords(text):
    """Check for confirmed open/closed keywords."""
    t = text.lower()
    open_hits = [kw for kw in CONFIRMED_OPEN if kw in t]
    closed_hits = [kw for kw in CONFIRMED_CLOSED if kw in t]
    return open_hits, closed_hits

# ── PAGE FETCH ────────────────────────────────────────────────────────────────

def fetch_page(page, url):
    try:
        page.goto(url, timeout=25000, wait_until="networkidle")
        page.wait_for_timeout(3000)
        text = page.inner_text("body")
        return text, None
    except Exception as e:
        return None, str(e)

# ── ASSESS ────────────────────────────────────────────────────────────────────

def assess(firm_name, new_text, snapshots):
    open_hits, closed_hits = check_keywords(new_text)
    old_snap = snapshots.get(firm_name)

    # Keyword-based assessment first
    if open_hits and not closed_hits:
        keyword_status = "CONFIRMED OPEN"
    elif open_hits and closed_hits:
        keyword_status = "MIXED"
    elif closed_hits:
        keyword_status = "CONFIRMED CLOSED"
    else:
        keyword_status = "NO KEYWORDS"

    # Page change detection
    change_status = "FIRST RUN"
    change_pct = 0
    if old_snap:
        sim = similarity(old_snap["text"], new_text)
        change_pct = round((1 - sim) * 100, 1)
        if change_pct >= 20:
            change_status = "SIGNIFICANT CHANGE"
        elif change_pct >= 8:
            change_status = "MINOR CHANGE"
        else:
            change_status = "NO CHANGE"

    # Final decision
    if keyword_status == "CONFIRMED OPEN":
        final = "LIKELY OPEN"
    elif keyword_status == "CONFIRMED CLOSED":
        final = "LIKELY CLOSED"
    elif change_status == "SIGNIFICANT CHANGE":
        final = "PAGE CHANGED — CHECK NOW"
    elif change_status == "MINOR CHANGE":
        final = "MINOR CHANGE"
    else:
        final = "NO CHANGE"

    return {
        "status": final,
        "keyword_status": keyword_status,
        "change_status": change_status,
        "change_pct": change_pct,
        "open_keywords": open_hits,
        "closed_keywords": closed_hits,
    }

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    print(f"Starting check — {datetime.datetime.now().isoformat()}")
    print(f"Checking {len(FIRMS)} firms with page change detection...")

    snapshots = load_snapshots()
    results = []
    urgent = []
    changed = []
    new_snapshots = dict(snapshots)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for i, firm in enumerate(FIRMS):
            name = firm["name"]
            print(f"[{i+1}/{len(FIRMS)}] {name}...")

            text, error = fetch_page(page, firm["url"])

            if error or not text:
                result = {
                    "firm": name, "role": firm["role"], "prob": firm["prob"],
                    "url": firm["url"], "status": "ERROR", "keyword_status": "ERROR",
                    "change_status": "ERROR", "change_pct": 0,
                    "open_keywords": [], "closed_keywords": [],
                    "checked_at": datetime.datetime.now().isoformat(),
                }
                print(f"  → ERROR: {error}")
            else:
                assessment = assess(name, text, snapshots)
                result = {
                    "firm": name, "role": firm["role"], "prob": firm["prob"],
                    "url": firm["url"],
                    "checked_at": datetime.datetime.now().isoformat(),
                    **assessment
                }
                print(f"  → {result['status']} | change: {result['change_pct']}% | keywords: {result['open_keywords'][:3]}")

                # Update snapshot
                new_snapshots[name] = {
                    "text": text[:50000],  # store first 50k chars
                    "hash": content_hash(text),
                    "captured_at": datetime.datetime.now().isoformat(),
                }

                if result["status"] == "LIKELY OPEN":
                    urgent.append(name)
                elif result["status"] in ["PAGE CHANGED — CHECK NOW", "MINOR CHANGE"]:
                    changed.append(name)

            results.append(result)
            time.sleep(2)

        browser.close()

    # Save updated snapshots
    save_snapshots(new_snapshots)

    # Save results
    output = {
        "checked_at": datetime.datetime.now().isoformat(),
        "summary": {
            "likely_open": urgent,
            "page_changed": changed,
            "total_checked": len(results),
        },
        "results": results,
    }
    with open(RESULTS_FILE, "w") as f:
        json.dump(output, f, indent=2)

    # Summary
    print("\n" + "="*60)
    print("CHECK COMPLETE")
    print(f"Likely open       : {', '.join(urgent) if urgent else 'none'}")
    print(f"Page changed      : {', '.join(changed) if changed else 'none'}")
    print(f"Total checked     : {len(results)}")
    print("="*60)

if __name__ == "__main__":
    main()

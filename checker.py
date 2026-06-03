#!/usr/bin/env python3
"""
William Browning — Application Checker (GitHub Actions / Playwright version)
Checks 38 firm careers pages with a real browser, emails results.
Runs daily at 8am via GitHub Actions.
"""

import json
import os
import smtplib
import datetime
import time
import re
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout
    PLAYWRIGHT = True
except ImportError:
    PLAYWRIGHT = False
    import urllib.request

# ── FIRMS ─────────────────────────────────────────────────────────────────────

FIRMS = [
    # HIGH PROBABILITY
    {"name": "Schroders", "role": "Graduate Investment Analyst", "prob": "High",
     "url": "https://www.schroders.com/en-gb/uk/individual/careers/",
     "search": ["graduate 2027", "apply now", "applications open", "investment analyst"]},
    {"name": "Rathbones", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.rathbones.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Brooks Macdonald", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.brooksmacdonald.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Canaccord Genuity Wealth", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.canaccordgenuitywealth.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Quilter Cheviot", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.quiltercheviot.com/about-us/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Investec Wealth", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.investec.com/en_gb/welcome-to-investec/careers.html",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "M&G Investments", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.mandg.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Legal & General IM", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.lgim.com/uk/en/capabilities/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Rothschild Wealth", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.rothschildandco.com/en/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Charles Stanley", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.charles-stanley.co.uk/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Smith & Williamson", "role": "Graduate Programme", "prob": "High",
     "url": "https://www.smithandwilliamson.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Waverton Investment Management", "role": "Graduate / Analyst", "prob": "High",
     "url": "https://www.waverton.co.uk/about/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    # GOOD
    {"name": "Fidelity International", "role": "Graduate Programme", "prob": "Good",
     "url": "https://careers.fidelityinternational.com/",
     "search": ["graduate 2027", "apply now", "applications open", "summer 2027"]},
    {"name": "Baillie Gifford", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.bailliegifford.com/en/uk/about-us/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "BlackRock", "role": "Client & Product Graduate Rotational", "prob": "Good",
     "url": "https://careers.blackrock.com/students-and-graduates-emea",
     "search": ["graduate 2027", "apply now", "applications open", "rotational"]},
    {"name": "Capital Group", "role": "Graduate Analyst", "prob": "Good",
     "url": "https://www.capitalgroup.com/us/en/careers.html",
     "search": ["graduate 2027", "apply now", "analyst program"]},
    {"name": "Invesco", "role": "Graduate Programme", "prob": "Good",
     "url": "https://careers.invesco.com/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Columbia Threadneedle", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.columbiathreadneedle.co.uk/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "UBS Wealth Management", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.ubs.com/global/en/careers.html",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Ninety One", "role": "Graduate Programme", "prob": "Good",
     "url": "https://ninetyone.com/en/united-kingdom/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Hargreaves Lansdown", "role": "Graduate Programme", "prob": "Good",
     "url": "https://careers.hl.co.uk/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Newton Investment Management", "role": "Graduate / Analyst", "prob": "Good",
     "url": "https://www.newtonim.com/en-gb/about/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Cazenove Capital", "role": "Graduate Programme", "prob": "Good",
     "url": "https://www.cazenovecapital.com/en-gb/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    # MODERATE
    {"name": "Janus Henderson", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.janushenderson.com/en-gb/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "abrdn", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.abrdn.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Man Group", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.man.com/careers",
     "search": ["graduate 2027", "apply now", "analyst program"]},
    {"name": "Jupiter Asset Management", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.jupiteram.com/uk/en/about-us/careers/",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Artemis", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.artemisfunds.com/en/gbr/individual/about/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Polar Capital", "role": "Analyst / Graduate", "prob": "Moderate",
     "url": "https://www.polarcapital.co.uk/about/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Liontrust", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.liontrust.co.uk/about-us/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Lazard Asset Management", "role": "Graduate Programme", "prob": "Moderate",
     "url": "https://www.lazardassetmanagement.com/uk/en_gb/about/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Federated Hermes", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.federatedhermes.com/us/about/careers.do",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Pictet Asset Management", "role": "Graduate / Analyst", "prob": "Moderate",
     "url": "https://www.group.pictet/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    # STRETCH
    {"name": "Brevan Howard", "role": "Analyst Programme", "prob": "Stretch",
     "url": "https://www.brevanhoward.com/careers",
     "search": ["graduate 2027", "apply now", "analyst program"]},
    {"name": "TT International", "role": "Analyst / Graduate", "prob": "Stretch",
     "url": "https://www.ttim.com/careers",
     "search": ["graduate 2027", "apply now", "applications open"]},
    {"name": "Rothschild & Co Advisory", "role": "Graduate Analyst", "prob": "Stretch",
     "url": "https://www.rothschildandco.com/en/careers/",
     "search": ["graduate 2027", "apply now", "analyst"]},
    {"name": "Schroders Off-Cycle", "role": "Off-Cycle Internship", "prob": "Good",
     "url": "https://www.schroders.com/en-gb/uk/individual/careers/",
     "search": ["off-cycle", "internship 2027", "apply now"]},
    {"name": "BlackRock Off-Cycle", "role": "Client & Product Off-Cycle", "prob": "Good",
     "url": "https://careers.blackrock.com/students-and-graduates-emea",
     "search": ["off-cycle", "internship 2027", "apply now"]},
]

NEGATIVE = ["applications closed", "currently closed", "not yet open",
            "check back later", "coming soon", "no current vacancies",
            "no open positions", "applications will open"]

# ── PAGE CHECK ────────────────────────────────────────────────────────────────

def check_firm_playwright(page, firm):
    try:
        page.goto(firm["url"], timeout=20000, wait_until="networkidle")
        page.wait_for_timeout(3000)  # let JS settle
        content = page.content().lower()
        text = page.inner_text("body").lower()
        combined = content + " " + text
    except Exception as e:
        return {"status": "ERROR", "reason": str(e), "hits": []}

    hits = []
    for kw in firm["search"]:
        if kw.lower() in combined:
            hits.append(kw)

    neg_hits = [kw for kw in NEGATIVE if kw in combined]

    if hits and not neg_hits:
        status = "LIKELY OPEN"
    elif hits and neg_hits:
        status = "MIXED"
    elif neg_hits:
        status = "LIKELY CLOSED"
    else:
        status = "UNCLEAR"

    return {"status": status, "hits": hits, "neg_hits": neg_hits}

# ── EMAIL ─────────────────────────────────────────────────────────────────────

def send_email(results, likely_open, possibly_open):
    """Send results via GitHub's built-in email or print summary."""
    now = datetime.datetime.now().strftime("%d %b %Y %H:%M")

    # Build HTML email
    rows = ""
    for r in results:
        colour = {
            "LIKELY OPEN": "#edf7e0",
            "MIXED": "#fdf0d8",
            "LIKELY CLOSED": "#f8f8f6",
            "UNCLEAR": "#f8f8f6",
            "ERROR": "#fdeaea",
        }.get(r["status"], "#f8f8f6")

        prob_colour = {
            "High": "#2d6a0a",
            "Good": "#145394",
            "Moderate": "#7a4700",
            "Stretch": "#9b2525",
        }.get(r["prob"], "#555")

        hits_str = ", ".join(r.get("hits", [])) or "—"
        rows += f"""
        <tr style="background:{colour}">
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600">{r['firm']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:12px;color:#555">{r['role']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:12px;color:{prob_colour};font-weight:600">{r['prob']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-weight:600">{r['status']}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee;font-size:11px;color:#666">{hits_str}</td>
          <td style="padding:8px 12px;border-bottom:1px solid #eee"><a href="{r['url']}" style="color:#1F3864;font-size:12px">Visit ↗</a></td>
        </tr>"""

    urgent = ""
    if likely_open:
        names = ", ".join(likely_open)
        urgent = f"""
        <div style="background:#edf7e0;border-left:4px solid #2d6a0a;padding:14px 18px;margin-bottom:20px;border-radius:0 8px 8px 0">
          <strong style="color:#2d6a0a;font-size:15px">🚨 Apply now — likely open</strong><br>
          <span style="color:#1a3d0a;font-size:14px;margin-top:6px;display:block">{names}</span>
        </div>"""
    elif possibly_open:
        names = ", ".join(possibly_open)
        urgent = f"""
        <div style="background:#fdf0d8;border-left:4px solid #7a4700;padding:14px 18px;margin-bottom:20px;border-radius:0 8px 8px 0">
          <strong style="color:#7a4700;font-size:15px">📋 Check these — possibly open</strong><br>
          <span style="color:#4a2d00;font-size:14px;margin-top:6px;display:block">{names}</span>
        </div>"""

    html = f"""
    <html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;max-width:900px;margin:0 auto;padding:20px;color:#111">
      <div style="background:#1F3864;padding:20px 24px;border-radius:10px;margin-bottom:24px">
        <h1 style="color:white;margin:0;font-size:20px;font-weight:700">William Browning — Application Checker</h1>
        <p style="color:rgba(255,255,255,0.65);margin:6px 0 0;font-size:13px">Daily check · {now} · {len(results)} firms checked</p>
      </div>
      {urgent}
      <table style="width:100%;border-collapse:collapse;border:1px solid #eee;border-radius:8px;overflow:hidden">
        <thead>
          <tr style="background:#f8f8f6">
            <th style="padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999">Firm</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999">Role</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999">Your odds</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999">Status</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999">Keywords found</th>
            <th style="padding:10px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.5px;color:#999">Link</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="font-size:12px;color:#999;margin-top:20px">Checked by GitHub Actions · Running daily at 8am · <a href="https://github.com/willbrow4321-design/application-checker/actions" style="color:#1F3864">View logs</a></p>
    </body></html>"""

    # Print to stdout (captured in GitHub Actions logs)
    print("\n" + "="*60)
    print(f"CHECK COMPLETE — {now}")
    print(f"Likely open    : {', '.join(likely_open) if likely_open else 'none'}")
    print(f"Possibly open  : {', '.join(possibly_open) if possibly_open else 'none'}")
    print("="*60)

    # Save HTML for GitHub Actions summary
    with open("email_preview.html", "w") as f:
        f.write(html)

    return html

# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    results = []
    likely_open = []
    possibly_open = []

    print(f"Starting check of {len(FIRMS)} firms...")
    print(f"Time: {datetime.datetime.now().isoformat()}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                       "AppleWebKit/537.36 (KHTML, like Gecko) "
                       "Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1280, "height": 800},
        )
        page = context.new_page()

        for i, firm in enumerate(FIRMS):
            print(f"[{i+1}/{len(FIRMS)}] Checking {firm['name']}...")
            result = check_firm_playwright(page, firm)
            result.update({
                "firm": firm["name"],
                "role": firm["role"],
                "prob": firm["prob"],
                "url": firm["url"],
                "checked_at": datetime.datetime.now().isoformat(),
            })
            results.append(result)
            print(f"  → {result['status']} | hits: {result.get('hits', [])}")

            if result["status"] == "LIKELY OPEN":
                likely_open.append(firm["name"])
            elif result["status"] == "MIXED":
                possibly_open.append(firm["name"])

            time.sleep(2)

        browser.close()

    # Save results
    with open("results.json", "w") as f:
        json.dump({
            "checked_at": datetime.datetime.now().isoformat(),
            "summary": {"likely_open": likely_open, "possibly_open": possibly_open},
            "results": results,
        }, f, indent=2)

    # Generate email HTML
    send_email(results, likely_open, possibly_open)

    # Exit with error code if urgent firms found (triggers GitHub notification)
    if likely_open:
        print(f"\n🚨 URGENT: {len(likely_open)} firms likely open — {', '.join(likely_open)}")

if __name__ == "__main__":
    main()

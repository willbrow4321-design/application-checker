# William Browning — Application Checker

Checks 38 asset management and wealth management careers pages daily using a real browser (Playwright/Chromium). Runs automatically at 8am UK time via GitHub Actions.

## How it works

1. GitHub Actions spins up a server at 8am every morning
2. Playwright opens each of the 38 careers pages with a real Chromium browser
3. JavaScript runs, dynamic content loads — exactly what a human would see
4. Each page is scanned for keywords indicating live applications
5. Results are saved and you get an email if anything looks open

## Setup (one time only — follow these steps)

### Step 1 — Enable GitHub Actions emails
1. Go to github.com and sign in
2. Click your profile photo → Settings
3. Click Notifications (left sidebar)
4. Under "Actions" make sure email notifications are turned on
5. Set it to notify you on "Failed workflows" AND "Successful workflows"

### Step 2 — Enable the workflow
1. Go to your repository on GitHub
2. Click the "Actions" tab
3. Click "I understand my workflows, go ahead and enable them"

### Step 3 — Test it manually
1. Go to Actions tab
2. Click "Daily Application Checker" on the left
3. Click "Run workflow" → "Run workflow"
4. Watch it run in real time

### Step 4 — It runs automatically from here
Every morning at 8am UK time it runs automatically. You'll get a GitHub notification email with the results.

## Reading results
- **LIKELY OPEN** — keywords found, no negative signals. Visit the portal immediately.
- **MIXED** — some positive and negative signals. Worth checking manually.
- **LIKELY CLOSED** — negative keywords found. Check back in a few weeks.
- **UNCLEAR** — no strong signals either way. Check manually once a week.

## Viewing past results
Go to Actions tab → click any run → scroll down to Artifacts → download results.json

# The One-Person LLC AI Playbook

A friendly operating manual for running a one-person LLC with AI as the co-pilot — written the way Asdale Dynamics, LLC writes everything: plain English, step by step, never condescending.

**The one rule: AI drafts. You decide.**

## What's inside

| Chapter | Covers |
|---|---|
| [Email drafts](docs/emails.md) | Drafting reader/customer emails with AI, without sounding like a robot |
| [The monthly money-date](docs/money-date.md) | A 60-minute monthly routine for looking at your numbers calmly |
| [Decision journal](docs/decision-journal.md) | A tiny log that makes every big decision smarter |
| [Simple SOPs](docs/sops.md) | Checklists so routine tasks stop living in your head |
| [Marketing calendar](docs/marketing-calendar.md) | A light 3-3-1 weekly rhythm plus year anchors |
| [Reply templates](docs/reply-templates.md) | Copy-paste starting points for the messages you get every week |
| [Honest limits](docs/honest-limits.md) | When NOT to trust AI — the most important chapter |
| [Worksheets](docs/worksheets/index.md) | Blank, print-ready versions of every template |

## Run it

Everything is markdown + a zero-dependency Python build script. No accounts, no API keys, no cloud. Local-first.

```bash
python3 build.py            # build the static site into site/
python3 build.py --check    # build, verify every internal link, then clean up (CI-style test)
python3 -m http.server -d site 8000   # optional: browse at http://localhost:8000
```

Requires Python 3.9+ (stdlib only). The chapters under `docs/` read fine as plain markdown; the site output is for reading or hosting anywhere static.

## Relationship to cashflow-simple-ledger

This playbook **complements, and deliberately does not repeat**, the bookkeeping material in [cashflow-simple-ledger](../cashflow-simple-ledger). That project is the ledger — the how and where of tracking income and expenses. This manual's money-date chapter adds the habit: the 60-minute monthly ritual, the six questions, and how AI can act as a calm reviewer without ever becoming an accountant.

## Colophon

Copyright (c) 2026 Asdale Dynamics, LLC. Released under the MIT license (see [LICENSE](LICENSE)). Built from local markdown files by `build.py` — no secrets, no personal data, no build-time network calls.

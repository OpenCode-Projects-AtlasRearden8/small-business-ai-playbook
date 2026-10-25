# STATUS

## What was built

**The One-Person LLC AI Playbook** — a complete operating manual for running a one-person LLC (Asdale Dynamics, LLC) with AI as the co-pilot, in a warm plain-English voice ("AI drafts. You decide.").

### Content (`docs/`, markdown)

- `index.md` — start-here page, roadmap, the one rule
- `emails.md` — the three-step process for AI-drafted reader/customer emails, 60-second send pass, prompt library pattern
- `money-date.md` — 60-minute monthly money routine (the six questions, AI-as-reviewer boundaries). Explicitly complements — and points to, without repeating — **cashflow-simple-ledger** for the bookkeeping itself
- `decision-journal.md` — before-the-outcome decision log, grading ritual, AI friction-testing only
- `sops.md` — 8-line SOP format with gotchas section, living-update rules
- `marketing-calendar.md` — 3-3-1 weekly rhythm, four year anchors, monthly 15-minute review
- `reply-templates.md` — 8 copy-paste reply templates (questions, declines, refunds both ways, mistakes, collabs)
- `honest-limits.md` — when NOT to trust AI: never for tax/legal/medical, the 3-question fact check, flavor-warning list
- `worksheets/` — 5 print-ready worksheet templates + index

### Tooling

- `build.py` — zero-dependency (Python stdlib only) static site generator: markdown → styled HTML with sidebar nav, prev/next, link rewriting, and a link/fragment verifier that fails the build on any broken internal link
- `site/` — generated output (gitignored), self-contained, no external assets

### Meta

- `LICENSE` — MIT, copyright line exactly "Copyright (c) 2026 Asdale Dynamics, LLC"
- `README.md` — run instructions, credits Asdale Dynamics, LLC
- No secrets, API keys, or personal data anywhere. Local-first: no accounts, no network at build or run time.

## How to run it

```bash
python3 build.py                    # build site/ and verify all internal links
python3 build.py --check            # build + verify, then remove site/ (test artifacts)
python3 -m http.server -d site 8000 # optional local preview
```

Requires Python 3.9+. Nothing else.

## Verification results

- `python3 build.py` → **Build OK — 14 pages, all internal links verified.**
- `python3 build.py --check` → passes (build, verify, clean up)
- Serving test with `python3 -m http.server`: `/`, `/emails.html`, `/honest-limits.html`, `/reply-templates.html`, `/worksheets/money-date-worksheet.html` all returned **200**
- Rendered-output spot checks: headings, tables, blockquotes, code blocks, and heading anchors (e.g. `#3-the-60-second-pass`) all convert correctly; no unconverted markdown leftovers in any page
- Link checker previously caught a real bug (stem collision between `docs/index.md` and `docs/worksheets/index.md`) — fixed with directory-aware page keys

## Known gaps

- The markdown converter is deliberately minimal: supports the subset used by this manual (headings h1–h4, lists, checkboxes, tables, blockquotes, code fences, inline formatting, links). It is not a full CommonMark implementation — exotic markdown (nested lists, footnotes, image syntax) is not promised and untested
- No search, RSS, or dark mode in the site chrome
- No automated test suite beyond the built-in build/link verification; there is no external HTML-validation dependency (kept stdlib-only by design)
- The `cashflow-simple-ledger` cross-reference is textual; this repo makes no assumption about that project's location or API
- Site output is gitignored (regenerate with `build.py`); anyone wanting to publish statically would run the build first

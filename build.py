#!/usr/bin/env python3
"""Build the static HTML site from docs/ into site/.

Zero external dependencies (Python standard library only), local-first:
run it, get a self-contained site you can open from disk or host anywhere.

Usage:
    python3 build.py            # build site/ and verify every internal link
    python3 build.py --check    # build, verify, then remove site/ (test without artifacts)
"""

import html
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
SITE = ROOT / "site"

MANUAL_ORDER = [
    "index",
    "emails",
    "money-date",
    "decision-journal",
    "sops",
    "marketing-calendar",
    "reply-templates",
    "honest-limits",
]
WORKSHEETS_ORDER = [
    "index",
    "money-date-worksheet",
    "decision-journal-template",
    "sop-template",
    "marketing-calendar-worksheet",
    "email-drafts-worksheet",
]

# (group title, ordered keys, output directory, per-group title overrides)
NAV_GROUPS = [
    ("The Playbook", MANUAL_ORDER, "", {}),
    ("Worksheets", WORKSHEETS_ORDER, "worksheets/", {"index": "All worksheets"}),
]

NAV_TITLES = {
    "index": "Start here",
    "emails": "Email drafts",
    "money-date": "The monthly money-date",
    "decision-journal": "Decision journal",
    "sops": "Simple SOPs",
    "marketing-calendar": "Marketing calendar",
    "reply-templates": "Reply templates",
    "honest-limits": "Honest limits",
    "money-date-worksheet": "Money-date worksheet",
    "decision-journal-template": "Decision journal template",
    "sop-template": "SOP template",
    "marketing-calendar-worksheet": "Marketing calendar",
    "email-drafts-worksheet": "Email drafts worksheet",
}

WORKSHEET_STEMS = set(WORKSHEETS_ORDER)
MANUAL_STEMS = set(MANUAL_ORDER)

CSS = """\
:root{--bg:#faf6ef;--ink:#2b2620;--soft:#6b6058;--accent:#b05c2e;--line:#e8dfd2;--card:#fffdf8}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--ink);font:17px/1.65 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif}
a{color:var(--accent);text-decoration:none}
a:hover{text-decoration:underline}
code{background:#f1e8da;border-radius:4px;padding:.1em .35em;font-size:.9em}
pre{background:#f6efe3;border:1px solid var(--line);border-radius:8px;padding:1rem .9rem;overflow-x:auto;font-size:.86em;line-height:1.5}
pre code{background:none;padding:0}
.wrap{display:flex;max-width:1080px;margin:0 auto;min-height:100vh}
aside{width:240px;padding:2rem 1.2rem;border-right:1px solid var(--line);background:var(--card)}
aside .brand{font-family:Georgia,serif;font-size:1.15rem;font-weight:700;color:var(--ink);display:block;margin-bottom:.2rem}
aside .brand-sub{font-size:.8rem;color:var(--soft);display:block;margin-bottom:1.6rem}
aside h3{font-size:.72rem;letter-spacing:.09em;text-transform:uppercase;color:var(--soft);margin:1.4rem 0 .45rem}
aside ul{list-style:none;margin:0;padding:0}
aside li a{display:block;padding:.28rem .5rem;border-radius:6px;font-size:.92rem;color:var(--ink)}
aside li a:hover{background:#f1e8da;text-decoration:none}
aside li a.active{background:#eaddca;font-weight:600;color:var(--accent)}
main{flex:1;padding:2.5rem 3rem;max-width:820px}
main h1{font-family:Georgia,serif;font-size:2rem;line-height:1.25;margin:0 0 1.2rem}
main h2{font-family:Georgia,serif;font-size:1.4rem;margin:2.2rem 0 .6rem;border-bottom:1px solid var(--line);padding-bottom:.3rem}
main h3{font-size:1.08rem;margin:1.6rem 0 .5rem}
main p,main li{color:#3c3630}
main blockquote{border-left:3px solid var(--accent);margin:1.2rem 0;padding:.5rem 1rem;background:var(--card);border-radius:0 8px 8px 0;color:var(--soft)}
main blockquote p{margin:.2rem 0;color:inherit}
main table{border-collapse:collapse;width:100%;margin:1.2rem 0;font-size:.92rem}
main th,main td{border:1px solid var(--line);padding:.45rem .6rem;text-align:left;vertical-align:top}
main th{background:var(--card)}
main hr{border:none;border-top:1px solid var(--line);margin:2.5rem 0 1.4rem}
main .pn{display:flex;justify-content:space-between;gap:1rem;margin-top:3rem;border-top:1px solid var(--line);padding-top:1rem}
main .pn a{font-size:.92rem}
main .pn .prev{color:var(--soft)}
.fine{font-size:.78rem;color:var(--soft);margin-top:2.5rem}
footer{padding:1.2rem 3rem;font-size:.78rem;color:var(--soft);border-top:1px solid var(--line)}
li .cbx{color:var(--accent);font-weight:700}
@media(max-width:760px){.wrap{display:block}aside{width:auto;border-right:none;border-bottom:1px solid var(--line)}main,footer{padding:1.6rem 1.2rem}}
"""


def slugify(text: str) -> str:
    s = re.sub(r"[^\w\s-]", "", text.lower())
    return re.sub(r"\s+", "-", s.strip()).strip("-")


def resolve_link(target: str, page_dir: str) -> str:
    """Resolve a markdown link to a path relative to the page's location in site/.

    Inside a page, links may be written bare (stem only) or fully (worksheets/...).
    Manual pages live at site root; worksheets at site/worksheets/.
    """
    core, _, frag = target.partition("#")
    if core.startswith(("http://", "https://", "mailto:")):
        return target
    stem = core.rsplit("/", 1)[-1]
    if stem.endswith(".html"):
        stem = stem[:-5]
    stem = stem[:-3] if stem.endswith(".md") else stem
    if stem in WORKSHEET_STEMS:
        rel = f"{stem}.html" if page_dir else f"worksheets/{stem}.html"
    elif stem in MANUAL_STEMS:
        rel = ("../" if page_dir else "") + f"{stem}.html"
    else:
        rel = core  # unknown target: keep as-is, the verifier will flag it if broken
    return f"{rel}#{frag}" if frag else rel


def inline(text: str, page_dir: str) -> str:
    """Escape HTML then apply inline markdown."""
    out = html.escape(text, quote=False)
    out = re.sub(r"`([^`]+)`", r"<code>\1</code>", out)
    out = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", out)
    out = re.sub(r"\*([^*]+)\*", r"<em>\1</em>", out)
    out = re.sub(
        r"\[([^\]]+)\]\(([^)]+)\)",
        lambda m: f'<a href="{resolve_link(m.group(2), page_dir)}">{m.group(1)}</a>',
        out,
    )
    return out


def convert_blocks(md_text: str, page_dir: str):
    """Convert markdown to an HTML body. Returns (html, set of heading anchors)."""
    lines = md_text.splitlines()
    out = []
    i = 0
    n = len(lines)
    para = []
    anchors = set()

    def flush_para():
        if para:
            out.append(f"<p>{inline(' '.join(para), page_dir)}</p>")
            para.clear()

    while i < n:
        raw = lines[i]
        stripped = raw.strip()

        if stripped.startswith("```"):
            flush_para()
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # closing fence
            out.append(f"<pre><code>{html.escape(chr(10).join(code))}</code></pre>")
            continue

        m = re.match(r"^(#{1,4}) (.*)$", stripped)
        if m:
            flush_para()
            level = len(m.group(1))
            text = inline(m.group(2), page_dir)
            id_ = slugify(re.sub(r"[<!`*_]", "", m.group(2)))
            anchors.add(id_)
            out.append(f'<h{level} id="{id_}">{text}</h{level}>')
            i += 1
            continue

        if re.fullmatch(r"-{3,}", stripped):
            flush_para()
            out.append("<hr>")
            i += 1
            continue

        # Table: consecutive "|" lines, second one a separator
        if stripped.startswith("|") and i + 1 < n and re.fullmatch(r"\|[\s:|-]+\|", lines[i + 1].strip()):
            flush_para()
            header = [c.strip() for c in stripped.strip("|").split("|")]
            i += 2
            rows = []
            while i < n and lines[i].strip().startswith("|"):
                rows.append([c.strip() for c in lines[i].strip().strip("|").split("|")])
                i += 1
            cell = lambda c: inline(c.strip(), page_dir)
            head_html = "".join(f"<th>{cell(c)}</th>" for c in header)
            body_rows = "".join(
                "<tr>" + "".join(f"<td>{cell(c)}</td>" for c in row) + "</tr>" for row in rows
            )
            out.append(f"<table><thead><tr>{head_html}</tr></thead><tbody>{body_rows}</tbody></table>")
            continue

        m = re.match(r"^[-*] (.*)$", stripped)
        if m:
            flush_para()
            items = []
            while i < n and re.match(r"[-*] ", lines[i].strip()):
                item = re.sub(r"^[-*] ", "", lines[i].strip())
                cm = re.match(r"^\[([ xX])\] (.*)$", item)
                if cm:
                    mark = "[x]" if cm.group(1).lower() == "x" else "[ ]"
                    item = f'<span class="cbx">{mark}</span> {cm.group(2)}'
                items.append(inline(item, page_dir))
                i += 1
            out.append("<ul>" + "".join(f"<li>{x}</li>" for x in items) + "</ul>")
            continue

        m = re.match(r"^\d+\.\s+(.*)$", stripped)  # NOSONAR ordered list
        if m:
            flush_para()
            items = []
            while i < n and re.match(r"^\d+\.\s+", lines[i].strip()):
                items.append(inline(re.sub(r"^\d+\.\s+", "", lines[i].strip()), page_dir))
                i += 1
            out.append("<ol>" + "".join(f"<li>{x}</li>" for x in items) + "</ol>")
            continue

        if stripped.startswith(">"):
            flush_para()
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(re.sub(r"^>\s?", "", lines[i].strip()))
                i += 1
            out.append(f"<blockquote><p>{inline(' '.join(quote), page_dir)}</p></blockquote>")
            continue

        if not stripped:
            flush_para()
            i += 1
            continue

        para.append(stripped)
        i += 1

    flush_para()
    return "\n".join(out), anchors


def nav_html(current_output: str) -> str:
    in_worksheets = current_output.startswith("worksheets/")
    parts = []
    for group_title, order, out_dir, title_overrides in NAV_GROUPS:
        parts.append(f"<h3>{html.escape(group_title)}</h3><ul>")
        for key in order:
            out_rel = f"{out_dir}{key}.html"
            rel = (f"../{out_rel}" if in_worksheets else out_rel)
            label = title_overrides.get(key, NAV_TITLES.get(key, key))
            cls = ' class="active"' if out_rel == current_output else ""
            parts.append(f'<li><a href="{rel}"{cls}>{html.escape(label)}</a></li>')
        parts.append("</ul>")
    return "".join(parts)


def prevnext(current_output: str, page_dir: str, prev_key, next_key) -> str:
    if not prev_key and not next_key:
        return ""
    parts = []
    prefix = "../" if current_output.startswith("worksheets/") else ""
    if prev_key:
        parts.append(
            f'<a href="{prefix}{page_dir}{prev_key}.html" class="prev">&larr; '
            f"{html.escape(NAV_TITLES.get(prev_key, prev_key))}</a>"
        )
    if next_key:
        parts.append(
            f'<a href="{prefix}{page_dir}{next_key}.html">'
            f"{html.escape(NAV_TITLES.get(next_key, next_key))} &rarr;</a>"
        )
    return f'<div class="pn">{"".join(parts)}</div>'


def render_page(body_html: str, key: str, page_dir: str, out_rel: str, prev_key, next_key) -> str:
    title = NAV_TITLES.get(key, key.title())
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(title)} — The One-Person LLC AI Playbook</title>
<meta name="generator" content="build.py — local-first, stdlib-only">
<style>{CSS}</style>
</head>
<body>
<div class="wrap">
<aside>
  <span class="brand">The One-Person LLC AI Playbook</span>
  <span class="brand-sub">AI drafts. You decide.</span>
  {nav_html(out_rel)}
</aside>
<main>
{body_html}
{prevnext(out_rel, page_dir, prev_key, next_key)}
<p class="fine">Copyright (c) 2026 Asdale Dynamics, LLC — plain-English AI education, local-first.</p>
</main>
</div>
<footer>Asdale Dynamics, LLC · built from local markdown · no accounts, no keys, no cloud required</footer>
</body>
</html>
"""


def collect_links(content: str):
    return re.findall(r'(?:href)="([^"]+)"', content), re.findall(r'id="([^"]+)"', content)


def verify(generated: dict):
    """Check that every internal href resolves to an existing page (and fragment)."""
    problems = []
    for out_rel, content in generated.items():
        hrefs, ids = collect_links(content)
        id_set = set(ids)
        base_dir = os.path.dirname(out_rel)
        for ref in hrefs:
            if ref.startswith(("http://", "https://", "mailto:")):
                continue
            path, _, frag = ref.partition("#")
            if not path:
                if frag and frag not in id_set and not frag.startswith("fn"):
                    problems.append(f"{out_rel}: missing fragment #{frag}")
                continue
            if ".html" not in path and not path.endswith((".css", ".js", ".svg", ".png")):
                continue
            target = os.path.normpath(os.path.join(SITE, base_dir, path))
            if not os.path.exists(target):
                problems.append(f"{out_rel}: broken link -> {ref}")
                continue
            if frag and f'id="{frag}"' not in Path(target).read_text(encoding="utf-8"):
                problems.append(f"{out_rel}: fragment #{frag} missing in {path}")
    return problems


def build() -> list:
    """Build the site. Returns a list of problems (empty list = success)."""
    problems = []
    if not DOCS.is_dir():
        return ["docs/ directory missing"]
    md_files = sorted(DOCS.rglob("*.md"))
    if not md_files:
        return ["docs/ contains no markdown files"]

    if SITE.exists():
        shutil.rmtree(SITE)
    SITE.mkdir(parents=True)

    # Convert every markdown file. Key pages by their output path (dir-aware,
    # so docs/index.md and docs/worksheets/index.md never collide).
    parsed = {}
    for md in md_files:
        page_dir = "worksheets/" if md.parent.name == "worksheets" else ""
        expected_rel = f"{page_dir}{md.stem}.html"
        if expected_rel in parsed:
            problems.append(f"duplicate page key: {expected_rel}")
            continue
        body, anchors = convert_blocks(md.read_text(encoding="utf-8"), page_dir)
        parsed[expected_rel] = (body, anchors, page_dir)

    for group_title, order, out_dir, _ in NAV_GROUPS:
        members = [k for k in order if f"{out_dir}{k}.html" in parsed]
        for key in [k for k in order if k not in members]:
            problems.append(f"expected page missing: {out_dir}{key}.md")
        for idx, key in enumerate(members):
            out_rel = f"{out_dir}{key}.html"
            body, anchors, page_dir = parsed[out_rel]
            prev_key = members[idx - 1] if idx > 0 else None
            next_key = members[idx + 1] if idx < len(members) - 1 else None
            content = render_page(body, key, page_dir, out_rel, prev_key, next_key)
            out_path = SITE / out_rel
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(content, encoding="utf-8")

    generated = {
        str(p.relative_to(SITE)): p.read_text(encoding="utf-8")
        for p in sorted(SITE.rglob("*.html"))
    }
    problems.extend(verify(generated))

    # Anchors referenced in markdown must exist on the target page.
    for md in md_files:
        text = md.read_text(encoding="utf-8")
        for page, frag in re.findall(r"\]\(([^)#]+\.html)#([^)]+)\)", text):
            base = (SITE / ("worksheets/" if "/" in page else "") / page).resolve()
            if base.exists() and f'id="{frag}"' not in base.read_text(encoding="utf-8"):
                problems.append(f"{md.name}: fragment #{frag} missing in {page}")
    return problems


def main():
    check_only = "--check" in sys.argv
    problems = build()
    if problems:
        print(f"BUILD FAILED — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        if check_only and SITE.exists():
            shutil.rmtree(SITE)
        sys.exit(1)
    n_pages = len(list(SITE.rglob("*.html")))
    if check_only:
        shutil.rmtree(SITE)
    print(f"Build OK — {n_pages} pages, all internal links verified.")
    if check_only:
        print("Check mode: site/ removed after successful verification.")


if __name__ == "__main__":
    main()

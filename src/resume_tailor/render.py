"""Render a resume markdown file to PDF (plan-review gap #1, 2026-07-19).

One-page by default (Gary, 2026-07-27): a mid-level resume should fit one page —
it's a benefit for the *human* skimming it, not for the ATS parser (which reads
text regardless of length). See docs/reference/resume-style-guide.md.

Pipeline: markdown (frontmatter + fact-ref comments stripped) -> styled HTML
-> Chromium print-to-PDF via Playwright. To reach one page the renderer first
applies a dense ATS-safe stylesheet, then, if still overflowing, trims each
role to its top-N bullets (the .md keeps every bullet — only the PDF is capped;
after tailoring reorders strongest-first, top-N is the most relevant N).
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown as md_lib

from resume_tailor.validation import parse_resume

_FACT_REF_RE = re.compile(r"\s*<!--\s*facts:[^>]*-->")
_ROLE_RE = re.compile(r"^### ")
_BULLET_RE = re.compile(r"^\s*[-*]\s+")

# Dense but ATS-safe: single column, real text, standard serif, no tables/graphics.
_CSS = """
  @page { size: Letter; margin: 0.42in 0.6in; }
  body { font-family: Georgia, 'Times New Roman', serif; font-size: 10pt;
         line-height: 1.24; color: #111; }
  h1 { font-size: 16pt; margin: 0 0 1pt; letter-spacing: 0.01em; }
  h1 + p { margin-top: 0; }
  h2 { font-size: 10.5pt; text-transform: uppercase; letter-spacing: 0.08em;
       border-bottom: 0.75pt solid #999; padding-bottom: 1.5pt; margin: 9pt 0 4pt; }
  h3 { font-size: 10pt; margin: 5pt 0 1pt; }
  p { margin: 3pt 0; }
  ul { margin: 1pt 0 4pt; padding-left: 15pt; }
  li { margin-bottom: 1.5pt; }
"""


def cap_bullets_per_role(body: str, max_bullets: int) -> str:
    """Keep only the first `max_bullets` bullet lines under each `### role`.

    Bullets before the first role heading (rare) are untouched. Whole bullets
    are dropped, so fact-citations stay intact. `max_bullets<=0` = no cap.
    """
    if max_bullets <= 0:
        return body
    out, kept, in_role = [], 0, False
    for line in body.splitlines():
        if _ROLE_RE.match(line):
            in_role, kept = True, 0
            out.append(line)
        elif in_role and _BULLET_RE.match(line):
            kept += 1
            if kept <= max_bullets:
                out.append(line)
        else:
            if line.startswith("## "):  # a new top-level section ends role-capping
                in_role = False
            out.append(line)
    return "\n".join(out)


def resume_to_html(text: str, max_bullets_per_role: int = 0) -> str:
    """Frontmattered resume markdown -> full HTML document (fact refs stripped)."""
    _, body = parse_resume(text)
    body = cap_bullets_per_role(body, max_bullets_per_role)
    body = _FACT_REF_RE.sub("", body)
    html_body = md_lib.markdown(body)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{html_body}</body></html>"
    )


def count_pdf_pages(path: Path) -> int:
    from pypdf import PdfReader

    return len(PdfReader(str(path)).pages)


def _write_pdf(html: str, out_path: Path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(path=str(out_path), format="Letter", print_background=True)
        browser.close()


def render_pdf(
    resume_path: Path,
    out_path: Path | None = None,
    *,
    one_page: bool = True,
    min_bullets_per_role: int = 3,
) -> tuple[Path, int]:
    """Render a resume .md to PDF. Returns (path, page_count).

    one_page=True (default): render full, and if it overflows one page, trim each
    role's bullets down step by step (never below `min_bullets_per_role`) until it
    fits or the floor is reached. The source .md is never modified.
    """
    out_path = out_path or resume_path.with_suffix(".pdf")
    text = resume_path.read_text()

    _write_pdf(resume_to_html(text), out_path)
    pages = count_pdf_pages(out_path)
    if not one_page or pages <= 1:
        return out_path, pages

    # too long: count the largest role, trim from there down to the floor
    _, body = parse_resume(text)
    max_role_bullets = max(
        (sum(1 for _ in g) for g in _role_bullet_groups(body)), default=0
    )
    for cap in range(max_role_bullets - 1, min_bullets_per_role - 1, -1):
        _write_pdf(resume_to_html(text, max_bullets_per_role=cap), out_path)
        pages = count_pdf_pages(out_path)
        if pages <= 1:
            return out_path, pages
    return out_path, pages  # best effort at the floor


def _role_bullet_groups(body: str):
    group, in_role = [], False
    for line in body.splitlines():
        if _ROLE_RE.match(line):
            if group:
                yield group
            group, in_role = [], True
        elif in_role and _BULLET_RE.match(line):
            group.append(line)
        elif line.startswith("## "):
            if group:
                yield group
            group, in_role = [], False
    if group:
        yield group

"""Render a resume markdown file to PDF (plan-review gap #1, 2026-07-19).

Pipeline: markdown (frontmatter + fact-ref comments stripped) -> styled HTML
-> Chromium print-to-PDF via Playwright (already a project dependency).
ATS-friendly: single column, real text (selectable/parseable), standard fonts.
"""

from __future__ import annotations

import re
from pathlib import Path

import markdown as md_lib

from resume_tailor.validation import parse_resume

_FACT_REF_RE = re.compile(r"\s*<!--\s*facts:[^>]*-->")

# Deliberately plain: ATS parsers choke on columns, tables, and graphics.
_CSS = """
  @page { size: Letter; margin: 0.55in 0.7in; }
  body { font-family: Georgia, 'Times New Roman', serif; font-size: 10.5pt;
         line-height: 1.38; color: #111; }
  h1 { font-size: 17pt; margin: 0 0 2pt; letter-spacing: 0.02em; }
  h1 + p { margin-top: 0; }
  h2 { font-size: 11pt; text-transform: uppercase; letter-spacing: 0.09em;
       border-bottom: 1pt solid #999; padding-bottom: 2pt; margin: 13pt 0 6pt; }
  h3 { font-size: 10.5pt; margin: 8pt 0 2pt; }
  p { margin: 4pt 0; }
  ul { margin: 2pt 0 6pt; padding-left: 16pt; }
  li { margin-bottom: 2.5pt; }
"""


def resume_to_html(text: str) -> str:
    """Frontmattered resume markdown -> full HTML document (fact refs stripped)."""
    _, body = parse_resume(text)
    body = _FACT_REF_RE.sub("", body)
    html_body = md_lib.markdown(body)
    return (
        "<!doctype html><html><head><meta charset='utf-8'>"
        f"<style>{_CSS}</style></head><body>{html_body}</body></html>"
    )


def render_pdf(resume_path: Path, out_path: Path | None = None) -> Path:
    """Render one resume .md to a PDF next to it (or at out_path)."""
    from playwright.sync_api import sync_playwright

    out_path = out_path or resume_path.with_suffix(".pdf")
    html = resume_to_html(resume_path.read_text())
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.set_content(html, wait_until="load")
        page.pdf(path=str(out_path), format="Letter", print_background=True)
        browser.close()
    return out_path

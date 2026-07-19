"""Track C spike: can Playwright fill a Greenhouse application form with a dummy resume?

Decides go/no-go for stage 4 (auto-apply). See docs/tasks/PROGRESS.md.

SAFETY: this script fills fields and screenshots the result. It NEVER clicks
submit — there is deliberately no code path that submits anything, and the fill
data is obviously fake. Keep it that way; real submissions belong to stage 4,
behind batched user approval.

Usage:
    python spike/greenhouse_spike.py <greenhouse job posting URL> [more URLs...]

Output: per-URL field report on stdout + screenshot in spike/out/.
"""

from __future__ import annotations

import sys
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

OUT_DIR = Path(__file__).parent / "out"
DUMMY_PDF = Path(__file__).parent / "dummy_resume.pdf"

DUMMY = {
    "first_name": "Testfirst",
    "last_name": "Testlast",
    "email": "dummy-applicant@example.com",
    "phone": "555-000-0000",
}

# (field key, list of selectors to try — old embed boards + new job-boards React UI)
TEXT_FIELDS = [
    ("first_name", ["#first_name", "input[name='first_name']", "input[aria-label*='First' i]"]),
    ("last_name", ["#last_name", "input[name='last_name']", "input[aria-label*='Last' i]"]),
    ("email", ["#email", "input[name='email']", "input[type='email']"]),
    ("phone", ["#phone", "input[name='phone']", "input[type='tel']"]),
]
RESUME_INPUTS = ["input[type='file']"]


def make_dummy_pdf() -> None:
    """Write a minimal valid one-page PDF (no dependencies)."""
    if DUMMY_PDF.exists():
        return
    content = b"BT /F1 24 Tf 72 720 Td (Dummy resume - spike test) Tj ET"
    objs = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Contents 4 0 R "
        b"/Resources << /Font << /F1 5 0 R >> >> >>",
        b"<< /Length %d >>\nstream\n%s\nendstream" % (len(content), content),
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    out = bytearray(b"%PDF-1.4\n")
    offsets = []
    for i, obj in enumerate(objs, start=1):
        offsets.append(len(out))
        out += b"%d 0 obj\n%s\nendobj\n" % (i, obj)
    xref_at = len(out)
    out += b"xref\n0 %d\n0000000000 65535 f \n" % (len(objs) + 1)
    for off in offsets:
        out += b"%010d 00000 n \n" % off
    out += b"trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n" % (
        len(objs) + 1, xref_at)
    DUMMY_PDF.write_bytes(bytes(out))


def try_fill(page: Page, selectors: list[str], value: str) -> str | None:
    """Return the selector that worked, or None."""
    for sel in selectors:
        loc = page.locator(sel).first
        try:
            if loc.count() and loc.is_visible():
                loc.fill(value, timeout=3000)
                if loc.input_value() == value:
                    return sel
        except Exception:
            continue
    return None


def run_one(page: Page, url: str, slug: str) -> dict[str, str | None]:
    page.goto(url, wait_until="domcontentloaded", timeout=45000)
    page.wait_for_timeout(2500)  # let React boards hydrate

    # Old embed boards show the form only after an "Apply" click
    for label in ("Apply for this job", "Apply Now", "Apply"):
        btn = page.get_by_role("button", name=label).first
        try:
            if btn.count() and btn.is_visible():
                btn.click(timeout=3000)
                page.wait_for_timeout(1500)
                break
        except Exception:
            continue

    results: dict[str, str | None] = {}
    for key, selectors in TEXT_FIELDS:
        results[key] = try_fill(page, selectors, DUMMY[key])

    results["resume_upload"] = None
    for sel in RESUME_INPUTS:
        loc = page.locator(sel).first
        try:
            if loc.count():
                loc.set_input_files(str(DUMMY_PDF), timeout=5000)
                results["resume_upload"] = sel
                break
        except Exception:
            continue

    page.wait_for_timeout(2000)  # let any resume-parse UI settle
    OUT_DIR.mkdir(exist_ok=True)
    page.screenshot(path=str(OUT_DIR / f"{slug}.png"), full_page=True)
    return results


def main() -> None:
    urls = sys.argv[1:]
    if not urls:
        sys.exit("usage: greenhouse_spike.py <job posting URL> [...]")
    make_dummy_pdf()

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        for i, url in enumerate(urls, 1):
            slug = f"attempt-{i}"
            print(f"\n=== {url}")
            try:
                results = run_one(page, url, slug)
            except Exception as exc:
                print(f"  FAILED to load/interact: {exc}")
                continue
            filled = [k for k, v in results.items() if v]
            missed = [k for k, v in results.items() if not v]
            for k, v in results.items():
                print(f"  {k:14s} {'OK  via ' + v if v else 'NOT FOUND'}")
            print(f"  screenshot: spike/out/{slug}.png")
            print(f"  verdict: {len(filled)}/{len(results)} fields "
                  f"({'PROMISING' if len(filled) >= 4 else 'NEEDS WORK'})")
        browser.close()


if __name__ == "__main__":
    main()

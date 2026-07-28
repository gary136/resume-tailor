"""Greenhouse application-form filler — DEV-MODE, never submits.

Selectors validated live in the Track-C spike (spike/FINDINGS.md). This module
fills the standard fields + uploads the resume PDF + screenshots the result.
It contains NO submit action by design: there is no code path that clicks a
submit button, so a rehearsal can never send an application.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from resume_tailor.apply.profile import ApplicantProfile

_TEXT_FIELDS = [
    ("first_name", ["#first_name", "input[name='first_name']", "input[aria-label*='First' i]"]),
    ("last_name", ["#last_name", "input[name='last_name']", "input[aria-label*='Last' i]"]),
    ("email", ["#email", "input[name='email']", "input[type='email']"]),
    ("phone", ["#phone", "input[name='phone']", "input[type='tel']"]),
]
_APPLY_LABELS = ("Apply for this job", "Apply Now", "Apply")


@dataclass
class FillResult:
    filled: dict[str, str | None]   # field -> selector that worked (or None)
    screenshot: Path
    submitted: bool = False         # ALWAYS False — invariant, asserted by tests

    @property
    def ok(self) -> bool:
        core = ["first_name", "last_name", "email", "resume"]
        return all(self.filled.get(k) for k in core)


def _try_fill(page, selectors: list[str], value: str) -> str | None:
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


def fill_application(
    job_url: str, profile: ApplicantProfile, resume_pdf: Path, screenshot: Path
) -> FillResult:
    """Fill (never submit) the Greenhouse form at job_url. Screenshots the result."""
    from playwright.sync_api import sync_playwright

    values = {
        "first_name": profile.first_name,
        "last_name": profile.last_name,
        "email": profile.email,
        "phone": profile.phone,
    }
    filled: dict[str, str | None] = {}
    screenshot.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        for label in _APPLY_LABELS:  # old embed boards reveal the form on click
            btn = page.get_by_role("button", name=label).first
            try:
                if btn.count() and btn.is_visible():
                    btn.click(timeout=3000)
                    page.wait_for_timeout(1500)
                    break
            except Exception:
                continue

        for key, selectors in _TEXT_FIELDS:
            filled[key] = _try_fill(page, selectors, values[key])

        filled["resume"] = None
        loc = page.locator("input[type='file']").first
        try:
            if loc.count():
                loc.set_input_files(str(resume_pdf), timeout=5000)
                filled["resume"] = "input[type='file']"
        except Exception:
            pass

        page.wait_for_timeout(1500)  # let any resume-parse UI settle
        page.screenshot(path=str(screenshot), full_page=True)
        browser.close()

    # invariant: this module never submits.
    return FillResult(filled=filled, screenshot=screenshot, submitted=False)

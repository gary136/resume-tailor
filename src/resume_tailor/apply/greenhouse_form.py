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
    questions: dict[str, str | None] | None = None  # custom question -> answer filled (or None)
    captcha_kind: str = "unchecked"    # from apply.captcha.detect_captcha
    unattended_submit_ok: bool = False
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


def _extract_native_questions(page):
    """Custom questions rendered as native <select> or <textarea> (Greenhouse's
    common shapes). Returns [(label, kind, options, control_locator)]. Custom
    React widgets are not extracted here — they're reported as unfilled."""
    from resume_tailor.apply.questions import Question

    found = []
    # native selects
    for sel in page.locator("select").all():
        try:
            label = _label_for(page, sel)
            if not label:
                continue
            opts = tuple(o.strip() for o in sel.locator("option").all_inner_texts() if o.strip())
            found.append((Question(label, "select", opts), sel))
        except Exception:
            continue
    # textareas (free-text questions like "why us")
    for ta in page.locator("textarea").all():
        try:
            label = _label_for(page, ta)
            if label:
                found.append((Question(label, "text"), ta))
        except Exception:
            continue
    return found


_CORE_LABELS = {"first name", "last name", "email", "phone", "attach", "enter manually",
                "country", "resume/cv", "cover letter"}


def _react_select_questions(page):
    """GitLab-style react-select dropdown questions. Yields (Question, control, options_opener).

    Each question <label> is paired with the next combobox after it in the DOM.
    Options are read by opening the widget. Fragile by nature (custom widget)."""
    from resume_tailor.apply.questions import Question

    out = []
    for lab in page.locator("label").all():
        try:
            text = lab.inner_text().strip()
        except Exception:
            continue
        low = text.strip("*").strip().lower()
        if not text or low in _CORE_LABELS or len(text) < 8:
            continue
        combo = lab.locator("xpath=following::*[@role='combobox'][1]").first
        if not combo.count():
            continue
        out.append((Question(text.rstrip("*").strip(), "select"), combo))
    return out


def _fill_react_select(page, combo, answer: str) -> bool:
    """Open a react-select control and click the option matching `answer`.

    Options are scoped to THIS widget's own listbox (via aria-controls) — a global
    [role='option'] search wrongly picks up other widgets' menus (e.g. the phone
    country-code list has 250+ options). Best-effort; fragile custom widget."""
    try:
        combo.scroll_into_view_if_needed(timeout=2000)
        combo.click(timeout=2000)
        page.wait_for_timeout(350)
        listbox_id = combo.get_attribute("aria-controls") or combo.get_attribute("aria-owns")
        opts = page.locator(f"#{listbox_id} [role='option']") if listbox_id else None
        if not opts or not opts.count():
            # fall back to react-select's option class, still menu-scoped where possible
            opts = page.locator("[class*='select__menu'] [role='option'], [class*='select__option']")
        want = answer.strip().lower()
        n = opts.count()
        # exact match first, then contains — avoids "No" matching "Not sure"
        for match in (lambda t: t == want, lambda t: want in t or t in want):
            for i in range(n):
                txt = (opts.nth(i).inner_text() or "").strip().lower()
                if match(txt):
                    opts.nth(i).click(timeout=2000)
                    return True
        page.keyboard.press("Escape")
    except Exception:
        pass
    return False


def _label_for(page, control):
    """Best-effort label text for a control: aria-label, or the <label for=id>, or
    the nearest preceding label text."""
    try:
        aria = control.get_attribute("aria-label")
        if aria:
            return aria.strip()
        cid = control.get_attribute("id")
        if cid:
            lab = page.locator(f"label[for='{cid}']").first
            if lab.count():
                return lab.inner_text().strip()
    except Exception:
        pass
    return None


def fill_application(
    job_url: str,
    profile: ApplicantProfile,
    resume_pdf: Path,
    screenshot: Path,
    *,
    facts=None,
    answers=None,
    company: str = "",
    backend=None,
) -> FillResult:
    """Fill (never submit) the Greenhouse form at job_url. Screenshots the result.

    If facts+answers are given, also answers custom questions (work-auth
    deterministically & truthfully; softer ones from the answer bank)."""
    from playwright.sync_api import sync_playwright

    from resume_tailor.apply.questions import FLAG_HUMAN, answer_question

    values = {
        "first_name": profile.first_name, "last_name": profile.last_name,
        "email": profile.email, "phone": profile.phone,
    }
    filled: dict[str, str | None] = {}
    questions: dict[str, str | None] = {}
    screenshot.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(job_url, wait_until="domcontentloaded", timeout=45000)
        page.wait_for_timeout(2500)
        for label in _APPLY_LABELS:
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

        if facts is not None and answers is not None:
            # native <select>/<textarea>
            for q, control in _extract_native_questions(page):
                ans = answer_question(q, facts, answers, company=company, backend=backend)
                if not ans:
                    questions[q.label] = None
                    continue
                try:
                    if q.kind == "select":
                        control.select_option(label=ans, timeout=2000)
                    else:
                        control.fill(ans, timeout=2000)
                    questions[q.label] = ans
                except Exception:
                    questions[q.label] = None
            # react-select dropdown questions (GitLab-style)
            for q, combo in _react_select_questions(page):
                if q.label in questions:
                    continue
                ans = answer_question(q, facts, answers, company=company, backend=backend)
                questions[q.label] = ans if (ans and _fill_react_select(page, combo, ans)) else None

        from resume_tailor.apply.captcha import detect_captcha
        cap = detect_captcha(page)

        page.wait_for_timeout(1000)
        page.screenshot(path=str(screenshot), full_page=True)
        browser.close()

    return FillResult(filled=filled, screenshot=screenshot, questions=questions or None,
                      captcha_kind=cap.kind, unattended_submit_ok=cap.unattended_submit_ok,
                      submitted=False)

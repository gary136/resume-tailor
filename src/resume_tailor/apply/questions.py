"""Answer custom application-form questions from the applicant's data.

Split by risk:
- WORK-AUTHORIZATION questions (sponsorship, US-authorized, citizenship) are
  answered DETERMINISTICALLY from the auth-us-work fact — never by the model.
  A wrong answer here is visa fraud, not a typo, so it must be exact and stable.
- Everything else (preferred name, why-us, previously-worked, self-ID) is mapped
  from the answer bank, with the LLM only for genuinely free-text questions.
Unmappable questions return None (left blank; flagged for the human).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Optional

from resume_tailor.contracts import AnswerBank, FactInventory

# Work-auth answers must be truthful and are NEVER left to the model.
FLAG_HUMAN = "__NEEDS_HUMAN_REVIEW__"  # a work-auth question we won't risk auto-answering

_SPONSOR_RE = re.compile(r"sponsor|sponsorship", re.I)
_WITHOUT_SPONSOR_RE = re.compile(
    r"without\b.{0,30}sponsor|not\s+(require|need)\w*\b.{0,20}sponsor|"
    r"don'?t\s+(require|need)\w*\b.{0,20}sponsor|no sponsorship",
    re.I)
_AUTHORIZED_RE = re.compile(r"authoriz(ed|ation) to work|legally authorized|eligible to work", re.I)
_CITIZEN_RE = re.compile(r"citizen", re.I)
_PREV_RE = re.compile(r"previously|worked (at|for)|consulted for", re.I)
_NAME_RE = re.compile(r"preferred name|name.{0,20}prefer|prefer.{0,20}name|preferred first name", re.I)
_LINKEDIN_RE = re.compile(r"linkedin", re.I)
_SELFID_RE = re.compile(r"gender|race|ethnic|veteran|disability|hispanic|latino", re.I)
_WHY_RE = re.compile(r"why|interested in|excited|motivat", re.I)


@dataclass
class Question:
    label: str
    kind: str = "text"                 # "text" | "select"
    options: tuple[str, ...] = ()      # for selects


def _pick_option(value: str, options: tuple[str, ...]) -> Optional[str]:
    """Best-match an intended answer to one of a select's real options."""
    if not options:
        return value
    v = value.strip().lower()
    for o in options:
        if o.strip().lower() == v:
            return o
    for o in options:
        if v in o.lower() or o.lower() in v:
            return o
    # yes/no fallbacks
    if v in ("yes", "no"):
        for o in options:
            if o.strip().lower() == v:
                return o
    return None


def _forced(value: str, options: tuple[str, ...]) -> str:
    """Map a forced truthful yes/no to a real option. A work-auth question with no
    yes/no options (free text, or options we can't match) is FLAGGED for the human —
    we never type a bare 'Yes'/'No' into a free-text work-auth field."""
    if not options:
        return FLAG_HUMAN
    return _pick_option(value, options) or FLAG_HUMAN


def work_auth_answer(
    label: str, options: tuple[str, ...], *, authorized: bool, needs_sponsorship: bool
) -> tuple[bool, Optional[str]]:
    """(is_work_auth, answer). answer is FLAG_HUMAN when it's a work-auth question we
    won't risk auto-answering. Truthful and deterministic — the model is never consulted."""
    is_wa = bool(_SPONSOR_RE.search(label) or _AUTHORIZED_RE.search(label) or _CITIZEN_RE.search(label))
    if not is_wa:
        return False, None
    if _CITIZEN_RE.search(label):
        return True, _forced("No", options)                       # H-1B, never claim citizenship
    if _WITHOUT_SPONSOR_RE.search(label):
        return True, _forced("No", options)                       # can't work WITHOUT sponsorship
    if _SPONSOR_RE.search(label):
        return True, _forced("Yes" if needs_sponsorship else "No", options)  # requires sponsorship
    if _AUTHORIZED_RE.search(label):
        return True, _forced("Yes" if authorized else "No", options)  # H-1B IS authorized
    return True, FLAG_HUMAN                                        # work-auth but unrecognized


def answer_question(
    q: Question,
    facts: FactInventory,
    answers: AnswerBank,
    *,
    company: str,
    backend=None,
) -> Optional[str]:
    """Return an answer string for one question, or None if unmappable."""
    is_wa, wa = work_auth_answer(
        q.label, q.options, authorized=True, needs_sponsorship=True
    )
    if is_wa:
        # FLAG_HUMAN and None both mean "leave blank"; the caller flags work-auth blanks loudly.
        return None if wa == FLAG_HUMAN else wa
    if _NAME_RE.search(q.label):
        first = answers.preferred_name or ""
        return first or None
    if _LINKEDIN_RE.search(q.label):
        return answers.linkedin_url or None
    if _SELFID_RE.search(q.label):
        return _pick_option(answers.self_identification, q.options) or answers.self_identification
    if _PREV_RE.search(q.label):
        return _pick_option(answers.previously_worked_here_default, q.options) \
            or answers.previously_worked_here_default
    if _WHY_RE.search(q.label) and q.kind == "text":
        if backend is None:
            return answers.why_company_seed
        text = backend.complete_text(
            system=("Write a 2-3 sentence, specific, honest answer to a job-application "
                    "question, in the candidate's voice. No fabrication; if unsure, keep it "
                    "general. Base it on the candidate's theme below."),
            user=(f"Company: {company}\nQuestion: {q.label}\n"
                  f"Candidate's theme: {answers.why_company_seed}"),
        )
        return (text or answers.why_company_seed).strip()
    return None  # unmappable -> leave blank, flag for the human


def answer_all(questions: list[Question], facts, answers, *, company: str, backend=None):
    """Map every question; returns {label: answer|None}."""
    return {q.label: answer_question(q, facts, answers, company=company, backend=backend)
            for q in questions}

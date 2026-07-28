"""Assemble the values that go into an application form, from existing records.

Identity (name/email/phone) is parsed from the `contact-info` fact so there's one
source of truth; form answers (location, salary, …) come from the answer bank.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from resume_tailor.contracts import AnswerBank, FactInventory

_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
_PHONE_RE = re.compile(r"\+?\d[\d\s().-]{7,}\d")


@dataclass
class ApplicantProfile:
    first_name: str
    last_name: str
    email: str
    phone: str
    location: str
    salary_base_range: str
    salary_total_range: str


def _parse_contact(statement: str) -> tuple[str, str, str, str]:
    """('First', 'Last', email, phone) from the contact-info fact statement."""
    email = (_EMAIL_RE.search(statement) or [""])[0] if _EMAIL_RE.search(statement) else ""
    phone_m = _PHONE_RE.search(statement)
    phone = phone_m.group(0).strip() if phone_m else ""
    # name is the leading run before the first ' — ' / ' - ' separator or the email
    head = re.split(r"\s[—-]\s", statement, maxsplit=1)[0].strip()
    # strip a parenthetical nickname: "Hung-Ting (Gary) Lee" -> keep given + family
    parts = head.replace("(", "").replace(")", "").split()
    first = parts[0] if parts else ""
    last = parts[-1] if len(parts) > 1 else ""
    return first, last, email, phone


def build_profile(facts: FactInventory, answers: AnswerBank) -> ApplicantProfile:
    contact = next((f for f in facts.facts if f.id == "contact-info"), None)
    if contact is None:
        raise ValueError("no 'contact-info' fact — cannot fill applicant identity")
    first, last, email, phone = _parse_contact(contact.statement)
    return ApplicantProfile(
        first_name=first,
        last_name=last,
        email=email,
        phone=phone,
        location=answers.location_policy,
        salary_base_range=answers.salary_base_range,
        salary_total_range=answers.salary_total_range,
    )

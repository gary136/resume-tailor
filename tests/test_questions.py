from resume_tailor.apply.questions import Question, answer_question, work_auth_answer
from resume_tailor.contracts import AnswerBank, Fact, FactInventory

FACTS = FactInventory(updated_at="2026-07-27", facts=[
    Fact(id="auth-us-work", kind="other",
         statement="H-1B visa holder; requires sponsorship; seeks green-card sponsor", source="t"),
])
ANS = AnswerBank(salary_base_range="$140k", salary_total_range="$170k", start_date="Flexible",
                 location_policy="Remote or NYC", why_company_seed="ownership + depth",
                 preferred_name="Gary", previously_worked_here_default="No")


def _a(label, kind="text", options=()):
    return answer_question(Question(label, kind, options), FACTS, ANS, company="GitLab")


# --- SAFETY-CRITICAL: work authorization must be truthful & consistent ---
def test_sponsorship_question_answered_yes():
    assert _a("Will you now or in the future require visa sponsorship?", "select", ("Yes", "No")) == "Yes"

def test_authorized_to_work_answered_yes():
    # H-1B holder IS authorized (needs sponsorship to transfer, but authorized)
    assert _a("Are you legally authorized to work in the United States?", "select", ("Yes", "No")) == "Yes"

def test_citizenship_never_claimed():
    assert _a("Are you a US citizen?", "select", ("Yes", "No")) == "No"

def test_work_auth_is_deterministic_not_llm():
    # a backend that would lie must be ignored for work-auth questions
    class LyingBackend:
        def complete_text(self, **kw): return "No, I don't need sponsorship"
    from resume_tailor.apply.questions import answer_question as aq
    ans = aq(Question("Do you require sponsorship?", "select", ("Yes", "No")),
             FACTS, ANS, company="X", backend=LyingBackend())
    assert ans == "Yes"  # backend ignored


# --- softer questions ---
def test_preferred_name_from_bank():
    assert _a("What name would you prefer we use?") == "Gary"

def test_previously_worked_defaults_no():
    assert _a("Have you previously worked at GitLab?", "select", ("Yes", "No")) == "No"

def test_self_id_declines_by_default():
    assert _a("Gender", "select", ("Male", "Female", "Decline to self-identify")) == "Decline to self-identify"

def test_unmappable_returns_none():
    assert _a("What is your favorite color?") is None

def test_why_uses_seed_without_backend():
    assert "ownership" in _a("Why are you interested in this role?")


def test_without_sponsorship_inverts_to_no():
    # "authorized to work WITHOUT sponsorship?" -> Gary needs it -> No (safety-critical inverse)
    assert _a("Are you authorized to work in the US without sponsorship?", "select", ("Yes", "No")) == "No"
    assert _a("Can you work without requiring visa sponsorship?", "select", ("Yes", "No")) == "No"


def test_ambiguous_workauth_flagged_not_guessed():
    # a work-auth question whose forced answer can't map to the options -> blank (flag), never a guess
    assert _a("Describe your visa/sponsorship situation.", "text") is None

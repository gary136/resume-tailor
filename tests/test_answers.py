from resume_tailor.contracts import AnswerBank
from resume_tailor.store.files import load_answers, save_answers


def test_answer_bank_roundtrip(tmp_path):
    bank = AnswerBank(
        salary_base_range="$140k–$180k",
        salary_total_range="$170k–$250k total compensation",
        start_date="Flexible",
        location_policy="Remote, or NYC hybrid ≤3 days/week",
        why_company_seed="Product ownership + technical depth; improvise where it doesn't fit.",
    )
    path = save_answers(bank, tmp_path / "answers.yaml")
    loaded = load_answers(path)
    assert loaded == bank
    assert loaded.why_company_strategy == "seed-adapt-per-company"

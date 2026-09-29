from app.diagnostic import diagnose
from app.models import UserAnswers


def base(**kw):
    data = dict(income=100000, essential_expenses=50000, discretionary_expenses=10000,
                debt_payment=10000, total_debt=200000, savings=100000, has_overdue=False,
                tracks_expenses=True, has_budget=True, impulse_spending=False,
                emergency_goal=True, major_goal=True, income_stability="стабильный")
    data.update(kw)
    return UserAnswers(**data)


def test_healthy_profile_has_low_risk():
    r=diagnose(base())
    assert r.balance == 30000
    assert r.level == "низкий"
    assert r.debt_ratio == 0.1


def test_negative_balance_is_detected():
    r=diagnose(base(essential_expenses=80000, discretionary_expenses=30000))
    assert any(f.code == "negative_balance" for f in r.findings)
    assert r.balance < 0


def test_high_debt_and_overdue_raise_risk():
    r=diagnose(base(debt_payment=60000, has_overdue=True, savings=0))
    codes={f.code for f in r.findings}
    assert "high_debt_load" in codes
    assert "overdue" in codes
    assert r.level == "высокий"


def test_no_tracking_and_impulse_spending_are_detected():
    r=diagnose(base(tracks_expenses=False, has_budget=False, impulse_spending=True))
    codes={f.code for f in r.findings}
    assert {"no_tracking","no_budget","impulse"}.issubset(codes)

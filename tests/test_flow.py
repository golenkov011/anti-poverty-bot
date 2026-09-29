from app.diagnostic import diagnose
from app.models import UserAnswers


def test_result_contains_actionable_plan():
    a=UserAnswers(80000,60000,15000,10000,150000,5000,False,False,False,True,False,False,"нестабильный")
    r=diagnose(a)
    assert len(r.findings) >= 3
    assert 1 <= len(r.plan) <= 6
    assert all(isinstance(x,str) and x for x in r.plan)

from dataclasses import dataclass, field
from typing import Optional

@dataclass
class UserAnswers:
    income: float
    essential_expenses: float
    discretionary_expenses: float
    debt_payment: float
    total_debt: float
    savings: float
    has_overdue: bool
    tracks_expenses: bool
    has_budget: bool
    impulse_spending: bool
    emergency_goal: bool
    major_goal: bool
    income_stability: str
    user_id: Optional[int] = None
    raw: dict = field(default_factory=dict)

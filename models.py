from dataclasses import dataclass

@dataclass
class UserAnswers:
    user_id: int
    income: float = 0.0
    essential_expenses: float = 0.0
    discretionary_expenses: float = 0.0
    debt_payment: float = 0.0
    savings: float = 0.0
    has_overdue: bool = False
    tracks_expenses: bool = False
    has_budget: bool = False
    impulse_spending: bool = False
    income_stability: str = "stable"
    current_step: str = "start"

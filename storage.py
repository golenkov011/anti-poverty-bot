import sqlite3
from contextlib import contextmanager
from .models import UserAnswers

DB_PATH = "users_data.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS user_answers (user_id INTEGER PRIMARY KEY, income REAL DEFAULT 0, essential_expenses REAL DEFAULT 0, discretionary_expenses REAL DEFAULT 0, debt_payment REAL DEFAULT 0, savings REAL DEFAULT 0, has_overdue INTEGER DEFAULT 0, tracks_expenses INTEGER DEFAULT 0, has_budget INTEGER DEFAULT 0, impulse_spending INTEGER DEFAULT 0, income_stability TEXT DEFAULT 'stable', current_step TEXT DEFAULT 'start')")
        conn.commit()

def get_user(user_id: int) -> UserAnswers:
    with get_db() as conn:
        row = conn.execute("SELECT * FROM user_answers WHERE user_id = ?", (user_id,)).fetchone()
        if row is None:
            return UserAnswers(user_id=user_id)
        return UserAnswers(
            user_id=row["user_id"],
            income=row["income"] or 0.0,
            essential_expenses=row["essential_expenses"] or 0.0,
            discretionary_expenses=row["discretionary_expenses"] or 0.0,
            debt_payment=row["debt_payment"] or 0.0,
            savings=row["savings"] or 0.0,
            has_overdue=bool(row["has_overdue"]),
            tracks_expenses=bool(row["tracks_expenses"]),
            has_budget=bool(row["has_budget"]),
            impulse_spending=bool(row["impulse_spending"]),
            income_stability=row["income_stability"] or "stable",
            current_step=row["current_step"] or "start"
        )

def save_user(answers: UserAnswers):
    with get_db() as conn:
        conn.execute("INSERT OR REPLACE INTO user_answers (user_id, income, essential_expenses, discretionary_expenses, debt_payment, savings, has_overdue, tracks_expenses, has_budget, impulse_spending, income_stability, current_step) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", (
            answers.user_id, answers.income, answers.essential_expenses,
            answers.discretionary_expenses, answers.debt_payment, answers.savings,
            int(answers.has_overdue), int(answers.tracks_expenses),
            int(answers.has_budget), int(answers.impulse_spending),
            answers.income_stability, answers.current_step
        ))
        conn.commit()

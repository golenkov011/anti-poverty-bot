from dataclasses import dataclass
from typing import List
from models import UserAnswers

@dataclass
class Finding:
    code: str
    title: str
    severity: str
    evidence: str
    actions: List[str]

@dataclass
class DiagnosticResult:
    balance: float
    debt_ratio: float
    reserve_months: float
    risk_score: int
    level: str
    findings: List[Finding]
    summary: str
    plan: List[str]

def _clamp_money(v: float) -> float:
    return max(0.0, float(v))

def diagnose(a: UserAnswers) -> DiagnosticResult:
    income = _clamp_money(a.income)
    essential = _clamp_money(a.essential_expenses)
    discretionary = _clamp_money(a.discretionary_expenses)
    debt_payment = _clamp_money(a.debt_payment)
    savings = _clamp_money(a.savings)
    
    balance = income - essential - discretionary - debt_payment
    debt_ratio = debt_payment / income if income else 1.0
    reserve_months = savings / max(essential + debt_payment, 1.0)
    
    findings: List[Finding] = []
    score = 0
    
    if balance < 0:
        score += 3
        findings.append(Finding("negative_balance", "Расходы выше доходов", "high", f"Баланс: {balance:,.0f}", ["Остановить необязательные покупки на 14 дней", "Разделить расходы на обязательные и временные", "Найти статью для сокращения"]))
    if debt_ratio >= 0.5:
        score += 3
        findings.append(Finding("high_debt", "Высокая долговая нагрузка", "high", f"Долги: {debt_ratio:.0%}", ["Не брать новые долги", "Составить таблицу всех долгов", "Планировать досрочное погашение"]))
    elif debt_ratio >= 0.3:
        score += 2
        findings.append(Finding("moderate_debt", "Заметная долговая нагрузка", "medium", f"Долги: {debt_ratio:.0%}", ["Не наращивать платежи", "Сравнить стоимость долгов"]))
    if a.has_overdue:
        score += 3
        findings.append(Finding("overdue", "Есть просрочки", "high", "Пользователь указал просрочку", ["Составить список просрочек", "Связаться с кредиторами", "Не добавлять новые платежи"]))
    if not a.tracks_expenses:
        score += 2
        findings.append(Finding("no_tracking", "Нет учёта расходов", "medium", "Расходы не фиксируются", ["14 дней фиксировать каждый расход", "Разделить на обязательные и необязательные"]))
    if not a.has_budget:
        score += 1
        findings.append(Finding("no_budget", "Нет бюджета", "low", "Нет месячного плана", ["Собрать простой бюджет на месяц"]))
    if a.impulse_spending:
        score += 2
        findings.append(Finding("impulse", "Импульсивные покупки", "medium", "Покупки без плана", ["Ввести правило паузы для крупных покупок", "Отмечать эмоциональные траты"]))
    if reserve_months < 0.25:
        score += 2
        findings.append(Finding("no_reserve", "Нет резерва", "medium", f"Резерв: {reserve_months:.1f} мес.", ["Начать формировать небольшой ликвидный резерв"]))
    elif reserve_months < 1:
        score += 1
        findings.append(Finding("small_reserve", "Малый резерв", "low", f"Резерв: {reserve_months:.1f} мес.", ["Определить цель и пополнять регулярно"]))
    if a.income_stability == "unstable":
        score += 1
        findings.append(Finding("unstable_income", "Нестабильный доход", "medium", "Доход нестабилен", ["Планировать расходы консервативно", "Отделить обязательные платежи"]))
        
    if score >= 8:
        level = "high"
    elif score >= 4:
        level = "medium"
    else:
        level = "low"
    
    summary = "Критичных сигналов нет. Поддерживай учёт." if not findings else f"Уровень риска: {level}. Найдено проблем: {len(findings)}."
    
    priority = sorted(findings, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x.severity])
    plan = []
    for f in priority:
        for action in f.actions:
            if action not in plan:
                plan.append(action)
            if len(plan) >= 6:
                break
        if len(plan) >= 6:
            break
        
    return DiagnosticResult(balance, debt_ratio, reserve_months, score, level, findings, summary, plan)

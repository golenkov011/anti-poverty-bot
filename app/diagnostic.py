from dataclasses import dataclass
from .models import UserAnswers

@dataclass
class Finding:
    code: str
    title: str
    severity: str
    evidence: str
    actions: list[str]

@dataclass
class DiagnosticResult:
    balance: float
    debt_ratio: float
    reserve_months: float
    risk_score: int
    level: str
    findings: list[Finding]
    summary: str
    plan: list[str]


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

    findings: list[Finding] = []
    score = 0

    if balance < 0:
        score += 3
        findings.append(Finding(
            "negative_balance", "Расходы выше доходов", "high",
            f"Расчётный месячный баланс: {balance:,.0f} ₽.",
            ["На 14 дней остановить необязательные крупные покупки.", "Разделить расходы на обязательные, регулируемые и временно отключаемые.", "Найти минимум одну статью, которую можно сократить без ущерба базовым потребностям."]
        ))
    elif balance < income * 0.1:
        score += 2
        findings.append(Finding(
            "thin_margin", "Очень небольшой запас месяца", "medium",
            f"После заявленных расходов остаётся около {balance:,.0f} ₽.",
            ["Зафиксировать фактические расходы за 30 дней.", "Не увеличивать обязательные платежи до появления устойчивого запаса."]
        ))

    if debt_ratio >= 0.5:
        score += 3
        findings.append(Finding(
            "high_debt_load", "Высокая долговая нагрузка", "high",
            f"Платежи по долгам составляют около {debt_ratio:.0%} дохода.",
            ["Не брать новый долг для покрытия текущих расходов без отдельного расчёта.", "Собрать таблицу всех долгов: остаток, ставка, платёж, срок.", "Проверить сценарий досрочного погашения только после сохранения базового денежного резерва."]
        ))
    elif debt_ratio >= 0.3:
        score += 2
        findings.append(Finding(
            "moderate_debt_load", "Заметная долговая нагрузка", "medium",
            f"Платежи по долгам составляют около {debt_ratio:.0%} дохода.",
            ["Не наращивать обязательные платежи без необходимости.", "Сравнить стоимость всех долгов и определить порядок их сокращения."]
        ))

    if a.has_overdue:
        score += 3
        findings.append(Finding(
            "overdue", "Есть просроченные обязательства", "high",
            "Пользователь указал наличие просрочки.",
            ["Сначала составить полный список просроченных обязательств.", "Уточнить актуальные суммы и сроки у кредиторов.", "До стабилизации ситуации не добавлять новые обязательные платежи без расчёта."]
        ))

    if not a.tracks_expenses:
        score += 2
        findings.append(Finding(
            "no_tracking", "Нет регулярного учёта расходов", "medium",
            "Расходы сейчас не фиксируются системно.",
            ["14 дней фиксировать каждый расход одной таблицей.", "Разделить расходы минимум на обязательные и необязательные."]
        ))

    if not a.has_budget:
        score += 1
        findings.append(Finding(
            "no_budget", "Нет рабочего бюджета", "low",
            "Пользователь не использует месячный план расходов.",
            ["Собрать простой бюджет на один месяц до оптимизации расходов."]
        ))

    if a.impulse_spending:
        score += 2
        findings.append(Finding(
            "impulse", "Есть импульсивные покупки", "medium",
            "Пользователь отмечает покупки без предварительного плана.",
            ["Ввести правило паузы для необязательных покупок выше выбранного личного лимита.", "Отдельно отмечать эмоциональные покупки в течение 14 дней."]
        ))

    if reserve_months < 0.25:
        score += 2
        findings.append(Finding(
            "no_reserve", "Почти нет финансового резерва", "medium",
            f"Расчётный резерв покрывает около {reserve_months:.1f} месяца базовых расходов.",
            ["После стабилизации текущего баланса начать формировать небольшой ликвидный резерв."]
        ))
    elif reserve_months < 1:
        score += 1
        findings.append(Finding(
            "small_reserve", "Небольшой финансовый резерв", "low",
            f"Расчётный резерв покрывает около {reserve_months:.1f} месяца базовых расходов.",
            ["Определить целевой размер резерва и пополнять его регулярной небольшой суммой."]
        ))

    if a.income_stability == "нестабильный":
        score += 1
        findings.append(Finding(
            "income_instability", "Нестабильный доход", "medium",
            "Доход отмечен как нестабильный.",
            ["Планировать обязательные расходы по консервативному уровню дохода.", "Отделить обязательные платежи от расходов, которые можно переносить."]
        ))

    if score >= 8:
        level = "высокий"
    elif score >= 4:
        level = "средний"
    else:
        level = "низкий"

    if not findings:
        summary = "По введённым данным критичных сигналов не обнаружено. Следующий шаг — поддерживать учёт и постепенно укреплять резерв."
    else:
        summary = f"Основной результат диагностики: уровень финансового риска — {level}. Найдено зон внимания: {len(findings)}."

    # Keep the plan short and prioritized.
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

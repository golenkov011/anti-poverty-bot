import os
from .diagnostic import DiagnosticResult

async def explain_with_ai(result: DiagnosticResult) -> str | None:
    """Optional layer. Core diagnosis remains deterministic if API is unavailable."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return None
    try:
        from openai import AsyncOpenAI
        client = AsyncOpenAI(api_key=key)
        findings = "\n".join(f"- {f.title}: {f.evidence}" for f in result.findings[:4])
        prompt = (
            "Ты объясняешь результат финансовой самодиагностики простым русским языком. "
            "Не давай персональных инвестиционных/кредитных обещаний, не выдумывай факты. "
            "Не меняй уровень риска и не добавляй диагнозов. Максимум 700 знаков.\n\n"
            f"Уровень: {result.level}\n{findings}\n"
            f"План: {'; '.join(result.plan[:4])}"
        )
        response = await client.responses.create(model=os.getenv("OPENAI_MODEL", "gpt-5.6-mini"), input=prompt)
        return response.output_text.strip()
    except Exception:
        return None

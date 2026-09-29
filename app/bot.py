import logging
from aiogram import Router, F
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from .storage import init_db, get_user, save_user
from .diagnostic import diagnose
from .models import UserAnswers

logging.basicConfig(level=logging.INFO)
router = Router()

class DiagnosticForm(StatesGroup):
    income = State()
    essential = State()
    discretionary = State()
    debt = State()
    savings = State()
    overdue = State()
    tracking = State()
    budget = State()
    impulse = State()
    stability = State()

def get_kb(*buttons: str) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=b)] for b in buttons], resize_keyboard=True)

@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer("Привет! Я проанализирую твои финансы. Нажми кнопку ниже.", reply_markup=get_kb("Начать диагностику"))

@router.message(Command("info"))
async def cmd_info(message: Message):
    await message.answer("10 вопросов -> анализ данных -> план действий.")

@router.message(F.text == "Начать диагностику")
async def start_diag(message: Message, state: FSMContext):
    user = get_user(message.from_user.id)
    await state.update_data(user_answers=user)
    await message.answer("Вопрос 1/10: Какой твой среднемесячный доход? (введи число, например 50000)")
    await state.set_state(DiagnosticForm.income)

async def process_number(message: Message, state: FSMContext, field: str, next_state: State, next_text: str):
    try:
        val = float(message.text.replace(" ", "").replace(",", ".").replace("₽", "").replace("руб", ""))
        if val < 0:
            raise ValueError
    except ValueError:
        return await message.answer("Введи положительное число. Пример: 50000")
    data = await state.get_data()
    setattr(data["user_answers"], field, val)
    await state.update_data(user_answers=data["user_answers"])
    await message.answer(next_text)
    await state.set_state(next_state)

@router.message(DiagnosticForm.income)
async def p_income(message: Message, state: FSMContext):
    await process_number(message, state, "income", DiagnosticForm.essential, "Вопрос 2/10: Обязательные расходы (аренда, еда, транспорт)?")

@router.message(DiagnosticForm.essential)
async def p_essential(message: Message, state: FSMContext):
    await process_number(message, state, "essential_expenses", DiagnosticForm.discretionary, "Вопрос 3/10: Необязательные расходы (развлечения, хобби)?")

@router.message(DiagnosticForm.discretionary)
async def p_discretionary(message: Message, state: FSMContext):
    await process_number(message, state, "discretionary_expenses", DiagnosticForm.debt, "Вопрос 4/10: Платежи по долгам/кредитам в месяц? (если нет, введи 0)")

@router.message(DiagnosticForm.debt)
async def p_debt(message: Message, state: FSMContext):
    await process_number(message, state, "debt_payment", DiagnosticForm.savings, "Вопрос 5/10: Сколько у тебя сбережений? (введи число)")

@router.message(DiagnosticForm.savings)
async def p_savings(message: Message, state: FSMContext):
    await process_number(message, state, "savings", DiagnosticForm.overdue, "Вопрос 6/10: Есть ли просроченные платежи?")

@router.message(DiagnosticForm.overdue)
async def p_overdue(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        return await message.answer("Ответь Да или Нет")
    data = await state.get_data()
    data["user_answers"].has_overdue = (message.text == "Да")
    await state.update_data(user_answers=data["user_answers"])
    await message.answer("Вопрос 7/10: Ведёшь ли учёт расходов?")
    await state.set_state(DiagnosticForm.tracking)

@router.message(DiagnosticForm.tracking)
async def p_tracking(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        return await message.answer("Ответь Да или Нет")
    data = await state.get_data()
    data["user_answers"].tracks_expenses = (message.text == "Да")
    await state.update_data(user_answers=data["user_answers"])
    await message.answer("Вопрос 8/10: Планируешь ли месячный бюджет?")
    await state.set_state(DiagnosticForm.budget)

@router.message(DiagnosticForm.budget)
async def p_budget(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        return await message.answer("Ответь Да или Нет")
    data = await state.get_data()
    data["user_answers"].has_budget = (message.text == "Да")
    await state.update_data(user_answers=data["user_answers"])
    await message.answer("Вопрос 9/10: Бывают ли импульсивные покупки?")
    await state.set_state(DiagnosticForm.impulse)

@router.message(DiagnosticForm.impulse)
async def p_impulse(message: Message, state: FSMContext):
    if message.text not in ["Да", "Нет"]:
        return await message.answer("Ответь Да или Нет")
    data = await state.get_data()
    data["user_answers"].impulse_spending = (message.text == "Да")
    await state.update_data(user_answers=data["user_answers"])
    await message.answer("Вопрос 10/10: Насколько стабилен твой доход?")
    await state.set_state(DiagnosticForm.stability)

@router.message(DiagnosticForm.stability)
async def p_stability(message: Message, state: FSMContext):
    if message.text not in ["Стабильный", "Нестабильный"]:
        return await message.answer("Ответь Стабильный или Нестабильный")
    data = await state.get_data()
    answers = data["user_answers"]
    answers.income_stability = message.text.lower()
    save_user(answers)
    result = diagnose(answers)
    
    text = f"РЕЗУЛЬТАТ ДИАГНОСТИКИ\n\nУровень риска: {result.level}\nБаланс: {int(result.balance)} руб/мес\nДолговая нагрузка: {int(result.debt_ratio*100)}%\nРезерв: {round(result.reserve_months, 1)} мес.\n\n{result.summary}\n\nПЛАН ДЕЙСТВИЙ:\n"
    for i, action in enumerate(result.plan, 1):
        text += f"{i}. {action}\n"
        
    await message.answer(text, reply_markup=get_kb("Начать диагностику"))
    await state.clear()

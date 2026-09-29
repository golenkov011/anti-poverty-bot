import os
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from dotenv import load_dotenv

from .models import UserAnswers
from .diagnostic import diagnose
from .storage import Storage
from .ai import explain_with_ai

load_dotenv()

class Form(StatesGroup):
    income = State(); essential = State(); discretionary = State(); debt_payment = State(); total_debt = State(); savings = State()
    overdue = State(); tracks = State(); budget = State(); impulse = State(); emergency = State(); major_goal = State(); stability = State()


def kb(*items):
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=x)] for x in items], resize_keyboard=True, one_time_keyboard=True)


def money(v: str) -> float:
    v = v.lower().replace("₽", "").replace("руб", "").replace(" ", "").replace(",", ".")
    return float(v)


def parse_bool(text: str) -> bool:
    return text in {"Да", "Есть", "Учитываю", "Веду", "Планирую", "Иногда"}


def result_text(r):
    lines = ["📊 ВАША ДИАГНОСТИКА", "", r.summary, "", f"Баланс месяца: {r.balance:,.0f} ₽", f"Долговая нагрузка: {r.debt_ratio:.0%}", f"Резерв: {r.reserve_months:.1f} мес.", ""]
    if r.findings:
        lines += ["Зоны внимания:"] + [f"• {f.title}" for f in r.findings[:4]] + [""]
    lines += ["Первые действия:"] + [f"{i+1}. {x}" for i, x in enumerate(r.plan[:6])]
    lines += ["", "Это информационная самодиагностика, а не индивидуальная финансовая рекомендация."]
    return "\n".join(lines)


def make_app():
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set. Copy .env.example to .env and add your Telegram bot token.")
    bot = Bot(token=token)
    dp = Dispatcher()
    storage = Storage(os.getenv("DB_PATH", "data/bot.sqlite3"))

    @dp.message(CommandStart())
    async def start(message: Message, state: FSMContext):
        await state.clear()
        await message.answer(
            "Привет. Это MVP «Анти-бедность через решения».\n\n"
            "Бот не обещает быстрых денег и не принимает решения за вас. Он помогает увидеть финансовые узкие места и выбрать первые практические действия.\n\n"
            "Диагностика займёт несколько минут.", reply_markup=kb("Начать диагностику")
        )

    @dp.message(Command("help"))
    async def help_cmd(message: Message):
        await message.answer("/start — начать\n/restart — пройти заново\n/privacy — о данных")

    @dp.message(Command("privacy"))
    async def privacy(message: Message):
        await message.answer("MVP хранит ответы локально в SQLite на сервере владельца бота. Не вводите паспортные данные, номера карт, пароли и другие секретные данные.")

    @dp.message(Command("restart"))
    async def restart(message: Message, state: FSMContext):
        await state.clear(); await message.answer("Начинаем заново.", reply_markup=kb("Начать диагностику"))

    @dp.message(F.text == "Начать диагностику")
    async def begin(message: Message, state: FSMContext):
        await state.clear(); await state.set_state(Form.income)
        await message.answer("1/13. Средний месячный доход семьи после налогов, ₽?", reply_markup=ReplyKeyboardRemove())

    async def ask_num(message, state, next_state, text):
        try:
            val = money(message.text)
            if val < 0: raise ValueError
        except ValueError:
            await message.answer("Введите число, например: 120000")
            return False
        await state.update_data(**{state.state.split(":")[-1]: val})
        await state.set_state(next_state); await message.answer(text)
        return True

    @dp.message(Form.income)
    async def q_income(m, s): await ask_num(m,s,Form.essential,"2/13. Сколько в месяц уходит на обязательные расходы: жильё, еда, коммунальные, транспорт и т.п.? ₽")
    @dp.message(Form.essential)
    async def q_essential(m,s): await ask_num(m,s,Form.discretionary,"3/13. Сколько примерно уходит на необязательные расходы и покупки? ₽")
    @dp.message(Form.discretionary)
    async def q_disc(m,s): await ask_num(m,s,Form.debt_payment,"4/13. Сколько всего платите по кредитам/займам в месяц? ₽")
    @dp.message(Form.debt_payment)
    async def q_dp(m,s): await ask_num(m,s,Form.total_debt,"5/13. Примерный общий остаток долгов? ₽")
    @dp.message(Form.total_debt)
    async def q_td(m,s): await ask_num(m,s,Form.savings,"6/13. Сколько сейчас есть доступных накоплений/резерва? ₽")

    async def yesno(m, s, next_state, key, text, label):
        val = m.text in {"Да", "Есть", "Веду", "Планирую"}
        await s.update_data(**{key: val}); await s.set_state(next_state); await m.answer(text, reply_markup=kb("Да", "Нет"))

    @dp.message(Form.savings)
    async def q_sav(m,s):
        try: val=money(m.text); assert val>=0
        except: await m.answer("Введите число, например: 50000"); return
        await s.update_data(savings=val); await s.set_state(Form.overdue); await m.answer("7/13. Есть ли сейчас просроченные обязательства?", reply_markup=kb("Да","Нет"))
    @dp.message(Form.overdue)
    async def q_over(m,s): await yesno(m,s,Form.tracks,"has_overdue","8/13. Ведёте ли вы регулярный учёт расходов?","Учёт")
    @dp.message(Form.tracks)
    async def q_tracks(m,s):
        val=m.text=="Да"; await s.update_data(tracks_expenses=val); await s.set_state(Form.budget); await m.answer("9/13. Есть ли у семьи заранее составленный месячный бюджет?", reply_markup=kb("Да","Нет"))
    @dp.message(Form.budget)
    async def q_budget(m,s):
        val=m.text=="Да"; await s.update_data(has_budget=val); await s.set_state(Form.impulse); await m.answer("10/13. Бывают ли покупки, о которых позже жалеете, потому что они были импульсивными?", reply_markup=kb("Да","Нет"))
    @dp.message(Form.impulse)
    async def q_impulse(m,s):
        val=m.text=="Да"; await s.update_data(impulse_spending=val); await s.set_state(Form.emergency); await m.answer("11/13. Есть ли сейчас конкретная цель сформировать финансовый резерв?", reply_markup=kb("Да","Нет"))
    @dp.message(Form.emergency)
    async def q_em(m,s):
        val=m.text=="Да"; await s.update_data(emergency_goal=val); await s.set_state(Form.major_goal); await m.answer("12/13. Есть ли крупная финансовая цель на ближайшие 1–3 года?", reply_markup=kb("Да","Нет"))
    @dp.message(Form.major_goal)
    async def q_goal(m,s):
        val=m.text=="Да"; await s.update_data(major_goal=val); await s.set_state(Form.stability); await m.answer("13/13. Какой сейчас доход?", reply_markup=kb("Стабильный","Нестабильный"))
    @dp.message(Form.stability)
    async def q_stab(m,s):
        await s.update_data(income_stability="нестабильный" if m.text=="Нестабильный" else "стабильный")
        data=await s.get_data(); a=UserAnswers(**data); r=diagnose(a); storage.save(m.from_user.id,a)
        await m.answer(result_text(r), reply_markup=kb("Пройти заново"))
        ai=await explain_with_ai(r)
        if ai: await m.answer("🤖 Пояснение:\n"+ai)
        await s.clear()
    @dp.message(F.text == "Пройти заново")
    async def again(m,s): await s.set_state(Form.income); await m.answer("Начинаем заново.\n\n1/13. Средний месячный доход семьи после налогов, ₽?", reply_markup=ReplyKeyboardRemove())
    return bot, dp

async def run():
    bot, dp = make_app()
    await dp.start_polling(bot)

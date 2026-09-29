import os
import sys
import asyncio
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

# Добавляем папку app в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from bot import router
from storage import init_db

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN not found")
    sys.exit(1)

async def main():
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    init_db()
    print("Bot started")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())

# main.py
import asyncio
from aiogram import Bot, Dispatcher
from config import BOT_TOKEN, DOWNLOAD_DIR
from db.database import create_tables
from handlers import router
import os


async def main():
    create_tables()
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

    dp.include_router(router)

    print("Bot started...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Bot stopped.")

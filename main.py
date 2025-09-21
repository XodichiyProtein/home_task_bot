import logging
import asyncio
from aiogram import Dispatcher
from src.config import setup_logger, bot
from src.handlers import dp as handlers_dp
from src.button_handle import dp as buttons_dp

logger = logging.getLogger(__name__)

dp = Dispatcher()

dp.include_router(handlers_dp)
dp.include_router(buttons_dp)


async def main():
    setup_logger()
    # Удаляем вызов setup_table(), так как таблица будет инициализироваться
    # только после того, как пользователь выберет класс
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted and stopped.")
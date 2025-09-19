import logging
import asyncio
from aiogram import Dispatcher
from src.file_data import get_table_from_file
from src.table_data import HomeworkDataFrame
from src.config import setup_logger, bot, set_manager
from src.handlers import dp as handlers_dp
from src.button_handle import dp as buttons_dp

logger = logging.getLogger(__name__)

dp = Dispatcher()

dp.include_router(handlers_dp)
dp.include_router(buttons_dp)


def setup_table():
    pd_table = get_table_from_file()
    data_frame = HomeworkDataFrame(pd_table)
    set_manager(data_frame)


async def main():
    setup_logger()
    setup_table()
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot interrupted and stopped.")

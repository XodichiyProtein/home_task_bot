import logging
import sys
from config import STANDARD_LOG_FORMAT, CUSTOM_LOG_FORMAT


class CustomLoggerAdapter(logging.LoggerAdapter):
    """
    Адаптер, который безопасно добавляет поля 'user_id', 'action', 'handler' к лог-записи,
    подставляя 'N/A', если поля отсутствуют. Это предотвращает ошибки KeyError.
    """

    def process(self, msg, kwargs):
        extra = kwargs.setdefault("extra", {})

        extra.update(
            {
                "user_id": extra.get("user_id", "N/A"),
                "action": extra.get("action", "N/A"),
                "handler": extra.get("handler", "N/A"),
            }
        )

        return msg, kwargs


def setup_logging():
    """
    Централизованная функция настройки логирования.
    Создает два отдельных файла для системных логов и логов активности.
    """
    # Создаем форматтеры
    standard_formatter = logging.Formatter(STANDARD_LOG_FORMAT)
    custom_formatter = logging.Formatter(CUSTOM_LOG_FORMAT)

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.INFO)
    root_logger.handlers.clear()

    system_file_handler = logging.FileHandler(
        "system_bot.log", mode="a", encoding="utf-8"
    )
    system_file_handler.setFormatter(standard_formatter)
    system_file_handler.setLevel(logging.INFO)
    root_logger.addHandler(system_file_handler)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(standard_formatter)
    root_logger.addHandler(console_handler)

    bot_base_logger = logging.getLogger("bot_logger")
    bot_base_logger.setLevel(logging.INFO)
    # Ключевой шаг: Отключаем распространение логов в root_logger
    bot_base_logger.propagate = False

    custom_file_handler = logging.FileHandler(
        "user_activity.log", mode="a", encoding="utf-8"
    )
    custom_file_handler.setFormatter(custom_formatter)

    bot_base_logger.handlers.clear()
    bot_base_logger.addHandler(custom_file_handler)

    return CustomLoggerAdapter(bot_base_logger, {})


bot_logger = setup_logging()

import sqlite3
from typing import Optional, Tuple

DB_NAME = "db/school_bot.db"


def create_connection():
    """Создает соединение с базой данных SQLite."""
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_tables():
    """Создает таблицу 'users' для хранения данных о классе."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            class_number INTEGER,
            class_letter TEXT
        )
    """)
    conn.commit()
    conn.close()


def get_user_class(user_id: int) -> Optional[Tuple[int, str]]:
    """Получает класс и букву пользователя."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT class_number, class_letter FROM users WHERE user_id = ?", (user_id,)
    )
    result = cursor.fetchone()

    conn.close()
    return result


def set_user_class(user_id: int, class_number: int, class_letter: str):
    """Сохраняет или обновляет класс и букву пользователя."""
    conn = create_connection()
    cursor = conn.cursor()

    # Используем REPLACE INTO для вставки новой записи или замены существующей
    cursor.execute(
        """
        REPLACE INTO users (user_id, class_number, class_letter)
        VALUES (?, ?, ?)
    """,
        (user_id, class_number, class_letter),
    )

    conn.commit()
    conn.close()

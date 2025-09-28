import sqlite3
from typing import Optional, Tuple

DB_NAME = "db/school_bot.db"


def create_connection():
    """Создает соединение с базой данных SQLite."""
    conn = sqlite3.connect(DB_NAME)
    return conn


def create_tables():
    """Создает таблицу 'users' для хранения данных о классе, имени пользователя и правах разработчика."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            user_name TEXT,  
            class_number INTEGER,
            class_letter TEXT,
            is_developer INTEGER DEFAULT 0 --  права разработчика (1=Да, 0=Нет)
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


def set_user_class(user_id: int, class_number: int, class_letter: str, user_name: str):
    """Сохраняет или обновляет класс и букву пользователя."""
    conn = create_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        REPLACE INTO users (user_id, class_number, class_letter, user_name)
        VALUES (?, ?, ?, ?)
    """,
        (user_id, class_number, class_letter, user_name),
    )

    conn.commit()
    conn.close()


def is_developer(user_id: int = None, user_name: str = None) -> bool:
    """Проверяет, имеет ли пользователь права разработчика (админа)."""
    conn = create_connection()
    cursor = conn.cursor()
    
    if user_id != None:
        cursor.execute(
            "SELECT is_developer FROM users WHERE user_id = ?", (user_id,)
        )
    elif user_name != None:
        cursor.execute(
            "SELECT is_developer FROM users WHERE user_name  = ?", (user_name,)
        )
    result = cursor.fetchone()

    conn.close()
    if result != None and result[0] == 1:
        return True
    else:
        return False


def remove_developer_status(user_name: str) -> bool:
    """
    Удаляет (сбрасывает) права разработчика для указанного пользователя.
    Возвращает True, если пользователь найден и права были сброшены.
    """
    conn = None
    try:
        conn = create_connection()
        cursor = conn.cursor()

        # Обновляем столбец is_developer, устанавливая его в 0 (Нет)
        cursor.execute(
            """
            UPDATE users
            SET is_developer = 0
            WHERE user_name = ?
        """,
            (user_name,),
        )

        conn.commit()
        # Проверяем, была ли обновлена хотя бы одна строка
        return cursor.rowcount > 0

    except sqlite3.Error as e:
        print(f"Database error during removal: {e}")
        return False
    finally:
        if conn:
            conn.close()


def add_developer_status(user_name: str) -> bool:
    """
    Добавляет права разработчика для указанного пользователя.
    Возвращает True, если пользователь найден и права были установлены.
    """
    conn = None
    conn = create_connection()
    cursor = conn.cursor()

    # Обновляем столбец is_developer, устанавливая его в 1 (Да)
    cursor.execute(
        """
        UPDATE users
        SET is_developer = 1
        WHERE user_name = ?
    """,
        (user_name,),
    )

    conn.commit()
    conn.close()
    # Проверяем, была ли обновлена хотя бы одна строка
    return cursor.rowcount > 0

# parser.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import io
from typing import List, Dict
import shutil
from datetime import datetime
import csv
import re

# Указываем базовый путь для расписаний
BASE_DIR = "schedules"


def parse_excel_to_csv(file_path: str):
    """Парсит Excel файл и создает CSV с колонкой для домашнего задания."""
    try:
        df = pd.read_excel(file_path, header=None)
        date_str = _extract_date(df)
        classes = _extract_classes(df)
        all_schedules = []

        for i, class_name in enumerate(classes):
            class_df = _create_class_dataframe(df, class_name, i, date_str)
            if not class_df.empty:
                _save_class_csv(class_df, class_name, date_str)
                all_schedules.append(class_df)

        if all_schedules:
            combined_df = pd.concat(all_schedules, ignore_index=True)
            _save_combined_csv(combined_df, date_str)

        print("✅ Парсинг завершен успешно!")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False


def _extract_date(df: pd.DataFrame) -> str:
    """Извлекает дату из DataFrame."""
    try:
        raw_date = df.iloc[0, 0]
        match = re.search(r"\d{2}.\d{2}.\d{4}", str(raw_date))
        if match:
            date_obj = datetime.strptime(match.group(0), "%d.%m.%Y")
            return date_obj.strftime("%Y-%m-%d")
        else:
            # Альтернативный способ извлечения даты
            if isinstance(raw_date, datetime):
                return raw_date.strftime("%Y-%m-%d")
            return datetime.now().strftime("%Y-%m-%d")
    except:
        return datetime.now().strftime("%Y-%m-%d")


def _extract_classes(df: pd.DataFrame) -> List[str]:
    """Извлекает названия классов из DataFrame."""
    try:
        classes_raw = df.iloc[2, 3:19]  # Колонки D до S (как в исходном примере)
        classes = [
            str(c).strip() for c in classes_raw if pd.notna(c) and str(c).strip() != ""
        ]
        print(f"Найдены классы: {classes}")
        return classes
    except Exception as e:
        print(f"Ошибка при извлечении классов: {e}")
        return []


def _create_class_dataframe(
    df: pd.DataFrame, class_name: str, class_index: int, date_str: str
) -> pd.DataFrame:
    """Создает DataFrame для отдельного класса."""
    try:
        class_col_index = 3 + class_index

        lessons_data = []

        for row_idx in range(3, len(df)):
            # Проверяем, что строка содержит урок (есть номер урока и время)
            if (
                pd.notna(df.iloc[row_idx, 1])  # номер урока (колонка B)
                and pd.notna(df.iloc[row_idx, 2])
            ):  # время (колонка C)
                lesson_number = df.iloc[row_idx, 1]
                time_slot = df.iloc[row_idx, 2]
                subject = df.iloc[row_idx, class_col_index]

                # Пропускаем пустые предметы
                if pd.isna(subject) or str(subject).strip() == "":
                    continue

                # Кабинет из следующей строки
                classroom = ""
                # Проверяем, что следующая строка существует в DataFrame
                if row_idx + 1 < len(df):
                    classroom_cell = df.iloc[row_idx + 1, class_col_index]
                    if pd.notna(classroom_cell):
                        classroom = str(classroom_cell)

                lesson_data = {
                    "date": date_str,
                    "class": class_name,
                    "lesson_number": int(lesson_number)
                    if pd.notna(lesson_number)
                    else None,
                    "time_slot": str(time_slot) if pd.notna(time_slot) else "",
                    "subject": str(subject),
                    "classroom": classroom,
                    "homework": "",  # Пустая колонка для домашнего задания
                    "weekday": _get_weekday_ru(date_str),
                    "class_column": chr(65 + class_col_index),  # Буква колонки Excel
                }

                lessons_data.append(lesson_data)

        return pd.DataFrame(lessons_data)

    except Exception as e:
        print(f"Ошибка при создании DataFrame для класса {class_name}: {e}")
        return pd.DataFrame()


def _save_class_csv(df: pd.DataFrame, class_name: str, date_str: str):
    """Сохраняет DataFrame в CSV файл для отдельного класса."""
    try:
        # Очищаем имя класса от пробелов
        class_name = class_name.replace(" ", "")
        class_dir = os.path.join(BASE_DIR, class_name)
        os.makedirs(class_dir, exist_ok=True)

        file_path = os.path.join(class_dir, f"{date_str}.csv")

        # Сохраняем с правильным порядком колонок
        column_order = [
            "date",
            "class",
            "lesson_number",
            "time_slot",
            "subject",
            "classroom",
            "homework",
            "weekday",
            "class_column",
        ]

        # Оставляем только существующие колонки
        existing_columns = [col for col in column_order if col in df.columns]
        df = df[existing_columns]

        df.to_csv(file_path, index=False, encoding="utf-8")
        print(f"✅ CSV для класса {class_name} создан: {file_path} (уроков: {len(df)})")

    except Exception as e:
        print(f"❌ Ошибка при сохранении CSV для класса {class_name}: {e}")


def _get_weekday_ru(date_str: str) -> str:
    """Получает название дня недели на русском."""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        weekdays_ru = [
            "понедельник",
            "вторник",
            "среда",
            "четверг",
            "пятница",
            "суббота",
            "воскресенье",
        ]
        return weekdays_ru[date_obj.weekday()]
    except:
        return ""


def _save_combined_csv(df: pd.DataFrame, date_str: str):
    """Сохраняет объединенный CSV файл."""
    try:
        combined_file = os.path.join(BASE_DIR, f"all_classes_{date_str}.csv")
        df.to_csv(combined_file, index=False, encoding="utf-8")
        print(f"📊 Объединенный файл: {combined_file}")
    except Exception as e:
        print(f"❌ Ошибка при сохранении объединенного файла: {e}")


def create_schedule_image(class_num: int, class_letter: str, date: str) -> io.BytesIO:
    """
    Создает изображение таблицы расписания на основе данных из CSV.

    :param class_num: Номер класса (например, 9).
    :param class_letter: Буква класса (например, 'а').
    :param date: Дата в формате 'гггг-мм-дд'.
    :return: Объект BytesIO с данными изображения.
    """
    try:
        class_folder = f"{class_num}{class_letter}"
        file_path = os.path.join(BASE_DIR, class_folder, f"{date}.csv")

        if not os.path.exists(file_path):
            print(f"❌ Файл не найден: {file_path}")
            return None

        df = pd.read_csv(file_path)
        df = df.fillna("")

        # Оставляем только нужные колонки для отображения
        display_columns = []
        column_mapping = {
            "lesson_number": "№",
            "time_slot": "Время",
            "subject": "Предмет",
            "classroom": "Кабинет",
            "homework": "Домашнее задание",
        }

        for original_col, display_name in column_mapping.items():
            if original_col in df.columns:
                display_columns.append(original_col)

        df_display = df[display_columns].copy()
        df_display.columns = [column_mapping.get(col, col) for col in display_columns]

        # Создаем изображение
        fig, ax = plt.subplots(figsize=(12, 8))
        ax.axis("tight")
        ax.axis("off")

        # Создаем таблицу
        table = ax.table(
            cellText=df_display.values,
            colLabels=df_display.columns,
            loc="center",
            cellLoc="left",
        )

        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1.2, 2)

        # Заголовок
        plt.title(
            f"Расписание {class_num}{class_letter} на {date}", fontsize=14, pad=20
        )

        buf = io.BytesIO()
        plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.5, dpi=150)
        buf.seek(0)
        plt.close(fig)

        return buf

    except Exception as e:
        print(f"❌ Ошибка при создании изображения: {e}")
        return None


def get_lesson_numbers(class_num: int, class_letter: str, date: str) -> List[int]:
    """
    Получает отсортированный список номеров уроков из CSV-файла.

    :param class_num: Номер класса (например, 9).
    :param class_letter: Буква класса (например, 'а').
    :param date: Дата в формате 'гггг-мм-дд'.
    :return: Список номеров уроков ([1, 2, 3, 4, 5, 7]) или пустой список, если файл не найден.
    """
    try:
        class_folder = f"{class_num}{class_letter}"
        file_path = os.path.join(BASE_DIR, class_folder, f"{date}.csv")

        if not os.path.exists(file_path):
            return []

        df = pd.read_csv(file_path)

        if "lesson_number" not in df.columns:
            return []

        # Убираем NaN значения и преобразуем к int
        lesson_numbers = [int(x) for x in df["lesson_number"].dropna().unique()]
        lesson_numbers.sort()

        return lesson_numbers

    except Exception as e:
        print(f"❌ Ошибка при чтении файла {file_path}: {e}")
        return []


def run(filepath: str):
    """Основная функция для запуска парсинга."""
    try:
        return parse_excel_to_csv(filepath)
    except Exception as e:
        print(f"❌ Ошибка при запуске парсера: {e}")
        return False


def edit_homework(
    class_num: int, class_letter: str, date: str, lesson_number: int, new_homework: str
) -> bool:
    """
    Редактирует домашнее задание для указанного урока в CSV-файле.

    :param class_num: Номер класса (например, 9).
    :param class_letter: Буква класса (например, 'а').
    :param date: Дата в формате 'гггг-мм-дд'.
    :param lesson_number: Номер урока.
    :param new_homework: Новое домашнее задание.
    :return: True, если обновление прошло успешно, False в противном случае.
    """
    try:
        class_folder = f"{class_num}{class_letter}"
        file_path = os.path.join(BASE_DIR, class_folder, f"{date}.csv")

        if not os.path.exists(file_path):
            print(f"❌ Ошибка: Файл {file_path} не найден.")
            return False

        df = pd.read_csv(file_path)

        # Проверяем существование урока
        if lesson_number not in df["lesson_number"].values:
            print(f"❌ Урок №{lesson_number} не найден в расписании.")
            return False

        # Обновляем домашнее задание
        df.loc[df["lesson_number"] == lesson_number, "homework"] = new_homework

        # Сохраняем обратно
        df.to_csv(file_path, index=False, encoding="utf-8")

        print(f"✅ Домашнее задание для урока {lesson_number} успешно обновлено.")
        return True

    except Exception as e:
        print(f"❌ Ошибка при редактировании файла: {e}")
        return False


def get_class_schedule(class_num: int, class_letter: str, date: str) -> pd.DataFrame:
    """
    Получает расписание класса в виде DataFrame.

    :param class_num: Номер класса
    :param class_letter: Буква класса
    :param date: Дата
    :return: DataFrame с расписанием или None если не найден
    """
    try:
        class_folder = f"{class_num}{class_letter}"
        file_path = os.path.join(BASE_DIR, class_folder, f"{date}.csv")

        if os.path.exists(file_path):
            return pd.read_csv(file_path)
        return None
    except Exception as e:
        print(f"❌ Ошибка при получении расписания: {e}")
        return None


# Дополнительная функция для отладки
def debug_file_structure(file_path: str):
    """Функция для отладки структуры Excel файла"""
    try:
        df = pd.read_excel(file_path, header=None)
        print("🔍 Структура файла:")
        print(f"Размер: {df.shape}")
        print("\nПервые 5 строк:")
        print(df.head(10))
        print("\nКлассы в строке 3:")
        print(df.iloc[2, 2:].tolist())
    except Exception as e:
        print(f"❌ Ошибка при анализе файла: {e}")

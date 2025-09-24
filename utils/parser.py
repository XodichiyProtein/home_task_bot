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
    except:
        return ""


def _extract_classes(df: pd.DataFrame) -> List[str]:
    """Извлекает названия классов из DataFrame."""
    try:
        classes_raw = df.iloc[2, 2:]
        return [str(c).strip() for c in classes_raw if pd.notna(c)]
    except:
        return []


def _create_class_dataframe(
    df: pd.DataFrame, class_name: str, class_index: int, date_str: str
) -> pd.DataFrame:
    """Создает DataFrame для отдельного класса."""
    try:
        class_column_start = 2 + class_index
        class_column_end = class_column_start + 2

        # Добавляем 1 столбец для домашнего задания
        columns_to_extract = [1] + list(range(class_column_start, class_column_end))
        class_df = df.iloc[4:, columns_to_extract].copy()
        class_df.columns = ["lesson_number", "subject"]
        class_df["homework"] = ""
        class_df["class"] = class_name
        class_df["date"] = date_str
        class_df["weekday"] = _get_weekday_ru(date_str)
        class_df["class_column"] = ""

        class_df = class_df.dropna(subset=["lesson_number", "subject"], how="all")
        return class_df
    except:
        return pd.DataFrame()


def _save_class_csv(df: pd.DataFrame, class_name: str, date_str: str):
    """Сохраняет DataFrame в CSV файл для отдельного класса."""
    class_name = class_name.replace(" ", "")
    class_dir = os.path.join(BASE_DIR, class_name)
    os.makedirs(class_dir, exist_ok=True)
    file_path = os.path.join(class_dir, f"{date_str}.csv")
    df.to_csv(file_path, index=False, encoding="utf-8")
    print(f"✅ CSV для класса {class_name} создан: {file_path}")


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
    combined_file = os.path.join(BASE_DIR, f"all_classes_{date_str}.csv")
    df.to_csv(combined_file, index=False, encoding="utf-8")
    print(f"📊 Объединенный файл: {combined_file}")


def create_schedule_image(class_num: int, class_letter: str, date: str) -> io.BytesIO:
    """
    Создает изображение таблицы расписания на основе данных из CSV.

    :param class_num: Номер класса (например, 9).
    :param class_letter: Буква класса (например, 'а').
    :param date: Дата в формате 'гггг-мм-дд'.
    :return: Объект BytesIO с данными изображения.
    """
    class_folder = f"{class_num}{class_letter}"
    file_path = f"schedules/{class_folder}/{date}.csv"

    if not os.path.exists(file_path):
        return None

    df = pd.read_csv(file_path)

    df = df.fillna("")
    cols_to_drop = ["date", "class", "weekday", "class_column"]
    df = df.drop(
        columns=[col for col in cols_to_drop if col in df.columns], errors="ignore"
    )

    if "lesson_number" in df.columns:
        df = df.rename(columns={"lesson_number": "№"})
    if "time_slot" in df.columns:
        df = df.rename(columns={"time_slot": "время"})
    if "classroom" in df.columns:
        df = df.rename(columns={"classroom": "каб"})
    if "subject" in df.columns:
        df = df.rename(columns={"subject": "урок"})
    if "homework" in df.columns:
        df = df.rename(columns={"homework": "ДЗ"})

    fig, ax = plt.subplots(figsize=(8, 12))
    ax.axis("tight")
    ax.axis("off")

    table = ax.table(cellText=df.values, colLabels=df.columns, loc="center")
    table.auto_set_font_size(False)
    table.set_fontsize(12)
    table.scale(1.2, 1.2)

    for i in range(len(df.columns)):
        table.auto_set_column_width(col=i)

    buf = io.BytesIO()
    plt.savefig(buf, format="png", bbox_inches="tight", pad_inches=0.5)
    buf.seek(0)
    plt.close(fig)

    return buf


def get_lesson_numbers(class_num: int, class_letter: str, date: str) -> List[int]:
    """
    Получает отсортированный список номеров уроков из CSV-файла.

    :param class_num: Номер класса (например, 9).
    :param class_letter: Буква класса (например, 'а').
    :param date: Дата в формате 'гггг-мм-дд'.
    :return: Список номеров уроков ([1, 2, 3, 4, 5, 7]) или пустой список, если файл не найден.
    """
    class_folder = f"{class_num}{class_letter}"
    file_path = f"schedules/{class_folder}/{date}.csv"

    if not os.path.exists(file_path):
        return []

    try:
        df = pd.read_csv(file_path)

        if "lesson_number" not in df.columns:
            return []

        lesson_numbers = df["lesson_number"].unique().tolist()
        lesson_numbers.sort()

        return lesson_numbers

    except Exception as e:
        print(f"Ошибка при чтении файла {file_path}: {e}")
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
    class_folder = f"{class_num}{class_letter}"
    file_path = f"schedules/{class_folder}/{date}.csv"

    if not os.path.exists(file_path):
        print(f"❌ Ошибка: Файл {file_path} не найден.")
        return False

    try:
        df = pd.read_csv(file_path)

        # Находим строку, которую нужно обновить
        # Используем .loc для безопасного обновления
        df.loc[df["lesson_number"] == lesson_number, "homework"] = new_homework

        # Сохраняем измененный DataFrame обратно в CSV
        df.to_csv(file_path, index=False)

        print(f"✅ Домашнее задание для урока {lesson_number} успешно обновлено.")
        return True

    except Exception as e:
        print(f"❌ Ошибка при редактировании файла: {e}")
        return False

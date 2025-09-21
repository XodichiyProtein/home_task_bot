# src/table_data.py

import logging
from enum import Enum
from typing import TypeAlias
from pandas import DataFrame
import pandas as pd
import textwrap
import matplotlib.pyplot as plt
from src.file_data import save_to_file

logger = logging.getLogger(__name__)


class Subject(Enum):
    # Основные предметы
    MATH = "Математика"
    RUSSIAN = "Русский язык"
    LITERATURE = "Литература"
    ENGLISH = "Английский язык"

    # Естественные науки
    PHYSICS = "Физика"
    CHEMISTRY = "Химия"
    BIOLOGY = "Биология"
    GEOGRAPHY = "География"

    # Гуманитарные науки
    HISTORY = "История"
    SOCSCIENCE = "Обществознание"

    # Технические предметы
    COMPSIENCE = "Информатика"

    OBZH = "ОБЖ"


class Day(Enum):
    MONDAY = "Понедельник"
    TUESDAY = "Вторник"
    WEDNESDAY = "Среда"
    THURSDAY = "Четверг"
    FRIDAY = "Пятница"
    SATURDAY = "Суббота"


Homework: TypeAlias = str


def wrap_text_in_dataframe(df, width=30):
    """
    Оборачивает текст в DataFrame, чтобы он не был слишком длинным.
    """
    # Исправлено: замена .applymap на .map для избежания предупреждения
    wrapped_df = df.map(lambda x: textwrap.fill(str(x), width) if x else "")
    return wrapped_df


class HomeworkDataFrame:
    def __init__(self, pd_table: DataFrame, class_name: str) -> None:
        self.table: DataFrame = pd_table
        self.class_name: str = class_name

    def get_homework(self, subject: Subject, day: Day) -> Homework | None:
        try:
            homework_text = self.table.loc[subject.value, day.value]
            return str(homework_text).strip()
        except KeyError as e:
            logger.error("Неправильно имя столбца или колонки: %s", e)
            return None

    def set_homework(self, subject: Subject, day: Day, homework: Homework) -> bool:
        try:
            self.table.loc[subject.value, day.value] = homework

            self._save()
            logger.info(
                "Пользователь добавил домашнюю работу для %s, %s %s",
                self.class_name,
                subject.value,
                day.value,
            )
            return True
        except KeyError as e:
            logger.error("Неправильно имя столбца или колонки: %s", e)
            return False

    def clear_homework(self, subject: Subject, day: Day) -> bool:
        try:
            self.table.loc[subject.value, day.value] = ""
            self._save()
            logger.info(
                "Пользователь удалил домашнюю работу для %s, %s %s",
                self.class_name,
                subject.value,
                day.value,
            )
            return True
        except KeyError as e:
            logger.error("Неправильно имя столбца или колонки: %s", e)
            return False

    def to_markdown(self) -> str:
        md = self.table.to_markdown()
        return md

    def _save(self):
        save_to_file(self.table, self.class_name)

    def table_to_image(self, filename: str) -> str:
        if isinstance(self.table, DataFrame):
            table_copy = self.table.copy()
            processed_table = wrap_text_in_dataframe(table_copy, width=20)
            
            # Исправлено: замена .applymap на .map для избежания предупреждения
            max_len = processed_table.map(lambda x: len(x)).values.max()

            data = processed_table.values
            columns = processed_table.columns.tolist()
            rows = processed_table.index.tolist()

            # Создаем фигуру и оси
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis("off")
            # Создаем таблицу
            table = ax.table(
                cellText=data,
                colLabels=columns,
                rowLabels=rows,
                loc="center",
            )

            # Настраиваем стиль таблицы
            table.auto_set_font_size(False)
            if max_len <= 52:
                table.set_fontsize(10)
            elif max_len <= 140:
                table.set_fontsize(6)
            elif max_len <= 332:
                table.set_fontsize(4)
            else:
                table.set_fontsize(3.5)
            table.scale(1, 6)

            # Исправлено: замена fig.tight_layout() на настройку bbox_inches
            # это решает проблему с отступами и предупреждением
            
            # Сохраняем изображение в файл
            plt.savefig(filename, bbox_inches="tight", dpi=150)
            plt.close(fig)

            return filename
        return ""
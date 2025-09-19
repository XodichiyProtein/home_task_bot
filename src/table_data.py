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
    ASTRONOMY = "Астрономия"

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
    Оборачивает текст в каждой ячейке DataFrame, чтобы он не выходил за границы.
    """
    for col in df.columns:
        # Проверяем, является ли столбец строковым (object)
        if df[col].dtype == "object":
            df[col] = df[col].apply(
                lambda x: "\n".join(textwrap.wrap(x, width))
                if isinstance(x, str)
                else x
            )
    return df


class HomeworkDataFrame:
    def __init__(self, pd_table: DataFrame) -> None:
        self.table: DataFrame = pd_table

    def get_homework(self, subject: Subject, day: Day) -> Homework | None:
        try:
            homework: Homework = str(self.table.loc[subject.value, day.value])
            return homework
        except KeyError as e:
            logger.error("Неправильно имя столбца или колонки: %s", e)
            return None

    def set_homework(self, subject: Subject, day: Day, homework: Homework) -> bool:
        try:
            self.table.loc[subject.value, day.value] = homework

            self._save()
            logger.info(
                "Пользователь добавил домашнюю работу, %s %s", subject.value, day.value
            )
            return True
        except KeyError as e:
            logger.error("Неправильно имя столбца или колонки: %s", e)
            return False

    def clear_homework(self, subject: Subject, day: Day) -> bool:
        try:
            self.table.loc[subject.value, day.value] = ""
            self._save()
            return True
        except KeyError as e:
            logger.error("Неправильно имя столбца или колонки: %s", e)
            return False

    def to_list_of_lists(self) -> list[list[str]]:
        headers = ["Предмет"] + self.table.columns.tolist()

        data_rows = []
        for idx, row in self.table.iterrows():
            row_data = [str(idx)] + [str(val) if pd.notnull(val) else "" for val in row]
            data_rows.append(row_data)

        return [headers] + data_rows

    def table_to_string(self, max_width: int = 20) -> str:
        table_list = self.to_list_of_lists()

        if not table_list or not table_list[0]:
            return "┌\n│ Пустая таблица\n└"

        # Calculate column widths, considering wrapped text
        wrapped_table = []
        for row in table_list:
            wrapped_row = []
            max_lines = 1
            for cell in row:
                wrapped_cell = textwrap.wrap(str(cell), width=max_width)
                wrapped_row.append(wrapped_cell)
                if len(wrapped_cell) > max_lines:
                    max_lines = len(wrapped_cell)
            # Pad wrapped cells to have the same number of lines
            for i in range(len(wrapped_row)):
                wrapped_row[i] += [""] * (max_lines - len(wrapped_row[i]))
            wrapped_table.append(wrapped_row)

        col_widths = [0] * len(table_list[0])
        for row in wrapped_table:
            for j, cell_lines in enumerate(row):
                for line in cell_lines:
                    if len(line) > col_widths[j]:
                        col_widths[j] = len(line)

        # Build the table string
        result = []
        # Top border
        result.append("┌" + "─".join("─" * (w + 2) for w in col_widths) + "┐")

        for i, row in enumerate(wrapped_table):
            max_lines_in_row = max(len(cell_lines) for cell_lines in row)
            for line_idx in range(max_lines_in_row):
                formatted_row = []
                for j, cell_lines in enumerate(row):
                    content = cell_lines[line_idx] if line_idx < len(cell_lines) else ""
                    formatted_row.append(f" {content:<{col_widths[j]}} ")
                result.append("│" + "│".join(formatted_row) + "│")
            if i == 0:  # Header separator
                result.append("├" + "─".join("─" * (w + 2) for w in col_widths) + "┤")

        # Bottom border
        result.append("└" + "─".join("─" * (w + 2) for w in col_widths) + "┘")

        return f"```{'\n'.join(result)}```"

    def get_max_cell_length(self) -> int:
        """
        Вычисляет максимальную длину текста во всех ячейках DataFrame,
        включая заголовки.
        """
        # 1. Сначала найдем максимальную длину среди всех значений в таблице
        # Преобразуем DataFrame в строковый формат, чтобы корректно посчитать длину
        df_str = self.table.astype(str)

        # Используем stack() для преобразования DataFrame в Series,
        # что упрощает поиск максимальной длины
        max_data_length = df_str.stack().str.len().max()

        # 2. Затем найдем максимальную длину среди заголовков столбцов
        max_header_length = max(len(str(col)) for col in self.table.columns)

        # 3. Вернем максимальное значение из двух
        return max(max_data_length, max_header_length)

    def _save(self):
        save_to_file(self.table)

    def table_to_image(self, filename: str = "homework_table.png") -> str | None:
        try:
            max_len = self.get_max_cell_length()
            # 💡 Новая строка: обрабатываем таблицу перед генерацией
            if max_len <= 52:
                print(1)
                processed_table = wrap_text_in_dataframe(self.table.copy(), 10)
            elif max_len <= 140:
                print(2)
                processed_table = wrap_text_in_dataframe(self.table.copy(), 20)
            elif max_len <= 332:
                print(3)
                processed_table = wrap_text_in_dataframe(self.table.copy(), 31)
            else:
                print(4)
                processed_table = wrap_text_in_dataframe(self.table.copy(), 40)

            # Получаем данные и заголовки из обработанного DataFrame
            data = processed_table.values
            columns = processed_table.columns.tolist()
            rows = processed_table.index.tolist()

            # Создаем фигуру и оси
            fig, ax = plt.subplots(figsize=(10, 4))
            ax.axis("off")  # Скрываем оси

            # Создаем таблицу
            table = ax.table(
                cellText=data,  # type: ignore
                colLabels=columns,
                rowLabels=rows,
                loc="center",  # type: ignore
            )

            # Настраиваем стиль таблицы
            table.auto_set_font_size(False)
            if max_len <= 52:
                print(1)
                table.set_fontsize(10)
            elif max_len <= 140:
                print(2)
                table.set_fontsize(6)
            elif max_len <= 332:
                print(3)
                table.set_fontsize(4)
            else:
                print(4)
                table.set_fontsize(3.5)
            table.scale(1, 6)

            # Подгоняем размер фигуры под таблицу
            fig.tight_layout()

            # Сохраняем изображение в файл
            plt.savefig(filename, bbox_inches="tight", dpi=150)
            plt.close(fig)  # Закрываем фигуру

            return filename

        except Exception as e:
            # logger.error(f"Ошибка при генерации изображения: {e}")
            print(f"Ошибка при генерации изображения: {e}")
            return None

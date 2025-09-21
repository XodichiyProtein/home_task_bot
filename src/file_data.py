import pandas as pd
from pandas import DataFrame
import re
from io import StringIO
import src.config as conf
from pathlib import Path

yaml = ""


def _get_text_from_file(file_path: Path) -> str:
    """
    Читает содержимое Markdown файла. Если файл не существует, создает пустую таблицу.
    """
    if not file_path.exists():
        # Возвращаем пустую таблицу Markdown
        return "| Предмет | Понедельник | Вторник | Среда | Четверг | Пятница | Суббота |\n| :--- | :--- | :--- | :--- | :--- | :--- | :--- |\n| Математика | | | | | | |\n| Русский язык | | | | | | |\n| Литература | | | | | | |\n| Английский язык | | | | | | |\n| Физика | | | | | | |\n| Химия | | | | | | |\n| Биология | | | | | | |\n| География | | | | | | |\n| Астрономия | | | | | | |\n| История | | | | | | |\n| Обществознание | | | | | | |\n| Информатика | | | | | | |\n| ОБЖ | | | | | | |\n"

    with open(file_path, mode="r", encoding="utf-8") as file:
        text = file.read()
    return text


def _remove_frontmatter(md_text: str) -> str:
    global yaml
    frontmatter_match = re.match(r"^---(.*?)---\s*", md_text, flags=re.DOTALL)
    frontmatter = ""
    table = md_text

    if frontmatter_match:
        frontmatter = frontmatter_match.group(0)
        yaml = frontmatter
        table = re.sub(r"^---.*?---\s*", "", md_text, flags=re.DOTALL).strip()

    lines = table.splitlines()

    lines_filtered = [
        line
        for line in lines
        if not (
            all(part.strip("- ") == "" for part in line.split("|")[1:-1])
            or re.match(r"^\|[:\s-]+?\|", line)
        )
    ]

    table = "\n".join(lines_filtered)

    return table


def _clean_dataframe(df: DataFrame) -> DataFrame:
    df.columns = df.columns.str.strip()

    df = df.fillna("")

    for col in df.select_dtypes(include=["object"]):
        df[col] = df[col].str.strip()
        df[col] = df[col].str.replace(r"\s+", " ", regex=True)

    return df


def get_table_from_file(class_name: str) -> DataFrame:
    """
    Загружает таблицу из файла, соответствующего классу.
    """
    file_path = conf.get_table_path_for_class(class_name)
    text = _get_text_from_file(file_path)
    text_table = _remove_frontmatter(text)

    table = pd.read_csv(
        StringIO(text_table), sep="|", engine="python", skipinitialspace=True
    ).iloc[:, 1:-1]
    table = _clean_dataframe(table)

    table.set_index("Предмет", inplace=True)

    return table


def save_to_file(table: DataFrame, class_name: str) -> None:
    """
    Сохраняет DataFrame в Markdown файл, соответствующий классу.
    """
    global yaml
    file_path = conf.get_table_path_for_class(class_name)
    df_to_save = table.reset_index()
    markdown_table = df_to_save.to_markdown(index=False)

    with open(file_path, mode="w", encoding="utf-8") as file:
        if yaml:
            file.write(yaml)
        file.write(markdown_table + "\n")
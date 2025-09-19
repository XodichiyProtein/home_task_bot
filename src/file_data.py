import pandas as pd
from pandas import DataFrame
import re
from io import StringIO
import src.config as conf

yaml = ""


def _get_text_from_file() -> str:
    with open(conf.FILE_PATH, mode="r", encoding="utf-8") as file:
        text = file.read()
    file.close()
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

    # Фильтруем строки, содержащие только тире или разделители Markdown (:---, ---, :--:, etc.)
    lines_filtered = [
        line
        for line in lines
        if not (
            all(part.strip("- ") == "" for part in line.split("|")[1:-1])
            or re.match(r"^\|[:\s-]+?\|", line)
        )
    ]

    # Склеиваем строки обратно
    table = "\n".join(lines_filtered)

    return table


def _clean_dataframe(df: DataFrame) -> DataFrame:
    df.columns = df.columns.str.strip()

    df = df.fillna("")

    for col in df.select_dtypes(include=["object"]):
        df[col] = df[col].str.strip()
        df[col] = df[col].str.replace(r"\s+", " ", regex=True)

    return df


def get_table_from_file() -> DataFrame:
    text = _get_text_from_file()
    text_table = _remove_frontmatter(text)

    print("Очищенный текст таблицы:\n", text_table)

    table = pd.read_csv(
        StringIO(text_table), sep="|", engine="python", skipinitialspace=True
    ).iloc[:, 1:-1]
    table = _clean_dataframe(table)

    print("Имена столбцов до установки индекса:", table.columns.tolist())
    table.set_index("Предмет", inplace=True)

    print("Имена столбцов после очистки:", table.columns.tolist())
    print("Индексы после установки:", table.index.tolist())

    return table


def save_to_file(table: DataFrame) -> None:
    global yaml
    df_to_save = table.reset_index()
    markdown_table = df_to_save.to_markdown(index=False)

    with open(conf.FILE_PATH, mode="w", encoding="utf-8") as file:
        if yaml:
            file.write(yaml)
        file.write(markdown_table + "\n")

    file.close()

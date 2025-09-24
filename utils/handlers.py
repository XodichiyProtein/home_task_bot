import os
from typing import List
from dotenv import set_key, find_dotenv

DOTENV_PATH = find_dotenv()


def UPDATE_DEVELOPER_IDS_PERMANENTLY(new_id: int, current_dev_list: List[int]):
    if new_id not in current_dev_list:
        current_dev_list.append(new_id)
    new_dev_ids_str = ",".join(map(str, current_dev_list))
    set_key(
        dotenv_path=DOTENV_PATH,
        key_to_set="DEVELOPER_IDS",
        value_to_set=new_dev_ids_str,
    )
    print(
        f"ID {new_id} добавлен в DEVELOPER_IDS. Обновлен файл .env. Текущий список: {current_dev_list}"
    )


def REMOVE_DEVELOPER_ID_PERMANENTLY(remove_id: int, current_dev_list: List[int]):
    if remove_id in current_dev_list:
        current_dev_list.remove(remove_id)
    else:
        return False
    new_dev_ids_str = ",".join(map(str, current_dev_list))
    set_key(
        dotenv_path=DOTENV_PATH,
        key_to_set="DEVELOPER_IDS",
        value_to_set=new_dev_ids_str,
    )
    print(f"ID {remove_id} удален из DEVELOPER_IDS. Обновлен файл .env.")
    return True

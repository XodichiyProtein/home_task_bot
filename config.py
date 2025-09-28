from typing import Dict, List
from dotenv import load_dotenv, find_dotenv
import os
import logging
import sys


load_dotenv(find_dotenv())

BOT_TOKEN = os.getenv("BOT_TOKEN")

CLASS_CONFIG: Dict[int, List[str]] = {
    5: ["а", "б"],
    6: ["а", "б"],
    7: ["а", "б", "в"],
    8: ["а", "б", "в"],
    9: ["а", "б", "в"],
    10: ["а", "б"],
    11: ["а", "б"],
}

DOWNLOAD_DIR = "downloads/"

COMPLAINTS_FILE = 'db/complaints.json'
COMPLAINTS_DATA = [] 
NEXT_COMPLAINT_ID = 1

ANNOUNCEMENTS_DATA = [] 
NEXT_ANNOUNCEMENT_ID = 1 
ANNOUNCEMENTS_FILE = 'db/announcements.json'


CLASS_PREFIX = "select_class_"
LETTER_PREFIX = "select_letter_"
MENU_PREFIX = "menu_"
DEV_PREFIX = "dev_"
EDIT_HOMEWORK_PREFIX = "edit_hw_"
BACK_PREFIX = "back_"
ANN_PREFIX = "ann_" 
FB_PREFIX = "fb_"

CUSTOM_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - UserID:%(user_id)s - Action:%(action)s - Handler:%(handler)s - %(message)s"
STANDARD_LOG_FORMAT = "%(asctime)s - [%(levelname)s] - %(name)s - %(message)s"



import os
from dotenv import load_dotenv

# Загружаем переменные из файла .env
load_dotenv()
class Config:
    ORDERS_PATH = os.getenv("ORDERS_PATH")
    SAVE_SCANNED_TXT_PATH = os.getenv("SAVE_SCANNED_TXT_PATH")
    host = os.getenv("host")
    port=int(os.getenv("port"))
    USER_DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("USER_DB_USER"),
        "password": os.getenv("USER_DB_PASSWORD"),
        "db": os.getenv("USER_DB_NAME"),
    }
    DM_DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("DM_DB_USER"),
        "password": os.getenv("DM_DB_PASSWORD"),
        "db": os.getenv("DM_DB_NAME"),
    }
    CNT_DB_CONFIG = {
        "host": os.getenv("DB_HOST"),
        "user": os.getenv("CNT_DB_USER"),
        "password": os.getenv("CNT_DB_PASSWORD"),
        "db": os.getenv("CNT_DB_NAME"),
    }
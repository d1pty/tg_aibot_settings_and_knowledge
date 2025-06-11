import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
F5AI_API_KEY = os.getenv("F5AI_API_KEY")
ADMIN_GROUP_ID = int(os.getenv("ADMIN_GROUP_ID", -1000000000))
DB_PATH = os.getenv("DB_PATH", "bot_data.db")

# Кнопки для главного меню и подменю
BTN_SETTINGS = "🔧 Настройки"
BTN_KNOWLEDGE = "📚 Знания"
BTN_CHANGE = "Изменить"
BTN_BACK = "Назад"
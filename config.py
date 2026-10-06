"""
Конфигурация демонстрационного стенда Hermes Agent для Битрикс24 и 1C:ERP.
Автоматически считывает переменные окружения из .env и системного профиля Hermes.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Пути к директориям
BASE_DIR = Path(__file__).resolve().parent
HERMES_USER_ENV = Path(os.environ.get("USERPROFILE", "C:/Users/ai86")) / "AppData" / "Local" / "hermes" / ".env"

# 1. Сначала загружаем локальный .env (если есть)
load_dotenv(BASE_DIR / ".env")

# 2. Затем догружаем системный .env от Hermes
if HERMES_USER_ENV.exists():
    load_dotenv(HERMES_USER_ENV, override=False)

# Telegram настройки
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ROP_CHAT_ID = os.getenv("TELEGRAM_ROP_CHAT_ID", "")  # ID чата РОПа для дашборда

# Битрикс24 настройки
# Формат вебхука: https://your-domain.bitrix24.ru/rest/USER_ID/WEBHOOK_CODE/
BITRIX24_WEBHOOK_URL = os.getenv("BITRIX24_WEBHOOK_URL", "")

# LLM настройки (для анализа звонков и распознавания голоса/команд)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY", "")

# Флаг принудительной симуляции (если ключи не указаны или нет интернета, стенд работает на 100% стабильно)
SIMULATION_MODE = os.getenv("HERMES_SIMULATION_MODE", "true").lower() in ("true", "1", "yes")

# Порт локального веб-дашборда
DASHBOARD_PORT = int(os.getenv("DASHBOARD_PORT", "8000"))

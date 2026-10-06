"""
Telegram-бот Hermes Agent для демонстрации на созвоне.
Работает через официальный Telegram Bot API (httpx long-polling).
Позволяет отправлять голосовые и текстовые команды руководителю и РОПу.
"""

import sys
import time
import httpx
from typing import Optional

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import TELEGRAM_BOT_TOKEN
from modules.bitrix_client import BitrixClient
from modules.call_analyzer import CallAnalyzer
from modules.erp_prompter import ErpPrompter
from modules.erp_auditor import ErpAuditor
from modules.task_parser import TaskParser
from modules.telegram_reporter import TelegramReporter
from sample_data import SAMPLE_CALLS

b24 = BitrixClient()
analyzer = CallAnalyzer(b24)
prompter = ErpPrompter()
auditor = ErpAuditor()
task_parser = TaskParser(b24)
reporter = TelegramReporter()

def send_msg(chat_id: int, text: str, reply_markup: Optional[dict] = None):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        with httpx.Client(timeout=10.0) as client:
            client.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки Telegram: {e}")

def get_main_keyboard():
    return {
        "keyboard": [
            [{"text": "📞 Разбор звонков (Битрикс24)"}, {"text": "🧠 1C:ERP Суфлёр"}],
            [{"text": "🚨 1С:ERP Аудит ошибок"}, {"text": "📊 Вечерний дашборд РОПа"}],
            [{"text": "📌 Поставить задачу технологу"}]
        ],
        "resize_keyboard": True
    }

def handle_message(msg: dict):
    chat_id = msg["chat"]["id"]
    text = msg.get("text", "")
    voice = msg.get("voice")

    # Обработка голосового сообщения
    if voice:
        send_msg(chat_id, "🎙 <i>Hermes Agent распознает голосовое сообщение...</i>")
        time.sleep(1.0)
        # Симулируем распознавание реальной фразы из ТЗ Яны
        recognized_text = "Поставь задачу технологу Петрову проверить чертеж партии к 15:00"
        send_msg(chat_id, f"📝 <b>Распознано:</b> «{recognized_text}»")
        
        # Создаем задачу
        res = task_parser.parse_and_create_task(recognized_text, creator="Руководитель (голос)")
        send_msg(chat_id, res["confirmation"])
        return

    # Текстовые команды и кнопки
    if text in ("/start", "start"):
        welcome = """🤖 <b>Добро пожаловать в Hermes Agent B2B Supervisor!</b>

Я интеллектуальный ассистент над <b>Битрикс24</b> и <b>1C:ERP</b>:
• Контролирую соблюдение регламентов продаж в звонках
• Подсказываю менеджерам остатки и задолженности из 1С
• Провожу аудит зависших заказов на производстве
• Принимаю голосовые поручения и ставлю задачи в CRM

Выберите сценарий на кнопках ниже или отправьте голосовое сообщение!"""
        send_msg(chat_id, welcome, get_main_keyboard())

    elif "разбор звонков" in text.lower() or text == "/call":
        send_msg(chat_id, "⏳ <i>Загружаю аудиозапись последнего звонка из Битрикс24...</i>")
        time.sleep(1.0)
        res = analyzer.analyze_call(SAMPLE_CALLS["call_poor"])
        send_msg(chat_id, res["timeline_comment"])
        if res.get("task_created"):
            t = res["task_created"]
            warn = (
                f"⚡️ <b>АВТО-РЕАКЦИЯ В CRM:</b>\n"
                f"Так как оценка {res['score']}/10 и нет следующего шага, создана задача в Битрикс24:\n"
                f"<b>{t['title']}</b>\n"
                f"Исполнитель: Менеджер Иванов С. (Дедлайн: сегодня 18:00)"
            )
            send_msg(chat_id, warn)

    elif "суфлёр" in text.lower() or text == "/prompter":
        card = prompter.get_prompt_for_client("CLIENT_001")
        send_msg(chat_id, card["formatted_card"])

    elif "аудит" in text.lower() or text == "/audit":
        audit_res = auditor.run_daily_audit()
        send_msg(chat_id, audit_res["director_report"])

    elif "дашборд" in text.lower() or text == "/report":
        digest = reporter.generate_rop_evening_digest()
        send_msg(chat_id, digest)

    elif "поставить задачу" in text.lower() or text.lower().startswith("поставь задачу"):
        sample = text if len(text) > 20 else "Поставь задачу технологу Петрову проверить чертеж партии к 15:00"
        res = task_parser.parse_and_create_task(sample, creator="Руководитель")
        send_msg(chat_id, res["confirmation"])

    else:
        # Пытаемся разобрать произвольный текст как поручение
        res = task_parser.parse_and_create_task(text, creator="Руководитель")
        send_msg(chat_id, res["confirmation"])

def run_bot():
    if not TELEGRAM_BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN не задан. Бот работает в режиме консольной симуляции.")
        return

    print(f"[*] Hermes Telegram Bot запущен в режиме polling...")
    offset = 0
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/getUpdates"

    while True:
        try:
            with httpx.Client(timeout=30.0) as client:
                resp = client.get(url, params={"offset": offset, "timeout": 20})
                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get("result", []):
                        offset = update["update_id"] + 1
                        if "message" in update:
                            handle_message(update["message"])
                elif resp.status_code == 409:
                    print("[!] Конфликт getUpdates (возможно, другой процесс слушает этого бота). Пауза 5 сек...")
                    time.sleep(5)
                else:
                    time.sleep(2)
        except Exception as e:
            print(f"[!] Ошибка polling: {e}")
            time.sleep(3)

if __name__ == "__main__":
    run_bot()

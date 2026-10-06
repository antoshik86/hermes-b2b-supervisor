"""
Модуль формирования вечерних сводок и отправки отчетов в Telegram для РОПа и руководства.
"""

from typing import Dict, Any, Optional
import httpx
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_ROP_CHAT_ID

class TelegramReporter:
    def __init__(self, bot_token: Optional[str] = None, rop_chat_id: Optional[str] = None):
        self.bot_token = bot_token or TELEGRAM_BOT_TOKEN
        self.rop_chat_id = rop_chat_id or TELEGRAM_ROP_CHAT_ID

    def generate_rop_evening_digest(self) -> str:
        """
        Формирует вечерний аналитический дашборд для РОПа.
        """
        digest = """📊 <b>HERMES SALES INTELLIGENCE: Вечерний дашборд РОПа</b>
📅 <i>Итоги рабочего дня | Завод металлоконструкций</i>
━━━━━━━━━━━━━━━━━━━━━━━━━━━

📞 <b>Контроль звонков и CRM:</b>
• Всего обработано звонков: <b>45</b>
• Средний балл по регламенту: <b>7.8 / 10</b> ⭐️
• Звонков с нарушениями регламента: <b>4</b> (задачи на перезвон поставлены)

🏆 <b>Рейтинг менеджеров:</b>
🥇 <b>Смирнова Анна:</b> 18 звонков | Средний балл: <b>9.4</b> (100% со следующим шагом)
🥈 <b>Ковалев Дмитрий:</b> 15 звонков | Средний балл: <b>8.1</b> (1 перенос)
⚠️ <b>Иванов Сергей:</b> 12 звонков | Средний балл: <b>6.2</b> 
    ↳ <i>3 зависших лида без даты след. контакта (авто-задачи созданы: #1024, #1025)</i>

━━━━━━━━━━━━━━━━━━━━━━━━━━━
⚙️ <b>Синхронизация с 1C:ERP:</b>
• Новых запросов проверено суфлёром: <b>14</b>
• Предотвращено отгрузок клиентам с долгом: <b>2</b> (на сумму 425 000 ₽)
• Зависших заказов в цехах: <b>1</b> (Заказ №ПЗ-1084, простой 38 ч.)

━━━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 <b>Фокус на завтра:</b>
1. Иванову провести разбор по сделке «СеверСпецСтрой» (детали МН-1).
2. Проконтролировать закрытие смены по партии фланцев №ВЫП-412."""
        return digest

    def send_telegram_message(self, text: str, chat_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправка сообщения в Telegram через Bot API.
        """
        target_chat = chat_id or self.rop_chat_id
        if not self.bot_token or not target_chat:
            return {"status": "skipped", "reason": "No bot token or chat_id configured"}

        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": target_chat,
            "text": text,
            "parse_mode": "HTML"
        }
        try:
            with httpx.Client(timeout=10.0) as client:
                res = client.post(url, json=payload)
                return res.json()
        except Exception as e:
            return {"status": "error", "error": str(e)}

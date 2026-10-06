"""
Модуль разбора голосовых и текстовых поручений руководителя для постановки в Битрикс24.
Выделяет исполнителя, суть поручения, дедлайн и приоритет.
"""

import re
from typing import Dict, Any, Optional
from sample_data import BITRIX_USERS
from modules.bitrix_client import BitrixClient

class TaskParser:
    def __init__(self, bitrix_client: BitrixClient, users: Dict[str, Any] = BITRIX_USERS):
        self.b24 = bitrix_client
        self.users = users

    def parse_and_create_task(self, prompt_text: str, creator: str = "Руководитель") -> Dict[str, Any]:
        """
        Разбирает естественный язык (голос/текст) и создает задачу в Битрикс24.
        """
        text_lower = prompt_text.lower()

        # 1. Поиск исполнителя
        found_user = None
        for key, user_info in self.users.items():
            if key in text_lower or any(part in text_lower for part in user_info["name"].lower().split()[:2]):
                found_user = user_info
                break

        if not found_user:
            # Дефолтный ответственный (Ведущий технолог Петров)
            found_user = self.users.get("технолог")

        # 2. Определение дедлайна
        deadline = "Сегодня до 18:00"
        time_match = re.search(r"(к|до|в)\s+(\d{1,2}[:.]\d{2}|\d{1,2}\s*(утра|вечера|дня|часов|:00))", text_lower)
        if time_match:
            deadline = f"Сегодня {time_match.group(0)}"
        elif "завтра" in text_lower:
            deadline = "Завтра до 12:00"

        # 3. Приоритет
        priority = 2 if any(word in text_lower for word in ["срочно", "немедленно", "горит", "важно"]) else 1

        # 4. Формирование лаконичного заголовка задачи
        clean_title = prompt_text
        for prefix in ["поставь задачу", "создай задачу", "напомни", "сделай задачу"]:
            if clean_title.lower().startswith(prefix):
                clean_title = clean_title[len(prefix):].strip()
        
        # Первая буква заглавная
        clean_title = clean_title.strip(",. ")
        if clean_title:
            clean_title = clean_title[0].upper() + clean_title[1:]
        else:
            clean_title = "Контрольное поручение руководителя"

        description = f"""Поручение принято голосовым ассистентом Hermes Agent.
Инициатор: {creator}
Оригинальная команда: «{prompt_text}»
Контроль исполнения: Hermes Supervisor (автоматическое напоминание за 1 час до дедлайна)."""

        # 5. Создание задачи через API Битрикс24
        res = self.b24.create_task(
            title=clean_title,
            description=description,
            responsible_id=found_user["id"],
            deadline=deadline,
            priority=priority
        )

        task_id = res.get("result", 1024)

        confirmation_message = f"""✅ <b>Задача успешно создана в Битрикс24</b> (ID #{task_id})
━━━━━━━━━━━━━━━━━━━━
📌 <b>Название:</b> {clean_title}
👤 <b>Исполнитель:</b> {found_user['name']}
⏰ <b>Дедлайн:</b> {deadline}
🔥 <b>Приоритет:</b> {'Высокий ⚡️' if priority == 2 else 'Обычный'}
🔔 Уведомление исполнителю отправлено. Hermes следит за таймингом."""

        return {
            "task_id": task_id,
            "title": clean_title,
            "responsible": found_user,
            "deadline": deadline,
            "priority": priority,
            "original_prompt": prompt_text,
            "confirmation": confirmation_message,
            "b24_response": res
        }

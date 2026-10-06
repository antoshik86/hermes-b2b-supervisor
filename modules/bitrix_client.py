"""
Клиент интеграции Hermes Agent с Битрикс24 через REST API (Webhooks).
Поддерживает как реальные сетевые вызовы в живой портал Битрикс24,
так и режим высокоточной симуляции для демонстрации на экране без привязки к живому порталу.
"""

import time
import httpx
from typing import Dict, Any, Optional
from config import BITRIX24_WEBHOOK_URL

# Журнал последних действий для вывода в демо-интерфейсе
AUDIT_LOG_CRM = []

class BitrixClient:
    def __init__(self, webhook_url: Optional[str] = None):
        self.webhook_url = (webhook_url or BITRIX24_WEBHOOK_URL).rstrip("/")
        self.is_live = bool(self.webhook_url and self.webhook_url.startswith("http"))

    def _call(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Универсальный вызов метода Битрикс24."""
        timestamp = time.strftime("%H:%M:%S")

        if self.is_live:
            url = f"{self.webhook_url}/{method}.json"
            try:
                with httpx.Client(timeout=10.0) as client:
                    resp = client.post(url, json=params)
                    data = resp.json()
                    AUDIT_LOG_CRM.append({
                        "time": timestamp,
                        "mode": "LIVE_PORTAL",
                        "method": method,
                        "params": params,
                        "response": data,
                        "status": "OK" if resp.is_success else "ERROR"
                    })
                    return data
            except Exception as e:
                AUDIT_LOG_CRM.append({
                    "time": timestamp,
                    "mode": "FALLBACK_SIMULATION",
                    "method": method,
                    "params": params,
                    "error": str(e),
                    "status": "FALLBACK"
                })

        # Режим симуляции (демонстрационный стенд)
        simulated_id = int(time.time() * 1000) % 100000
        simulated_res = {
            "result": simulated_id,
            "time": {
                "start": time.time(),
                "finish": time.time() + 0.04,
                "duration": 0.04,
                "processing": 0.02,
                "date_start": time.strftime("%Y-%m-%dT%H:%M:%S+03:00"),
                "date_finish": time.strftime("%Y-%m-%dT%H:%M:%S+03:00")
            }
        }
        AUDIT_LOG_CRM.append({
            "time": timestamp,
            "mode": "SIMULATION_STAND",
            "method": method,
            "params": params,
            "response": simulated_res,
            "status": "SUCCESS"
        })
        return simulated_res

    def add_timeline_comment(self, entity_id: str, comment: str, entity_type: str = "deal") -> Dict[str, Any]:
        """
        Добавляет структурированную карточку/комментарий в таймлайн сделки Битрикс24.
        Метод: crm.timeline.comment.add
        """
        clean_id = entity_id.replace("DEAL_", "")
        params = {
            "fields": {
                "ENTITY_ID": clean_id,
                "ENTITY_TYPE": entity_type,
                "COMMENT": comment
            }
        }
        return self._call("crm.timeline.comment.add", params)

    def create_task(self, title: str, description: str, responsible_id: int, 
                    deadline: Optional[str] = None, priority: int = 1,
                    deal_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Создает задачу менеджеру или сотруднику в Битрикс24.
        Метод: tasks.task.add
        """
        fields = {
            "TITLE": title,
            "DESCRIPTION": description,
            "RESPONSIBLE_ID": responsible_id,
            "PRIORITY": priority,  # 1 = обычный, 2 = высокий
            "ALLOW_CHANGE_DEADLINE": "N",
            "TASK_CONTROL": "Y"
        }
        if deadline:
            fields["DEADLINE"] = deadline
        if deal_id:
            clean_id = deal_id.replace("DEAL_", "")
            fields["UF_CRM_TASK"] = [f"D_{clean_id}"]

        return self._call("tasks.task.add", {"fields": fields})

    def get_audit_log(self):
        return AUDIT_LOG_CRM

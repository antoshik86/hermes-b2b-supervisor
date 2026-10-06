"""
Модуль аудита ошибок учёта и производства в 1C:ERP для Hermes Agent.
Проверяет:
1. Зависшие производственные заказы без движения (>24 часов).
2. Расхождения складского учета (ГП оприходована, а сырье не списано).
3. Пропущенные аналитики и обязательные реквизиты (статьи ДДС, технологи).
Формирует персональные уведомления ответственным и сводку руководству.
"""

from typing import List, Dict, Any
from sample_data import ERP_AUDIT_DISCREPANCIES

class ErpAuditor:
    def __init__(self, discrepancies: List[Dict[str, Any]] = ERP_AUDIT_DISCREPANCIES):
        self.discrepancies = discrepancies

    def run_daily_audit(self) -> Dict[str, Any]:
        """
        Запуск процедуры регулярного аудита базы 1С:ERP.
        """
        critical_count = sum(1 for d in self.discrepancies if d["severity"] == "CRITICAL")
        high_count = sum(1 for d in self.discrepancies if d["severity"] == "HIGH")
        medium_count = sum(1 for d in self.discrepancies if d["severity"] == "MEDIUM")

        director_report_lines = [
            "🚨 <b>HERMES 1C:ERP: Ежедневный аудит производства и учёта</b>",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            f"Всего выявлено расхождений: <b>{len(self.discrepancies)}</b> (Критических: {critical_count}, Высоких: {high_count})\n"
        ]

        employee_notifications = []

        for item in self.discrepancies:
            badge = "🔴" if item["severity"] == "CRITICAL" else ("🟠" if item["severity"] == "HIGH" else "🟡")
            director_report_lines.append(
                f"{badge} <b>{item['entity']}</b>\n"
                f"   • Суть: {item['order_title']}\n"
                f"   • Ответственный: {item['responsible_person']} ({item['telegram_user']})\n"
                f"   • Зависание: {item['stuck_hours']} ч. | Статус: {item['current_status']}\n"
                f"   • Проблема: {item['description']}\n"
            )

            # Персональное сообщение виновному сотруднику
            msg_to_emp = f"""⚠️ <b>Уведомление Hermes ERP Control</b>
Здравствуйте, {item['responsible_person'].split()[0]}!
По объекту: <b>{item['entity']}</b> ({item['order_title']}) обнаружено расхождение:
👉 <i>{item['description']}</i>

Пожалуйста, оформите недостающие документы до 16:00, чтобы избежать блокировки смены."""

            employee_notifications.append({
                "recipient": item["responsible_person"],
                "tg": item["telegram_user"],
                "message": msg_to_emp
            })

        director_summary = "\n".join(director_report_lines)

        return {
            "total_issues": len(self.discrepancies),
            "critical_count": critical_count,
            "high_count": high_count,
            "medium_count": medium_count,
            "director_report": director_summary,
            "employee_notifications": employee_notifications,
            "raw_items": self.discrepancies
        }

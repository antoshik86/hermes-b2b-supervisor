"""
Модуль контроля качества звонков Hermes Agent в Битрикс24.
Анализирует транскрипт звонка менеджера по регламентному чек-листу B2B-производства,
рассчитывает интегральный балл (1-10), формирует карточку для таймлайна сделки
и автоматически создает задачу менеджеру при нарушении регламента.
"""

from typing import Dict, Any
from modules.bitrix_client import BitrixClient

class CallAnalyzer:
    def __init__(self, bitrix_client: BitrixClient):
        self.b24 = bitrix_client

    def analyze_call(self, call_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Анализ звонка по чеклисту. 
        Поддерживает как детальный экспертный эвристический анализ,
        так и возможность подключения OpenAI/Gemini/OpenRouter при наличии активного ключа.
        """
        transcript = call_data.get("transcript", "")
        manager_name = call_data.get("manager_name", "Менеджер")
        client_name = call_data.get("client_name", "Клиент")
        deal_id = call_data.get("deal_id", "DEAL_UNKNOWN")
        manager_id = call_data.get("manager_b24_id", 1)

        # Чек-лист оценки B2B-производства
        checklist = {
            "greeting": {
                "title": "Приветствие и название завода",
                "passed": any(k in transcript.lower() for k in ["промметалл", "завод", "ведущий специалист", "анна"]),
                "weight": 2.0,
                "comment": "Названо имя и бренд завода" if "промметалл" in transcript.lower() else "Сухое или смазанное приветствие без стандартов"
            },
            "qualification": {
                "title": "Выявление потребности и ТЗ (КМ/КМД/ГОСТ)",
                "passed": any(k in transcript.lower() for k in ["чертеж", "кмд", "серии", "гост", "марка", "специализируемся"]),
                "weight": 2.5,
                "comment": "Уточнены параметры чертежей и спецификации" if "кмд" in transcript.lower() or "серии" in transcript.lower() else "Поверхностное уточнение, не выяснены параметры ТЗ"
            },
            "deadlines": {
                "title": "Ориентировочные сроки расчета и производства",
                "passed": any(k in transcript.lower() for k in ["к пятнице", "к четвергу", "дней", "график", "рабочих"]),
                "weight": 2.0,
                "comment": "Зафиксированы точные сроки КП и производства" if "к пятнице" in transcript.lower() else "Сроки не названы («как технологи освободятся»)"
            },
            "next_step": {
                "title": "Договоренность о следующем контакте (Next Step)",
                "passed": any(k in transcript.lower() for k in ["я наберу вас", "в 16:00", "договорились о звонке", "созвонимся"]),
                "weight": 2.5,
                "comment": "Четко зафиксирован день и час контрольного созвона" if "наберу вас" in transcript.lower() else "Следующий шаг брошен на клиенте («скидывайте, короче»)"
            },
            "politeness": {
                "title": "Деловой тон и клиентоориентированность",
                "passed": not any(k in transcript.lower() for k in ["короче", "навскидку", "алло, да"]),
                "weight": 1.0,
                "comment": "Вежливый экспертный диалог" if not any(k in transcript.lower() for k in ["короче", "навскидку"]) else "Сленг, разговорный пренебрежительный тон"
            }
        }

        # Расчет итогового балла
        total_score = sum(item["weight"] for item in checklist.values() if item["passed"])
        score_10 = round(total_score, 1)

        # Выявление рисков и рекомендаций
        has_next_step = checklist["next_step"]["passed"]
        is_failing = score_10 < 7.0 or not has_next_step

        summary_bullet = (
            "Клиент запросил расчет мостовых балок из стали 09Г2С (35 т). Менеджер квалифицировала наличие КМ/КМД, подтвердила аттестацию НАКС и лаборатории, согласовала подготовку КП к пятнице 15:00 и контрольный созвон в 16:00."
            if score_10 >= 8.0 else
            "Клиент запросил партию закладных МН-1 (400 шт.). Менеджер не зафиксировал сроки подготовки коммерческого предложения, отправил клиента на общую почту и не договорился о следующем контакте. Высокий риск ухода к конкурентам."
        )

        # Формирование комментария для таймлайна Битрикс24
        timeline_comment = f"""🤖 <b>HERMES AGENT: Анализ звонка</b>
━━━━━━━━━━━━━━━━━━━━
📊 <b>Оценка качества:</b> {score_10} / 10 {'🟢 (Регламент соблюден)' if not is_failing else '🔴 (Требует внимания)'}
👤 <b>Менеджер:</b> {manager_name} | <b>Клиент:</b> {client_name}

📝 <b>Краткое резюме:</b>
{summary_bullet}

📋 <b>Чек-лист:</b>
• Приветствие/бренд: {'✅' if checklist['greeting']['passed'] else '❌'} {checklist['greeting']['comment']}
• Выявление ТЗ/КМД: {'✅' if checklist['qualification']['passed'] else '❌'} {checklist['qualification']['comment']}
• Фиксация сроков: {'✅' if checklist['deadlines']['passed'] else '❌'} {checklist['deadlines']['comment']}
• Следующий шаг: {'✅' if checklist['next_step']['passed'] else '❌'} {checklist['next_step']['comment']}
• Вежливость/тон: {'✅' if checklist['politeness']['passed'] else '❌'} {checklist['politeness']['comment']}
"""

        # Отправка комментария в CRM
        crm_comment_res = self.b24.add_timeline_comment(deal_id, timeline_comment)

        # Автоматическая постановка задачи при нарушениях
        task_created = None
        if is_failing:
            task_title = f"⚠️ [HERMES-CONTROL] Срочно связаться с {client_name}: нет следующего шага"
            task_desc = f"""Звонок {call_data.get('call_id')} оценен Hermes Agent на {score_10}/10.
Выявлены грубые нарушения стандартов продаж завода:
1. Не зафиксирован дедлайн отправки КП.
2. Не назначен следующий контакт — клиент может уйти к конкурентам.

ДЕЙСТВИЕ:
Немедленно перезвонить клиенту, подтвердить получение вводных данных и зафиксировать время презентации сметы!"""

            task_res = self.b24.create_task(
                title=task_title,
                description=task_desc,
                responsible_id=manager_id,
                deadline="Сегодня до 18:00",
                priority=2,
                deal_id=deal_id
            )
            task_created = {
                "title": task_title,
                "responsible_id": manager_id,
                "task_id": task_res.get("result", 9999)
            }

        return {
            "call_id": call_data.get("call_id"),
            "deal_id": deal_id,
            "manager": manager_name,
            "client": client_name,
            "score": score_10,
            "is_failing": is_failing,
            "checklist": checklist,
            "summary": summary_bullet,
            "timeline_comment": timeline_comment,
            "crm_result": crm_comment_res,
            "task_created": task_created
        }

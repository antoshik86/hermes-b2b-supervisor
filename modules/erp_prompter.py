"""
Модуль суфлёра Hermes Agent по данным 1C:ERP.
Предоставляет менеджеру контекстную подсказку в CRM или Telegram:
- Проверка дебиторской задолженности и оплат клиента
- Наличие остатков готовой продукции на складе ГП
- Наличие сырья (металлопроката/метизов) в цехах и сроки изготовления
- Готовая тактическая рекомендация для переговоров
"""

from typing import Dict, Any
from sample_data import ERP_CLIENT_DATABASE

class ErpPrompter:
    def __init__(self, db: Dict[str, Any] = ERP_CLIENT_DATABASE):
        self.db = db

    def get_prompt_for_client(self, client_id: str = "CLIENT_001") -> Dict[str, Any]:
        """
        Формирует суфлирующую подсказку для менеджера по клиенту.
        """
        data = self.db.get(client_id, self.db["CLIENT_001"])
        fin = data["financials"]
        stock = data["stock"]
        name = data["name"]
        order_item = data.get("order_item", "Заказ продукции")

        debt_rub = fin["total_debt_rub"]
        overdue_rub = fin["overdue_debt_rub"]
        overdue_days = fin["overdue_days"]
        fg_avail = stock["finished_goods_available"]
        raw_avail = stock["raw_material_in_stock"]
        prod_days = stock["production_time_days"]
        raw_desc = stock["raw_material_desc"]

        # Формирование умной тактики переговоров
        tactics = []
        if overdue_rub > 0:
            tactics.append(f"🔴 <b>ДЕБИТОРКА:</b> У клиента просроченный долг {overdue_rub:,.0f} ₽ ({overdue_days} дн. просрочки). Без погашения отгрузку в долг НЕ согласовывать.")
        else:
            tactics.append("🟢 <b>ПЛАТЕЖНЫЙ СТАТУС:</b> Клиент надёжный, задолженность отсутствует.")

        if fg_avail > 0:
            tactics.append(f"📦 <b>СКЛАД ГП:</b> В наличии {fg_avail} шт. готовой продукции — можно отгрузить хоть сегодня.")
        else:
            tactics.append("📦 <b>СКЛАД ГП:</b> Готовой продукции на складе 0 шт. Требуется полный цикл производства.")

        if raw_avail:
            tactics.append(f"⚙️ <b>ПРОИЗВОДСТВО:</b> Сырьё есть ({raw_desc}). Линия свободна ({stock['production_capacity_free_from']}). Срок довыпуска партии: {prod_days} раб. дня.")
        else:
            tactics.append("⚠️ <b>ПРОИЗВОДСТВО:</b> Сырьё отсутствует на складе, требуется закупка у металлотрейдера (+5 дней).")

        # Итоговый скрипт для менеджера
        if overdue_rub > 0 and fg_avail > 0:
            pitch = (
                f"«У клиента долг {debt_rub:,.0f} ₽. На складе уже готово {fg_avail} шт., "
                f"остаток партии доизготовим за {prod_days} дня.\n"
                f"💡 <b>РЕКОМЕНДАЦИЯ МЕНЕДЖЕРУ:</b> Предложи клиенту отгрузить готовые {fg_avail} шт. "
                f"сразу под условие закрытия старого долга + 50% предоплаты за новую партию!»"
            )
        elif overdue_rub == 0:
            pitch = (
                f"«У клиента чистая кредитная история. Металл в наличии на складе.\n"
                f"💡 <b>РЕКОМЕНДАЦИЯ МЕНЕДЖЕРУ:</b> Предлагай срок поставки {prod_days} рабочих дней "
                f"с фиксацией цены при оплате счета в течение 3 дней.»"
            )
        else:
            pitch = "💡 <b>РЕКОМЕНДАЦИЯ МЕНЕДЖЕРУ:</b> Требуется согласование финансового контролера."

        formatted_card = f"""🧠 <b>HERMES 1C:ERP СУФЛЁР</b>
━━━━━━━━━━━━━━━━━━━━
🏢 <b>Клиент:</b> {name} (ИНН {data['inn']})
🎯 <b>Запрос:</b> {order_item}

📊 <b>Оперативные данные из 1С:</b>
{chr(10).join(tactics)}

━━━━━━━━━━━━━━━━━━━━
{pitch}
"""
        return {
            "client_id": client_id,
            "client_name": name,
            "inn": data["inn"],
            "deal_id": data.get("active_deal_id"),
            "financials": fin,
            "stock": stock,
            "formatted_card": formatted_card,
            "recommended_pitch": pitch
        }

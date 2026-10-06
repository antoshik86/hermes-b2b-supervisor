"""
Интерактивный демонстрационный стенд Hermes Agent для B2B-производства.
Позволяет наглядно показать заказчику все 4 сценария работы:
1. Контроль звонков Битрикс24 + чек-лист + авто-задачи
2. Суфлёр по данным 1C:ERP (склад, металл, дебиторка)
3. Аудит ошибок учёта и зависших заказов в 1C:ERP
4. Постановка задач из естественной речи руководителя
5. Вечерний дашборд РОПа в Telegram
"""

import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt

from modules.bitrix_client import BitrixClient
from modules.call_analyzer import CallAnalyzer
from modules.erp_prompter import ErpPrompter
from modules.erp_auditor import ErpAuditor
from modules.task_parser import TaskParser
from modules.telegram_reporter import TelegramReporter
from sample_data import SAMPLE_CALLS, ERP_CLIENT_DATABASE

console = Console()

def print_header():
    console.clear()
    banner = """
    ╔════════════════════════════════════════════════════════════════════════╗
    ║        🤖 HERMES AGENT: B2B SUPERVISOR (БИТРИКС24 + 1C:ERP)            ║
    ║        Интеллектуальный контроль продаж, производства и учёта          ║
    ╚════════════════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")

def run_case_poor_call(analyzer: CallAnalyzer):
    console.print(Panel("[bold yellow]СЦЕНАРИЙ 1: Проблемный звонок менеджера (Иванов С.)[/bold yellow]\n"
                        "Клиент запросил закладные детали МН-1 (400 шт.). Менеджер нарушил стандарты продаж.", 
                        border_style="yellow"))
    
    with console.status("[bold green]Hermes анализирует аудиозапись и транскрипт...[/bold green]", spinner="dots"):
        time.sleep(1.0)
        result = analyzer.analyze_call(SAMPLE_CALLS["call_poor"])

    # Вывод оценки
    table = Table(title=f"Результаты проверки чек-листа (Звонок {result['call_id']})", border_style="cyan")
    table.add_column("Критерий чек-листа", style="bold white")
    table.add_column("Статус", justify="center")
    table.add_column("Комментарий аудитора Hermes", style="dim")

    for key, item in result["checklist"].items():
        status_badge = "[green]✓ ПРОЙДЕН[/green]" if item["passed"] else "[bold red]✗ ПРОВАЛ[/bold red]"
        table.add_row(item["title"], status_badge, item["comment"])

    console.print(table)
    console.print(f"\n[bold]Итоговый балл:[/bold] [bold red]{result['score']} / 10[/bold red] ⚠️ [red]Грубое нарушение регламента![/red]")
    
    # Показ сформированного комментария в CRM
    console.print(Panel(result["timeline_comment"], title="[bold blue]Сформировано для таймлайна сделки Битрикс24[/bold blue]", border_style="blue"))
    
    # Показ созданной задачи
    if result.get("task_created"):
        t = result["task_created"]
        console.print(Panel(
            f"[bold red]АВТОМАТИЧЕСКАЯ РЕАКЦИЯ АГЕНТА:[/bold red]\n"
            f"Поставлена срочная задача в Битрикс24:\n"
            f"📌 <b>{t['title']}</b>\n"
            f"👤 Ответственный: Менеджер Иванов Сергей (ID {t['responsible_id']})\n"
            f"⏰ Дедлайн: Сегодня до 18:00\n"
            f"🎯 Статус задачи в CRM: [bold green]Создана (ID #{t['task_id']})[/bold green]",
            title="[bold red]⚡️ Triggered Action: tasks.task.add[/bold red]",
            border_style="red"
        ))

def run_case_excellent_call(analyzer: CallAnalyzer):
    console.print(Panel("[bold green]СЦЕНАРИЙ 2: Эталонный звонок менеджера (Смирнова А.)[/bold green]\n"
                        "Сложный заказ: балки 140Б ст 09Г2С (35 тонн). Менеджер вела диалог по стандарту.", 
                        border_style="green"))
    
    with console.status("[bold green]Hermes анализирует аудиозапись и транскрипт...[/bold green]", spinner="dots"):
        time.sleep(1.0)
        result = analyzer.analyze_call(SAMPLE_CALLS["call_excellent"])

    table = Table(title=f"Результаты проверки чек-листа (Звонок {result['call_id']})", border_style="green")
    table.add_column("Критерий чек-листа", style="bold white")
    table.add_column("Статус", justify="center")
    table.add_column("Комментарий аудитора Hermes", style="dim")

    for key, item in result["checklist"].items():
        status_badge = "[green]✓ ПРОЙДЕН[/green]" if item["passed"] else "[bold red]✗ ПРОВАЛ[/bold red]"
        table.add_row(item["title"], status_badge, item["comment"])

    console.print(table)
    console.print(f"\n[bold]Итоговый балл:[/bold] [bold green]{result['score']} / 10[/bold green] ⭐️ [green]Регламент полностью соблюден![/green]")
    console.print(Panel(result["timeline_comment"], title="[bold blue]Сформировано для таймлайна сделки Битрикс24[/bold blue]", border_style="blue"))
    console.print("[dim green]Замечаний нет. Задачи на исправление не требуются.[/dim green]")

def run_case_erp_prompter(prompter: ErpPrompter):
    console.print(Panel("[bold magenta]СЦЕНАРИЙ 3: Суфлёр по 1C:ERP для менеджера на переговорах[/bold magenta]\n"
                        "Клиент «СеверСпецСтрой» обсуждает заказ. Hermes мгновенно поднимает данные из 1С.", 
                        border_style="magenta"))
    
    with console.status("[bold green]Запрос в 1C:ERP по REST API (склад, дебиторка, график цеха)...[/bold green]", spinner="dots"):
        time.sleep(0.8)
        card = prompter.get_prompt_for_client("CLIENT_001")

    console.print(Panel(card["formatted_card"], title="[bold magenta]Интеллектуальная подсказка Hermes в CRM / Telegram[/bold magenta]", border_style="magenta"))

def run_case_erp_audit(auditor: ErpAuditor):
    console.print(Panel("[bold red]СЦЕНАРИЙ 4: Ночной/ежедневный аудит 1C:ERP (производство и бухгалтерия)[/bold red]\n"
                        "Поиск зависших заказов, несоответствий выпуска сырью и пропущенных реквизитов.", 
                        border_style="red"))
    
    with console.status("[bold green]Hermes сканирует регистры и документы 1C:ERP...[/bold green]", spinner="dots"):
        time.sleep(1.2)
        audit_res = auditor.run_daily_audit()

    console.print(Panel(audit_res["director_report"], title="[bold red]Сводка для Генерального директора и РОПа[/bold red]", border_style="red"))
    
    console.print("\n[bold yellow]Персональные авто-уведомления ответственным сотрудникам:[/bold yellow]")
    for notif in audit_res["employee_notifications"]:
        console.print(f"👉 [bold cyan]{notif['recipient']}[/bold cyan] ({notif['tg']}):\n[dim]{notif['message']}[/dim]\n")

def run_case_voice_task(parser: TaskParser):
    console.print(Panel("[bold cyan]СЦЕНАРИЙ 5: Голосовое поручение руководителя в Telegram-бот[/bold cyan]", border_style="cyan"))
    
    sample_phrase = "Поставь задачу технологу Петрову проверить чертеж партии к 15:00 срочно"
    console.print(f"🎙 [bold green]Входящая голосовая команда руководителя:[/bold green] «{sample_phrase}»\n")
    
    with console.status("[bold green]Hermes распознает речь, выделяет сущности и вызывает API Битрикс24...[/bold green]", spinner="dots"):
        time.sleep(1.0)
        res = parser.parse_and_create_task(sample_phrase, creator="Генеральный директор")

    console.print(Panel(res["confirmation"], title="[bold green]Ответ бота в Telegram[/bold green]", border_style="green"))

def run_case_rop_digest(reporter: TelegramReporter):
    console.print(Panel("[bold blue]СЦЕНАРИЙ 6: Вечерняя сводка РОПа в Telegram[/bold blue]", border_style="blue"))
    digest = reporter.generate_rop_evening_digest()
    console.print(Panel(digest, title="[bold blue]Telegram Сообщение для РОПа в 19:00[/bold blue]", border_style="blue"))

def run_full_auto_demo(analyzer, prompter, auditor, parser, reporter):
    console.print(Panel("[bold green]🚀 ЗАПУСК ПОЛНОГО СКВОЗНОГО СЦЕНАРИЯ ДЛЯ ПОКАЗА НА СОЗВОНЕ[/bold green]\n"
                        "Последовательная демонстрация всех 4 блоков с таймингом.", border_style="green"))
    time.sleep(1)
    
    console.print("\n[bold cyan]▶ ШАГ 1: Контроль звонка с нарушениями[/bold cyan]")
    run_case_poor_call(analyzer)
    time.sleep(2)
    
    console.print("\n[bold cyan]▶ ШАГ 2: Суфлёр по данным 1C:ERP[/bold cyan]")
    run_case_erp_prompter(prompter)
    time.sleep(2)
    
    console.print("\n[bold cyan]▶ ШАГ 3: Аудит ошибок учета в 1С[/bold cyan]")
    run_case_erp_audit(auditor)
    time.sleep(2)
    
    console.print("\n[bold cyan]▶ ШАГ 4: Постановка задачи голосом[/bold cyan]")
    run_case_voice_task(parser)
    time.sleep(2)
    
    console.print("\n[bold cyan]▶ ШАГ 5: Вечерний дашборд РОПа[/bold cyan]")
    run_case_rop_digest(reporter)
    
    console.print("\n[bold green]✅ ПОЛНЫЙ ДЕМО-ЦИКЛ ЗАВЕРШЕН! Стенд готов к демонстрации заказчику.[/bold green]\n")

def main():
    b24 = BitrixClient()
    analyzer = CallAnalyzer(b24)
    prompter = ErpPrompter()
    auditor = ErpAuditor()
    parser = TaskParser(b24)
    reporter = TelegramReporter()

    while True:
        print_header()
        console.print("[bold white]Выберите сценарий для демонстрации:[/bold white]")
        console.print("  [1] [yellow]Анализ звонка с ошибками[/yellow] (оценка 5/10, авто-задача в Битрикс24)")
        console.print("  [2] [green]Анализ эталонного звонка[/green] (оценка 9.5/10, карточка в CRM)")
        console.print("  [3] [magenta]1С:ERP Суфлёр[/magenta] (остатки, металл, долг, тактика переговоров)")
        console.print("  [4] [red]1С:ERP Аудит[/red] (зависшие заказы, сырье без списания, алерты)")
        console.print("  [5] [cyan]Постановка задачи голосом[/cyan] («Поставь задачу технологу Петрову...»)")
        console.print("  [6] [blue]Вечерний дашборд РОПа[/blue] (сводка по продажам и производству)")
        console.print("  [7] [bold green]🚀 ПОЛНЫЙ СКВОЗНОЙ ПРОГОН (для созвона)[/bold green]")
        console.print("  [0] Выход\n")

        choice = Prompt.ask("[bold cyan]Введите номер сценария[/bold cyan]", choices=["0", "1", "2", "3", "4", "5", "6", "7"], default="7")

        if choice == "0":
            console.print("[bold yellow]Завершение работы демо-стенда.[/bold yellow]")
            break
        elif choice == "1":
            run_case_poor_call(analyzer)
        elif choice == "2":
            run_case_excellent_call(analyzer)
        elif choice == "3":
            run_case_erp_prompter(prompter)
        elif choice == "4":
            run_case_erp_audit(auditor)
        elif choice == "5":
            run_case_voice_task(parser)
        elif choice == "6":
            run_case_rop_digest(reporter)
        elif choice == "7":
            run_full_auto_demo(analyzer, prompter, auditor, parser, reporter)

        input("\nНажмите Enter для возврата в меню...")

if __name__ == "__main__":
    main()

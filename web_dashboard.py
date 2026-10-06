"""
FastAPI сервер визуального дашборда для демонстрационного стенда Hermes Agent.
Запускает локальный веб-интерфейс на http://127.0.0.1:8000.
"""

import sys
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from config import DASHBOARD_PORT
from modules.bitrix_client import BitrixClient
from modules.call_analyzer import CallAnalyzer
from modules.erp_prompter import ErpPrompter
from modules.erp_auditor import ErpAuditor
from modules.task_parser import TaskParser
from modules.telegram_reporter import TelegramReporter
from sample_data import SAMPLE_CALLS, ERP_CLIENT_DATABASE, ERP_AUDIT_DISCREPANCIES

app = FastAPI(title="Hermes Agent B2B Supervisor Demo")

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

b24 = BitrixClient()
analyzer = CallAnalyzer(b24)
prompter = ErpPrompter()
auditor = ErpAuditor()
task_parser = TaskParser(b24)
reporter = TelegramReporter()

@app.get("/", response_class=HTMLResponse)
async def get_index():
    index_path = STATIC_DIR / "index.html"
    return FileResponse(index_path)

@app.get("/api/call/analyze/{call_type}")
async def api_analyze_call(call_type: str = "poor"):
    call_data = SAMPLE_CALLS.get(f"call_{call_type}", SAMPLE_CALLS["call_poor"])
    return analyzer.analyze_call(call_data)

@app.get("/api/prompter/{client_id}")
async def api_prompter(client_id: str = "CLIENT_001"):
    return prompter.get_prompt_for_client(client_id)

@app.get("/api/audit")
async def api_audit():
    return auditor.run_daily_audit()

@app.get("/api/rop/digest")
async def api_rop_digest():
    return {"digest": reporter.generate_rop_evening_digest()}

@app.post("/api/task/create")
async def api_create_task(prompt: str):
    return task_parser.parse_and_create_task(prompt)

if __name__ == "__main__":
    print(f"\n[+] Запуск веб-дашборда Hermes Agent на http://127.0.0.1:{DASHBOARD_PORT}")
    print(f"[+] Откройте http://127.0.0.1:{DASHBOARD_PORT} в браузере для показа экрана на созвоне!\n")
    uvicorn.run(app, host="127.0.0.1", port=DASHBOARD_PORT, log_level="warning")

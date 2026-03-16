"""
Shared configuration — reads settings from environment variables.
Docker Compose passes these from the .env file automatically.
Falls back to defaults for local development.
"""

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path setup — so we can reach the existing agent prompts/ folder
# ---------------------------------------------------------------------------
AGENT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_ROOT))

# ---------------------------------------------------------------------------
# Database  (env vars set by docker-compose from .env)
# ---------------------------------------------------------------------------
DB_USER = os.getenv("DB_USER", "kishore")
DB_PASSWORD = os.getenv("DB_PASSWORD", "Gpohealth!#!")
DB_HOST = os.getenv("DB_HOST", "dev-db-test.c969yoyq9cyy.us-east-1.rds.amazonaws.com")
DB_PORT = os.getenv("DB_PORT", "3306")
DB_NAME = os.getenv("DB_NAME", "joblog_metadata")

DB_URI = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# ---------------------------------------------------------------------------
# LLM  (Ollama)
# ---------------------------------------------------------------------------
LLM_BASE_URL = os.getenv("LLM_BASE_URL", "http://172.31.27.7:11434")
LLM_MODEL = os.getenv("LLM_MODEL", "llama3.1:8b")

# Tell requests / httpx to skip proxy for the Ollama private IP
_ollama_host = LLM_BASE_URL.split("//")[-1].split(":")[0]
os.environ["NO_PROXY"] = _ollama_host
os.environ["no_proxy"] = _ollama_host

# ---------------------------------------------------------------------------
# Prompts  (reuse existing prompt text files — zero changes)
# ---------------------------------------------------------------------------
PROMPT_DIR = AGENT_ROOT / "prompts"

def load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text()

STATUS_SYSTEM_MESSAGE = load_prompt("status_tracker.txt")
SUMMARY_MESSAGE = load_prompt("contract_summary.txt")
SQL_PROMPT = load_prompt("sql_generator.txt")
DELIVERY_PROMPT = load_prompt("delivery_normalizer.txt")
ANALYST_PROMPT = load_prompt("contract_analyst_prompt.txt")
FORMAT_PROMPT = load_prompt("response_formatter.txt")

# ---------------------------------------------------------------------------
# Airflow
# ---------------------------------------------------------------------------
TABLE_NAME = "admin_fee_metadata"
FILE_PATH = os.getenv("EXCEL_INPUT_PATH", "/home/ubuntu/adminfee_data_pipeline/Data/agent_input/contracts.xlsx")
AIRFLOW_CMD = os.getenv("AIRFLOW_CMD", "/home/ubuntu/run_airflow.sh dags trigger execute_adminfee_data_pipeline_v1").split()
REMOTE_AIRFLOW_CMD = os.getenv("AIRFLOW_CMD", "/home/ubuntu/run_airflow.sh dags trigger execute_adminfee_data_pipeline_v1")
UBUNTU_HOST = os.getenv("AIRFLOW_HOST", "ubuntu@172.31.25.132")

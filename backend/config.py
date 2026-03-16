"""
Shared configuration - reads from existing agent files' settings.
This module centralizes DB, LLM, and prompt configuration
so the wrapper reuses the same backend as the CLI agents.
"""

import os
import sys
from pathlib import Path

# Add parent directory so we can import from existing agent files
AGENT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(AGENT_ROOT))

os.environ["NO_PROXY"] = "172.31.27.7"
os.environ["no_proxy"] = "172.31.27.7"

# --- Database ---
DB_URI = "mysql+pymysql://kishore:Gpohealth!#!@dev-db-test.c969yoyq9cyy.us-east-1.rds.amazonaws.com:3306/joblog_metadata"

# --- Prompts (reuse existing prompt files) ---
PROMPT_DIR = AGENT_ROOT / "prompts"

def load_prompt(filename: str) -> str:
    return (PROMPT_DIR / filename).read_text()

STATUS_SYSTEM_MESSAGE = load_prompt("status_tracker.txt")
SUMMARY_MESSAGE = load_prompt("contract_summary.txt")
SQL_PROMPT = load_prompt("sql_generator.txt")
DELIVERY_PROMPT = load_prompt("delivery_normalizer.txt")
ANALYST_PROMPT = load_prompt("contract_analyst_prompt.txt")
FORMAT_PROMPT = load_prompt("response_formatter.txt")

# --- LLM ---
LLM_BASE_URL = "http://172.31.27.7:11434"
LLM_MODEL = "llama3.1:8b"

# --- Airflow ---
TABLE_NAME = "admin_fee_metadata"
FILE_PATH = r'/home/ubuntu/adminfee_data_pipeline/Data/agent_input/contracts.xlsx'
AIRFLOW_CMD = [
    "/home/ubuntu/run_airflow.sh",
    "dags",
    "trigger",
    "execute_adminfee_data_pipeline_v1"
]
REMOTE_AIRFLOW_CMD = "/home/ubuntu/run_airflow.sh dags trigger execute_adminFee_Data_Pipeline_v1"
UBUNTU_HOST = "ubuntu@172.31.25.132"

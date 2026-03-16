"""
Wrapper module that provides reusable functions from the existing agent code.
Imports helpers and builds on the same DB/LLM infrastructure without modifying
the original agent files.

Updated to match main branch changes:
  - File input now downloads from S3 via extract_input_template_S3
  - Pipeline trigger now uses paramiko SSH via trigger_airflow_dag
  - Output goes to S3 bucket etlhunter at adminfee_output/{delivery}
"""

import re
import time
import pandas as pd
from sqlalchemy import create_engine, text
from langchain_ollama import ChatOllama

from config import (
    DB_URI, TABLE_NAME, LLM_BASE_URL, LLM_MODEL,
    STATUS_SYSTEM_MESSAGE, SUMMARY_MESSAGE, SQL_PROMPT,
    DELIVERY_PROMPT, ANALYST_PROMPT, FORMAT_PROMPT,
    S3_BUCKET, S3_INPUT_KEY, S3_OUTPUT_PREFIX,
    SSH_HOST, SSH_USERNAME, SSH_KEY_PATH,
    AIRFLOW_START_CMD, AIRFLOW_TRIGGER_CMD,
)

engine = create_engine(DB_URI)

llm = ChatOllama(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    temperature=0,
    timeout=60,
)

llm_analysis = ChatOllama(
    model=LLM_MODEL,
    base_url=LLM_BASE_URL,
    temperature=0.9,
    timeout=60,
    model_kwargs={"num_predict": 600, "top_p": 0.9},
)


# ---------------------------------------------------------------------------
# Reuse extract_sql_query from existing adminfee_processing_agent.py logic
# ---------------------------------------------------------------------------
def extract_sql_query(llm_response: str) -> str:
    if not llm_response:
        raise ValueError("Empty response")

    txt = llm_response.strip()

    code_block = re.search(r"```sql(.*?)```", txt, re.IGNORECASE | re.DOTALL)
    if code_block:
        return code_block.group(1).strip()

    prefixes = ["sql_query:", "sql:", "query:", "sql_statement:", "sql statement:"]
    lower_text = txt.lower()
    for prefix in prefixes:
        if prefix in lower_text:
            idx = lower_text.find(prefix)
            txt = txt[idx + len(prefix):].strip()

    sql_keywords = ["select", "insert", "update", "delete", "with"]
    pattern = r"(?i)\b(" + "|".join(sql_keywords) + r")\b"
    match = re.search(pattern, txt)
    if not match:
        raise ValueError("No SQL keyword found in response")

    sql_part = txt[match.start():].strip()
    semicolon_match = re.search(r";", sql_part)
    if semicolon_match:
        sql_query = sql_part[:semicolon_match.end()]
    else:
        sql_query = sql_part

    return sql_query.replace("\n", " ").replace("`", "").strip()


def run_sql(query: str):
    with engine.begin() as conn:
        result = conn.execute(text(query)).fetchall()
    return [dict(row._mapping) for row in result]


# ---------------------------------------------------------------------------
# Phase 1: Processing workflow steps
# ---------------------------------------------------------------------------

def _get_aws_credentials():
    """Fetch AWS credentials from the metadata DB (same source as host scripts)."""
    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT `key`, `value` FROM joblog_metadata.metadata_table_database")
        ).fetchall()
    creds = {row[0]: row[1] for row in rows}
    return creds["S3_AccessKey"], creds["S3_Secret_Access_Key"]


def load_contracts_from_input(input_type: str, contracts_csv: str = ""):
    """
    Load contracts from S3 file or manual CSV input.
    - file: Downloads input_template.xlsx from S3 using AWS creds from DB.
            Works inside Docker (no host-path dependencies).
    - manual: Parses comma-separated contract names
    """
    if input_type == "file":
        import boto3
        import tempfile

        access_key, secret_key = _get_aws_credentials()
        s3 = boto3.client(
            "s3",
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name="us-east-1",
        )

        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            s3.download_file(S3_BUCKET, S3_INPUT_KEY, tmp.name)
            local_path = tmp.name

        df = pd.read_excel(local_path)
        import os
        os.unlink(local_path)
        return df["contract_names"].dropna().tolist()
    else:
        return [c.strip() for c in contracts_csv.split(",") if c.strip()]


def update_metadata(contracts: list, delivery: str):
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE TABLE {TABLE_NAME}"))
        for contract in contracts:
            conn.execute(
                text(f"INSERT INTO {TABLE_NAME}(CONTRACT_NAME, DELIVERY) VALUES(:contract, :delivery)"),
                {"contract": contract, "delivery": delivery},
            )


def trigger_pipeline():
    """
    Trigger Airflow DAG via paramiko SSH (matches main branch).
    Connects to Ubuntu server, starts Airflow services, then triggers the DAG.
    Raises on failure so the API returns a proper error to the frontend.
    """
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
    from trigger_airflow_dag import trigger_airflow_dag
    trigger_airflow_dag()
    return {"status": "TRIGGERED", "output": "Pipeline triggered via SSH"}


def get_output_path(delivery: str):
    """Return S3 output path for completed delivery."""
    return {
        "bucket": S3_BUCKET,
        "path": f"{S3_OUTPUT_PREFIX}/{delivery}",
        "full": f"s3://{S3_BUCKET}/{S3_OUTPUT_PREFIX}/{delivery}",
    }


def get_status_summary():
    query = f"""
    SELECT
        COUNT(*) AS total,
        SUM(CASE WHEN STATUS = 0 THEN 1 ELSE 0 END) AS completed,
        SUM(CASE WHEN STATUS != 0 THEN 1 ELSE 0 END) AS in_progress
    FROM {TABLE_NAME}
    """
    result = run_sql(query)
    if result:
        row = result[0]
        return {
            "total": row.get("total", 0),
            "completed": row.get("completed", 0),
            "in_progress": row.get("in_progress", 0),
            "is_completed": row.get("in_progress", 0) == 0,
        }
    return {"total": 0, "completed": 0, "in_progress": 0, "is_completed": False}


def ask_status_question(question: str, delivery: str):
    sql_prompt = f"{STATUS_SYSTEM_MESSAGE}\n\nUser Question:\n{question}\n\nDelivery Name: {delivery}"
    llm_response = llm.invoke(sql_prompt).content.strip()
    try:
        sql_query = extract_sql_query(llm_response)
        db_result = run_sql(sql_query)
    except Exception:
        db_result = []
        sql_query = ""

    interpretation_prompt = (
        f"{STATUS_SYSTEM_MESSAGE}\n\nUser Question: {question}\n\n"
        f"SQL Result:\n{db_result}\n\nProvide user friendly answer."
    )
    response = llm.invoke(interpretation_prompt).content
    return {"answer": response, "sql": sql_query, "raw_result": db_result}


def get_contract_summary(contracts: list):
    summary = []
    for contract in contracts:
        contract2 = contract.replace("-", "_").strip()
        table = f"admin_fee.PO_Master_{contract2}_v1"

        po_sql = f"SELECT SUM(PO_Base_Spend_actual) AS PO_SPEND, SUM(INV_Extended_Spend_actual) AS INV_SPEND FROM {table}"
        report_sql = "SELECT SUM(`Sales_Volume`) AS SALES_VOLUME FROM admin_fee.admin_fee_report WHERE `Contract ID`=:contract_id"

        try:
            with engine.begin() as conn:
                po_result = conn.execute(text(po_sql)).mappings().fetchone()
                report_result = conn.execute(text(report_sql), {"contract_id": contract}).mappings().fetchone()

            po_spend = (po_result["PO_SPEND"] or 0) if po_result else 0
            inv_spend = (po_result["INV_SPEND"] or 0) if po_result else 0
            selected_spend = max(po_spend, inv_spend)

            if report_result:
                report_spend = report_result["SALES_VOLUME"] or 0
            else:
                report_spend = None

            if report_spend is None:
                status = "Contract not found in adminFee report"
                difference = None
            elif selected_spend > report_spend:
                status = "PO Master is high"
                difference = abs(selected_spend - report_spend)
            elif selected_spend < report_spend:
                status = "Report higher"
                difference = abs(selected_spend - report_spend)
            else:
                status = "MATCH"
                difference = 0

            summary.append({
                "contract": contract,
                "report_spend": report_spend,
                "po_spend": po_spend,
                "inv_spend": inv_spend,
                "selected_spend": selected_spend,
                "difference": difference,
                "status": status,
            })
        except Exception as e:
            summary.append({"contract": contract, "error": str(e)})
    return summary


def generate_summary_report(summary_data):
    prompt = SUMMARY_MESSAGE.format(summary_data=summary_data)
    response = llm.invoke(prompt)
    return response.content


# ---------------------------------------------------------------------------
# Phase 2: Contract Analysis
# ---------------------------------------------------------------------------

def normalize_delivery(user_input: str) -> str:
    prompt = DELIVERY_PROMPT.format(delivery=user_input)
    response = llm_analysis.invoke(prompt)
    return response.content.strip().lower()


def get_contracts_for_delivery(delivery: str):
    query = f"SELECT DISTINCT CONTRACT_NAME FROM {TABLE_NAME} WHERE DELIVERY = :delivery"
    with engine.begin() as conn:
        result = conn.execute(text(query), {"delivery": delivery}).fetchall()
    return [row[0] for row in result]


def analyze_question(question: str, contracts: list):
    prompt = SQL_PROMPT.format(question=question, contracts=contracts)
    response = llm_analysis.invoke(prompt)
    sql = extract_sql_query(response.content)

    data = run_sql(sql)
    results = [{"result": data}]

    analysis_prompt = ANALYST_PROMPT.format(question=question, result=results)
    analysis_response = llm_analysis.invoke(analysis_prompt)

    format_prompt = FORMAT_PROMPT.format(analysis=analysis_response.content)
    final_response = llm_analysis.invoke(format_prompt)

    return {
        "answer": final_response.content,
        "sql": sql,
        "raw_result": data,
    }

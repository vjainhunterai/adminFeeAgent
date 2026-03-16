"""
Phase 1 API routes — Process NEW contracts.
Wraps the existing adminfee_processing_agent.py workflow.
Updated: S3 file input, paramiko Airflow trigger, S3 output paths.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from wrapper import (
    load_contracts_from_input,
    update_metadata,
    trigger_pipeline,
    get_output_path,
    get_status_summary,
    ask_status_question,
    get_contract_summary,
    generate_summary_report,
)

router = APIRouter(prefix="/api/processing", tags=["Processing"])


class ContractInput(BaseModel):
    input_type: str  # "manual" or "file"
    contracts: str = ""  # comma-separated for manual
    delivery_name: str


class StatusQuestionInput(BaseModel):
    question: str
    delivery_name: str


class SummaryInput(BaseModel):
    contracts: List[str]


# Step 1: Load contracts + update metadata + trigger pipeline
@router.post("/start")
def start_processing(payload: ContractInput):
    try:
        contracts_list = load_contracts_from_input(payload.input_type, payload.contracts)
        if not contracts_list:
            raise HTTPException(status_code=400, detail="No contracts provided")

        update_metadata(contracts_list, payload.delivery_name)
        pipeline_result = trigger_pipeline()
        output_path = get_output_path(payload.delivery_name)

        return {
            "contracts": contracts_list,
            "delivery_name": payload.delivery_name,
            "pipeline": pipeline_result,
            "output": output_path,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Step 2: Check status
@router.get("/status")
def check_status():
    try:
        return get_status_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Step 3: Ask a status question (AI-powered)
@router.post("/status/ask")
def status_question(payload: StatusQuestionInput):
    try:
        return ask_status_question(payload.question, payload.delivery_name)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Step 4: Get contract summary
@router.post("/summary")
def contract_summary(payload: SummaryInput):
    try:
        summary = get_contract_summary(payload.contracts)
        report = generate_summary_report(summary)
        return {"summary": summary, "report": report}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

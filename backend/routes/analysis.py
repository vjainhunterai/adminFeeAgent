"""
Phase 2 API routes — Analyze EXISTING contracts.
Wraps the existing contract_analyst_agent_cot.py workflow.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from wrapper import (
    normalize_delivery,
    get_contracts_for_delivery,
    analyze_question,
)

router = APIRouter(prefix="/api/analysis", tags=["Analysis"])


class DeliveryInput(BaseModel):
    delivery_name: str


class QuestionInput(BaseModel):
    question: str
    contracts: list


# Step 1: Normalize delivery name and fetch contracts
@router.post("/delivery")
def fetch_delivery_contracts(payload: DeliveryInput):
    try:
        normalized = normalize_delivery(payload.delivery_name)
        contracts = get_contracts_for_delivery(normalized)
        return {"delivery": normalized, "contracts": contracts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Step 2: Ask analysis question
@router.post("/ask")
def ask_question(payload: QuestionInput):
    try:
        result = analyze_question(payload.question, payload.contracts)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

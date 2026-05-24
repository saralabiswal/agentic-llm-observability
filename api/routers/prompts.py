"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import get_session
from api.schemas import PromptStatus, PromptVersion
from prompts.ab_evaluator import ABEvaluator, ABResult
from prompts.version_store import PromptVersionStore

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptVersionCreate(BaseModel):
    use_case: str
    version: str
    prompt_text: str
    model: str
    status: PromptStatus = PromptStatus.TESTING


@router.get("/versions", response_model=list[PromptVersion])
async def prompt_versions(
    session: Annotated[AsyncSession, Depends(get_session)],
    use_case: str = "banking_payment_risk",
) -> list[PromptVersion]:
    return await PromptVersionStore(session).get_versions(use_case)


@router.post("/versions", response_model=PromptVersion)
async def register_prompt_version(
    payload: PromptVersionCreate,
    session: Annotated[AsyncSession, Depends(get_session)],
) -> PromptVersion:
    return await PromptVersionStore(session).register_version(
        payload.use_case,
        payload.version,
        payload.prompt_text,
        payload.model,
        payload.status,
    )


@router.get("/compare", response_model=ABResult)
async def compare_prompt_versions(
    session: Annotated[AsyncSession, Depends(get_session)],
    a: str,
    b: str,
) -> ABResult:
    return await ABEvaluator(PromptVersionStore(session)).compare(a, b)

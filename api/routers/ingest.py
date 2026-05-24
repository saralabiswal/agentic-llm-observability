"""
FastAPI route module exposing one LLMOps telemetry surface to the UI and SDK.

Author: Sarala Biswal
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import Settings, get_session, get_settings
from api.schemas import LLMCallRecord
from costs.cost_calculator import CostCalculator
from drift.alert_engine import AlertEngine
from quality.hallucination_detector import HallucinationDetector
from quality.llm_judge import JudgeInput, LLMJudge
from tracking.token_tracker import TokenTracker

router = APIRouter(prefix="/ingest", tags=["ingest"])


@router.post("")
async def ingest_call(
    record: LLMCallRecord,
    session: Annotated[AsyncSession, Depends(get_session)],
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | int]:
    cost = CostCalculator().calculate_call_cost(
        record.model,
        record.provider,
        record.input_tokens,
        record.output_tokens,
    )
    updated = record.model_copy(update={"cost_usd": cost})

    if settings.enable_quality_scoring and record.response_text and record.context_text:
        judge = LLMJudge(settings)
        score = await judge.score(
            JudgeInput(
                use_case=record.use_case,
                model=record.model,
                prompt=record.prompt_version,
                response=record.response_text,
                context=record.context_text,
            )
        )
        hallucination = await HallucinationDetector(settings).detect(
            record.response_text,
            record.context_text,
        )
        if score is not None:
            updated = updated.model_copy(
                update={
                    "quality_score": score.composite_score,
                    "quality_gate_passed": score.gate_passed,
                    "hallucination_flag": bool(hallucination),
                }
            )

    await TokenTracker(session).record_call(updated)
    alerts = await AlertEngine(session, settings).check_thresholds(
        use_case=updated.use_case,
        quality_score=updated.quality_score,
    )
    return {"status": "accepted", "call_id": updated.call_id, "alerts_created": len(alerts)}

"""
Token and latency helpers that normalize per-call observability measurements.

Author: Sarala Biswal
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import Select, desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import LLMCallRecord, Provider
from audit.models import LLMCall


class TokenTracker:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def record_call(self, record: LLMCallRecord) -> None:
        self.session.add(
            LLMCall(
                call_id=record.call_id,
                timestamp=record.timestamp,
                model=record.model,
                provider=record.provider.value,
                use_case=record.use_case,
                prompt_version=record.prompt_version,
                input_tokens=record.input_tokens,
                output_tokens=record.output_tokens,
                total_tokens=record.total_tokens,
                latency_ms=record.latency_ms,
                cost_usd=record.cost_usd,
                quality_score=record.quality_score,
                hallucination_flag=record.hallucination_flag,
                quality_gate_passed=record.quality_gate_passed,
                response_text=record.response_text,
                context_text=record.context_text,
            )
        )
        await self.session.commit()

    async def get_calls(
        self,
        *,
        model: str | None = None,
        provider: Provider | None = None,
        use_case: str | None = None,
        days: int | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[LLMCallRecord]:
        statement: Select[tuple[LLMCall]] = select(LLMCall).order_by(desc(LLMCall.timestamp))
        if model is not None:
            statement = statement.where(LLMCall.model == model)
        if provider is not None:
            statement = statement.where(LLMCall.provider == provider.value)
        if use_case is not None:
            statement = statement.where(LLMCall.use_case == use_case)
        if days is not None:
            since = datetime.now(UTC) - timedelta(days=days)
            statement = statement.where(LLMCall.timestamp >= since)

        result = await self.session.execute(statement.limit(limit).offset(offset))
        return [_row_to_record(row) for row in result.scalars().all()]


def _row_to_record(row: LLMCall) -> LLMCallRecord:
    return LLMCallRecord(
        call_id=row.call_id,
        timestamp=row.timestamp,
        model=row.model,
        provider=Provider(row.provider),
        use_case=row.use_case,
        prompt_version=row.prompt_version,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        latency_ms=row.latency_ms,
        cost_usd=Decimal(row.cost_usd),
        quality_score=float(row.quality_score) if row.quality_score is not None else None,
        hallucination_flag=row.hallucination_flag,
        quality_gate_passed=row.quality_gate_passed,
        response_text=row.response_text,
        context_text=row.context_text,
    )

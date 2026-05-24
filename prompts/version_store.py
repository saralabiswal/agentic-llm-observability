"""
Prompt registry, version tracking, and comparison support for governance workflows.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from api.schemas import PromptStatus, PromptVersion
from audit.models import LLMCall, PromptVersionRow


class PromptVersionStore:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def register_version(
        self,
        use_case: str,
        version: str,
        prompt_text: str,
        model: str,
        status: PromptStatus = PromptStatus.TESTING,
    ) -> PromptVersion:
        prompt_version = PromptVersion(
            version_id=str(uuid4()),
            use_case=use_case,
            version=version,
            prompt_text=prompt_text,
            model=model,
            status=status,
            deployed_at=datetime.now(UTC) if status == PromptStatus.ACTIVE else None,
        )
        self.session.add(
            PromptVersionRow(
                version_id=prompt_version.version_id,
                use_case=prompt_version.use_case,
                version=prompt_version.version,
                prompt_text=prompt_version.prompt_text,
                model=prompt_version.model,
                status=prompt_version.status.value,
                deployed_at=prompt_version.deployed_at,
                created_at=prompt_version.created_at,
                avg_quality_score=None,
                avg_cost_usd=None,
                avg_latency_ms=None,
            )
        )
        await self.session.commit()
        return prompt_version

    async def get_versions(self, use_case: str) -> list[PromptVersion]:
        result = await self.session.execute(
            select(PromptVersionRow)
            .where(PromptVersionRow.use_case == use_case)
            .order_by(PromptVersionRow.created_at)
        )
        return [_row_to_prompt_version(row) for row in result.scalars().all()]

    async def get_performance(self, version_id: str) -> dict[str, Decimal | float | int]:
        version = await self.session.get(PromptVersionRow, version_id)
        if version is None:
            raise ValueError(f"Unknown prompt version: {version_id}")

        result = await self.session.execute(
            select(
                func.count(LLMCall.call_id),
                func.avg(LLMCall.quality_score),
                func.avg(LLMCall.cost_usd),
                func.avg(LLMCall.latency_ms),
            ).where(LLMCall.prompt_version == version.version)
        )
        call_count, avg_quality, avg_cost, avg_latency = result.one()
        return {
            "call_count": int(call_count or 0),
            "avg_quality_score": float(avg_quality or 0.0),
            "avg_cost_usd": Decimal(avg_cost or 0),
            "avg_latency_ms": int(avg_latency or 0),
        }


def _row_to_prompt_version(row: PromptVersionRow) -> PromptVersion:
    return PromptVersion(
        version_id=row.version_id,
        use_case=row.use_case,
        version=row.version,
        prompt_text=row.prompt_text,
        model=row.model,
        status=PromptStatus(row.status),
        deployed_at=row.deployed_at,
        created_at=row.created_at,
        avg_quality_score=(
            float(row.avg_quality_score) if row.avg_quality_score is not None else None
        ),
        avg_cost_usd=Decimal(row.avg_cost_usd) if row.avg_cost_usd is not None else None,
        avg_latency_ms=row.avg_latency_ms,
    )

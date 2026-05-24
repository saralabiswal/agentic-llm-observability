"""
Database models that persist LLM calls, quality scores, prompt versions, drift, and
alerts.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class LLMCall(Base):
    __tablename__ = "llm_calls"

    call_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    model: Mapped[str] = mapped_column(String(128), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    use_case: Mapped[str] = mapped_column(String(128), index=True)
    prompt_version: Mapped[str] = mapped_column(String(64), index=True)
    input_tokens: Mapped[int] = mapped_column(Integer)
    output_tokens: Mapped[int] = mapped_column(Integer)
    total_tokens: Mapped[int] = mapped_column(Integer)
    latency_ms: Mapped[int] = mapped_column(Integer)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    quality_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    hallucination_flag: Mapped[bool] = mapped_column(Boolean, default=False)
    quality_gate_passed: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    response_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    context_text: Mapped[str | None] = mapped_column(Text, nullable=True)


class CostSnapshot(Base):
    __tablename__ = "cost_snapshots"

    snapshot_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), index=True
    )
    model: Mapped[str] = mapped_column(String(128), index=True)
    provider: Mapped[str] = mapped_column(String(32), index=True)
    use_case: Mapped[str] = mapped_column(String(128), index=True)
    total_cost_usd: Mapped[Decimal] = mapped_column(Numeric(18, 6))
    call_count: Mapped[int] = mapped_column(Integer)


class QualityScoreRow(Base):
    __tablename__ = "quality_scores"

    score_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    use_case: Mapped[str] = mapped_column(String(128), index=True)
    model: Mapped[str] = mapped_column(String(128), index=True)
    faithfulness: Mapped[float] = mapped_column(Numeric(5, 4))
    relevance: Mapped[float] = mapped_column(Numeric(5, 4))
    coherence: Mapped[float] = mapped_column(Numeric(5, 4))
    composite_score: Mapped[float] = mapped_column(Numeric(5, 4))
    gate_passed: Mapped[bool] = mapped_column(Boolean)


class DriftScoreRow(Base):
    __tablename__ = "drift_scores"

    drift_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    use_case: Mapped[str] = mapped_column(String(128), index=True)
    model: Mapped[str] = mapped_column(String(128), index=True)
    drift_score: Mapped[float] = mapped_column(Numeric(5, 4))
    baseline_similarity: Mapped[float] = mapped_column(Numeric(6, 4))
    alert_triggered: Mapped[bool] = mapped_column(Boolean)


class PromptVersionRow(Base):
    __tablename__ = "prompt_versions"

    version_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    use_case: Mapped[str] = mapped_column(String(128), index=True)
    version: Mapped[str] = mapped_column(String(64), index=True)
    prompt_text: Mapped[str] = mapped_column(Text)
    model: Mapped[str] = mapped_column(String(128), index=True)
    status: Mapped[str] = mapped_column(String(32), index=True)
    deployed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    avg_quality_score: Mapped[float | None] = mapped_column(Numeric(5, 4), nullable=True)
    avg_cost_usd: Mapped[Decimal | None] = mapped_column(Numeric(18, 6), nullable=True)
    avg_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)


class AlertHistory(Base):
    __tablename__ = "alert_history"

    alert_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    timestamp: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    alert_type: Mapped[str] = mapped_column(String(32), index=True)
    severity: Mapped[str] = mapped_column(String(32), index=True)
    use_case: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    message: Mapped[str] = mapped_column(Text)
    metric_value: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    threshold_value: Mapped[float | None] = mapped_column(Numeric(10, 4), nullable=True)
    resolved: Mapped[bool] = mapped_column(Boolean, default=False)

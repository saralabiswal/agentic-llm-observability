"""
Semantic drift scoring and alert generation for prompt and output behavior changes.

Author: Sarala Biswal
"""

from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from api.dependencies import Settings, get_settings
from api.schemas import AlertRecord, AlertSeverity, AlertType
from audit.models import AlertHistory


class AlertEngine:
    def __init__(
        self,
        session: AsyncSession | None = None,
        settings: Settings | None = None,
    ) -> None:
        self.session = session
        self.settings = settings or get_settings()

    async def check_thresholds(
        self,
        *,
        drift_score: float | None = None,
        use_case: str | None = None,
        monthly_spend_pct: float | None = None,
        quality_score: float | None = None,
    ) -> list[AlertRecord]:
        alerts: list[AlertRecord] = []
        if drift_score is not None and drift_score > self.settings.drift_alert_threshold:
            alerts.append(
                self._build_alert(
                    alert_type=AlertType.DRIFT,
                    severity=_drift_severity(drift_score),
                    use_case=use_case,
                    message=(
                        f"Drift {drift_score:.3f} exceeds threshold "
                        f"{self.settings.drift_alert_threshold:.3f}"
                    ),
                    metric_value=drift_score,
                    threshold_value=self.settings.drift_alert_threshold,
                )
            )
        if monthly_spend_pct is not None and monthly_spend_pct > 0.80:
            alerts.append(
                self._build_alert(
                    alert_type=AlertType.COST,
                    severity=AlertSeverity.MEDIUM,
                    use_case=use_case,
                    message=f"Monthly budget {monthly_spend_pct:.0%} consumed",
                    metric_value=monthly_spend_pct,
                    threshold_value=0.80,
                )
            )
        if quality_score is not None and quality_score < self.settings.quality_gate_threshold:
            alerts.append(
                self._build_alert(
                    alert_type=AlertType.QUALITY,
                    severity=AlertSeverity.HIGH,
                    use_case=use_case,
                    message=(
                        f"Quality score {quality_score:.2f} below gate "
                        f"{self.settings.quality_gate_threshold:.2f}"
                    ),
                    metric_value=quality_score,
                    threshold_value=self.settings.quality_gate_threshold,
                )
            )
        if self.session is not None:
            for alert in alerts:
                self.session.add(_to_row(alert))
            await self.session.commit()
        return alerts

    @staticmethod
    def _build_alert(
        *,
        alert_type: AlertType,
        severity: AlertSeverity,
        use_case: str | None,
        message: str,
        metric_value: float,
        threshold_value: float,
    ) -> AlertRecord:
        return AlertRecord(
            alert_id=str(uuid4()),
            timestamp=datetime.now(UTC),
            alert_type=alert_type,
            severity=severity,
            use_case=use_case,
            message=message,
            metric_value=metric_value,
            threshold_value=threshold_value,
        )


def _drift_severity(score: float) -> AlertSeverity:
    if score > 0.60:
        return AlertSeverity.CRITICAL
    if score > 0.35:
        return AlertSeverity.HIGH
    if score > 0.20:
        return AlertSeverity.MEDIUM
    return AlertSeverity.LOW


def _to_row(alert: AlertRecord) -> AlertHistory:
    return AlertHistory(
        alert_id=alert.alert_id,
        timestamp=alert.timestamp,
        alert_type=alert.alert_type.value,
        severity=alert.severity.value,
        use_case=alert.use_case,
        message=alert.message,
        metric_value=alert.metric_value,
        threshold_value=alert.threshold_value,
        resolved=alert.resolved,
    )

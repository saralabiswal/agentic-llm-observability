"""
Integration adapters that expose collected telemetry to external operations tools.

Author: Sarala Biswal
"""

from collections import defaultdict
from dataclasses import dataclass, field


@dataclass
class PrometheusMetrics:
    counters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    gauges: dict[str, float] = field(default_factory=dict)
    histograms: dict[str, list[float]] = field(default_factory=lambda: defaultdict(list))

    def inc_counter(self, name: str, amount: float = 1.0) -> None:
        self.counters[name] += amount

    def set_gauge(self, name: str, value: float) -> None:
        self.gauges[name] = value

    def observe_histogram(self, name: str, value: float) -> None:
        self.histograms[name].append(value)

    def render(self) -> str:
        lines: list[str] = []
        for name, value in sorted(self.counters.items()):
            lines.extend([f"# TYPE {name} counter", f"{name} {value}"])
        for name, value in sorted(self.gauges.items()):
            lines.extend([f"# TYPE {name} gauge", f"{name} {value}"])
        for name, values in sorted(self.histograms.items()):
            count = len(values)
            total = sum(values)
            lines.extend(
                [
                    f"# TYPE {name} histogram",
                    f"{name}_count {count}",
                    f"{name}_sum {total}",
                ]
            )
        return "\n".join(lines) + "\n"


def default_metrics() -> PrometheusMetrics:
    metrics = PrometheusMetrics()
    metrics.inc_counter("llm_calls_total", 0)
    metrics.inc_counter("llm_cost_usd_total", 0)
    metrics.observe_histogram("llm_latency_ms", 0)
    metrics.observe_histogram("llm_quality_score", 0)
    metrics.set_gauge("active_alerts", 0)
    metrics.set_gauge("drift_score", 0)
    return metrics

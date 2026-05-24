/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import { Activity, Clock3, Gauge, Route, TimerReset, Zap } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  displayModelName,
  getLatencyPercentiles,
  getLatencyTimeline,
  type LatencyPercentiles,
  type LatencyTimelinePoint,
} from "../api/client";
import { EmptyState, SectionHeader, SkeletonLoader, StatusBadge } from "../components";

const REVENUE_USE_CASE = "quote_to_cash_revenue_command_center";

export function LatencyTracker() {
  const [loading, setLoading] = useState(true);
  const [percentiles, setPercentiles] = useState<LatencyPercentiles[]>([]);
  const [timeline, setTimeline] = useState<LatencyTimelinePoint[]>([]);

  useEffect(() => {
    function load() {
      Promise.all([
        getLatencyPercentiles(REVENUE_USE_CASE),
        getLatencyTimeline(REVENUE_USE_CASE),
      ])
        .then(([nextPercentiles, nextTimeline]) => {
          setPercentiles(nextPercentiles);
          setTimeline(nextTimeline);
        })
        .catch(() => {
          setPercentiles([]);
          setTimeline([]);
        })
        .finally(() => setLoading(false));
    }
    load();
    window.addEventListener("llmobs:data-updated", load);
    return () => window.removeEventListener("llmobs:data-updated", load);
  }, []);

  const summary = useMemo(() => {
    const primary = [...percentiles].sort((a, b) => b.p95_ms - a.p95_ms)[0];
    const avgCompliance = percentiles.length
      ? percentiles.reduce((sum, item) => sum + item.slo_compliance_pct, 0) / percentiles.length
      : 0;
    const breaches = percentiles.reduce((sum, item) => sum + item.breach_count_24h, 0);
    const p99 = percentiles.length ? Math.max(...percentiles.map((item) => item.p99_ms)) : 0;
    return { primary, avgCompliance, breaches, p99 };
  }, [percentiles]);

  if (loading) {
    return <SkeletonLoader rows={8} />;
  }

  if (!percentiles.length) {
    return (
      <EmptyState
        icon={Clock3}
        title="Latency data is not connected"
        sub="Run the Quote-to-Cash Agentic Flow to view p95, p99, and SLO compliance."
        action="Refresh"
        onAction={() => window.location.reload()}
      />
    );
  }

  const status = summary.avgCompliance >= 98 ? "healthy" : summary.avgCompliance >= 95 ? "warning" : "critical";

  return (
    <>
      <SectionHeader
        eyebrow="Runtime performance"
        title="Latency SLOs and percentile view"
        sub="Runtime performance controls for agent chains: p50, p95, p99, breach behavior, and model-level latency hotspots."
      />

      <section className="ops-command-strip">
        <OpsCommandCard icon={Clock3} label="Worst p95" value={`${summary.primary?.p95_ms ?? 0}ms`} detail={summary.primary ? displayModelName(summary.primary.model) : "no model"} status={status} />
        <OpsCommandCard icon={Gauge} label="SLO Compliance" value={`${summary.avgCompliance.toFixed(1)}%`} detail="model average" status={status} />
        <OpsCommandCard icon={TimerReset} label="p99 Ceiling" value={`${summary.p99}ms`} detail="tail latency" status={summary.p99 > 2500 ? "warning" : "healthy"} />
        <OpsCommandCard icon={Activity} label="24h Breaches" value={summary.breaches.toString()} detail="SLO threshold misses" status={summary.breaches > 0 ? "warning" : "stable"} />
      </section>

      <div className="ops-board-grid">
        <section className="ops-panel ops-panel-primary">
          <div className="ops-panel-head">
            <div>
              <p className="detail-kicker">Latency decision</p>
              <h3>Keep quote review interactive while five agent calls execute</h3>
              <p>
                The latency tab shows whether the full Quote-to-Cash agent chain remains usable for
                a revenue operator, with tail latency and breach counts separated from the average.
              </p>
            </div>
            <Zap size={22} aria-hidden="true" />
          </div>
          <div className="ops-impact-grid">
            <OpsImpact label="p50 best path" value={`${Math.min(...percentiles.map((item) => item.p50_ms))}ms`} positive />
            <OpsImpact label="p95 hotspot" value={`${summary.primary?.p95_ms ?? 0}ms`} positive={(summary.primary?.p95_ms ?? 0) <= (summary.primary?.slo_target_ms ?? 2000)} />
            <OpsImpact label="SLO target" value={`${summary.primary?.slo_target_ms ?? 0}ms`} positive />
          </div>
          <div className="ops-comparison-list">
            {percentiles.map((item) => (
              <LatencyRow key={item.model} item={item} />
            ))}
          </div>
        </section>

        <section className="ops-panel">
          <div className="ops-panel-head ops-panel-head-compact">
            <div>
              <p className="detail-kicker">Control policy</p>
              <h3>Interactive quote SLO</h3>
            </div>
            <StatusBadge status={status} />
          </div>
          <div className="ops-policy-stack">
            <OpsPolicyItem icon={Route} title="Measure the whole agent chain" copy="Each prompt call records latency so slow steps can be separated from total quote-run latency." />
            <OpsPolicyItem icon={TimerReset} title="Use p95 and p99 for operator experience" copy="Tail latency is tracked explicitly because averages hide slow approval or negotiation prompts." />
            <OpsPolicyItem icon={Zap} title="Route high-volume runs to faster local models" copy="Settings can move local runs across Llama, Qwen, and Mistral while the SLO view exposes performance impact." />
          </div>
        </section>
      </div>

      <section className="ops-panel">
        <div className="ops-panel-head ops-panel-head-compact">
          <div>
            <p className="detail-kicker">Latency evidence registry</p>
            <h3>Model percentile profile</h3>
          </div>
          <span className="ops-count">{timeline.length} daily points</span>
        </div>
        <div className="ops-registry">
          {percentiles.map((item) => (
            <article className="ops-registry-row ops-registry-row-latency" key={item.model}>
              <div>
                <strong>{displayModelName(item.model)}</strong>
                <span>{`${item.slo_compliance_pct.toFixed(1)}% SLO compliance`}</span>
              </div>
              <StatusBadge status={item.slo_compliance_pct < 95 ? "critical" : item.slo_compliance_pct < 98 ? "warning" : "healthy"} />
              <span>{`p50 ${item.p50_ms}ms`}</span>
              <span>{`p95 ${item.p95_ms}ms`}</span>
              <span>{`p99 ${item.p99_ms}ms`}</span>
              <span>{`${item.breach_count_24h} breaches`}</span>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function LatencyRow({ item }: { item: LatencyPercentiles }) {
  return (
    <article className="ops-comparison-row">
      <div>
        <strong>{displayModelName(item.model)}</strong>
        <span>{`target ${item.slo_target_ms}ms`}</span>
      </div>
      <OpsMetricBar icon={Clock3} label="p50" value={item.p50_ms} max={item.slo_target_ms * 1.4} display={`${item.p50_ms}ms`} invert />
      <OpsMetricBar icon={Gauge} label="p95" value={item.p95_ms} max={item.slo_target_ms * 1.4} display={`${item.p95_ms}ms`} invert />
      <OpsMetricBar icon={TimerReset} label="p99" value={item.p99_ms} max={item.slo_target_ms * 1.4} display={`${item.p99_ms}ms`} invert />
    </article>
  );
}

function OpsCommandCard({ icon: Icon, label, value, detail, status }: { icon: LucideIcon; label: string; value: string; detail: string; status: string }) {
  return (
    <article className="ops-command-card">
      <Icon size={18} aria-hidden="true" />
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
      <StatusBadge status={status} />
    </article>
  );
}

function OpsImpact({ label, value, positive }: { label: string; value: string; positive: boolean }) {
  return (
    <div className={`ops-impact ${positive ? "ops-impact-positive" : "ops-impact-watch"}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function OpsMetricBar({ icon: Icon, label, value, max, display, invert = false }: { icon: LucideIcon; label: string; value: number; max: number; display: string; invert?: boolean }) {
  const pct = Math.max(4, Math.min(100, (value / max) * 100));
  return (
    <div className="ops-metric-bar">
      <span><Icon size={13} aria-hidden="true" />{label}</span>
      <div className="ops-bar-track">
        <div className={invert ? "ops-bar-fill ops-bar-fill-amber" : "ops-bar-fill"} style={{ width: `${pct}%` }} />
      </div>
      <strong>{display}</strong>
    </div>
  );
}

function OpsPolicyItem({ icon: Icon, title, copy }: { icon: LucideIcon; title: string; copy: string }) {
  return (
    <article className="ops-policy-item">
      <Icon size={18} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <p>{copy}</p>
      </div>
    </article>
  );
}

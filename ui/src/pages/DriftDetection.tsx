/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import { AlertTriangle, Bell, GitBranch, Radar, ShieldCheck, TrendingUp } from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { displayModelName, getDriftAlerts, getDriftScores, type AlertRecord, type DriftScore } from "../api/client";
import { EmptyState, SectionHeader, SkeletonLoader, StatusBadge } from "../components";

const REVENUE_USE_CASE = "quote_to_cash_revenue_command_center";
const USE_CASE_LABELS: Record<string, string> = {
  quote_to_cash_revenue_command_center: "Quote-to-Cash Agentic Flow",
  banking_payment_risk: "Banking Payment Risk",
  renewal_agent: "Renewal Agent",
  quote_generation: "Quote Generation",
  cdp_churn_prediction: "CDP Churn Prediction",
  hr_onboarding: "HR Onboarding",
};

export function DriftDetection() {
  const [loading, setLoading] = useState(true);
  const [scores, setScores] = useState<DriftScore[]>([]);
  const [alerts, setAlerts] = useState<AlertRecord[]>([]);

  useEffect(() => {
    function load() {
      Promise.all([getDriftScores(REVENUE_USE_CASE), getDriftAlerts(REVENUE_USE_CASE)])
        .then(([nextScores, nextAlerts]) => {
          setScores(nextScores);
          setAlerts(nextAlerts);
        })
        .catch(() => {
          setScores([]);
          setAlerts([]);
        })
        .finally(() => setLoading(false));
    }
    load();
    window.addEventListener("llmobs:data-updated", load);
    return () => window.removeEventListener("llmobs:data-updated", load);
  }, []);

  const summary = useMemo(() => {
    const latest = scores[scores.length - 1];
    const peak = scores.length ? Math.max(...scores.map((item) => item.drift_score)) : 0;
    const avgSimilarity = scores.length
      ? scores.reduce((sum, item) => sum + item.baseline_similarity, 0) / scores.length
      : 0;
    const openAlerts = alerts.filter((alert) => !alert.resolved).length;
    return { latest, peak, avgSimilarity, openAlerts };
  }, [scores, alerts]);

  if (loading) {
    return <SkeletonLoader rows={8} />;
  }

  if (!scores.length) {
    return (
      <EmptyState
        icon={GitBranch}
        title="Drift data is not connected"
        sub="Run the Quote-to-Cash Agentic Flow to view semantic movement and threshold alerts."
        action="Refresh"
        onAction={() => window.location.reload()}
      />
    );
  }

  const latestScore = summary.latest?.drift_score ?? 0;
  const status = latestScore > 0.35 ? "critical" : latestScore > 0.2 ? "warning" : "stable";

  return (
    <>
      <SectionHeader
        eyebrow="Semantic drift"
        title="Drift and alert history"
        sub="Semantic movement controls for Quote-to-Cash outputs: baseline similarity, drift score, open alerts, and investigation state."
      />

      <section className="ops-command-strip">
        <OpsCommandCard icon={GitBranch} label="Latest Drift" value={latestScore.toFixed(2)} detail="current semantic movement" status={status} />
        <OpsCommandCard icon={Radar} label="Baseline Similarity" value={summary.avgSimilarity.toFixed(2)} detail="30-day average" status={summary.avgSimilarity < 0.75 ? "warning" : "healthy"} />
        <OpsCommandCard icon={TrendingUp} label="Peak Drift" value={summary.peak.toFixed(2)} detail="highest observed score" status={summary.peak > 0.35 ? "warning" : "stable"} />
        <OpsCommandCard icon={Bell} label="Open Alerts" value={summary.openAlerts.toString()} detail={`${alerts.length} total drift alerts`} status={summary.openAlerts > 0 ? "warning" : "stable"} />
      </section>

      <div className="ops-board-grid">
        <section className="ops-panel ops-panel-primary">
          <div className="ops-panel-head">
            <div>
              <p className="detail-kicker">Drift decision</p>
              <h3>Watch semantic movement before it becomes quote-policy risk</h3>
              <p>
                The drift tab compares current Quote-to-Cash output behavior against its baseline.
                Movement above threshold means the agent may be responding differently to discount,
                margin, or approval evidence.
              </p>
            </div>
            <AlertTriangle size={22} aria-hidden="true" />
          </div>
          <div className="ops-impact-grid">
            <OpsImpact label="Alert threshold" value="0.35" positive={latestScore <= 0.35} />
            <OpsImpact label="Watch threshold" value="0.20" positive={latestScore <= 0.2} />
            <OpsImpact label="Current state" value={status.toUpperCase()} positive={status === "stable"} />
          </div>
          <div className="ops-comparison-list">
            {scores.slice(-5).reverse().map((score) => (
              <DriftScoreRow key={`${score.timestamp}-${score.model}`} score={score} />
            ))}
          </div>
        </section>

        <section className="ops-panel">
          <div className="ops-panel-head ops-panel-head-compact">
            <div>
              <p className="detail-kicker">Control policy</p>
              <h3>Semantic drift guardrail</h3>
            </div>
            <StatusBadge status={status} />
          </div>
          <div className="ops-policy-stack">
            <OpsPolicyItem icon={Radar} title="Compare output behavior against baseline" copy="Drift tracks semantic movement so prompt or model changes do not silently alter quote recommendations." />
            <OpsPolicyItem icon={Bell} title="Alert when drift crosses policy threshold" copy="Open alerts stay visible until reviewed, keeping production risk connected to operator action." />
            <OpsPolicyItem icon={ShieldCheck} title="Use drift with quality evidence" copy="A stable quality score with rising drift still deserves review because the decision pattern changed." />
          </div>
        </section>
      </div>

      <section className="ops-panel">
        <div className="ops-panel-head ops-panel-head-compact">
          <div>
            <p className="detail-kicker">Drift evidence registry</p>
            <h3>Alert and movement history</h3>
          </div>
          <span className="ops-count">{alerts.length} alerts</span>
        </div>
        <div className="ops-registry">
          {(alerts.length ? alerts : scores.slice(-5)).map((item) => {
            if ("alert_id" in item) {
              return (
                <article className="ops-registry-row ops-registry-row-drift" key={item.alert_id}>
                  <div>
                    <strong>{new Date(item.timestamp).toLocaleString()}</strong>
                    <span>{formatUseCase(item.use_case ?? "")}</span>
                  </div>
                  <StatusBadge status={item.severity} />
                  <span>{item.metric_value?.toFixed(2) ?? "n/a"}</span>
                  <span>{item.resolved ? "resolved" : "open"}</span>
                  <span>{item.message}</span>
                </article>
              );
            }
            return (
              <article className="ops-registry-row ops-registry-row-drift" key={`${item.timestamp}-${item.model}`}>
                <div>
                  <strong>{new Date(item.timestamp).toLocaleString()}</strong>
                  <span>{formatUseCase(item.use_case)}</span>
                </div>
                <StatusBadge status={item.alert_triggered ? "warning" : "stable"} />
                <span>{item.drift_score.toFixed(2)}</span>
                <span>{item.alert_triggered ? "open" : "clear"}</span>
                <span>{`baseline similarity ${item.baseline_similarity.toFixed(2)}`}</span>
              </article>
            );
          })}
        </div>
      </section>
    </>
  );
}

function DriftScoreRow({ score }: { score: DriftScore }) {
  return (
    <article className="ops-comparison-row">
      <div>
        <strong>{displayModelName(score.model)}</strong>
        <span>{new Date(score.timestamp).toLocaleString()}</span>
      </div>
      <OpsMetricBar icon={GitBranch} label="Drift" value={score.drift_score} max={0.5} display={score.drift_score.toFixed(2)} invert />
      <OpsMetricBar icon={Radar} label="Similarity" value={score.baseline_similarity} max={1} display={score.baseline_similarity.toFixed(2)} />
      <OpsMetricBar icon={Bell} label="Threshold" value={0.35} max={0.5} display="0.35" invert />
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

function formatUseCase(value: string): string {
  return USE_CASE_LABELS[value] ?? value.replace(/_/g, " ");
}

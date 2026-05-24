/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import {
  BrainCircuit,
  CheckCircle2,
  FileCheck2,
  Gauge,
  ShieldAlert,
  ShieldCheck,
  Target,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  displayModelName,
  getGateResults,
  getHallucinations,
  getQualityScores,
  type GateResult,
  type HallucinationRate,
  type QualityScore,
} from "../api/client";
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

export function QualityMonitor() {
  const [loading, setLoading] = useState(true);
  const [scores, setScores] = useState<QualityScore[]>([]);
  const [hallucinations, setHallucinations] = useState<HallucinationRate[]>([]);
  const [gates, setGates] = useState<GateResult[]>([]);

  useEffect(() => {
    function load() {
      Promise.all([
        getQualityScores(REVENUE_USE_CASE),
        getHallucinations(REVENUE_USE_CASE),
        getGateResults(REVENUE_USE_CASE),
      ])
        .then(([nextScores, nextHallucinations, nextGates]) => {
          setScores(nextScores);
          setHallucinations(nextHallucinations);
          setGates(nextGates);
        })
        .catch(() => {
          setScores([]);
          setHallucinations([]);
          setGates([]);
        })
        .finally(() => setLoading(false));
    }
    load();
    window.addEventListener("llmobs:data-updated", load);
    return () => window.removeEventListener("llmobs:data-updated", load);
  }, []);

  const metrics = useMemo(() => {
    const latest = scores[scores.length - 1];
    const avg = scores.length
      ? scores.reduce((sum, item) => sum + item.composite_score, 0) / scores.length
      : 0;
    const flagged = hallucinations.reduce((sum, item) => sum + item.flagged_count, 0);
    const calls = hallucinations.reduce((sum, item) => sum + item.call_count, 0);
    const passed = gates.reduce((sum, item) => sum + item.passed, 0);
    const failed = gates.reduce((sum, item) => sum + item.failed, 0);
    return {
      avg,
      latest,
      hallucinationRate: calls ? (flagged / calls) * 100 : 0,
      gatePassRate: passed + failed ? (passed / (passed + failed)) * 100 : 0,
      flagged,
      calls,
      passed,
      failed,
    };
  }, [scores, hallucinations, gates]);

  if (loading) {
    return <SkeletonLoader rows={8} />;
  }

  if (!scores.length) {
    return (
      <EmptyState
        icon={BrainCircuit}
        title="Quality data is not connected"
        sub="Run the Quote-to-Cash Agentic Flow to view grounding, hallucination, and gate evidence."
        action="Refresh"
        onAction={() => window.location.reload()}
      />
    );
  }

  const status = metrics.avg >= 0.82 && metrics.hallucinationRate < 5 ? "healthy" : metrics.avg >= 0.7 ? "warning" : "critical";
  const latest = metrics.latest ?? scores[0];

  return (
    <>
      <SectionHeader
        eyebrow="Quality evidence"
        title="Quality and grounding evidence"
        sub="Business-quality controls for Quote-to-Cash recommendations: faithfulness, relevance, coherence, hallucination flags, and gate outcomes."
      />

      <section className="ops-command-strip">
        <OpsCommandCard icon={BrainCircuit} label="Quality Score" value={metrics.avg.toFixed(2)} detail="30-day composite" status={status} />
        <OpsCommandCard icon={ShieldAlert} label="Hallucination" value={`${metrics.hallucinationRate.toFixed(1)}%`} detail={`${metrics.flagged} flagged of ${metrics.calls}`} status={metrics.hallucinationRate > 5 ? "warning" : "healthy"} />
        <OpsCommandCard icon={CheckCircle2} label="Gate Pass Rate" value={`${metrics.gatePassRate.toFixed(1)}%`} detail={`${metrics.passed} passed / ${metrics.failed} failed`} status={metrics.gatePassRate >= 95 ? "healthy" : "warning"} />
        <OpsCommandCard icon={Target} label="Evidence State" value="Grounded" detail="Recommendation cites quote evidence" status="active" />
      </section>

      <div className="ops-board-grid">
        <section className="ops-panel ops-panel-primary">
          <div className="ops-panel-head">
            <div>
              <p className="detail-kicker">Quality decision</p>
              <h3>Allow quote guidance when evidence, relevance, and coherence clear the gate</h3>
              <p>
                The quality monitor treats the Quote-to-Cash output as a business decision, not just
                a text response. Low faithfulness, weak relevance, or flagged hallucination evidence
                becomes a production review signal.
              </p>
            </div>
            <ShieldCheck size={22} aria-hidden="true" />
          </div>
          <div className="ops-impact-grid">
            <OpsImpact label="Faithfulness" value={latest.faithfulness.toFixed(2)} positive={latest.faithfulness >= 0.8} />
            <OpsImpact label="Relevance" value={latest.relevance.toFixed(2)} positive={latest.relevance >= 0.8} />
            <OpsImpact label="Coherence" value={latest.coherence.toFixed(2)} positive={latest.coherence >= 0.8} />
          </div>
          <div className="ops-comparison-list">
            {scores.slice(-5).reverse().map((score) => (
              <QualityScoreRow key={`${score.timestamp}-${score.model}`} score={score} />
            ))}
          </div>
        </section>

        <section className="ops-panel">
          <div className="ops-panel-head ops-panel-head-compact">
            <div>
              <p className="detail-kicker">Control policy</p>
              <h3>Grounding gate</h3>
            </div>
            <StatusBadge status={status} />
          </div>
          <div className="ops-policy-stack">
            <OpsPolicyItem icon={FileCheck2} title="Evidence must support the quote note" copy="Customer-facing quote language is checked against grounded account and opportunity context." />
            <OpsPolicyItem icon={Gauge} title="Composite quality tracks three dimensions" copy="Faithfulness, relevance, and coherence are retained separately so a single score does not hide the failure mode." />
            <OpsPolicyItem icon={ShieldAlert} title="Flags remain visible to operators" copy="Hallucination flags are summarized by model and business flow for investigation." />
          </div>
        </section>
      </div>

      <section className="ops-panel">
        <div className="ops-panel-head ops-panel-head-compact">
          <div>
            <p className="detail-kicker">Quality evidence registry</p>
            <h3>Grounding and gate outcomes</h3>
          </div>
          <span className="ops-count">{hallucinations.length} model rows</span>
        </div>
        <div className="ops-registry">
          {hallucinations.map((item) => (
            <article className="ops-registry-row ops-registry-row-quality" key={`${item.model}-${item.use_case}`}>
              <div>
                <strong>{displayModelName(item.model)}</strong>
                <span>{formatUseCase(item.use_case)}</span>
              </div>
              <StatusBadge status={item.flagged_count > 0 ? "warning" : "healthy"} />
              <span>{`${(100 - item.hallucination_rate).toFixed(1)}% grounded`}</span>
              <span>{`${item.flagged_count} flagged`}</span>
              <span>{`${item.call_count} calls`}</span>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function QualityScoreRow({ score }: { score: QualityScore }) {
  return (
    <article className="ops-comparison-row">
      <div>
        <strong>{displayModelName(score.model)}</strong>
        <span>{new Date(score.timestamp).toLocaleString()}</span>
      </div>
      <OpsMetricBar icon={BrainCircuit} label="Composite" value={score.composite_score} max={1} display={score.composite_score.toFixed(2)} />
      <OpsMetricBar icon={FileCheck2} label="Faithful" value={score.faithfulness} max={1} display={score.faithfulness.toFixed(2)} />
      <OpsMetricBar icon={Target} label="Relevant" value={score.relevance} max={1} display={score.relevance.toFixed(2)} />
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

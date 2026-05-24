/**
 * Quote-to-Cash workflow page where users run the agent flow and generate telemetry.
 *
 * Author: Sarala Biswal
 */
import {
  BadgeCheck,
  BarChart3,
  BriefcaseBusiness,
  CircleDollarSign,
  FileText,
  Gauge,
  Loader2,
  Route,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import {
  LOCAL_MODEL_OPTIONS,
  displayModelName,
  analyzeRevenueOpportunity,
  getRevenueControls,
  getRevenueOpportunities,
  type RevenueControls,
  type RevenueDeskResponse,
  type RevenueOpportunity,
} from "../api/client";
import { SectionHeader, StatusBadge } from "../components";

type RevenueCommandCenterProps = {
  selectedLocalModel: string;
  onOpenDashboard?: (index: number) => void;
  onTelemetryUpdated?: () => Promise<void> | void;
};

export function RevenueCommandCenter({
  selectedLocalModel,
  onOpenDashboard,
  onTelemetryUpdated,
}: RevenueCommandCenterProps) {
  const [opportunities, setOpportunities] = useState<RevenueOpportunity[]>([]);
  const [controls, setControls] = useState<RevenueControls>({
    prompt_versions: [
      { value: "v2.1", label: "Margin-aware prompt v2.1 - preserve target margin" },
      { value: "v2.2", label: "Approval-aware prompt v2.2 - policy-ready" },
      { value: "v1.0", label: "Baseline prompt v1.0 - fastest draft" },
    ],
  });
  const [selectedOpportunityId, setSelectedOpportunityId] = useState("");
  const [promptVersion, setPromptVersion] = useState("v2.1");
  const [guardrailsEnabled, setGuardrailsEnabled] = useState(true);
  const [result, setResult] = useState<RevenueDeskResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    let cancelled = false;
    async function load() {
      setLoading(true);
      setError("");
      try {
        const [items, loadedControls] = await Promise.all([
          getRevenueOpportunities(),
          getRevenueControls(),
        ]);
        if (!cancelled) {
          setOpportunities(items);
          setControls(loadedControls);
          setSelectedOpportunityId((current) => current || items[0]?.opportunity_id || "");
        }
      } catch {
        if (!cancelled) {
          setError("Quote-to-Cash workflow is unavailable.");
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selectedOpportunity = useMemo(
    () => opportunities.find((item) => item.opportunity_id === selectedOpportunityId),
    [opportunities, selectedOpportunityId],
  );
  const guardrailApplies = promptVersion === "v2.2";
  const effectiveGuardrailsEnabled = guardrailApplies && guardrailsEnabled;
  const guardrailHelper = guardrailApplies
    ? effectiveGuardrailsEnabled
      ? "Hard cap at approval policy"
      : "Advisory prompt only"
    : "Available with v2.2 strategy";

  async function runAnalysis() {
    if (!selectedOpportunityId) {
      return;
    }
    setAnalyzing(true);
    setError("");
    try {
      const response = await analyzeRevenueOpportunity({
        opportunity_id: selectedOpportunityId,
        prompt_version: promptVersion,
        model_mode: "ollama",
        local_model: selectedLocalModel,
        approval_guardrails_enabled: effectiveGuardrailsEnabled,
      });
      setResult(response);
      window.localStorage.setItem("llmobs:selected-use-case", response.trace.use_case);
      window.dispatchEvent(new CustomEvent("llmobs:data-updated"));
      await onTelemetryUpdated?.();
    } catch {
      setError("Analysis failed. Check the API server and selected model mode.");
    } finally {
      setAnalyzing(false);
    }
  }

  const active = result?.opportunity ?? selectedOpportunity;
  const recommendation = result?.recommendation;
  const trace = result?.trace;
  const selectedLocalModelLabel =
    LOCAL_MODEL_OPTIONS.find((item) => item.value === selectedLocalModel)?.label ?? selectedLocalModel;
  const selectedRuntimeLabel = `Local LLM - ${selectedLocalModelLabel}`;

  return (
    <>
      <SectionHeader
        eyebrow="Quote-to-Cash mini app"
        title="Quote-to-Cash Agentic Flow"
        sub="Run a quote analysis workflow and watch the observability telemetry update from the same action."
      />

      <div className="business-story-grid">
        <article>
          <span>Problem</span>
          <strong>Revenue teams cannot trust agentic quoting without evidence.</strong>
          <p>
            Discount pressure, renewal risk, margin exposure, and approval policy all move at once.
            Leaders need to know what the agent decided and what it cost to run.
          </p>
        </article>
        <article>
          <span>Solution</span>
          <strong>Run one governed Quote-to-Cash agent flow.</strong>
          <p>
            Select a real opportunity, generate a quote recommendation, apply margin-aware policy,
            and produce customer-facing guidance with cited business evidence.
          </p>
        </article>
        <article>
          <span>Proof</span>
          <strong>Show the observability matrix behind the decision.</strong>
          <p>
            The same run records cost, quality, latency, prompt version, model mode, drift, and alerts
            so the business output and operational telemetry stay connected.
          </p>
        </article>
      </div>

      <div className="revenue-command-panel">
        <div className="revenue-command-primary">
          <label className="field-label">
            Opportunity
            <select
              className="select-input revenue-opportunity-select"
              value={selectedOpportunityId}
              onChange={(event) => setSelectedOpportunityId(event.target.value)}
              disabled={loading || analyzing}
            >
              {opportunities.map((opportunity) => (
                <option key={opportunity.opportunity_id} value={opportunity.opportunity_id}>
                  {opportunity.account.name} - {opportunity.name}
                </option>
              ))}
            </select>
          </label>
          <label className="field-label">
            Prompt Strategy
            <select
              className="select-input"
              value={promptVersion}
              onChange={(event) => setPromptVersion(event.target.value)}
              disabled={analyzing}
            >
              {controls.prompt_versions.map((item) => (
                <option key={item.value} value={item.value}>
                  {item.label}
                </option>
              ))}
            </select>
          </label>
        </div>
        <div className="runtime-readout" aria-label="Runtime Path">
          <span>Runtime Path</span>
          <strong>{selectedRuntimeLabel}</strong>
          <em>Managed in Settings</em>
        </div>
        <label className={`guardrail-control ${guardrailApplies ? "" : "guardrail-control-disabled"}`}>
          <input
            type="checkbox"
            checked={effectiveGuardrailsEnabled}
            onChange={(event) => setGuardrailsEnabled(event.target.checked)}
            disabled={analyzing || !guardrailApplies}
          />
          <span>
            <strong>Enforce approval policy</strong>
            <em>{guardrailHelper}</em>
          </span>
        </label>
        <button
          className="guided-run-button"
          type="button"
          onClick={runAnalysis}
          disabled={loading || analyzing || !selectedOpportunityId}
        >
          {analyzing ? <Loader2 size={16} aria-hidden="true" /> : <Sparkles size={16} aria-hidden="true" />}
          <span>
            <strong>{analyzing ? "Analyzing" : "Run Agent Flow"}</strong>
            <em>Quote + telemetry</em>
          </span>
        </button>
      </div>

      {error ? <div className="alert-banner alert-warning">{error}</div> : null}

      {active ? (
        <>
          <div className="revenue-snapshot-strip">
            <SnapshotMetric icon={CircleDollarSign} label="ARR" value={money(active.arr_usd)} sub={`${active.contract_terms_months} month term`} />
            <SnapshotMetric icon={BadgeCheck} label="Requested discount" value={`${active.requested_discount_pct.toFixed(1)}%`} sub={`current ${active.current_discount_pct.toFixed(1)}%`} />
            <SnapshotMetric icon={Gauge} label="Margin target" value={`${active.target_margin_pct.toFixed(1)}%`} sub={`current ${active.current_margin_pct.toFixed(1)}%`} />
            <SnapshotMetric icon={ShieldCheck} label="Renewal risk" value={titleCase(active.renewal_risk)} sub={`health ${active.account.customer_health}`} />
          </div>

          <div className="revenue-layout">
            <section className="chart-card revenue-panel">
              <div className="revenue-panel-head">
                <BriefcaseBusiness size={18} aria-hidden="true" />
                <div>
                  <h3 className="chart-title">{active.account.name}</h3>
                  <p className="chart-sub">
                    {active.name} · {titleCase(active.scenario)} · {active.stage}
                  </p>
                </div>
              </div>
              <div className="revenue-fact-grid">
                <Fact label="Region" value={active.account.region} />
                <Fact label="Tier" value={titleCase(active.product_tier)} />
                <Fact label="Expansion ARR" value={money(active.expansion_arr_usd)} />
                <Fact label="Forecast TCV" value={money(active.total_contract_value_usd)} />
              </div>
              <ListBlock title="Pain Points" items={active.pain_points} />
              <ListBlock title="Grounded Evidence" items={active.grounded_evidence} />
            </section>

            <section className="chart-card revenue-panel revenue-recommendation-panel">
              <div className="revenue-panel-head">
                <FileText size={18} aria-hidden="true" />
                <div>
                  <h3 className="chart-title">Recommendation</h3>
                  <p className="chart-sub">
                    {recommendation ? "Generated quote guidance" : "Ready for analysis"}
                  </p>
                </div>
              </div>
              {recommendation ? (
                <>
                  <div className="revenue-decision-strip">
                    <Fact label="Recommended Discount" value={`${recommendation.recommended_discount_pct.toFixed(1)}%`} />
                    <Fact label="Expected Margin" value={`${recommendation.expected_margin_pct.toFixed(1)}%`} />
                    <Fact label="Approval" value={titleCase(recommendation.approval_recommendation)} />
                  </div>
                  <p className="revenue-copy">{recommendation.renewal_risk_summary}</p>
                  <p className="revenue-copy">{recommendation.margin_risk_assessment}</p>
                  <ListBlock title="Negotiation Guidance" items={recommendation.negotiation_guidance} />
                  <div className="quote-note">
                    <p className="detail-kicker">Customer-facing quote note</p>
                    <p>{recommendation.customer_facing_quote_note}</p>
                  </div>
                </>
              ) : (
                <div className="empty-state revenue-empty">
                  <Route size={28} aria-hidden="true" />
                  <p className="empty-title">No quote analysis yet</p>
                  <p className="empty-sub">Select the deal controls and run the revenue agent.</p>
                </div>
              )}
            </section>
          </div>

          {trace ? (
            <section className="chart-card revenue-trace-panel">
              <div className="revenue-panel-head">
                <Route size={18} aria-hidden="true" />
                <div>
                  <h3 className="chart-title">Latest Observability Trace</h3>
                  <p className="chart-sub">
                    {trace.model_mode} · {displayModelName(trace.model)} · {trace.prompt_version} · {trace.input_tokens + trace.output_tokens} tokens · ${Number(trace.cost_usd).toFixed(6)}
                  </p>
                </div>
                <StatusBadge status={trace.alerts_created > 0 ? "warning" : "healthy"} />
              </div>
              <div className="trace-step-grid">
                {trace.steps.map((step) => (
                  <article className="trace-step" key={step.call_id}>
                    <span className="trace-system">{step.system} · {step.prompt_version}</span>
                    <strong>{step.agent_name}</strong>
                    <span className="trace-step-label">{step.label}</span>
                    <div className="trace-step-metrics">
                      <span>{step.input_tokens + step.output_tokens} tokens</span>
                      <span>{step.latency_ms}ms</span>
                      <span>${Number(step.cost_usd).toFixed(6)}</span>
                      <span>Q {step.quality_score.toFixed(2)}</span>
                    </div>
                    <p>{step.detail}</p>
                  </article>
                ))}
              </div>
              <div className="observability-matrix">
                <Fact label="Cost" value={`$${Number(trace.cost_usd).toFixed(6)}`} />
                <Fact label="Quality" value={trace.quality_score.toFixed(2)} />
                <Fact label="Latency" value={`${trace.latency_ms}ms`} />
                <Fact label="Prompt" value={trace.prompt_version} />
                <Fact label="Model" value={displayModelName(trace.model)} />
                <Fact label="Margin Risk" value={trace.margin_risk_score.toFixed(2)} />
              </div>
              <div className="revenue-flow-actions">
                <span className="trace-system">Continue observability flow</span>
                <button type="button" className="action-button" onClick={() => onOpenDashboard?.(2)}>
                  <BarChart3 size={15} aria-hidden="true" />
                  Cost
                </button>
                <button type="button" className="action-button" onClick={() => onOpenDashboard?.(3)}>
                  <ShieldCheck size={15} aria-hidden="true" />
                  Quality
                </button>
                <button type="button" className="action-button" onClick={() => onOpenDashboard?.(4)}>
                  <Gauge size={15} aria-hidden="true" />
                  Latency
                </button>
                <button type="button" className="action-button" onClick={() => onOpenDashboard?.(5)}>
                  <FileText size={15} aria-hidden="true" />
                  Prompts
                </button>
                <button type="button" className="action-button" onClick={() => onOpenDashboard?.(6)}>
                  <Route size={15} aria-hidden="true" />
                  Drift
                </button>
              </div>
            </section>
          ) : null}
        </>
      ) : null}
    </>
  );
}

function Fact({ label, value }: { label: string; value: string }) {
  return (
    <div className="revenue-fact">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function SnapshotMetric({
  icon: Icon,
  label,
  value,
  sub,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  sub: string;
}) {
  return (
    <article className="revenue-snapshot-item">
      <Icon size={15} aria-hidden="true" />
      <span>{label}</span>
      <strong>{value}</strong>
      <em>{sub}</em>
    </article>
  );
}

function ListBlock({ title, items }: { title: string; items: string[] }) {
  return (
    <div className="revenue-list-block">
      <p className="detail-kicker">{title}</p>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </div>
  );
}

function money(value: string): string {
  return `$${Number(value).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function titleCase(value: string): string {
  return value
    .replace(/_/g, " ")
    .replace(/\w\S*/g, (word: string) => word.charAt(0).toUpperCase() + word.slice(1).toLowerCase());
}

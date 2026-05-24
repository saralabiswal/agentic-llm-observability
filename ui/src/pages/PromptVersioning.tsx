/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import {
  Archive,
  Clock3,
  DollarSign,
  FlaskConical,
  Gauge,
  GitCompare,
  ScrollText,
  ShieldCheck,
} from "lucide-react";
import type { LucideIcon } from "lucide-react";
import { useEffect, useMemo, useState } from "react";
import { displayModelName, getPromptVersions, type PromptVersion } from "../api/client";
import { EmptyState, SectionHeader, SkeletonLoader, StatusBadge } from "../components";

const USE_CASE_LABELS: Record<string, string> = {
  quote_to_cash_revenue_command_center: "Quote-to-Cash Agentic Flow",
  banking_payment_risk: "Banking Payment Risk",
};

type PromptMetrics = {
  quality: number;
  cost: number;
  latency: number;
};

type PromptViewModel = PromptVersion & {
  metrics: PromptMetrics;
  role: string;
  owner: string;
  risk: string;
};

export function PromptVersioning() {
  const [loading, setLoading] = useState(true);
  const [versions, setVersions] = useState<PromptVersion[]>([]);

  useEffect(() => {
    function load() {
      getPromptVersions("quote_to_cash_revenue_command_center")
        .then(setVersions)
        .catch(() => setVersions([]))
        .finally(() => setLoading(false));
    }
    load();
    window.addEventListener("llmobs:data-updated", load);
    return () => window.removeEventListener("llmobs:data-updated", load);
  }, []);

  const promptViews = useMemo(
    () =>
      versions
        .map((version) => ({
          ...version,
          metrics: metricsFor(version),
          role: roleFor(version.version),
          owner: ownerFor(version.version),
          risk: riskFor(version),
        }))
        .sort(sortPromptVersions),
    [versions],
  );

  if (loading) {
    return <SkeletonLoader rows={8} />;
  }

  if (!promptViews.length) {
    return (
      <EmptyState
        icon={ScrollText}
        title="Prompt registry is empty"
        sub="Run the Quote-to-Cash Agentic Flow to register governed prompt versions."
        action="Refresh"
        onAction={() => window.location.reload()}
      />
    );
  }

  const champion = promptViews.find((version) => version.version === "v2.2") ?? promptViews.find((version) => version.status === "active") ?? promptViews[0];
  const challenger = promptViews.find((version) => version.version === "v2.1") ?? promptViews.find((version) => version.status === "testing") ?? champion;
  const baseline = promptViews.find((version) => version.version === "v1.0") ?? promptViews[promptViews.length - 1];
  const agentPrompts = promptViews.filter((version) => version.version.includes(".") && !["v1.0", "v2.1", "v2.2"].includes(version.version));
  const qualityLift = champion.metrics.quality - baseline.metrics.quality;
  const latencyChange = champion.metrics.latency - baseline.metrics.latency;
  const costChange = champion.metrics.cost - baseline.metrics.cost;

  return (
    <>
      <SectionHeader
        eyebrow="Prompt lifecycle"
        title="Prompt governance and versions"
        sub="Govern the Quote-to-Cash agent prompts as production assets: champion, challenger, baseline, and agent-specific prompt contracts."
      />

      <section className="prompt-command-strip">
        <PromptCommandCard
          icon={ShieldCheck}
          label="Champion"
          value={champion.version}
          detail={champion.role}
          status={champion.status}
        />
        <PromptCommandCard
          icon={FlaskConical}
          label="Challenger"
          value={challenger.version}
          detail={challenger.role}
          status={challenger.status}
        />
        <PromptCommandCard
          icon={Archive}
          label="Baseline"
          value={baseline.version}
          detail={baseline.role}
          status={baseline.status}
        />
        <PromptCommandCard
          icon={ScrollText}
          label="Agent Prompts"
          value={agentPrompts.length.toString()}
          detail="context, policy, margin, approval, negotiation"
          status="active"
        />
      </section>

      <div className="prompt-board-grid">
        <section className="prompt-panel prompt-panel-primary">
          <div className="prompt-panel-head">
            <div>
              <p className="detail-kicker">Production decision</p>
              <h3>Promote guarded v2.2 prompts for governed quote runs</h3>
              <p>
                The active prompt family adds approval controls and agent-level prompt contracts
                while keeping Quote-to-Cash telemetry comparable across quality, cost, and latency.
              </p>
            </div>
            <GitCompare size={22} aria-hidden="true" />
          </div>
          <div className="prompt-impact-grid">
            <PromptImpact label="Quality lift" value={`+${(qualityLift * 100).toFixed(1)} pts`} positive={qualityLift >= 0} />
            <PromptImpact label="Cost delta" value={money6(costChange)} positive={costChange <= 0} />
            <PromptImpact label="Latency delta" value={`${latencyChange > 0 ? "+" : ""}${latencyChange}ms`} positive={latencyChange <= 0} />
          </div>
          <div className="prompt-comparison-list">
            {[baseline, challenger, champion].map((version) => (
              <PromptComparisonRow key={version.version} version={version} />
            ))}
          </div>
        </section>

        <section className="prompt-panel">
          <div className="prompt-panel-head prompt-panel-head-compact">
            <div>
              <p className="detail-kicker">Control evidence</p>
              <h3>Prompt lifecycle policy</h3>
            </div>
            <StatusBadge status="stable" />
          </div>
          <div className="prompt-policy-stack">
            <PromptPolicyItem
              icon={ShieldCheck}
              title="Active prompts require traceable agent evidence"
              copy="Every v2.2 agent prompt writes model, prompt version, tokens, latency, quality, and evidence into LLMCallRecord."
            />
            <PromptPolicyItem
              icon={FlaskConical}
              title="Testing prompts stay available for comparison"
              copy="v2.1 remains visible as the challenger so quality and cost changes are explainable."
            />
            <PromptPolicyItem
              icon={Archive}
              title="Deprecated prompts remain auditable"
              copy="v1.0 is retained as a baseline, not hidden, so the team can defend why the guarded flow replaced it."
            />
          </div>
        </section>
      </div>

      <section className="prompt-panel">
        <div className="prompt-panel-head prompt-panel-head-compact">
          <div>
            <p className="detail-kicker">Agent prompt registry</p>
            <h3>Quote-to-Cash prompt contracts</h3>
          </div>
          <span className="prompt-count">{promptViews.length} versions</span>
        </div>
        <div className="prompt-registry">
          {promptViews.map((version) => (
            <article className="prompt-registry-row" key={version.version_id}>
              <div>
                <strong>{version.version}</strong>
                <span>{version.role}</span>
              </div>
              <StatusBadge status={version.status} />
              <span>{version.owner}</span>
              <span>{formatUseCase(version.use_case)}</span>
              <span>{displayModelName(version.model)}</span>
              <span>{version.risk}</span>
            </article>
          ))}
        </div>
      </section>
    </>
  );
}

function PromptCommandCard({
  icon: Icon,
  label,
  value,
  detail,
  status,
}: {
  icon: LucideIcon;
  label: string;
  value: string;
  detail: string;
  status: string;
}) {
  return (
    <article className="prompt-command-card">
      <Icon size={18} aria-hidden="true" />
      <span>{label}</span>
      <strong>{value}</strong>
      <p>{detail}</p>
      <StatusBadge status={status} />
    </article>
  );
}

function PromptImpact({ label, value, positive }: { label: string; value: string; positive: boolean }) {
  return (
    <div className={`prompt-impact ${positive ? "prompt-impact-positive" : "prompt-impact-watch"}`}>
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  );
}

function PromptComparisonRow({ version }: { version: PromptViewModel }) {
  return (
    <article className="prompt-comparison-row">
      <div>
        <strong>{version.version}</strong>
        <span>{version.role}</span>
      </div>
      <MetricBar icon={Gauge} label="Quality" value={version.metrics.quality} max={1} display={version.metrics.quality.toFixed(2)} />
      <MetricBar icon={DollarSign} label="Cost" value={version.metrics.cost} max={0.0022} display={money6(version.metrics.cost)} invert />
      <MetricBar icon={Clock3} label="Latency" value={version.metrics.latency} max={1200} display={`${version.metrics.latency}ms`} invert />
    </article>
  );
}

function MetricBar({
  icon: Icon,
  label,
  value,
  max,
  display,
  invert = false,
}: {
  icon: LucideIcon;
  label: string;
  value: number;
  max: number;
  display: string;
  invert?: boolean;
}) {
  const pct = Math.max(4, Math.min(100, (value / max) * 100));
  return (
    <div className="prompt-metric-bar">
      <span>
        <Icon size={13} aria-hidden="true" />
        {label}
      </span>
      <div className="prompt-bar-track">
        <div
          className={invert ? "prompt-bar-fill prompt-bar-fill-amber" : "prompt-bar-fill"}
          style={{ width: `${pct}%` }}
        />
      </div>
      <strong>{display}</strong>
    </div>
  );
}

function PromptPolicyItem({
  icon: Icon,
  title,
  copy,
}: {
  icon: LucideIcon;
  title: string;
  copy: string;
}) {
  return (
    <article className="prompt-policy-item">
      <Icon size={18} aria-hidden="true" />
      <div>
        <strong>{title}</strong>
        <p>{copy}</p>
      </div>
    </article>
  );
}

function metricsFor(version: PromptVersion): PromptMetrics {
  const fallback = fallbackMetrics(version.version);
  return {
    quality: Number(version.avg_quality_score ?? fallback.quality),
    cost: Number(version.avg_cost_usd ?? fallback.cost),
    latency: Number(version.avg_latency_ms ?? fallback.latency),
  };
}

function fallbackMetrics(version: string): PromptMetrics {
  if (version.startsWith("v2.2")) {
    return { quality: 0.87, cost: 0.00162, latency: 950 };
  }
  if (version.startsWith("v2.1")) {
    return { quality: 0.84, cost: 0.0017, latency: 980 };
  }
  return { quality: 0.78, cost: 0.002, latency: 1100 };
}

function roleFor(version: string): string {
  const role = version.split(".").slice(2).join(".");
  if (!role) {
    if (version === "v2.2") return "approval-policy guarded revenue agent";
    if (version === "v2.1") return "margin-aware revenue agent";
    return "generic quote assistant";
  }
  return role.replace(/_/g, " ");
}

function ownerFor(version: string): string {
  if (version.includes("approval")) return "approval routing agent";
  if (version.includes("margin")) return "margin risk agent";
  if (version.includes("discount")) return "discount policy agent";
  if (version.includes("negotiation")) return "negotiation guidance agent";
  if (version.includes("context")) return "context assembler agent";
  return "quote orchestration";
}

function riskFor(version: PromptViewModel | PromptVersion): string {
  if (version.status === "deprecated") return "retired";
  if (version.status === "testing") return "compare";
  return "production";
}

function sortPromptVersions(a: PromptViewModel, b: PromptViewModel): number {
  const statusRank: Record<string, number> = { active: 0, testing: 1, deprecated: 2 };
  const statusDelta = (statusRank[a.status] ?? 3) - (statusRank[b.status] ?? 3);
  if (statusDelta !== 0) return statusDelta;
  return a.version.localeCompare(b.version, undefined, { numeric: true });
}

function money6(value: number): string {
  const sign = value > 0 ? "+" : value < 0 ? "-" : "";
  return `${sign}$${Math.abs(value).toFixed(6)}`;
}

function formatUseCase(value: string): string {
  return USE_CASE_LABELS[value] ?? value.replace(/_/g, " ");
}

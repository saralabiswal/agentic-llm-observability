/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import { BarChart3, DollarSign, Gauge, LineChart as LineChartIcon, PiggyBank, RefreshCw } from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  CLOUD_PROVIDER_OPTIONS,
  displayModelName,
  getCostSummary,
  getCostTimeline,
  getOptimizationRecommendations,
  type CostSummary,
  type CostTimelinePoint,
  type CloudProviderOption,
  type OptimizationRecommendation,
} from "../api/client";
import { AlertBanner, ChartCard, DataTable, EmptyState, MetricCard, SectionHeader, SkeletonLoader, StatusBadge } from "../components";
import { AreaGradient, chartConfig } from "./chartConfig";

type Row = Record<string, string | JSX.Element>;
type CostDashboardProps = {
  selectedProviderRateCard: CloudProviderOption["value"];
  selectedLocalModel: string;
};
const REVENUE_USE_CASE = "quote_to_cash_revenue_command_center";
const USE_CASES = [{ value: "quote_to_cash_revenue_command_center", label: "Quote-to-Cash Agentic Flow" }];
const PROJECTION_VOLUMES = [
  { label: "Observed", value: 0 },
  { label: "10k quote runs/mo", value: 10_000 },
  { label: "50k quote runs/mo", value: 50_000 },
  { label: "100k quote runs/mo", value: 100_000 },
];

const USE_CASE_LABELS = Object.fromEntries(USE_CASES.map((item) => [item.value, item.label]));
const LOCAL_TOKEN_RATES_PER_MILLION: Record<string, number> = {
  "llama3.2": 0.2,
  "mistral": 0.18,
  "qwen2.5:7b": 0.24,
};
const QUOTE_FLOW_TOKEN_MIX = { input: 0.72, output: 0.28 };

export function CostDashboard({ selectedProviderRateCard, selectedLocalModel }: CostDashboardProps) {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [useCase] = useState(REVENUE_USE_CASE);
  const [summary, setSummary] = useState<CostSummary | null>(null);
  const [timeline, setTimeline] = useState<CostTimelinePoint[]>([]);
  const [recommendations, setRecommendations] = useState<OptimizationRecommendation[]>([]);
  const [projectionVolume, setProjectionVolume] = useState(10_000);
  const [lastUpdated, setLastUpdated] = useState<Date | null>(null);

  const loadData = useCallback(() => {
    setRefreshing(true);
    Promise.all([
      getCostSummary(useCase),
      getCostTimeline(useCase),
      getOptimizationRecommendations(useCase, selectedLocalModel),
    ])
      .then(([nextSummary, nextTimeline, nextRecommendations]) => {
        setSummary(nextSummary);
        setTimeline(nextTimeline);
        setRecommendations(nextRecommendations);
        setLastUpdated(new Date());
      })
      .catch(() => {
        setSummary(null);
        setTimeline([]);
        setRecommendations([]);
      })
      .finally(() => {
        setLoading(false);
        setRefreshing(false);
      });
  }, [selectedLocalModel, useCase]);

  useEffect(() => {
    loadData();
    const interval = window.setInterval(loadData, 15_000);
    const listener = () => {
      loadData();
    };
    window.addEventListener("llmobs:data-updated", listener);
    return () => {
      window.clearInterval(interval);
      window.removeEventListener("llmobs:data-updated", listener);
    };
  }, [loadData]);

  const settingsImpact = useMemo(() => {
    return recommendations.find((item) => item.recommended_model === selectedLocalModel) ?? null;
  }, [recommendations, selectedLocalModel]);

  const optimizerRecommendation = useMemo(() => {
    const selectedModel = settingsImpact?.recommended_model;
    return recommendations.find((item) => (
      item.recommended_model !== selectedModel
      && Number(item.monthly_savings_usd) > 0
      && item.quality_delta_pct >= -5
    )) ?? null;
  }, [recommendations, settingsImpact]);

  const impactForProjection = settingsImpact ?? optimizerRecommendation;

  const projection = useMemo(() => {
    const observedCalls = summary?.total_calls ?? 0;
    const volume = projectionVolume || observedCalls;
    const multiplier = observedCalls > 0 ? volume / observedCalls : 0;
    const projectedSpend = Number(summary?.total_cost_usd ?? 0) * multiplier;
    const selectedSavings = impactForProjection
      ? Number(impactForProjection.monthly_savings_usd) * multiplier
      : 0;
    return {
      volume,
      multiplier,
      projectedSpend,
      selectedSavings,
      observedCalls,
    };
  }, [impactForProjection, projectionVolume, summary]);

  const providerRateCard = CLOUD_PROVIDER_OPTIONS.find((item) => item.value === selectedProviderRateCard)
    ?? CLOUD_PROVIDER_OPTIONS[0];
  const providerProjection = useMemo(() => {
    const ratePerMillion = LOCAL_TOKEN_RATES_PER_MILLION[selectedLocalModel] ?? LOCAL_TOKEN_RATES_PER_MILLION["llama3.2"];
    const localObservedCost = Number((settingsImpact ?? optimizerRecommendation)?.recommended_cost_usd ?? summary?.total_cost_usd ?? 0);
    const observedMillionTokens = ratePerMillion > 0 ? localObservedCost / ratePerMillion : 0;
    const inputMillionTokens = observedMillionTokens * QUOTE_FLOW_TOKEN_MIX.input;
    const outputMillionTokens = observedMillionTokens * QUOTE_FLOW_TOKEN_MIX.output;
    const observedProviderCost = (
      inputMillionTokens * providerRateCard.inputPerMillion
      + outputMillionTokens * providerRateCard.outputPerMillion
    );
    const projectedProviderCost = observedProviderCost * projection.multiplier;
    const projectedLocalCost = settingsImpact
      ? Number(settingsImpact.recommended_cost_usd) * projection.multiplier
      : 0;
    return {
      observedMillionTokens,
      projectedProviderCost,
      projectedLocalCost,
      deltaVsLocal: projectedProviderCost - projectedLocalCost,
    };
  }, [optimizerRecommendation, projection.multiplier, providerRateCard, selectedLocalModel, settingsImpact, summary]);

  if (loading) {
    return <SkeletonLoader rows={8} />;
  }

  if (!summary) {
    return <EmptyState icon={BarChart3} title="Cost data is not connected" sub="Start the API and seed data to view spend analytics." action="Refresh" onAction={() => window.location.reload()} />;
  }

  const selectedModelLabel = displayModelName(selectedLocalModel);
  const settingsImpactLabel = settingsImpact ? displayModelName(settingsImpact.recommended_model) : selectedModelLabel;
  const optimizerModelLabel = optimizerRecommendation ? displayModelName(optimizerRecommendation.recommended_model) : null;
  const selectedImpactLabel = projection.selectedSavings >= 0 ? "savings" : "added cost";
  const settingsProjectedCost = settingsImpact
    ? Number(settingsImpact.recommended_cost_usd) * projection.multiplier
    : projection.projectedSpend;
  const optimizerProjectedCost = optimizerRecommendation
    ? Number(optimizerRecommendation.recommended_cost_usd) * projection.multiplier
    : null;
  const costLensData = [
    { lens: "Observed baseline", cost: projection.projectedSpend },
    { lens: `Local ${selectedModelLabel}`, cost: settingsProjectedCost },
    { lens: providerRateCard.label, cost: providerProjection.projectedProviderCost },
    ...(optimizerRecommendation && optimizerModelLabel
      ? [{ lens: `Best ${optimizerModelLabel}`, cost: Number(optimizerRecommendation.recommended_cost_usd) * projection.multiplier }]
      : []),
  ];
  const tableRows: Row[] = [
    {
      use_case: formatUseCase(useCase),
      cost_lens: "Observed baseline",
      route: "Historical production telemetry",
      projected_cost: money2(projection.projectedSpend),
      compared_with: "Current telemetry",
      projected_difference: "$0.00",
      quality_signal: <StatusBadge status="baseline" />,
    },
    {
      use_case: formatUseCase(useCase),
      cost_lens: "Actual execution",
      route: selectedModelLabel,
      projected_cost: money2(settingsProjectedCost),
      compared_with: "Observed baseline",
      projected_difference: settingsImpact ? money2(Number(settingsImpact.monthly_savings_usd) * projection.multiplier) : "$0.00",
      quality_signal: settingsImpact
        ? <StatusBadge status={settingsImpact.quality_delta_pct < -5 ? "critical" : settingsImpact.quality_delta_pct < -2 ? "warning" : "healthy"} />
        : <StatusBadge status="active" />,
    },
    {
      use_case: formatUseCase(useCase),
      cost_lens: selectedProviderRateCard === "local" ? "Local rate card" : "Cloud planning",
      route: `${providerRateCard.label} - ${providerRateCard.model}`,
      projected_cost: money2(providerProjection.projectedProviderCost),
      compared_with: selectedProviderRateCard === "local" ? "Actual local execution" : "Actual local execution",
      projected_difference: money2(providerProjection.deltaVsLocal),
      quality_signal: <StatusBadge status={selectedProviderRateCard === "local" ? "active" : "planning"} />,
    },
    ...(optimizerRecommendation && optimizerModelLabel && optimizerProjectedCost !== null
      ? [{
        use_case: formatUseCase(useCase),
        cost_lens: "Optimizer candidate",
        route: optimizerModelLabel,
        projected_cost: money2(optimizerProjectedCost),
        compared_with: "Observed baseline",
        projected_difference: money2(Number(optimizerRecommendation.monthly_savings_usd) * projection.multiplier),
        quality_signal: <StatusBadge status={optimizerRecommendation.quality_delta_pct < -5 ? "critical" : optimizerRecommendation.quality_delta_pct < -2 ? "warning" : "healthy"} />,
      }]
      : []),
  ];

  return (
    <>
      <SectionHeader eyebrow="Token economics" title="Cost impact from the agent run" sub="Optimization evidence and routing impact for the selected business flow." />
      <div className="control-bar">
        <div className="flow-context-pill">
          <span>Business flow</span>
          <strong>Quote-to-Cash Agentic Flow</strong>
        </div>
        <label className="field-label">
          Production projection
          <select
            className="select-input"
            value={projectionVolume}
            onChange={(event) => setProjectionVolume(Number(event.target.value))}
          >
            {PROJECTION_VOLUMES.map((item) => (
              <option key={item.label} value={item.value}>
                {item.label}
              </option>
            ))}
          </select>
        </label>
        <button className="command-button" type="button" onClick={loadData}>
          <RefreshCw size={16} aria-hidden="true" />
          <span>{refreshing ? "Refreshing" : "Refresh"}</span>
        </button>
        <span className="live-chip">Updated {lastUpdated?.toLocaleTimeString() ?? "waiting"}</span>
      </div>
      <div className="metric-row">
        <MetricCard label="Observed Spend" value={`$${Number(summary.total_cost_usd).toFixed(6)}`} sub={`${projection.observedCalls.toLocaleString()} Quote-to-Cash Agentic Flow calls`} icon={DollarSign} />
        <MetricCard label="Avg Cost/Call" value={`$${Number(summary.avg_cost_per_call).toFixed(6)}`} sub="observed average" icon={Gauge} />
        <MetricCard label="Projected Spend" value={money2(projection.projectedSpend)} sub={`${projection.volume.toLocaleString()} quote runs/month`} icon={LineChartIcon} />
        <MetricCard label="Provider Rate Card" value={money2(providerProjection.projectedProviderCost)} sub={`${providerRateCard.label} - ${providerRateCard.model}`} icon={DollarSign} />
        <MetricCard
          label={settingsImpact ? "Settings Cost Change" : "Best Cost Change"}
          value={money2(projection.selectedSavings)}
          delta={impactForProjection ? `${impactForProjection.cost_savings_pct.toFixed(1)}%` : "0%"}
          deltaColor={projection.selectedSavings >= 0 ? "green" : "amber"}
          icon={PiggyBank}
        />
      </div>
      <div className="projection-note">
        <strong>Projection model:</strong> Agent execution uses {selectedModelLabel}. Pricing uses the selected provider rate card: {providerRateCard.label} {providerRateCard.model} at {providerRateCard.sourceLabel}. Historical telemetry is retained as the observed baseline and scaled to {projection.volume.toLocaleString()} quote runs/month.
      </div>
      <section className="cost-recommendation">
        <div>
          <p className="detail-kicker">Provider rate card</p>
          <h3>{providerRateCard.label}: {providerRateCard.model}</h3>
          <p>
            Applying the selected provider rate card to the estimated Quote-to-Cash token volume gives{" "}
            {money2(providerProjection.projectedProviderCost)} at {projection.volume.toLocaleString()} quote runs/month.
            {selectedProviderRateCard !== "local" ? " The standalone app still executes the task with the local LLM; this card is for cost planning only." : ""}
            {settingsImpact && selectedProviderRateCard !== "local" ? ` That is ${money2(Math.abs(providerProjection.deltaVsLocal))} ${providerProjection.deltaVsLocal >= 0 ? "above" : "below"} the selected local route.` : ""}
          </p>
        </div>
        <div className="cost-recommendation-metrics">
          <span>
            <strong>${providerRateCard.inputPerMillion.toFixed(2)}</strong>
            input / 1M
          </span>
          <span>
            <strong>${providerRateCard.outputPerMillion.toFixed(2)}</strong>
            output / 1M
          </span>
          <StatusBadge status="rate-card" />
        </div>
      </section>
      {settingsImpact ? (
        <section className="cost-recommendation">
          <div>
            <p className="detail-kicker">Settings runtime impact</p>
            <h3>
              Settings runtime: {settingsImpactLabel}
            </h3>
            <p>
              This is the cost and quality impact of the model selected in Settings, compared with
              the observed baseline. At {projection.volume.toLocaleString()} quote runs/month, it shows{" "}
              {money2(Math.abs(Number(settingsImpact.monthly_savings_usd) * projection.multiplier))} in{" "}
              {selectedImpactLabel} with {settingsImpact.quality_delta_pct.toFixed(1)}% expected quality delta.
            </p>
          </div>
          <div className="cost-recommendation-metrics">
            <span>
              <strong>{settingsImpact.cost_savings_pct.toFixed(1)}%</strong>
              {settingsImpact.cost_savings_pct >= 0 ? "savings" : "cost increase"}
            </span>
            <span>
              <strong>{money2(Number(settingsImpact.recommended_cost_usd) * projection.multiplier)}</strong>
              routed cost
            </span>
            <StatusBadge status={settingsImpact.quality_delta_pct < -2 ? "warning" : "healthy"} />
          </div>
        </section>
      ) : null}
      <section className="cost-recommendation">
        <div>
          <p className="detail-kicker">Optimizer recommendation</p>
          <h3>
            {optimizerRecommendation && optimizerModelLabel
              ? `Best candidate: ${optimizerModelLabel}`
              : "No better routing policy found"}
          </h3>
          <p>
            {optimizerRecommendation && optimizerModelLabel
              ? `The optimizer compares candidate routes against the observed baseline and chooses ${optimizerModelLabel} when it improves cost while staying inside the quality floor.`
              : "The selected runtime is currently the best available policy in the returned candidate set, so the control plane does not invent a separate recommendation."}
          </p>
        </div>
        {optimizerRecommendation ? (
          <div className="cost-recommendation-metrics">
            <span>
              <strong>{optimizerRecommendation.cost_savings_pct.toFixed(1)}%</strong>
              savings
            </span>
            <span>
              <strong>{money2(Number(optimizerRecommendation.recommended_cost_usd) * projection.multiplier)}</strong>
              routed cost
            </span>
            <StatusBadge status={optimizerRecommendation.quality_delta_pct < -2 ? "warning" : "healthy"} />
          </div>
        ) : (
          <div className="cost-recommendation-metrics">
            <span>
              <strong>Truthful</strong>
              no forced recommendation
            </span>
            <StatusBadge status="stable" />
          </div>
        )}
      </section>
      <div className="chart-row page-grid-two">
        <ChartCard title="Daily Spend Trend" sub="USD over 30 days">
          <ResponsiveContainer width="100%" height={260}>
            <AreaChart data={timeline}>
              <AreaGradient id="cost" color="var(--chart-1)" />
              <CartesianGrid {...chartConfig.cartesianGrid} />
              <XAxis dataKey="date" {...chartConfig.xAxis} />
              <YAxis {...chartConfig.yAxis} />
              <Tooltip {...chartConfig.tooltip} />
              <Area dataKey="total_cost" stroke="var(--chart-1)" fill="url(#cost)" />
            </AreaChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Settings Cost Lens" sub="Projected spend by selected execution and provider rate card">
          <ResponsiveContainer width="100%" height={260}>
            <BarChart data={costLensData}>
              <CartesianGrid {...chartConfig.cartesianGrid} />
              <XAxis dataKey="lens" {...chartConfig.xAxis} />
              <YAxis {...chartConfig.yAxis} />
              <Tooltip {...chartConfig.tooltip} />
              <Bar dataKey="cost" fill="var(--chart-2)" />
            </BarChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>
      <DataTable<Row>
        columns={[
          { key: "use_case", label: "Use Case" },
          { key: "cost_lens", label: "Cost Lens" },
          { key: "route", label: "Execution / Rate Card" },
          { key: "projected_cost", label: "Projected Cost" },
          { key: "compared_with", label: "Compared With" },
          { key: "projected_difference", label: "Projected Difference" },
          { key: "quality_signal", label: "Quality Signal" },
        ]}
        rows={tableRows}
      />
      {summary.budget_burn_rate_pct > 80 ? <AlertBanner type="warning" title="Budget threshold reached" message="Projected monthly spend is above the configured budget threshold." /> : null}
    </>
  );
}

function formatUseCase(value: string): string {
  return USE_CASE_LABELS[value] ?? value.replace(/_/g, " ");
}

function money2(value: number): string {
  const sign = value < 0 ? "-" : "";
  return `${sign}$${Math.abs(value).toLocaleString(undefined, { maximumFractionDigits: 2, minimumFractionDigits: 2 })}`;
}

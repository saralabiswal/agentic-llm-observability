/**
 * React application shell that connects navigation, settings, live telemetry, and page routing.
 *
 * Author: Sarala Biswal
 */
import {
  BadgeDollarSign,
  BrainCircuit,
  Clock3,
  Code2,
  Command,
  Info,
  GitBranch,
  Loader2,
  Network,
  RefreshCw,
  ScrollText,
  Settings as SettingsIcon,
} from "lucide-react";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  CLOUD_PROVIDER_OPTIONS,
  displayModelName,
  getAlerts,
  getCostSummary,
  getQualityScores,
  type AlertRecord,
  type CloudProviderOption,
  type CostSummary,
  type QualityScore,
} from "./api/client";
import { StatusBadge } from "./components";
import { About } from "./pages/About";
import { CostDashboard } from "./pages/CostDashboard";
import { Architecture } from "./pages/Architecture";
import { DeveloperCorner } from "./pages/DeveloperCorner";
import { DriftDetection } from "./pages/DriftDetection";
import { LatencyTracker } from "./pages/LatencyTracker";
import { PromptVersioning } from "./pages/PromptVersioning";
import { QualityMonitor } from "./pages/QualityMonitor";
import { RevenueCommandCenter } from "./pages/RevenueCommandCenter";
import { Settings } from "./pages/Settings";

const NAV_GROUPS = [
  {
    label: "Overview",
    items: [
      { label: "About", icon: Info, index: "00" },
    ],
  },
  {
    label: "Quote Flow",
    items: [
      { label: "Quote Agentic Flow", icon: Command, index: "01" },
    ],
  },
  {
    label: "LLMOps Controls",
    items: [
      { label: "Cost Impact", icon: BadgeDollarSign, index: "02" },
      { label: "Quality Evidence", icon: BrainCircuit, index: "03" },
      { label: "Latency SLOs", icon: Clock3, index: "04" },
      { label: "Prompt Governance", icon: ScrollText, index: "05" },
      { label: "Drift & Alerts", icon: GitBranch, index: "06" },
    ],
  },
  {
    label: "Reference",
    items: [
      { label: "Architecture", icon: Network, index: "07" },
    ],
  },
  {
    label: "Runtime",
    items: [
      { label: "Settings", icon: SettingsIcon, index: "08" },
      { label: "Developer Corner", icon: Code2, index: "09" },
    ],
  },
];
const NAV_ITEMS = NAV_GROUPS.flatMap((group) => group.items);
const REVENUE_USE_CASE = "quote_to_cash_revenue_command_center";
// Settings are persisted locally so the standalone app behaves like a real operator console.
const LOCAL_MODEL_STORAGE_KEY = "llmobs:selected-local-model";
const PROVIDER_RATE_CARD_STORAGE_KEY = "llmobs:selected-provider-rate-card";

type LiveStats = {
  summary?: CostSummary;
  alerts: AlertRecord[];
  qualityScores: QualityScore[];
  connected: boolean;
  lastUpdated?: Date;
};

export default function App() {
  const [activeIndex, setActiveIndex] = useState(0);
  const [stats, setStats] = useState<LiveStats>({ alerts: [], qualityScores: [], connected: false });
  const [refreshing, setRefreshing] = useState(false);
  const [eventCount, setEventCount] = useState(0);
  const [selectedLocalModel, setSelectedLocalModel] = useState(() => {
    const stored = window.localStorage.getItem(LOCAL_MODEL_STORAGE_KEY);
    if (stored === "qwen2.5") {
      window.localStorage.setItem(LOCAL_MODEL_STORAGE_KEY, "qwen2.5:7b");
      return "qwen2.5:7b";
    }
    return stored ?? "llama3.2";
  });
  const [selectedProviderRateCard, setSelectedProviderRateCard] = useState<CloudProviderOption["value"]>(() => {
    const stored = window.localStorage.getItem(PROVIDER_RATE_CARD_STORAGE_KEY);
    const match = CLOUD_PROVIDER_OPTIONS.find((item) => item.value === stored);
    if (match) {
      return match.value;
    }
    return "local";
  });
  const activeItem = NAV_ITEMS[activeIndex];

  const loadStats = useCallback(async () => {
    setRefreshing(true);
    try {
      // Pull the same live telemetry surfaces that the Quote-to-Cash flow writes after each run.
      const [summary, alerts, qualityScores] = await Promise.all([
        getCostSummary(REVENUE_USE_CASE),
        getAlerts(REVENUE_USE_CASE),
        getQualityScores(REVENUE_USE_CASE),
      ]);
      setStats({ summary, alerts, qualityScores, connected: true, lastUpdated: new Date() });
    } catch {
      setStats((current) => ({
        alerts: current.alerts,
        qualityScores: current.qualityScores,
        connected: false,
      }));
    } finally {
      setRefreshing(false);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    async function tick() {
      if (!cancelled) {
        await loadStats();
      }
    }

    tick();
    const interval = window.setInterval(tick, 15_000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [loadStats]);

  async function handleBusinessTelemetryUpdated() {
    setEventCount((count) => count + 1);
    await loadStats();
  }

  function handleSelectedLocalModelChange(model: string) {
    setSelectedLocalModel(model);
    window.localStorage.setItem(LOCAL_MODEL_STORAGE_KEY, model);
    window.dispatchEvent(new CustomEvent("llmobs:model-settings-updated"));
  }

  function handleSelectedProviderRateCardChange(provider: CloudProviderOption["value"]) {
    setSelectedProviderRateCard(provider);
    window.localStorage.setItem(PROVIDER_RATE_CARD_STORAGE_KEY, provider);
    window.dispatchEvent(new CustomEvent("llmobs:model-settings-updated"));
  }

  const qualityAverage = useMemo(() => {
    if (!stats.qualityScores.length) {
      return 0;
    }
    return (
      stats.qualityScores.reduce((sum, score) => sum + score.composite_score, 0) /
      stats.qualityScores.length
    );
  }, [stats.qualityScores]);

  const liveValues = useMemo(
    () => ({
      calls: stats.summary?.total_calls.toLocaleString() ?? "0",
      spend: `$${Number(stats.summary?.total_cost_usd ?? 0).toFixed(6)}`,
      quality: stats.connected ? qualityAverage.toFixed(2) : "0.00",
      alerts: stats.alerts.length.toString(),
      updated: stats.lastUpdated?.toLocaleTimeString() ?? "waiting",
    }),
    [qualityAverage, stats],
  );
  const runtimeLabel = useMemo(() => displayModelName(selectedLocalModel), [selectedLocalModel]);

  return (
    <div className="app-shell">
      <aside className="side-nav">
        <div className="side-author" aria-label="Application author">
          <span>Author</span>
          <strong>Sarala Biswal</strong>
        </div>
        <nav className="nav-list" aria-label="Primary">
          {NAV_GROUPS.map((group) => (
            <div className="nav-cluster" key={group.label}>
              <p className="nav-cluster-label">{group.label}</p>
              {group.items.map((item) => {
                const Icon = item.icon;
                const index = NAV_ITEMS.findIndex((navItem) => navItem.label === item.label);
                return (
                  <button
                    className={`nav-item ${index === activeIndex ? "nav-item-active" : ""}`}
                    key={item.label}
                    type="button"
                    onClick={() => setActiveIndex(index)}
                  >
                    <Icon size={17} aria-hidden="true" />
                    <span className="nav-index">{item.index}</span>
                    <span className="nav-text">{item.label}</span>
                  </button>
                );
              })}
            </div>
          ))}

          <div className="sidebar-stats" aria-label="Quote flow health">
            <div className="sidebar-stats-head">
              <div>
                <p className="stats-label">Flow Health</p>
                <span>Quote-to-Cash live telemetry</span>
              </div>
              <StatusBadge status={stats.alerts.length > 0 ? "watch" : "stable"} />
            </div>
            <div className="stat-grid">
              <div className="stat-tile">
                <span>Calls</span>
                <strong>{liveValues.calls}</strong>
              </div>
              <div className="stat-tile">
                <span>Spend</span>
                <strong>{liveValues.spend}</strong>
              </div>
              <div className="stat-tile">
                <span>Quality</span>
                <strong>{liveValues.quality}</strong>
              </div>
              <div className="stat-tile">
                <span>Alerts</span>
                <strong>{liveValues.alerts}</strong>
              </div>
            </div>
            <div className="stat-session-row">
              <span>Session runs</span>
              <strong>{eventCount}</strong>
            </div>
          </div>
        </nav>
      </aside>

      <main className="content-shell">
        <header className="topbar">
          <div className="topbar-context">
            <div className="workspace-title">Quote-to-Cash LLMOps Control Plane</div>
            <div className="topbar-meta">
              <span>Workspace: Quote-to-Cash Agentic Flow</span>
              <span>{activeItem.index} · {activeItem.label}</span>
              <span>Updated {liveValues.updated}</span>
            </div>
          </div>
          <div className="topbar-badges">
            <StatusBadge status={stats.connected ? "healthy" : "unknown"} />
            <StatusBadge status={runtimeLabel} />
            <StatusBadge status={stats.alerts.length > 0 ? "warning" : "stable"} />
            <button
              className="icon-button"
              type="button"
              onClick={loadStats}
              title="Refresh dashboard data"
            >
              {refreshing ? <Loader2 size={16} aria-hidden="true" /> : <RefreshCw size={16} aria-hidden="true" />}
            </button>
          </div>
        </header>

        <section className="page-content">
          {activeIndex === 0 ? (
            <About />
          ) : activeIndex === 1 ? (
            <RevenueCommandCenter
              selectedLocalModel={selectedLocalModel}
              onOpenDashboard={setActiveIndex}
              onTelemetryUpdated={handleBusinessTelemetryUpdated}
            />
          ) : activeIndex === 2 ? (
            <CostDashboard
              selectedProviderRateCard={selectedProviderRateCard}
              selectedLocalModel={selectedLocalModel}
            />
          ) : activeIndex === 3 ? (
            <QualityMonitor />
          ) : activeIndex === 4 ? (
            <LatencyTracker />
          ) : activeIndex === 5 ? (
            <PromptVersioning />
          ) : activeIndex === 6 ? (
            <DriftDetection />
          ) : activeIndex === 7 ? (
            <Architecture />
          ) : activeIndex === 8 ? (
            <Settings
              selectedLocalModel={selectedLocalModel}
              selectedProviderRateCard={selectedProviderRateCard}
              onSelectedProviderRateCardChange={handleSelectedProviderRateCardChange}
              onSelectedLocalModelChange={handleSelectedLocalModelChange}
            />
          ) : activeIndex === 9 ? (
            <DeveloperCorner />
          ) : null}
        </section>
      </main>
    </div>
  );
}

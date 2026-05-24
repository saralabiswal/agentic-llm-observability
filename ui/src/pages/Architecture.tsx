/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import {
  ArrowRight,
  BadgeCheck,
  BarChart3,
  BrainCircuit,
  Braces,
  Clock3,
  Cpu,
  Database,
  FileText,
  Gauge,
  GitBranch,
  Layers3,
  Network,
  Route,
  Server,
  ShieldCheck,
  WalletCards,
} from "lucide-react";
import { useState } from "react";
import { ChartCard, MetricCard, SectionHeader } from "../components";

const runtimeStages = [
  {
    icon: BrainCircuit,
    label: "Business workload",
    title: "Quote-to-Cash agents",
    detail: "A reviewer runs a governed renewal quote flow with five local LLM calls.",
    evidence: "Quote-to-Cash Agentic Flow",
  },
  {
    icon: FileText,
    label: "Telemetry contract",
    title: "LLMCallRecord",
    detail: "Each prompt call emits tokens, model, provider, latency, quality, and evidence.",
    evidence: "Prompt-level records",
  },
  {
    icon: Server,
    label: "Collection layer",
    title: "FastAPI collector",
    detail: "The API validates records, persists them, and triggers quality and drift scoring.",
    evidence: "Ingest-compatible path",
  },
  {
    icon: Database,
    label: "Operational store",
    title: "SQLite evidence store",
    detail: "Calls, prompt versions, quality rows, drift rows, and alerts share one query surface.",
    evidence: "SQLAlchemy async",
  },
  {
    icon: Gauge,
    label: "Observability UI",
    title: "Cost and quality console",
    detail: "Dashboards show production-style cost, quality, latency, prompt, and drift signals.",
    evidence: "Live matrix tabs",
  },
];

const processors = [
  {
    icon: WalletCards,
    title: "Token Economics",
    detail: "Converts input and output tokens into provider/model cost and projection views.",
  },
  {
    icon: ShieldCheck,
    title: "Quality Gates",
    detail: "Records faithfulness, relevance, coherence, hallucination flags, and pass/fail status.",
  },
  {
    icon: Clock3,
    title: "Latency SLOs",
    detail: "Builds percentile views and flags workflow latency pressure across local model calls.",
  },
  {
    icon: GitBranch,
    title: "Drift and Alerts",
    detail: "Tracks semantic drift and raises alert history against configured thresholds.",
  },
];

const agentFlow = [
  "Opportunity Context",
  "Discount Policy",
  "Margin Risk",
  "Approval Routing",
  "Negotiation Guidance",
];

const contractRows = [
  ["Identity", "call_id, use_case, prompt_version", "Traceability and prompt governance"],
  ["Model runtime", "provider, model, rate card", "Local execution with provider cost planning"],
  ["Economics", "input_tokens, output_tokens, cost_usd", "Spend attribution and projection"],
  ["Reliability", "latency_ms, quality_score, quality_gate_passed", "SLO and release readiness"],
  ["Grounding", "response_text, context_text", "Evidence-backed quality and drift checks"],
];

const technicalLanes = [
  {
    title: "Experience Layer",
    nodes: [
      "About and use-case story",
      "Quote-to-Cash Agentic Flow",
      "Observability matrix tabs",
      "Architecture reference",
    ],
  },
  {
    title: "API and Orchestration",
    nodes: [
      "FastAPI routers",
      "RevenueCommandCenterService",
      "Agent chain coordinator",
      "Alert threshold checks",
    ],
  },
  {
    title: "Local LLM Runtime",
    nodes: [
      "Ollama local model from Settings",
      "Five prompt calls",
      "Prompt versions v2.2.*",
      "Mock and OpenAI fallback modes",
    ],
  },
  {
    title: "Telemetry Processing",
    nodes: [
      "TokenTracker",
      "CostCalculator",
      "QualityScoreRow",
      "DriftScoreRow",
    ],
  },
  {
    title: "Persistence and Evidence",
    nodes: [
      "llm_calls",
      "prompt_versions",
      "quality_scores",
      "drift_scores",
      "alert_history",
    ],
  },
];

type ArchitectureTab = "diagram" | "technical" | "runtime";

const architectureTabs: Array<{ key: ArchitectureTab; label: string; sub: string }> = [
  { key: "diagram", label: "Diagram", sub: "One-picture system map" },
  { key: "technical", label: "Technical Architecture", sub: "Implementation layers" },
  { key: "runtime", label: "Runtime", sub: "Flow, records, processors" },
];

export function Architecture() {
  const [activeTab, setActiveTab] = useState<ArchitectureTab>("diagram");

  return (
    <>
      <SectionHeader
        eyebrow="Reference Architecture"
        title="How observability plugs in"
        sub="A production-style view of the local LLM workload, telemetry contract, scoring pipeline, and dashboard surfaces."
      />

      <div className="architecture-tabs" role="tablist" aria-label="Architecture views">
        {architectureTabs.map((tab) => (
          <button
            aria-selected={activeTab === tab.key}
            className={`architecture-tab ${activeTab === tab.key ? "architecture-tab-active" : ""}`}
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            role="tab"
            type="button"
          >
            <strong>{tab.label}</strong>
            <span>{tab.sub}</span>
          </button>
        ))}
      </div>

      {activeTab === "diagram" ? <DiagramTab /> : null}
      {activeTab === "technical" ? <TechnicalArchitectureTab /> : null}
      {activeTab === "runtime" ? <RuntimeTab /> : null}
    </>
  );
}

function DiagramTab() {
  return (
    <>
      <div className="architecture-hero">
        <div className="architecture-hero-copy">
          <span className="architecture-kicker">One picture view</span>
          <h3>Quote-to-Cash is the workload. Quote-to-Cash LLMOps is the control plane.</h3>
          <p>
            One reviewer action fans out through five local LLM agent calls, records every
            prompt, stores the evidence, and feeds the cost, quality, latency, prompt, and
            drift views.
          </p>
        </div>
        <div className="architecture-signal-grid">
          <div>
            <span>Runtime model path</span>
            <strong>Settings-selected Ollama model</strong>
          </div>
          <div>
            <span>Workflow calls</span>
            <strong>5 agents</strong>
          </div>
          <div>
            <span>Telemetry grain</span>
            <strong>Per prompt</strong>
          </div>
          <div>
            <span>Control plane</span>
            <strong>Control matrix</strong>
          </div>
        </div>
      </div>

      <ChartCard title="End-to-End System Diagram" sub="The complete app flow in one view">
        <div className="architecture-picture" aria-label="End-to-end technical architecture diagram">
          <section className="picture-stage picture-stage-actor">
            <div className="picture-stage-title">Business actor</div>
            <div className="picture-node picture-node-primary picture-node-center">
              <Route size={20} aria-hidden="true" />
              <strong>Reviewer</strong>
              <span>Runs quote analysis</span>
            </div>
          </section>

          <ArrowRight className="picture-connector" size={22} aria-hidden="true" />

          <section className="picture-stage picture-stage-workload">
            <div className="picture-stage-title">Quote-to-Cash workload</div>
            <div className="picture-node">
              <BrainCircuit size={18} aria-hidden="true" />
              <strong>Quote-to-Cash Agentic Flow</strong>
              <span>Orchestrates opportunity, policy, margin, approval, and negotiation logic</span>
            </div>
            <div className="picture-agent-grid">
              {agentFlow.map((agent, index) => (
                <div className="picture-agent" key={agent}>
                  <span>{String(index + 1).padStart(2, "0")}</span>
                  <strong>{agent}</strong>
                </div>
              ))}
            </div>
          </section>

          <ArrowRight className="picture-connector" size={22} aria-hidden="true" />

          <section className="picture-stage picture-stage-runtime">
            <div className="picture-stage-title">Local LLM runtime</div>
            <div className="picture-node picture-node-accent">
              <Cpu size={18} aria-hidden="true" />
              <strong>Ollama local model</strong>
              <span>Five local prompt calls</span>
            </div>
            <div className="picture-node">
              <FileText size={18} aria-hidden="true" />
              <strong>LLMCallRecord</strong>
              <span>Tokens, latency, model, quality, evidence</span>
            </div>
          </section>

          <ArrowRight className="picture-connector" size={22} aria-hidden="true" />

          <section className="picture-stage picture-stage-control">
            <div className="picture-stage-title">LLMOps Control Plane</div>
            <div className="picture-control-grid">
              <div><WalletCards size={16} aria-hidden="true" />Cost</div>
              <div><ShieldCheck size={16} aria-hidden="true" />Quality</div>
              <div><Clock3 size={16} aria-hidden="true" />Latency</div>
              <div><GitBranch size={16} aria-hidden="true" />Drift</div>
              <div><FileText size={16} aria-hidden="true" />Prompts</div>
              <div><BarChart3 size={16} aria-hidden="true" />Dashboards</div>
            </div>
            <div className="picture-node">
              <Database size={18} aria-hidden="true" />
              <strong>SQLite evidence store</strong>
              <span>Calls, scores, versions, drift, alerts</span>
            </div>
          </section>
        </div>
      </ChartCard>
    </>
  );
}

function TechnicalArchitectureTab() {
  return (
    <ChartCard
      title="Technical Architecture Diagram"
      sub="The implementation map behind the standalone local LLM observability app"
    >
      <div className="technical-architecture">
        <div className="technical-lanes">
          {technicalLanes.map((lane, laneIndex) => (
            <section className="technical-lane" key={lane.title}>
              <div className="technical-lane-head">
                <span>{String(laneIndex + 1).padStart(2, "0")}</span>
                <strong>{lane.title}</strong>
              </div>
              <div className="technical-node-list">
                {lane.nodes.map((node) => (
                  <div className="technical-node" key={node}>
                    {node}
                  </div>
                ))}
              </div>
            </section>
          ))}
        </div>

        <div className="technical-crosscutting">
          <div>
            <Cpu size={18} aria-hidden="true" />
            <strong>Local-first execution</strong>
            <span>Ollama is the default model path for quote runs.</span>
          </div>
          <div>
            <Braces size={18} aria-hidden="true" />
            <strong>Structured contracts</strong>
            <span>Pydantic models keep business output and telemetry typed.</span>
          </div>
          <div>
            <Network size={18} aria-hidden="true" />
            <strong>Per-call observability</strong>
            <span>Every agent prompt becomes an auditable LLM call record.</span>
          </div>
        </div>
      </div>
    </ChartCard>
  );
}

function RuntimeTab() {
  return (
    <>
      <ChartCard title="Runtime Flow" sub="Business workflow to governed observability evidence">
        <div className="architecture-flow" aria-label="Runtime architecture flow">
          {runtimeStages.map((stage, index) => {
            const Icon = stage.icon;
            return (
              <div className="architecture-flow-item" key={stage.title}>
                <div className="architecture-stage">
                  <div className="architecture-stage-head">
                    <Icon size={18} aria-hidden="true" />
                    <span>{stage.label}</span>
                  </div>
                  <strong>{stage.title}</strong>
                  <p>{stage.detail}</p>
                  <em>{stage.evidence}</em>
                </div>
                {index < runtimeStages.length - 1 ? (
                  <ArrowRight className="architecture-arrow" size={20} aria-hidden="true" />
                ) : null}
              </div>
            );
          })}
        </div>
      </ChartCard>

      <div className="architecture-two-column">
        <ChartCard title="Quote-to-Cash Agent Chain" sub="The workload that generates the telemetry">
          <div className="architecture-agent-chain">
            {agentFlow.map((agent, index) => (
              <div className="architecture-agent-row" key={agent}>
                <span>{String(index + 1).padStart(2, "0")}</span>
                <strong>{agent}</strong>
                <p>{index === 0 ? "Loads account, opportunity, risk, and evidence." : "Runs its own local LLM prompt and telemetry record."}</p>
              </div>
            ))}
          </div>
        </ChartCard>

        <ChartCard title="Observability Processors" sub="How raw LLM calls become operational signals">
          <div className="architecture-processor-list">
            {processors.map((processor) => {
              const Icon = processor.icon;
              return (
                <div className="architecture-processor-row" key={processor.title}>
                  <Icon size={18} aria-hidden="true" />
                  <div>
                    <strong>{processor.title}</strong>
                    <p>{processor.detail}</p>
                  </div>
                </div>
              );
            })}
          </div>
        </ChartCard>
      </div>

      <ChartCard title="Telemetry Contract" sub="Fields that make the dashboards auditable">
        <div className="architecture-contract">
          {contractRows.map(([area, fields, outcome]) => (
            <div className="architecture-contract-row" key={area}>
              <strong>{area}</strong>
              <code>{fields}</code>
              <span>{outcome}</span>
            </div>
          ))}
        </div>
      </ChartCard>

      <div className="placeholder-grid">
        <MetricCard label="Runtime" value="Local LLM" sub="Ollama-first, mock fallback" icon={Network} />
        <MetricCard label="Governance" value="Versioned" sub="Prompt-level lineage" icon={BadgeCheck} />
        <MetricCard label="Storage" value="Auditable" sub="Calls, scores, drift, alerts" icon={Layers3} />
        <MetricCard label="Workflow" value="Agentic" sub="Five calls per quote run" icon={Route} />
      </div>
    </>
  );
}

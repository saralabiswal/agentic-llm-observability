/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import {
  ArrowRight,
  BadgeDollarSign,
  BrainCircuit,
  Clock3,
  Database,
  FileText,
  Gauge,
  Route,
  ShieldCheck,
} from "lucide-react";
import { SectionHeader } from "../components";

const operatingControls = [
  { label: "Cost", detail: "Token economics and model spend", icon: BadgeDollarSign },
  { label: "Quality", detail: "Grounding, gates, hallucination checks", icon: BrainCircuit },
  { label: "Latency", detail: "SLO view across multi-call agent runs", icon: Clock3 },
  { label: "Governance", detail: "Prompt versions, drift, and alerts", icon: ShieldCheck },
];

const flowSteps = [
  { label: "Run agentic flow", icon: Route },
  { label: "Persist telemetry", icon: Database },
  { label: "Score evidence", icon: FileText },
  { label: "Optimize controls", icon: Gauge },
];

const solutionSteps = [
  {
    label: "Capture every prompt",
    detail: "Each agent call records model, tokens, latency, cost, prompt version, and evidence.",
  },
  {
    label: "Evaluate business quality",
    detail: "Grounding, quality gates, hallucination checks, and drift signals are tracked per run.",
  },
  {
    label: "Optimize production routing",
    detail: "Cost and quality evidence guide model routing decisions before scale-up.",
  },
];

export function About() {
  return (
    <>
      <SectionHeader
        eyebrow="Production LLMOps objective"
        title="Manage agentic LLM cost and quality in production"
        sub="A Quote-to-Cash agentic workflow generates real LLM telemetry so production teams can manage cost, quality, latency, prompt governance, drift, and alerts."
      />

      <section className="about-briefing about-flow-card">
        <div className="about-briefing-main">
          <p className="detail-kicker">Business problem</p>
          <h3>Agentic quoting is valuable, but it cannot scale without operational proof.</h3>
          <p>
            The app uses a realistic Quote-to-Cash flow to show what leaders need before putting
            LLM agents into production: cost attribution, grounded quality, latency visibility,
            prompt lineage, drift monitoring, and alerting.
          </p>
        </div>
        <aside className="about-briefing-panel">
          <span>Primary use case</span>
          <strong>Quote-to-Cash Agentic Flow</strong>
          <p>One business action runs multiple local LLM prompts and writes auditable telemetry.</p>
        </aside>
      </section>

      <section className="about-solution about-flow-card">
        <div className="about-solution-heading">
          <p className="detail-kicker">Solution</p>
          <h3>Turn every agent run into measurable production evidence.</h3>
          <p>
            It turns a multi-agent quote workflow into measurable production evidence, so teams can
            decide which model to use, where quality risk appears, and how much the workflow costs
            before expanding usage.
          </p>
        </div>
        <div className="about-solution-steps">
          {solutionSteps.map((step, index) => (
            <article key={step.label}>
              <span>{String(index + 1).padStart(2, "0")}</span>
              <strong>{step.label}</strong>
              <p>{step.detail}</p>
            </article>
          ))}
        </div>
      </section>

      <section className="about-control-strip" aria-label="LLM production controls">
        {operatingControls.map((control) => {
          const Icon = control.icon;
          return (
            <article key={control.label}>
              <Icon size={17} aria-hidden="true" />
              <strong>{control.label}</strong>
              <span>{control.detail}</span>
            </article>
          );
        })}
      </section>

      <section className="about-flow-card about-runbook">
        <div>
          <p className="detail-kicker">How to read the app</p>
          <h3>Start with the flow, then inspect the operating controls.</h3>
          <p>
            Run <strong>Use Case 01 - Quote-to-Cash Agentic Flow</strong>. Then move across Cost
            Impact, Quality Evidence, Latency SLOs, Prompt Governance, and Drift & Alerts to see
            how the same agent run is managed like a production system.
          </p>
        </div>
        <div className="about-flow-line">
          {flowSteps.map((step, index) => {
            const Icon = step.icon;
            return (
              <div className="about-flow-item" key={step.label}>
                <span>
                  <Icon size={15} aria-hidden="true" />
                  {step.label}
                </span>
                {index < flowSteps.length - 1 ? <ArrowRight size={16} aria-hidden="true" /> : null}
              </div>
            );
          })}
        </div>
      </section>
    </>
  );
}

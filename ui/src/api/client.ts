/**
 * Typed API client used by the React app to call the FastAPI backend.
 *
 * Author: Sarala Biswal
 */
const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:9100";

export type CostSummary = {
  total_cost_usd: string;
  total_calls: number;
  avg_cost_per_call: string;
  cost_by_model: Record<string, string>;
  cost_by_usecase: Record<string, string>;
  top_cost_driver: string;
  projected_monthly_usd: string;
  budget_burn_rate_pct: number;
};

export type AlertRecord = {
  alert_id: string;
  timestamp: string;
  alert_type: string;
  severity: string;
  use_case?: string;
  message: string;
  metric_value?: number;
  threshold_value?: number;
  resolved: boolean;
};

export type CostByModel = {
  model: string;
  provider: string;
  total_cost: string;
  call_count: number;
  avg_cost: string;
};

export type CostByUsecase = {
  use_case: string;
  total_cost: string;
  call_count: number;
};

export type CostTimelinePoint = {
  date: string;
  total_cost: string;
};

export type OptimizationRecommendation = {
  use_case: string;
  current_model: string;
  current_cost_usd: string;
  recommended_model: string;
  recommended_cost_usd: string;
  quality_delta_pct: number;
  cost_savings_pct: number;
  monthly_savings_usd: string;
  rationale: string;
};

export type LatencyPercentiles = {
  model: string;
  p50_ms: number;
  p95_ms: number;
  p99_ms: number;
  slo_target_ms: number;
  slo_compliance_pct: number;
  breach_count_24h: number;
};

export type PromptVersion = {
  version_id: string;
  use_case: string;
  version: string;
  prompt_text: string;
  model: string;
  status: string;
  avg_quality_score?: number | null;
  avg_cost_usd?: string | null;
  avg_latency_ms?: number | null;
};

export type QualityScore = {
  use_case: string;
  model: string;
  timestamp: string;
  faithfulness: number;
  relevance: number;
  coherence: number;
  composite_score: number;
  gate_passed: boolean;
};

export type HallucinationRate = {
  model: string;
  use_case: string;
  call_count: number;
  flagged_count: number;
  hallucination_rate: number;
};

export type GateResult = {
  use_case: string;
  passed: number;
  failed: number;
};

export type LatencySlo = {
  model: string;
  slo_target_ms: number;
  slo_compliance_pct: number;
  breach_count_24h: number;
  status: string;
};

export type LatencyTimelinePoint = {
  date: string;
  model: string;
  p95_ms: number;
};

export type DriftScore = {
  use_case: string;
  model: string;
  timestamp: string;
  drift_score: number;
  baseline_similarity: number;
  alert_triggered: boolean;
};

export type RevenueAccount = {
  account_id: string;
  name: string;
  segment: string;
  industry: string;
  region: string;
  customer_health: number;
  executive_sponsor: string;
};

export type RevenueOpportunity = {
  opportunity_id: string;
  account: RevenueAccount;
  scenario: string;
  name: string;
  stage: string;
  arr_usd: string;
  expansion_arr_usd: string;
  current_discount_pct: number;
  requested_discount_pct: number;
  target_margin_pct: number;
  current_margin_pct: number;
  renewal_risk: string;
  product_tier: string;
  contract_terms_months: number;
  close_date: string;
  approval_flags: string[];
  pain_points: string[];
  success_plan: string[];
  grounded_evidence: string[];
  total_contract_value_usd: string;
};

export type RevenueRecommendation = {
  renewal_risk_summary: string;
  recommended_discount_pct: number;
  margin_risk_assessment: string;
  approval_recommendation: string;
  negotiation_guidance: string[];
  customer_facing_quote_note: string;
  evidence_citations: string[];
  forecast_arr_usd: string;
  forecast_tcv_usd: string;
  expected_margin_pct: number;
};

export type RevenueTraceStep = {
  step_id: string;
  label: string;
  system: string;
  agent_name: string;
  prompt_name: string;
  prompt_version: string;
  call_id: string;
  model: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  cost_usd: string;
  quality_score: number;
  status: string;
  detail: string;
  evidence: string[];
};

export type RevenueTrace = {
  trace_id: string;
  call_id: string;
  use_case: string;
  prompt_version: string;
  model_mode: string;
  model: string;
  provider: string;
  input_tokens: number;
  output_tokens: number;
  latency_ms: number;
  cost_usd: string;
  quality_score: number;
  margin_risk_score: number;
  alerts_created: number;
  created_at: string;
  steps: RevenueTraceStep[];
};

export type RevenueDeskResponse = {
  status: string;
  opportunity: RevenueOpportunity;
  recommendation: RevenueRecommendation;
  trace: RevenueTrace;
};

export type RevenueControls = {
  prompt_versions: Array<{ value: string; label: string }>;
};

export type DeveloperPrompt = {
  step_id: string;
  agent_name: string;
  prompt_name: string;
  prompt_contract: string;
  label: string;
  system: string;
  prompt: string;
  policy_source: {
    policy_id: string;
    title: string;
    owner: string;
    version: string;
    source: string;
    rules: string[];
  };
  observability_fields: string[];
};

export type DeveloperPromptPreview = {
  use_case: string;
  opportunity_id: string;
  opportunity_name: string;
  account_name: string;
  prompt_version: string;
  approval_guardrails_enabled: boolean;
  prompts: DeveloperPrompt[];
};

export type LocalModelOption = {
  value: "llama3.2" | "qwen2.5:7b" | "mistral";
  label: string;
  description: string;
  relativeCost: string;
};

export type CloudProviderOption = {
  value: "local" | "aws" | "azure" | "oci" | "gcp";
  label: string;
  model: string;
  inputPerMillion: number;
  outputPerMillion: number;
  description: string;
  sourceLabel: string;
};

export const LOCAL_MODEL_OPTIONS: LocalModelOption[] = [
  {
    value: "llama3.2",
    label: "Llama 3.2",
    description: "Balanced default for local Quote-to-Cash reasoning.",
    relativeCost: "$0.20 / 1M tokens",
  },
  {
    value: "qwen2.5:7b",
    label: "Qwen 2.5",
    description: "Higher local quality profile with a higher routed token cost.",
    relativeCost: "$0.24 / 1M tokens",
  },
  {
    value: "mistral",
    label: "Mistral",
    description: "Lower routed token cost for high-volume quote drafting.",
    relativeCost: "$0.18 / 1M tokens",
  },
];

export const CLOUD_PROVIDER_OPTIONS: CloudProviderOption[] = [
  {
    value: "local",
    label: "Local LLM",
    model: "Ollama local runtime",
    inputPerMillion: 0.2,
    outputPerMillion: 0.2,
    description: "Actual execution path for the standalone app using the selected local model.",
    sourceLabel: "$0.20 blended / 1M tokens",
  },
  {
    value: "aws",
    label: "AWS Bedrock",
    model: "Claude 3.5 Haiku",
    inputPerMillion: 0.8,
    outputPerMillion: 4.0,
    description: "Bedrock hosted fast Anthropic model for production agent workloads.",
    sourceLabel: "$0.80 input / $4.00 output per 1M tokens",
  },
  {
    value: "azure",
    label: "Azure OpenAI",
    model: "GPT-4o mini",
    inputPerMillion: 0.15,
    outputPerMillion: 0.6,
    description: "Azure OpenAI global deployment rate-card for low-cost quote reasoning.",
    sourceLabel: "$0.15 input / $0.60 output per 1M tokens",
  },
  {
    value: "oci",
    label: "OCI Generative AI",
    model: "Cohere Command R",
    inputPerMillion: 0.15,
    outputPerMillion: 0.6,
    description: "OCI-hosted Cohere Command R planning rate for enterprise RAG-style flows.",
    sourceLabel: "$0.15 input / $0.60 output per 1M tokens",
  },
  {
    value: "gcp",
    label: "Google Vertex AI",
    model: "Gemini 2.0 Flash",
    inputPerMillion: 0.15,
    outputPerMillion: 0.6,
    description: "Vertex AI Gemini Flash planning rate for fast agentic workflows.",
    sourceLabel: "$0.15 input / $0.60 output per 1M tokens",
  },
];

export function displayModelName(model: string): string {
  const direct = LOCAL_MODEL_OPTIONS.find((item) => item.value === model);
  if (direct) {
    return direct.label;
  }
  if (model === "qwen2.5") {
    return "Qwen 2.5";
  }
  if (model === "llama3.2:latest") {
    return "Llama 3.2";
  }
  if (model === "mistral:latest") {
    return "Mistral";
  }
  return model;
}

export async function getCostSummary(useCase?: string): Promise<CostSummary> {
  return request<CostSummary>(withUseCase("/costs/summary", useCase));
}

export async function getAlerts(useCase?: string): Promise<AlertRecord[]> {
  return request<AlertRecord[]>(withUseCase("/alerts/history", useCase));
}

export async function getLatencyPercentiles(useCase?: string): Promise<LatencyPercentiles[]> {
  return request<LatencyPercentiles[]>(withUseCase("/latency/percentiles", useCase));
}

export async function getPromptVersions(useCase: string): Promise<PromptVersion[]> {
  return request<PromptVersion[]>(`/prompts/versions?use_case=${encodeURIComponent(useCase)}`);
}

export async function getCostByModel(useCase?: string): Promise<CostByModel[]> {
  return request<CostByModel[]>(withUseCase("/costs/by-model", useCase));
}

export async function getCostByUsecase(): Promise<CostByUsecase[]> {
  return request<CostByUsecase[]>("/costs/by-usecase");
}

export async function getCostTimeline(useCase?: string): Promise<CostTimelinePoint[]> {
  return request<CostTimelinePoint[]>(withUseCase("/costs/timeline", useCase));
}

export async function getOptimizationRecommendations(
  useCase: string,
  targetModel?: string,
): Promise<OptimizationRecommendation[]> {
  const target = targetModel ? `&target_model=${encodeURIComponent(targetModel)}` : "";
  return request<OptimizationRecommendation[]>(`/costs/optimize?use_case=${encodeURIComponent(useCase)}${target}`);
}

export async function getQualityScores(useCase?: string): Promise<QualityScore[]> {
  return request<QualityScore[]>(withUseCase("/quality/scores", useCase));
}

export async function getHallucinations(useCase?: string): Promise<HallucinationRate[]> {
  return request<HallucinationRate[]>(withUseCase("/quality/hallucinations", useCase));
}

export async function getGateResults(useCase?: string): Promise<GateResult[]> {
  return request<GateResult[]>(withUseCase("/quality/gate-results", useCase));
}

export async function getLatencySlos(useCase?: string): Promise<LatencySlo[]> {
  return request<LatencySlo[]>(withUseCase("/latency/slos", useCase));
}

export async function getLatencyTimeline(useCase?: string): Promise<LatencyTimelinePoint[]> {
  return request<LatencyTimelinePoint[]>(withUseCase("/latency/timeline", useCase));
}

export async function getDriftScores(useCase?: string): Promise<DriftScore[]> {
  return request<DriftScore[]>(withUseCase("/drift/scores", useCase));
}

export async function getDriftAlerts(useCase?: string): Promise<AlertRecord[]> {
  return request<AlertRecord[]>(withUseCase("/drift/alerts", useCase));
}

export async function getRevenueOpportunities(): Promise<RevenueOpportunity[]> {
  return request<RevenueOpportunity[]>("/revenue-desk/opportunities");
}

export async function getRevenueControls(): Promise<RevenueControls> {
  return request<RevenueControls>("/revenue-desk/controls");
}

export async function getDeveloperPrompts(input: {
  opportunityId: string;
  promptVersion: string;
  approvalGuardrailsEnabled: boolean;
  reviewerNotes?: string;
}): Promise<DeveloperPromptPreview> {
  const params = new URLSearchParams({
    opportunity_id: input.opportunityId,
    prompt_version: input.promptVersion,
    approval_guardrails_enabled: String(input.approvalGuardrailsEnabled),
  });
  if (input.reviewerNotes) {
    params.set("reviewer_notes", input.reviewerNotes);
  }
  return request<DeveloperPromptPreview>(`/revenue-desk/developer/prompts?${params.toString()}`);
}

export async function analyzeRevenueOpportunity(input: {
  opportunity_id: string;
  prompt_version: string;
  model_mode: string;
  local_model?: string;
  approval_guardrails_enabled: boolean;
  reviewer_notes?: string;
}): Promise<RevenueDeskResponse> {
  return request<RevenueDeskResponse>("/revenue-desk/analyze", {
    method: "POST",
    body: JSON.stringify(input),
  });
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...init?.headers,
    },
    ...init,
  });
  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }
  return response.json() as Promise<T>;
}

function withUseCase(path: string, useCase?: string): string {
  if (!useCase) {
    return path;
  }
  const separator = path.includes("?") ? "&" : "?";
  return `${path}${separator}use_case=${encodeURIComponent(useCase)}`;
}

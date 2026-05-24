/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
import { Cloud, ServerCog, SlidersHorizontal } from "lucide-react";
import { CLOUD_PROVIDER_OPTIONS, LOCAL_MODEL_OPTIONS, type CloudProviderOption } from "../api/client";
import { SectionHeader, StatusBadge } from "../components";

type SettingsProps = {
  selectedLocalModel: string;
  selectedProviderRateCard: CloudProviderOption["value"];
  onSelectedLocalModelChange: (model: string) => void;
  onSelectedProviderRateCardChange: (provider: CloudProviderOption["value"]) => void;
};

export function Settings({
  selectedLocalModel,
  selectedProviderRateCard,
  onSelectedLocalModelChange,
  onSelectedProviderRateCardChange,
}: SettingsProps) {
  const selectedModel = LOCAL_MODEL_OPTIONS.find((item) => item.value === selectedLocalModel)
    ?? LOCAL_MODEL_OPTIONS[0];
  const selectedProvider = CLOUD_PROVIDER_OPTIONS.find((item) => item.value === selectedProviderRateCard)
    ?? CLOUD_PROVIDER_OPTIONS[0];
  const isLocalProvider = selectedProvider.value === "local";

  return (
    <>
      <SectionHeader
        eyebrow="Runtime Settings"
        title="Provider and model policy"
        sub="Choose the provider rate card used for cost planning. The standalone app executes Quote-to-Cash with the selected local LLM."
      />

      <section className="settings-panel">
        <div className="settings-summary">
          <ServerCog size={18} aria-hidden="true" />
          <div>
            <p className="detail-kicker">Active execution path</p>
            <h3>Local LLM - {selectedModel.label}</h3>
            <p>
              {isLocalProvider
                ? "Local LLM is both the execution path and the cost rate card."
                : `${selectedProvider.label} is used for cost planning only. Live agent execution stays on ${selectedModel.label} because cloud provider calls are not wired in this standalone app.`}
            </p>
          </div>
          <strong>{isLocalProvider ? selectedModel.relativeCost : selectedProvider.sourceLabel}</strong>
        </div>

        {!isLocalProvider ? (
          <div className="settings-disclaimer">
            <StatusBadge status="planning only" />
            <p>
              Cloud provider selection changes the Cost Impact rate card. It does not route live
              prompts to {selectedProvider.label}; the Quote-to-Cash flow still runs on the local LLM.
            </p>
          </div>
        ) : null}

        <div className="settings-section-heading">
          <h3>Provider</h3>
          <p>Select Local LLM for actual local execution pricing, or choose a cloud provider to estimate managed endpoint economics.</p>
        </div>

        <div className="settings-model-grid" role="radiogroup" aria-label="Provider rate card">
          {CLOUD_PROVIDER_OPTIONS.map((option) => (
            <button
              aria-checked={selectedProviderRateCard === option.value}
              className={`settings-model-card ${selectedProviderRateCard === option.value ? "settings-model-card-active" : ""}`}
              key={option.value}
              onClick={() => onSelectedProviderRateCardChange(option.value)}
              role="radio"
              type="button"
            >
              {option.value === "local" ? <ServerCog size={17} aria-hidden="true" /> : <Cloud size={17} aria-hidden="true" />}
              <strong>{option.label}</strong>
              <span>{option.model} - {option.description}</span>
              <em>{option.sourceLabel}</em>
            </button>
          ))}
        </div>

        <div className="settings-section-heading">
          <h3>Local execution model</h3>
          <p>Default is Llama 3.2. This is the model that actually runs the Quote-to-Cash agents in standalone mode.</p>
        </div>

        <div className="settings-model-grid" role="radiogroup" aria-label="Local LLM model">
          {LOCAL_MODEL_OPTIONS.map((option) => (
            <button
              aria-checked={selectedLocalModel === option.value}
              className={`settings-model-card ${selectedLocalModel === option.value ? "settings-model-card-active" : ""}`}
              key={option.value}
              onClick={() => onSelectedLocalModelChange(option.value)}
              role="radio"
              type="button"
            >
              <SlidersHorizontal size={17} aria-hidden="true" />
              <strong>{option.label}</strong>
              <span>{option.description}</span>
              <em>{option.relativeCost}</em>
            </button>
          ))}
        </div>
      </section>
    </>
  );
}

/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
import type { LucideIcon } from "lucide-react";

type MetricCardProps = {
  label: string;
  value: string;
  delta?: string;
  deltaColor?: "green" | "amber" | "red";
  sub?: string;
  icon: LucideIcon;
};

export function MetricCard({ label, value, delta, deltaColor = "green", sub, icon: Icon }: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-head">
        <span>{label}</span>
        <Icon size={18} aria-hidden="true" />
      </div>
      <div className="metric-value">{value}</div>
      {delta ? <span className={`delta delta-${deltaColor}`}>{delta}</span> : null}
      {sub ? <p className="metric-sub">{sub}</p> : null}
    </article>
  );
}

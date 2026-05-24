/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
type StatusBadgeProps = {
  status: string;
};

const STATUS_CLASS: Record<string, string> = {
  healthy: "badge-green",
  active: "badge-green",
  stable: "badge-green",
  warning: "badge-amber",
  watch: "badge-amber",
  testing: "badge-amber",
  critical: "badge-red",
  alert: "badge-red",
  failed: "badge-red",
  unknown: "badge-grey",
  deprecated: "badge-grey",
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const key = status.toLowerCase();
  return <span className={`badge ${STATUS_CLASS[key] ?? "badge-grey"}`}>{status}</span>;
}

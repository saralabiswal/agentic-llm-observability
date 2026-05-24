/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
import { AlertTriangle, Info } from "lucide-react";

type AlertBannerProps = {
  type: "warning" | "critical" | "info";
  title: string;
  message: string;
};

export function AlertBanner({ type, title, message }: AlertBannerProps) {
  const Icon = type === "info" ? Info : AlertTriangle;
  return (
    <aside className={`alert-banner alert-${type}`}>
      <Icon size={20} aria-hidden="true" />
      <div>
        <p className="alert-title">{title}</p>
        <p className="alert-message">{message}</p>
      </div>
    </aside>
  );
}

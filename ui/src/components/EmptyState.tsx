/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
import type { LucideIcon } from "lucide-react";

type EmptyStateProps = {
  icon: LucideIcon;
  title: string;
  sub: string;
  action: string;
  onAction: () => void;
};

export function EmptyState({ icon: Icon, title, sub, action, onAction }: EmptyStateProps) {
  return (
    <section className="empty-state">
      <Icon size={48} aria-hidden="true" />
      <h3 className="empty-title">{title}</h3>
      <p className="empty-sub">{sub}</p>
      <button className="action-button" type="button" onClick={onAction}>
        {action}
      </button>
    </section>
  );
}

/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
import type { ReactNode } from "react";

type ChartCardProps = {
  title: string;
  sub?: string;
  children: ReactNode;
};

export function ChartCard({ title, sub, children }: ChartCardProps) {
  return (
    <section className="chart-card">
      <h3 className="chart-title">{title}</h3>
      {sub ? <p className="chart-sub">{sub}</p> : null}
      {children}
    </section>
  );
}

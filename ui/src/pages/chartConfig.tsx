/**
 * Dashboard page for one LLMOps control area in the Quote-to-Cash story.
 *
 * Author: Sarala Biswal
 */
export const chartConfig = {
  cartesianGrid: { stroke: "var(--border)", strokeDasharray: "4 4" },
  xAxis: { stroke: "var(--border)", tick: { fill: "var(--ink-muted)", fontSize: 11 } },
  yAxis: { stroke: "var(--border)", tick: { fill: "var(--ink-muted)", fontSize: 11 } },
  tooltip: {
    contentStyle: {
      background: "var(--surface-mid)",
      border: "1px solid var(--border)",
      borderRadius: "8px",
      color: "var(--ink)",
      fontSize: "12px",
    },
    cursor: { fill: "rgba(59,130,246,0.08)" },
  },
  legend: { iconSize: 10, wrapperStyle: { fontSize: "12px", color: "var(--ink-muted)" } },
};

export function AreaGradient({ id, color }: { id: string; color: string }) {
  return (
    <defs>
      <linearGradient id={id} x1="0" y1="0" x2="0" y2="1">
        <stop offset="5%" stopColor={color} stopOpacity={0.25} />
        <stop offset="95%" stopColor={color} stopOpacity={0.02} />
      </linearGradient>
    </defs>
  );
}

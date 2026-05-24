/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
type SectionHeaderProps = {
  eyebrow: string;
  title: string;
  sub?: string;
};

export function SectionHeader({ eyebrow, title, sub }: SectionHeaderProps) {
  return (
    <header className="section-header">
      <p className="section-eyebrow">{eyebrow}</p>
      <h2 className="section-title">{title}</h2>
      {sub ? <p className="section-sub">{sub}</p> : null}
    </header>
  );
}

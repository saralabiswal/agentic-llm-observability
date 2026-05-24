/**
 * Reusable presentation component for the enterprise dashboard UI.
 *
 * Author: Sarala Biswal
 */
type SkeletonLoaderProps = {
  rows?: number;
};

export function SkeletonLoader({ rows = 4 }: SkeletonLoaderProps) {
  return (
    <div className="skeleton" aria-busy="true">
      {Array.from({ length: rows }).map((_, index) => (
        <div className="skeleton-row" key={index} />
      ))}
    </div>
  );
}

/**
 * Lightweight Suspense fallback shown while a lazy-loaded route chunk is
 * being fetched. Intentionally minimal — anything heavier here would defeat
 * the purpose of code splitting.
 */
export function RouteSkeleton(): JSX.Element {
  return (
    <div
      role="status"
      aria-live="polite"
      aria-label="Loading"
      style={{
        padding: "var(--space-6, 32px)",
        color: "var(--fg-muted, #5b6470)",
        fontSize: "var(--text-sm, 14px)",
      }}
    >
      Loading…
    </div>
  );
}

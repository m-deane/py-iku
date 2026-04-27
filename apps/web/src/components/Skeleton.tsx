import type { CSSProperties } from "react";

/**
 * Skeleton — reusable shimmer placeholder for network-bound views.
 *
 * Sprint 2C polish: every TanStack Query loading state should render a Skeleton
 * (not nothing/flicker). Animation comes from the shared `@keyframes
 * py-iku-skeleton` injected once at module load (see ConvertPage). We re-inject
 * defensively here so direct consumers of <Skeleton/> work even if ConvertPage
 * hasn't mounted yet.
 *
 * Tokens: uses `--surface-sunken` and `--surface-raised` so the gradient blends
 * with both light and dark themes.
 */

if (typeof document !== "undefined" && !document.getElementById("py-iku-skeleton-keyframes")) {
  const style = document.createElement("style");
  style.id = "py-iku-skeleton-keyframes";
  style.textContent =
    "@keyframes py-iku-skeleton { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }";
  document.head.appendChild(style);
}

export interface SkeletonProps {
  /** Visual shape — `"text"` is a one-line bar, `"card"` a rectangular block. */
  variant?: "text" | "card" | "circle" | "bar";
  /** Width override (CSS length). Defaults to 100%. */
  width?: number | string;
  /** Height override (CSS length). Defaults vary per variant. */
  height?: number | string;
  /** Visual gap below the skeleton — useful when stacking. */
  marginBottom?: number | string;
  /** Override testid for assertions. */
  "data-testid"?: string;
  /** Accessible label — falls back to "Loading…" announced via SR-only span. */
  ariaLabel?: string;
  /** Inline style passthrough (rarely needed). */
  style?: CSSProperties;
}

const VARIANT_DEFAULTS: Record<NonNullable<SkeletonProps["variant"]>, { height: number; radius: string }> = {
  text: { height: 14, radius: "var(--radius-sm, 4px)" },
  card: { height: 96, radius: "var(--radius-md, 8px)" },
  circle: { height: 32, radius: "9999px" },
  bar: { height: 8, radius: "var(--radius-pill, 9999px)" },
};

export function Skeleton(props: SkeletonProps): JSX.Element {
  const variant = props.variant ?? "text";
  const defaults = VARIANT_DEFAULTS[variant];
  const width = props.width ?? (variant === "circle" ? defaults.height : "100%");
  const height = props.height ?? defaults.height;

  const style: CSSProperties = {
    display: "block",
    width: typeof width === "number" ? `${width}px` : width,
    height: typeof height === "number" ? `${height}px` : height,
    borderRadius: defaults.radius,
    background:
      "linear-gradient(90deg, var(--surface-sunken, #f2f4f7) 25%, var(--surface-raised, #f7f8fa) 50%, var(--surface-sunken, #f2f4f7) 75%)",
    backgroundSize: "200% 100%",
    animation: "py-iku-skeleton 1.2s ease-in-out infinite",
    marginBottom:
      typeof props.marginBottom === "number"
        ? `${props.marginBottom}px`
        : props.marginBottom,
    ...props.style,
  };

  return (
    <span
      role="status"
      aria-live="polite"
      aria-busy="true"
      aria-label={props.ariaLabel ?? "Loading…"}
      data-testid={props["data-testid"] ?? "skeleton"}
      style={style}
    />
  );
}

/**
 * SkeletonGrid — convenience wrapper that renders N skeleton cards in a CSS
 * grid matching the catalog list layout. Used by RecipesList / ProcessorsList
 * to avoid a layout-jump when query data lands.
 */
export interface SkeletonGridProps {
  count?: number;
  /** Test seam for assertions. */
  "data-testid"?: string;
}

export function SkeletonGrid(props: SkeletonGridProps): JSX.Element {
  const count = props.count ?? 6;
  return (
    <div
      data-testid={props["data-testid"] ?? "skeleton-grid"}
      style={{
        display: "grid",
        gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))",
        gap: "0.75rem",
      }}
    >
      {Array.from({ length: count }).map((_, i) => (
        <Skeleton key={i} variant="card" data-testid={`skeleton-card-${i}`} />
      ))}
    </div>
  );
}

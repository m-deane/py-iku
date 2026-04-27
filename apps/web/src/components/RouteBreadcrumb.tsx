import { useLocation } from "react-router-dom";
import { Breadcrumb, type BreadcrumbItem } from "./Breadcrumb";

/**
 * Map route prefix → cluster label + leaf label.
 *
 * The prefix is matched in declaration order, so put longer paths first
 * (e.g. /settings/connections before /settings).
 */
interface RouteCrumb {
  prefix: string;
  cluster?: "Build" | "Library" | "Lifecycle" | "Account";
  leaf: string;
}

const ROUTE_CRUMBS: RouteCrumb[] = [
  // Build cluster
  { prefix: "/editor", cluster: "Build", leaf: "Editor" },
  { prefix: "/convert", cluster: "Build", leaf: "Convert" },
  { prefix: "/inspector", cluster: "Build", leaf: "Inspector" },
  { prefix: "/flow/", cluster: "Build", leaf: "Flow viewer" },

  // Library cluster
  { prefix: "/catalog", cluster: "Library", leaf: "Catalog" },
  { prefix: "/snippets", cluster: "Library", leaf: "Snippets" },
  { prefix: "/templates", cluster: "Library", leaf: "Templates" },

  // Lifecycle cluster
  { prefix: "/diff", cluster: "Lifecycle", leaf: "Diff" },
  { prefix: "/validation", cluster: "Lifecycle", leaf: "Validation" },
  { prefix: "/export", cluster: "Lifecycle", leaf: "Export" },
  { prefix: "/deploy", cluster: "Lifecycle", leaf: "Deploy" },
  { prefix: "/share/", cluster: "Lifecycle", leaf: "Share" },
  { prefix: "/audit", cluster: "Lifecycle", leaf: "Audit" },

  // Account cluster
  { prefix: "/settings/connections", cluster: "Account", leaf: "DSS Connections" },
  { prefix: "/settings", cluster: "Account", leaf: "Settings" },
];

/**
 * Renders a breadcrumb based on the current pathname. Returns nothing for
 * `/` so the home page stays clean.
 *
 * Format examples:
 *   /convert         → Build / Convert
 *   /diff            → Lifecycle / Diff
 *   /settings        → Account / Settings
 */
export function RouteBreadcrumb(): JSX.Element | null {
  const { pathname } = useLocation();

  if (pathname === "/" || pathname === "") return null;

  const match = ROUTE_CRUMBS.find((r) => pathname.startsWith(r.prefix));
  if (!match) return null;

  const items: BreadcrumbItem[] = [];
  if (match.cluster) {
    items.push({ label: match.cluster });
  }
  items.push({ label: match.leaf });

  return <Breadcrumb items={items} />;
}

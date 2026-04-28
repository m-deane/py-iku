import { useLocation } from "react-router-dom";
import { Breadcrumb, type BreadcrumbItem } from "./Breadcrumb";

/**
 * Map route prefix → cluster label + leaf label.
 *
 * The prefix is matched in declaration order, so put longer paths first.
 */
interface RouteCrumb {
  prefix: string;
  cluster?: "Build" | "Library" | "Account";
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

  // Account cluster
  { prefix: "/settings", cluster: "Account", leaf: "Settings" },
];

/**
 * Renders a breadcrumb based on the current pathname. Returns nothing for
 * `/` so the home page stays clean.
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

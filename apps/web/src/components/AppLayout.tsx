import { Link, NavLink } from "react-router-dom";
import { useEffect, useState, type ReactNode } from "react";
import { ThemeToggle } from "./ThemeToggle";
import { RouteBreadcrumb } from "./RouteBreadcrumb";
import { SettingsDrawer } from "../features/settings/SettingsDrawer";
import {
  CommandPalette,
  useCommandPaletteHotkey,
} from "../features/command-palette";
import { useCommandPaletteStore } from "../store/commandPalette";
import { useUiStore } from "../state/uiStore";
import styles from "./AppLayout.module.css";

export interface AppLayoutProps {
  children: ReactNode;
}

/**
 * Sidebar nav definition. Studio's scope reduction collapsed the previous
 * 4-cluster sidebar down to three: Build, Library, Account.
 *
 * Cluster headers render as small uppercase tracking-wide labels (Linear /
 * Vercel / Notion style) using `--fg-muted`. Active items use the accent
 * color from `ui-tokens.css`.
 */
interface NavLinkSpec {
  to: string;
  label: string;
  /** end=true for routes where prefix-match would over-highlight (e.g. "/"). */
  end?: boolean;
}

interface NavCluster {
  id: string;
  title: string;
  items: NavLinkSpec[];
}

const NAV_CLUSTERS: NavCluster[] = [
  {
    id: "build",
    title: "Build",
    items: [
      { to: "/editor", label: "Editor" },
      { to: "/convert", label: "Convert" },
      { to: "/inspector", label: "Inspector" },
    ],
  },
  {
    id: "library",
    title: "Library",
    items: [{ to: "/catalog", label: "Catalog" }],
  },
  {
    id: "account",
    title: "Account",
    items: [{ to: "/settings", label: "Settings" }],
  },
];

export function AppLayout({ children }: AppLayoutProps): JSX.Element {
  const openSettings = useUiStore((s) => s.openSettingsDrawer);
  const openPalette = useCommandPaletteStore((s) => s.open);
  // Sprint 5 — mobile sidebar drawer. Closed by default; toggled via the
  // hamburger button that's only visible at <800px viewports. Closes on any
  // nav-link click, on Escape, and when the viewport returns to desktop.
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  // Mount the global Cmd+K listener once at the shell level. Every route
  // sits below this so the shortcut works everywhere.
  useCommandPaletteHotkey();

  // Close the mobile drawer on Escape.
  useEffect(() => {
    if (!mobileNavOpen) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setMobileNavOpen(false);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [mobileNavOpen]);

  return (
    <div
      className={`${styles.shell} ${mobileNavOpen ? styles.mobileNavOpen : ""}`}
      data-mobile-nav-open={mobileNavOpen ? "true" : "false"}
    >
      <button
        type="button"
        className={styles.hamburger}
        data-testid="mobile-nav-toggle"
        aria-label={mobileNavOpen ? "Close navigation" : "Open navigation"}
        aria-expanded={mobileNavOpen}
        aria-controls="app-sidebar"
        onClick={() => setMobileNavOpen((v) => !v)}
      >
        {mobileNavOpen ? "✕" : "☰"}
      </button>
      {mobileNavOpen ? (
        <button
          type="button"
          aria-hidden
          tabIndex={-1}
          className={styles.mobileScrim}
          data-testid="mobile-nav-scrim"
          onClick={() => setMobileNavOpen(false)}
        />
      ) : null}
      <aside
        id="app-sidebar"
        className={styles.sidebar}
        aria-label="Primary navigation"
        data-testid="app-sidebar"
      >
        <Link
          to="/"
          className={styles.brand}
          onClick={() => setMobileNavOpen(false)}
        >
          <span className={styles.brandMark} aria-hidden>
            ◆
          </span>
          <span>py-iku-studio</span>
        </Link>
        {NAV_CLUSTERS.map((cluster) => (
          <div
            key={cluster.id}
            className={styles.cluster}
            data-testid={`nav-cluster-${cluster.id}`}
          >
            <h2 className={styles.clusterHeader}>{cluster.title}</h2>
            <ul className={styles.navList}>
              {cluster.items.map((item) => (
                <li key={item.to}>
                  <NavLink
                    to={item.to}
                    end={item.end}
                    onClick={() => setMobileNavOpen(false)}
                    className={({ isActive }) =>
                      `${styles.navItem} ${isActive ? styles.navItemActive : ""}`
                    }
                  >
                    {item.label}
                  </NavLink>
                </li>
              ))}
            </ul>
          </div>
        ))}
      </aside>

      <header className={styles.header}>
        <div className={styles.headerActions}>
          <button
            type="button"
            data-testid="command-palette-open-trigger"
            onClick={openPalette}
            aria-label="Open command palette (Cmd+K)"
            className={styles.iconBtn}
            title="Search · Cmd+K"
          >
            ⌕
          </button>
          <ThemeToggle />
          <button
            type="button"
            data-testid="settings-open-trigger"
            onClick={openSettings}
            aria-label="Open settings"
            className={styles.iconBtn}
          >
            ⚙
          </button>
        </div>
      </header>

      <div className={styles.body}>
        <RouteBreadcrumb />
        <main className={styles.main}>{children}</main>
      </div>

      <SettingsDrawer />
      <CommandPalette />
    </div>
  );
}

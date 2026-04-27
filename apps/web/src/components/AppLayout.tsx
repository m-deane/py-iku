import { Link, NavLink } from "react-router-dom";
import type { ReactNode } from "react";
import { ThemeToggle } from "./ThemeToggle";
import { RouteBreadcrumb } from "./RouteBreadcrumb";
import { SettingsDrawer } from "../features/settings/SettingsDrawer";
import {
  CommandPalette,
  useCommandPaletteHotkey,
} from "../features/command-palette";
import { useCommandPaletteStore } from "../store/commandPalette";
import { useUiStore } from "../state/uiStore";
import { useSettingsStore } from "../state/settingsStore";
import { useTabHotkeys } from "../store/useTabHotkeys";
import { ShareUrlButton, useShareUrlBoot } from "./ShareUrlButton";
import { ChatDrawer, useChatStore } from "../features/chat";
import { CostMeterWidget } from "../features/cost-meter/CostMeterWidget";
import styles from "./AppLayout.module.css";

export interface AppLayoutProps {
  children: ReactNode;
}

/**
 * Sidebar nav definition. The IA review reorganized 12 modules into four
 * clusters; previously the top bar exposed only 5 of those 12 as flat links.
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
    items: [
      { to: "/catalog", label: "Catalog" },
      { to: "/snippets", label: "Snippets" },
      { to: "/templates", label: "Templates" },
      { to: "/grel", label: "GREL Formulas" },
      { to: "/lmp", label: "LMP Nodes" },
    ],
  },
  {
    id: "lifecycle",
    title: "Lifecycle",
    items: [
      { to: "/diff", label: "Diff" },
      { to: "/diff/curves", label: "Curve Diff" },
      { to: "/validation", label: "Validation" },
      { to: "/export", label: "Export" },
      { to: "/deploy", label: "Deploy" },
      { to: "/share", label: "Share" },
      { to: "/audit", label: "Audit" },
    ],
  },
  {
    id: "account",
    title: "Account",
    items: [
      { to: "/settings", label: "Settings" },
      { to: "/llm-history", label: "LLM history" },
    ],
  },
];

export function AppLayout({ children }: AppLayoutProps): JSX.Element {
  const openSettings = useUiStore((s) => s.openSettingsDrawer);
  const openPalette = useCommandPaletteStore((s) => s.open);
  const multiTabEnabled = useSettingsStore((s) => s.multiTabEnabled);
  // Mount the global Cmd+K listener once at the shell level. Every route
  // sits below this so the shortcut works everywhere.
  useCommandPaletteHotkey();
  // Sprint 4 — gate Cmd+T/W/1..8 behind the multi-tab flag so users on the
  // legacy single-tab UI keep their browser-native behaviour intact.
  useTabHotkeys(multiTabEnabled);
  // Sprint 4 — restore tabs/theme/panels from `#state=...` if a colleague
  // pasted a share URL.
  useShareUrlBoot();

  return (
    <div className={styles.shell}>
      <aside
        className={styles.sidebar}
        aria-label="Primary navigation"
        data-testid="app-sidebar"
      >
        <Link to="/" className={styles.brand}>
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
          <CostMeterWidget />
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
          <ShareUrlButton />
          <button
            type="button"
            data-testid="chat-open-trigger"
            onClick={() => useChatStore.getState().toggleOpen()}
            aria-label="Open chat with flow (Cmd+I)"
            title="Chat with flow · Cmd+I"
            className={styles.iconBtn}
          >
            💬
          </button>
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
      <ChatDrawer />
    </div>
  );
}

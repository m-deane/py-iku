import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { ThemeToggle } from "./ThemeToggle";
import { SettingsDrawer } from "../features/settings/SettingsDrawer";
import { useUiStore } from "../state/uiStore";
import styles from "./AppLayout.module.css";

export interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps): JSX.Element {
  const openSettings = useUiStore((s) => s.openSettingsDrawer);

  return (
    <div className={styles.shell}>
      <header className={styles.header}>
        <Link to="/" className={styles.logo}>
          <span className={styles.logoMark} aria-hidden>
            ◆
          </span>
          <span>py-iku-studio</span>
        </Link>
        <nav className={styles.nav} aria-label="Primary">
          <Link to="/convert">Convert</Link>
          <Link to="/catalog">Catalog</Link>
          <Link to="/snippets">Snippets</Link>
          <Link to="/diff">Diff</Link>
          <Link to="/audit">Audit</Link>
        </nav>
        <div className={styles.headerActions}>
          <ThemeToggle />
          <button
            type="button"
            data-testid="settings-open-trigger"
            onClick={openSettings}
            aria-label="Open settings"
            className={styles.iconBtn}
            style={{
              background: "transparent",
              cursor: "pointer",
              fontSize: "1rem",
            }}
          >
            ⚙
          </button>
        </div>
      </header>
      <main className={styles.main}>{children}</main>
      <SettingsDrawer />
    </div>
  );
}

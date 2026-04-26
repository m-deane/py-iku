import { Link } from "react-router-dom";
import type { ReactNode } from "react";
import { ThemeToggle } from "./ThemeToggle";
import styles from "./AppLayout.module.css";

export interface AppLayoutProps {
  children: ReactNode;
}

export function AppLayout({ children }: AppLayoutProps): JSX.Element {
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
          <Link to="/diff">Diff</Link>
          <Link to="/audit">Audit</Link>
        </nav>
        <div className={styles.headerActions}>
          <ThemeToggle />
          <Link to="/settings" aria-label="Settings" className={styles.iconBtn}>
            ⚙
          </Link>
        </div>
      </header>
      <main className={styles.main}>{children}</main>
    </div>
  );
}

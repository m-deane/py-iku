import { Fragment } from "react";
import { Link } from "react-router-dom";
import styles from "./Breadcrumb.module.css";

/**
 * Single crumb in the trail. `to` makes it a link; omit for the leaf.
 */
export interface BreadcrumbItem {
  label: string;
  to?: string;
}

export interface BreadcrumbProps {
  items: BreadcrumbItem[];
  /** Optional slot rendered on the right (e.g. status pill, action). */
  trailing?: React.ReactNode;
}

/**
 * Thin horizontal sub-header that lives under the top app bar and above the
 * page content. The IA review called for breadcrumbs of the form
 * `Lifecycle / Diff`, `Build / Convert`, etc.; this is the surface that
 * renders them.
 *
 * Accessibility:
 *   - <nav aria-label="Breadcrumb"> wrapper (per the WAI-ARIA breadcrumb
 *     pattern).
 *   - Ordered list semantics via <ol>.
 *   - Final item gets `aria-current="page"`.
 *   - Separators are aria-hidden so screen readers read just the labels.
 */
export function Breadcrumb({ items, trailing }: BreadcrumbProps): JSX.Element | null {
  if (items.length === 0) return null;

  return (
    <nav aria-label="Breadcrumb" className={styles.bar}>
      <ol className={styles.list}>
        {items.map((item, idx) => {
          const isLast = idx === items.length - 1;
          return (
            <Fragment key={`${item.label}-${idx}`}>
              <li
                className={`${styles.crumb} ${
                  isLast ? styles.leaf : styles.cluster
                }`}
                aria-current={isLast ? "page" : undefined}
              >
                {item.to && !isLast ? (
                  <Link to={item.to} className={styles.link}>
                    {item.label}
                  </Link>
                ) : (
                  <span>{item.label}</span>
                )}
              </li>
              {!isLast ? (
                <li aria-hidden className={styles.sep}>
                  /
                </li>
              ) : null}
            </Fragment>
          );
        })}
      </ol>
      {trailing ? <div style={{ marginLeft: "auto" }}>{trailing}</div> : null}
    </nav>
  );
}

import { useNavigate } from "react-router-dom";
import {
  useRecentsStore,
  relativeTime,
  type RecentFlow,
} from "../store/recents";
import { useFlowStore } from "../state/flowStore";
import styles from "./RecentsRail.module.css";

export interface RecentsRailProps {
  /**
   * Where to navigate when an item is clicked. Defaults to /convert so
   * clicking on the home page lands the user on the editor with the source
   * pre-loaded.
   */
  navigateTo?: string;
  /** Optional label override; defaults to "Recent" / "Pinned". */
  recentsLabel?: string;
  pinnedLabel?: string;
}

/**
 * Two-section rail: Pinned (uncapped) at the top, Recent (max 10) below.
 *
 * Each entry shows: flow name, recipe count, relative timestamp.
 * Click → loads source into `flowStore.currentCode` and routes to /convert.
 * Each entry also has a small pin/unpin affordance (★ / ☆).
 *
 * Empty states render a muted hint rather than an empty section.
 */
export function RecentsRail({
  navigateTo = "/convert",
  recentsLabel = "Recent",
  pinnedLabel = "Pinned",
}: RecentsRailProps): JSX.Element {
  const recents = useRecentsStore((s) => s.recents);
  const pinned = useRecentsStore((s) => s.pinned);
  const togglePin = useRecentsStore((s) => s.togglePin);
  const isPinned = useRecentsStore((s) => s.isPinned);

  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const navigate = useNavigate();

  const onLoad = (entry: RecentFlow): void => {
    setCurrentCode(entry.source);
    navigate(navigateTo);
  };

  return (
    <aside className={styles.rail} aria-label="Flow history">
      <Section
        title={pinnedLabel}
        items={pinned}
        emptyHint="Pin a converted flow to keep it here."
        onLoad={onLoad}
        onTogglePin={togglePin}
        isPinned={() => true}
      />
      <Section
        title={recentsLabel}
        items={recents}
        emptyHint="Run a conversion to populate this list."
        onLoad={onLoad}
        onTogglePin={togglePin}
        isPinned={isPinned}
      />
    </aside>
  );
}

interface SectionProps {
  title: string;
  items: RecentFlow[];
  emptyHint: string;
  onLoad: (e: RecentFlow) => void;
  onTogglePin: (id: string) => void;
  isPinned: (id: string) => boolean;
}

function Section({
  title,
  items,
  emptyHint,
  onLoad,
  onTogglePin,
  isPinned,
}: SectionProps): JSX.Element {
  return (
    <section className={styles.section} aria-labelledby={`rail-${title}`}>
      <h3 className={styles.sectionHeader} id={`rail-${title}`}>
        {title}
      </h3>
      {items.length === 0 ? (
        <p className={styles.empty}>{emptyHint}</p>
      ) : (
        items.map((entry) => {
          const pinned = isPinned(entry.id);
          return (
            <button
              key={entry.id}
              type="button"
              className={styles.item}
              onClick={() => onLoad(entry)}
              aria-label={`Load ${entry.name}`}
            >
              <div className={styles.itemTop}>
                <span className={styles.itemName}>{entry.name}</span>
                <span
                  role="button"
                  tabIndex={0}
                  className={`${styles.pinBtn} ${pinned ? styles.pinned : ""}`}
                  aria-label={pinned ? `Unpin ${entry.name}` : `Pin ${entry.name}`}
                  aria-pressed={pinned}
                  onClick={(e) => {
                    e.stopPropagation();
                    onTogglePin(entry.id);
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      e.stopPropagation();
                      onTogglePin(entry.id);
                    }
                  }}
                >
                  {pinned ? "★" : "☆"}
                </span>
              </div>
              <div className={styles.itemMeta}>
                <span>
                  {entry.recipeCount}{" "}
                  {entry.recipeCount === 1 ? "recipe" : "recipes"}
                </span>
                <span aria-hidden>·</span>
                <span>{relativeTime(entry.timestamp)}</span>
              </div>
            </button>
          );
        })
      )}
    </section>
  );
}

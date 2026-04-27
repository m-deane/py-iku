import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
} from "react";
import { createPortal } from "react-dom";
import { useNavigate } from "react-router-dom";
import Fuse from "fuse.js";
import { useCommandPaletteStore } from "../../store/commandPalette";
import { useCommandPaletteSources } from "./useCommandPaletteSources";
import type { PaletteItem, PaletteSection } from "./types";
import styles from "./CommandPalette.module.css";

/**
 * Static order in which sections render. "Recently used" is conditionally
 * prepended when the search query is empty and the user has invoked at
 * least one item before.
 */
const SECTION_ORDER: PaletteSection[] = [
  "Recipes",
  "Datasets",
  "Snippets",
  "Audit events",
  "Actions",
  "Help",
];

const PER_SECTION_CAP = 5;

interface SectionGroup {
  section: PaletteSection;
  items: PaletteItem[];
}

function focusableElementsIn(container: HTMLElement): HTMLElement[] {
  return Array.from(
    container.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), textarea:not([disabled]), input:not([disabled]), select:not([disabled]), [tabindex]:not([tabindex="-1"])',
    ),
  );
}

/**
 * Group items by section, applying the per-section top-N cap. Sections
 * that have zero items are dropped — the palette never renders an empty
 * section header.
 */
function groupBySection(
  items: PaletteItem[],
  order: PaletteSection[],
): SectionGroup[] {
  const buckets = new Map<PaletteSection, PaletteItem[]>();
  for (const it of items) {
    const arr = buckets.get(it.section) ?? [];
    if (arr.length < PER_SECTION_CAP) arr.push(it);
    buckets.set(it.section, arr);
  }
  const groups: SectionGroup[] = [];
  for (const section of order) {
    const arr = buckets.get(section);
    if (arr && arr.length > 0) {
      groups.push({ section, items: arr });
    }
  }
  return groups;
}

interface KeyboardShortcutsHelpProps {
  onClose: () => void;
}

function KeyboardShortcutsHelp(props: KeyboardShortcutsHelpProps): JSX.Element {
  const { onClose } = props;
  useEffect(() => {
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") {
        e.preventDefault();
        onClose();
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [onClose]);

  const rows: Array<{ keys: string[]; desc: string }> = [
    { keys: ["⌘", "K"], desc: "Open command palette" },
    { keys: ["⌘", "Enter"], desc: "Convert (on Convert page)" },
    { keys: ["⌘", "S"], desc: "Export current flow" },
    { keys: ["↑", "↓"], desc: "Navigate palette items" },
    { keys: ["Enter"], desc: "Invoke highlighted item" },
    { keys: ["Esc"], desc: "Close palette / dialogs" },
  ];

  return (
    <div
      className={styles.backdrop}
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className={styles.helpDialog}
        role="dialog"
        aria-modal="true"
        aria-label="Keyboard shortcuts"
      >
        <div className={styles.helpHeader}>
          <h2 className={styles.helpTitle}>Keyboard shortcuts</h2>
          <button
            type="button"
            className={styles.helpClose}
            onClick={onClose}
            aria-label="Close shortcuts"
          >
            ×
          </button>
        </div>
        <dl className={styles.helpList}>
          {rows.map((row) => (
            <div key={row.desc} className={styles.helpRow}>
              <dt className={styles.helpKey}>
                {row.keys.map((k) => (
                  <kbd key={k} className={styles.kbd}>
                    {k}
                  </kbd>
                ))}
              </dt>
              <dd className={styles.helpDesc}>{row.desc}</dd>
            </div>
          ))}
        </dl>
      </div>
    </div>
  );
}

export interface CommandPaletteProps {
  /** Test seam — render in-place rather than portalling to body. */
  inlineForTesting?: boolean;
}

export function CommandPalette(props: CommandPaletteProps): JSX.Element | null {
  const isOpen = useCommandPaletteStore((s) => s.isOpen);
  const close = useCommandPaletteStore((s) => s.close);
  const recent = useCommandPaletteStore((s) => s.recent);
  const pushRecent = useCommandPaletteStore((s) => s.pushRecent);

  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [showShortcuts, setShowShortcuts] = useState(false);

  const dialogRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const itemRefs = useRef<Array<HTMLButtonElement | null>>([]);

  const handleClose = useCallback(() => {
    close();
  }, [close]);

  const openShortcutsHelp = useCallback(() => {
    setShowShortcuts(true);
  }, []);

  const { items, loading } = useCommandPaletteSources({
    enabled: isOpen,
    navigate,
    onClose: handleClose,
    onOpenShortcutsHelp: openShortcutsHelp,
  });

  // Build a Fuse index whenever the source list changes. Threshold 0.4 is
  // forgiving enough that "filt" matches "Filter on Value" but tight enough
  // that single-character queries don't return everything.
  const fuse = useMemo(
    () =>
      new Fuse(items, {
        threshold: 0.4,
        ignoreLocation: true,
        keys: [
          { name: "primary", weight: 0.5 },
          { name: "secondary", weight: 0.2 },
          { name: "keywords", weight: 0.2 },
          { name: "section", weight: 0.1 },
        ],
      }),
    [items],
  );

  // ------------------------------------------------------------------
  // Filtered + grouped result list
  // ------------------------------------------------------------------
  const groups: SectionGroup[] = useMemo(() => {
    const trimmed = query.trim();
    if (!trimmed) {
      // No query → recently-used at top, then full sections (each capped
      // at PER_SECTION_CAP).
      const baseGroups = groupBySection(items, SECTION_ORDER);
      if (recent.length === 0) return baseGroups;
      const recentItems: PaletteItem[] = recent
        // Only surface recents whose underlying item still resolves; if
        // a snippet/recipe disappears, drop the row silently.
        .map((r) => {
          const live = items.find((i) => i.id === r.id);
          if (live) return live;
          return null;
        })
        .filter((x): x is PaletteItem => x !== null)
        .slice(0, PER_SECTION_CAP);
      if (recentItems.length === 0) return baseGroups;
      return [
        { section: "Recently used" as PaletteSection, items: recentItems },
        ...baseGroups,
      ];
    }
    const matches = fuse.search(trimmed).map((r) => r.item);
    return groupBySection(matches, SECTION_ORDER);
  }, [query, items, fuse, recent]);

  // Flatten for keyboard navigation. Order matches render order so
  // index math is identical between rendering and key handling.
  const flat = useMemo(() => {
    const out: PaletteItem[] = [];
    for (const g of groups) out.push(...g.items);
    return out;
  }, [groups]);

  // Reset selection on query change.
  useEffect(() => {
    setActiveIndex(0);
  }, [query, flat.length]);

  // Capture and restore focus when the dialog opens/closes.
  useEffect(() => {
    if (!isOpen) return;
    triggerRef.current = (document.activeElement as HTMLElement | null) ?? null;
    setQuery("");
    setActiveIndex(0);
    setShowShortcuts(false);
    // Defer focus until after portal renders.
    const t = setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => {
      clearTimeout(t);
      // Restore focus to the previously focused element (the keyboard
      // shortcut handler doesn't have a literal "trigger" — fall back to
      // body if the previous element is gone).
      const prev = triggerRef.current;
      if (prev && document.body.contains(prev)) {
        prev.focus();
      }
    };
  }, [isOpen]);

  // Scroll active item into view. Guarded for jsdom which doesn't implement
  // scrollIntoView on HTMLElement.
  useEffect(() => {
    const el = itemRefs.current[activeIndex];
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  // Keyboard handling on the dialog.
  const onKeyDown = useCallback(
    (e: React.KeyboardEvent<HTMLDivElement>): void => {
      if (e.key === "Escape") {
        e.preventDefault();
        e.stopPropagation();
        if (showShortcuts) {
          setShowShortcuts(false);
          return;
        }
        handleClose();
        return;
      }
      if (showShortcuts) return;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        if (flat.length === 0) return;
        setActiveIndex((i) => (i + 1) % flat.length);
        return;
      }
      if (e.key === "ArrowUp") {
        e.preventDefault();
        if (flat.length === 0) return;
        setActiveIndex((i) => (i - 1 + flat.length) % flat.length);
        return;
      }
      if (e.key === "Home") {
        e.preventDefault();
        setActiveIndex(0);
        return;
      }
      if (e.key === "End") {
        e.preventDefault();
        setActiveIndex(Math.max(0, flat.length - 1));
        return;
      }
      if (e.key === "Enter") {
        e.preventDefault();
        const target = flat[activeIndex];
        if (target) {
          pushRecent({
            id: target.id,
            section: target.section,
            primary: target.primary,
            secondary: target.secondary,
            icon: target.icon,
          });
          target.invoke();
        }
        return;
      }
      if (e.key === "Tab") {
        // Focus trap: cycle tab focus inside the dialog.
        const root = dialogRef.current;
        if (!root) return;
        const focusables = focusableElementsIn(root);
        if (focusables.length === 0) return;
        const first = focusables[0];
        const last = focusables[focusables.length - 1];
        const active = document.activeElement as HTMLElement | null;
        if (e.shiftKey) {
          if (active === first || !root.contains(active)) {
            e.preventDefault();
            last.focus();
          }
        } else {
          if (active === last) {
            e.preventDefault();
            first.focus();
          }
        }
      }
    },
    [flat, activeIndex, handleClose, pushRecent, showShortcuts],
  );

  // Track index → ref so arrow-key navigation can scroll into view.
  itemRefs.current = new Array(flat.length).fill(null);

  if (!isOpen) return null;

  const dialogTree = (
    <div
      className={styles.backdrop}
      data-testid="command-palette-backdrop"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget) handleClose();
      }}
      onKeyDown={onKeyDown}
    >
      <div
        className={styles.dialog}
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        data-testid="command-palette"
      >
        <div className={styles.searchRow}>
          <span className={styles.searchIcon} aria-hidden>
            ⌕
          </span>
          <input
            ref={inputRef}
            type="search"
            className={styles.searchInput}
            placeholder="Search recipes, datasets, snippets, or actions… (Cmd+K)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            aria-label="Search palette"
            aria-controls="command-palette-results"
            aria-activedescendant={
              flat[activeIndex]?.id
                ? `cmdk-item-${flat[activeIndex].id}`
                : undefined
            }
            autoComplete="off"
            spellCheck={false}
            data-testid="command-palette-input"
          />
          <span className={styles.kbdHint} aria-hidden>
            <kbd className={styles.kbd}>Esc</kbd>
          </span>
        </div>

        <div
          id="command-palette-results"
          className={styles.results}
          role="listbox"
          aria-label="Palette results"
        >
          {loading && groups.length === 0 ? (
            <div className={styles.empty}>Loading…</div>
          ) : groups.length === 0 ? (
            <div className={styles.empty}>
              No matches for <strong>"{query}"</strong>
            </div>
          ) : (
            (() => {
              let runningIndex = -1;
              return groups.map((g) => (
                <div
                  key={g.section}
                  className={styles.section}
                  data-testid={`command-palette-section-${g.section.toLowerCase().replace(/\s+/g, "-")}`}
                >
                  <div className={styles.sectionHeader} role="presentation">
                    {g.section}
                  </div>
                  <ul className={styles.list} role="presentation">
                    {g.items.map((item) => {
                      runningIndex += 1;
                      const idx = runningIndex;
                      const active = idx === activeIndex;
                      return (
                        <li key={item.id} role="presentation">
                          <button
                            type="button"
                            id={`cmdk-item-${item.id}`}
                            ref={(el) => {
                              itemRefs.current[idx] = el;
                            }}
                            role="option"
                            aria-selected={active}
                            tabIndex={-1}
                            className={`${styles.item} ${active ? styles.itemActive : ""}`.trim()}
                            data-testid={`command-palette-item-${item.id}`}
                            onMouseMove={() => setActiveIndex(idx)}
                            onClick={() => {
                              pushRecent({
                                id: item.id,
                                section: item.section,
                                primary: item.primary,
                                secondary: item.secondary,
                                icon: item.icon,
                              });
                              item.invoke();
                            }}
                          >
                            <span className={styles.itemIcon} aria-hidden>
                              {item.icon ?? "·"}
                            </span>
                            <span className={styles.itemBody}>
                              <span className={styles.itemPrimary}>
                                {item.primary}
                              </span>
                              {item.secondary ? (
                                <span className={styles.itemSecondary}>
                                  {item.secondary}
                                </span>
                              ) : null}
                            </span>
                            {active ? (
                              <span className={styles.itemEnter} aria-hidden>
                                <kbd className={styles.kbd}>↵</kbd>
                              </span>
                            ) : null}
                          </button>
                        </li>
                      );
                    })}
                  </ul>
                </div>
              ));
            })()
          )}
        </div>

        <div className={styles.footer} aria-hidden>
          <span className={styles.footerHint}>
            <kbd className={styles.kbd}>↑</kbd>
            <kbd className={styles.kbd}>↓</kbd>
            navigate
          </span>
          <span className={styles.footerHint}>
            <kbd className={styles.kbd}>↵</kbd>
            select
          </span>
          <span className={styles.footerHint}>
            <kbd className={styles.kbd}>Esc</kbd>
            close
          </span>
          <span className={styles.footerHint} style={{ marginLeft: "auto" }}>
            <kbd className={styles.kbd}>⌘</kbd>
            <kbd className={styles.kbd}>K</kbd>
            toggle
          </span>
        </div>
      </div>

      {showShortcuts ? (
        <KeyboardShortcutsHelp onClose={() => setShowShortcuts(false)} />
      ) : null}
    </div>
  );

  if (props.inlineForTesting || typeof document === "undefined") {
    return dialogTree;
  }
  return createPortal(dialogTree, document.body);
}

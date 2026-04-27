import { useRef, useState } from "react";
import { useTabsStore, MAX_TABS, type WorkspaceTab } from "../store/tabs";

/**
 * Horizontal tab strip (Sprint 4 — power user feature 1).
 *
 * Renders the workspace tabs across the top of the editor pane. Behaviours:
 *   - click a tab to activate it
 *   - drag a tab onto another to reorder (HTML5 DnD — no extra deps)
 *   - "+" button creates a new tab (disabled at MAX_TABS)
 *   - "×" on each tab closes it (last tab is replaced rather than removed —
 *     see `closeTab` in the store)
 *
 * Cmd+T / Cmd+W / Cmd+1..8 are wired globally in `useTabHotkeys` so they
 * work outside the strip itself.
 */
export interface TabStripProps {
  /** Optional test seam — bypass internal store reads. */
  tabsImpl?: WorkspaceTab[];
  activeTabIdImpl?: string;
}

export function TabStrip(props: TabStripProps): JSX.Element {
  const tabs = useTabsStore((s) => (props.tabsImpl ?? s.tabs));
  const activeTabId = useTabsStore((s) =>
    props.activeTabIdImpl ?? s.activeTabId,
  );
  const newTab = useTabsStore((s) => s.newTab);
  const closeTab = useTabsStore((s) => s.closeTab);
  const setActiveTab = useTabsStore((s) => s.setActiveTab);
  const reorderTab = useTabsStore((s) => s.reorderTab);

  const [dragIndex, setDragIndex] = useState<number | null>(null);
  const stripRef = useRef<HTMLDivElement | null>(null);

  const atMax = tabs.length >= MAX_TABS;

  return (
    <div
      ref={stripRef}
      data-testid="tab-strip"
      role="tablist"
      aria-label="Workspace tabs"
      style={{
        display: "flex",
        alignItems: "stretch",
        gap: "var(--space-1, 4px)",
        padding: "var(--space-1, 4px) var(--space-2, 8px)",
        borderBottom: "1px solid var(--border, #eaecf0)",
        background: "var(--surface-sunken, #f2f4f7)",
        overflowX: "auto",
      }}
    >
      {tabs.map((t, i) => {
        const isActive = t.id === activeTabId;
        return (
          <div
            key={t.id}
            role="tab"
            aria-selected={isActive}
            data-testid={`tab-${t.id}`}
            data-active={isActive ? "true" : "false"}
            draggable
            onDragStart={() => setDragIndex(i)}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault();
              if (dragIndex !== null && dragIndex !== i) {
                reorderTab(dragIndex, i);
              }
              setDragIndex(null);
            }}
            onClick={() => setActiveTab(t.id)}
            style={{
              display: "inline-flex",
              alignItems: "center",
              gap: "var(--space-2, 8px)",
              padding: "var(--space-1, 4px) var(--space-3, 12px)",
              borderRadius: "var(--radius-sm, 4px) var(--radius-sm, 4px) 0 0",
              border: "1px solid var(--border, #eaecf0)",
              borderBottom: isActive
                ? "1px solid var(--surface, #ffffff)"
                : "1px solid var(--border, #eaecf0)",
              background: isActive
                ? "var(--surface, #ffffff)"
                : "var(--surface-raised, #f7f8fa)",
              color: isActive ? "var(--fg, #101828)" : "var(--fg-muted, #5b6470)",
              fontSize: "var(--text-sm, 14px)",
              fontWeight: isActive ? 600 : 500,
              cursor: "pointer",
              maxWidth: 220,
              minWidth: 80,
              userSelect: "none",
            }}
          >
            <span
              style={{
                whiteSpace: "nowrap",
                overflow: "hidden",
                textOverflow: "ellipsis",
                flex: 1,
              }}
            >
              {t.title}
            </span>
            <button
              type="button"
              data-testid={`tab-close-${t.id}`}
              aria-label={`Close ${t.title}`}
              onClick={(e) => {
                e.stopPropagation();
                closeTab(t.id);
              }}
              style={{
                background: "transparent",
                border: 0,
                color: "inherit",
                opacity: 0.7,
                cursor: "pointer",
                fontSize: "var(--text-xs, 12px)",
                padding: 0,
                lineHeight: 1,
              }}
            >
              ×
            </button>
          </div>
        );
      })}
      <button
        type="button"
        data-testid="tab-new"
        aria-label="New tab"
        title={atMax ? `Maximum ${MAX_TABS} tabs` : "New tab (Cmd+T)"}
        disabled={atMax}
        onClick={() => {
          if (!atMax) newTab();
        }}
        style={{
          padding: "var(--space-1, 4px) var(--space-2, 8px)",
          background: "transparent",
          border: "1px dashed var(--border, #eaecf0)",
          color: "var(--fg-muted, #5b6470)",
          borderRadius: "var(--radius-sm, 4px)",
          cursor: atMax ? "not-allowed" : "pointer",
          opacity: atMax ? 0.4 : 1,
          fontSize: "var(--text-sm, 14px)",
        }}
      >
        +
      </button>
    </div>
  );
}

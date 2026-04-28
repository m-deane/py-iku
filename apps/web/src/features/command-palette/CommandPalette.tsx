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
import { useFlowStore } from "../../state/flowStore";
import { useSettingsStore } from "../../state/settingsStore";
import {
  useCommandPaletteStore,
  type ArgStepValue,
} from "../../store/commandPalette";
import { useCommandPaletteSources } from "./useCommandPaletteSources";
import { PALETTE_TIPS, TIP_ROTATE_MS } from "./tips";
import type {
  ArgChoice,
  ArgSpec,
  PaletteItem,
  PaletteSection,
} from "./types";
import styles from "./CommandPalette.module.css";

/**
 * Static order in which sections render. "Recently used" and "Pinned" are
 * conditionally prepended when the search query is empty and the user has
 * data for them. Cmd+1..6 indexes against the visible (non-empty) sections,
 * not this static list.
 */
const SECTION_ORDER: PaletteSection[] = [
  "Recipes",
  "Datasets",
  "Actions",
  "Help",
];

const SECTION_ICONS: Record<PaletteSection, string> = {
  Pinned: "★",
  Recipes: "⊞",
  Datasets: "⌬",
  Actions: "▶",
  Help: "?",
};

const PER_SECTION_CAP = 5;
const PREVIEW_BREAKPOINT_PX = 900;
const SCALE_ANIMATION_MS = 150;

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
 * Group items by section, applying the per-section top-N cap. Sections that
 * have zero items are dropped — the palette never renders an empty header.
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

/** Resolve the next ArgSpec, honouring the optional `when` gate. */
function nextArgIndex(
  args: ArgSpec[],
  collected: unknown[],
  startFrom: number,
): number {
  for (let i = startFrom; i < args.length; i += 1) {
    const spec = args[i];
    if (!spec.when || spec.when(collected)) {
      return i;
    }
  }
  return args.length;
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

  // Tab hotkey bindings adapt to the host context — Cmd+T / Cmd+W in
  // standalone-PWA / Electron, Alt+T / Alt+W in vanilla browser tabs (where
  // Cmd+T / Cmd+W are reserved by the chrome). We surface BOTH bindings here
  // so users can discover whichever applies to their environment.
  const rows: Array<{ keys: string[]; desc: string }> = [
    { keys: ["⌘", "K"], desc: "Open / close command palette" },
    { keys: ["⌘", "Enter"], desc: "Convert (on Convert page)" },
    { keys: ["⌘", "S"], desc: "Save / export current flow" },
    { keys: ["⌘", "/"], desc: "Inline search" },
    { keys: ["⌘", "P"], desc: "Pin highlighted item" },
    { keys: ["⌘", "1..6"], desc: "Jump to section" },
    { keys: ["⌘", "1..8"], desc: "Switch tab (multi-tab workspace)" },
    {
      keys: ["⌥", "T"],
      desc: "New tab (browser); ⌘+T in standalone PWA / Electron",
    },
    {
      keys: ["⌥", "W"],
      desc: "Close tab (browser); ⌘+W in standalone PWA / Electron",
    },
    { keys: ["↑", "↓"], desc: "Move selection" },
    { keys: ["↵"], desc: "Invoke / next step" },
    { keys: ["⇥"], desc: "Cycle focus inside palette" },
    { keys: ["⇧", "⇥"], desc: "Reverse cycle" },
    { keys: ["Esc"], desc: "Back / close" },
    { keys: ["?"], desc: "Show this dialog" },
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
        data-testid="command-palette-shortcuts-modal"
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

interface ReleaseNotesModalProps {
  onClose: () => void;
}

interface ReleaseNotesPayload {
  api_version: string;
  py_iku_version: string;
  commit: string | null;
  commit_message: string;
}

function ReleaseNotesModal(props: ReleaseNotesModalProps): JSX.Element {
  const { onClose } = props;
  const [data, setData] = useState<ReleaseNotesPayload | null>(null);
  const [error, setError] = useState<string | null>(null);
  const apiBaseUrl = useSettingsStore((s) => s.apiBaseUrl);

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

  // Lazy-fetch the version payload when the modal mounts.
  useEffect(() => {
    let cancelled = false;
    const url = `${apiBaseUrl.replace(/\/$/, "")}/api/version`;
    void (async () => {
      try {
        const resp = await fetch(url, { headers: { Accept: "application/json" } });
        if (!resp.ok) {
          throw new Error(`HTTP ${resp.status}`);
        }
        const json = (await resp.json()) as ReleaseNotesPayload;
        if (!cancelled) setData(json);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [apiBaseUrl]);

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
        aria-label="Release notes"
        data-testid="command-palette-release-notes-modal"
      >
        <div className={styles.helpHeader}>
          <h2 className={styles.helpTitle}>Release notes</h2>
          <button
            type="button"
            className={styles.helpClose}
            onClick={onClose}
            aria-label="Close release notes"
          >
            ×
          </button>
        </div>
        {error ? (
          <p className={styles.helpDesc} data-testid="release-notes-error">
            Could not load release notes ({error}). Make sure the API is reachable.
          </p>
        ) : !data ? (
          <p className={styles.helpDesc}>Loading…</p>
        ) : (
          <div data-testid="release-notes-body">
            <p className={styles.releaseMeta}>
              <strong>API</strong> {data.api_version}{" "}
              <span aria-hidden>·</span> <strong>py-iku</strong>{" "}
              {data.py_iku_version}
              {data.commit ? (
                <>
                  {" "}
                  <span aria-hidden>·</span>{" "}
                  <code className={styles.commitSha}>{data.commit}</code>
                </>
              ) : null}
            </p>
            <pre className={styles.releaseBody}>{data.commit_message}</pre>
          </div>
        )}
      </div>
    </div>
  );
}

export interface CommandPaletteProps {
  /** Test seam — render in-place rather than portalling to body. */
  inlineForTesting?: boolean;
  /**
   * Test seam — controls whether the inline preview pane renders. Defaults
   * to ``window.innerWidth >= 900``. Tests force it on so jsdom doesn't
   * default to the narrow layout (innerWidth defaults to 1024 in jsdom but
   * we set this explicit prop to remove any ambiguity).
   */
  forcePreviewVisible?: boolean;
}

export function CommandPalette(props: CommandPaletteProps): JSX.Element | null {
  const isOpen = useCommandPaletteStore((s) => s.isOpen);
  const close = useCommandPaletteStore((s) => s.close);
  const pinnedIds = useCommandPaletteStore((s) => s.pinnedIds);
  const togglePin = useCommandPaletteStore((s) => s.togglePin);
  const currentArgsItemId = useCommandPaletteStore((s) => s.currentArgsItemId);
  const currentArgs = useCommandPaletteStore((s) => s.currentArgs);
  const beginArgs = useCommandPaletteStore((s) => s.beginArgs);
  const pushArg = useCommandPaletteStore((s) => s.pushArg);
  const popArg = useCommandPaletteStore((s) => s.popArg);
  const clearArgs = useCommandPaletteStore((s) => s.clearArgs);

  const setMode = useFlowStore((s) => s.setConversionMode);
  const setProvider = useSettingsStore((s) => s.setProvider);

  const navigate = useNavigate();
  const [query, setQuery] = useState("");
  const [activeIndex, setActiveIndex] = useState(0);
  const [showShortcuts, setShowShortcuts] = useState(false);
  const [showReleaseNotes, setShowReleaseNotes] = useState(false);
  const [tipIndex, setTipIndex] = useState(0);
  const [hasUserActivity, setHasUserActivity] = useState(false);
  const [animatingId, setAnimatingId] = useState<string | null>(null);
  const [previewVisible, setPreviewVisible] = useState<boolean>(() => {
    if (props.forcePreviewVisible !== undefined) return props.forcePreviewVisible;
    if (typeof window === "undefined") return true;
    return window.innerWidth >= PREVIEW_BREAKPOINT_PX;
  });

  const dialogRef = useRef<HTMLDivElement | null>(null);
  const inputRef = useRef<HTMLInputElement | null>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const itemRefs = useRef<Array<HTMLButtonElement | null>>([]);
  // Async-loaded choices for arg steps that supply a function.
  const [resolvedChoices, setResolvedChoices] = useState<ArgChoice[] | null>(
    null,
  );

  const handleClose = useCallback(() => {
    close();
  }, [close]);

  const openShortcutsHelp = useCallback(() => {
    setShowShortcuts(true);
  }, []);

  const openReleaseNotes = useCallback(() => {
    setShowReleaseNotes(true);
  }, []);

  // Bridge for the multi-step Convert action.
  const onRunConvert = useCallback(
    (mode: "rule" | "llm", provider?: "anthropic" | "openai") => {
      setMode(mode);
      if (provider) setProvider(provider);
      navigate("/convert");
    },
    [setMode, setProvider, navigate],
  );

  const { items, loading } = useCommandPaletteSources({
    enabled: isOpen,
    navigate,
    onClose: handleClose,
    onOpenShortcutsHelp: openShortcutsHelp,
    onOpenReleaseNotes: openReleaseNotes,
    onRunConvert,
  });

  // Resolve the active item being walked through (if any). When in arg-
  // collection mode, we lock the result list to the choices for the current
  // step instead of the global item list.
  const activeArgItem = useMemo<PaletteItem | null>(() => {
    if (!currentArgsItemId) return null;
    return items.find((i) => i.id === currentArgsItemId) ?? null;
  }, [currentArgsItemId, items]);

  const argsSpec = activeArgItem?.args ?? null;
  const collectedValues = useMemo(
    () => currentArgs.map((c) => c.value),
    [currentArgs],
  );
  const currentStepIndex = argsSpec
    ? nextArgIndex(argsSpec, collectedValues, currentArgs.length)
    : -1;
  const currentStep =
    argsSpec && currentStepIndex < argsSpec.length
      ? argsSpec[currentStepIndex]
      : null;

  // Resolve choices for the current step (sync or async).
  useEffect(() => {
    if (!currentStep) {
      setResolvedChoices(null);
      return;
    }
    if (Array.isArray(currentStep.choices)) {
      setResolvedChoices(currentStep.choices);
      return;
    }
    let cancelled = false;
    // Narrow once for TS: ``Array.isArray`` excludes the array branch above.
    const fn = currentStep.choices as () =>
      | ArgChoice[]
      | Promise<ArgChoice[]>;
    void (async () => {
      const result = await fn();
      if (!cancelled) setResolvedChoices(result);
    })();
    return () => {
      cancelled = true;
    };
  }, [currentStep]);

  // Filter the result list based on whether we're in arg-collection mode.
  const filteredItems = useMemo<PaletteItem[]>(() => {
    if (currentStep && resolvedChoices) {
      // Wrap each ArgChoice as a synthetic PaletteItem so the existing
      // render path works without branching.
      return resolvedChoices.map<PaletteItem>((c) => ({
        id: `arg:${currentStep.key}:${c.value}`,
        section: "Actions" as PaletteSection,
        primary: c.label,
        secondary: c.secondary,
        icon: "▷",
        keywords: [c.label, String(c.value), c.description ?? ""],
        description: c.description,
        invoke: () => {
          if (!activeArgItem || !argsSpec) return;
          // Push the value, advance the step, and either continue or run.
          const stepValue: ArgStepValue = {
            key: currentStep.key,
            label: currentStep.label,
            value: c.value,
            display: c.label,
          };
          const nextCollected = [...collectedValues, c.value];
          const next = nextArgIndex(
            argsSpec,
            nextCollected,
            currentStepIndex + 1,
          );
          pushArg(stepValue);
          if (next >= argsSpec.length) {
            // All steps complete — run the action.
            activeArgItem.invokeWithArgs?.(nextCollected);
            clearArgs();
          }
        },
      }));
    }
    return items;
  }, [
    items,
    currentStep,
    resolvedChoices,
    activeArgItem,
    argsSpec,
    collectedValues,
    currentStepIndex,
    pushArg,
    clearArgs,
  ]);

  // Build a Fuse index whenever the source list changes.
  const fuse = useMemo(
    () =>
      new Fuse(filteredItems, {
        threshold: 0.4,
        ignoreLocation: true,
        keys: [
          { name: "primary", weight: 0.5 },
          { name: "secondary", weight: 0.2 },
          { name: "keywords", weight: 0.2 },
          { name: "section", weight: 0.1 },
        ],
      }),
    [filteredItems],
  );

  // Pinned section: items resolve from the live list by id.
  const pinnedItems = useMemo<PaletteItem[]>(() => {
    if (currentStep) return [];
    if (pinnedIds.length === 0) return [];
    const out: PaletteItem[] = [];
    for (const id of pinnedIds) {
      const live = items.find((i) => i.id === id);
      if (live) {
        out.push({
          ...live,
          // Re-bucket into the Pinned section so groupBySection picks it up.
          section: "Pinned" as PaletteSection,
        });
      }
    }
    return out.slice(0, PER_SECTION_CAP);
  }, [pinnedIds, items, currentStep]);

  // Filtered + grouped result list.
  const groups: SectionGroup[] = useMemo(() => {
    const trimmed = query.trim();

    // In arg-collection mode the only section is the synthetic step list.
    if (currentStep) {
      if (filteredItems.length === 0) return [];
      const matches = trimmed
        ? fuse.search(trimmed).map((r) => r.item)
        : filteredItems;
      return [
        {
          section: "Actions" as PaletteSection,
          items: matches.slice(0, PER_SECTION_CAP),
        },
      ];
    }

    if (!trimmed) {
      const baseGroups = groupBySection(filteredItems, SECTION_ORDER);
      const prefix: SectionGroup[] = [];
      // Recently used (above Pinned per spec? — spec says Pinned above
      // Recently used; honour that ordering for the docked layout).
      if (pinnedItems.length > 0) {
        prefix.push({
          section: "Pinned" as PaletteSection,
          items: pinnedItems,
        });
      }
      return [...prefix, ...baseGroups];
    }

    const matches = fuse.search(trimmed).map((r) => r.item);
    return groupBySection(matches, SECTION_ORDER);
  }, [
    query,
    filteredItems,
    fuse,
    pinnedItems,
    currentStep,
  ]);

  // Flatten for keyboard navigation.
  const flat = useMemo(() => {
    const out: PaletteItem[] = [];
    for (const g of groups) out.push(...g.items);
    return out;
  }, [groups]);

  // Match-count summary line ("3 results across 2 sections").
  const matchSummary = useMemo<string | null>(() => {
    const trimmed = query.trim();
    if (!trimmed) return null;
    if (currentStep) return null;
    const total = groups.reduce((acc, g) => acc + g.items.length, 0);
    return `${total} result${total === 1 ? "" : "s"} across ${groups.length} section${groups.length === 1 ? "" : "s"}`;
  }, [query, groups, currentStep]);

  // Reset selection on query / step change.
  useEffect(() => {
    setActiveIndex(0);
  }, [query, flat.length, currentStepIndex]);

  // Capture and restore focus when the dialog opens/closes.
  useEffect(() => {
    if (!isOpen) return;
    triggerRef.current = (document.activeElement as HTMLElement | null) ?? null;
    setQuery("");
    setActiveIndex(0);
    setShowShortcuts(false);
    setShowReleaseNotes(false);
    setHasUserActivity(false);
    clearArgs();
    const t = setTimeout(() => {
      inputRef.current?.focus();
    }, 0);
    return () => {
      clearTimeout(t);
      const prev = triggerRef.current;
      if (prev && document.body.contains(prev)) {
        prev.focus();
      }
    };
  }, [isOpen, clearArgs]);

  // Track viewport so the preview pane disappears on narrow screens.
  useEffect(() => {
    if (props.forcePreviewVisible !== undefined) return;
    if (typeof window === "undefined") return;
    const onResize = (): void => {
      setPreviewVisible(window.innerWidth >= PREVIEW_BREAKPOINT_PX);
    };
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, [props.forcePreviewVisible]);

  // Tip carousel — rotates every TIP_ROTATE_MS ms while the input is empty
  // and the user has not interacted recently.
  useEffect(() => {
    if (!isOpen) return;
    if (query.length > 0) return;
    if (hasUserActivity) return;
    const t = setInterval(() => {
      setTipIndex((i) => (i + 1) % PALETTE_TIPS.length);
    }, TIP_ROTATE_MS);
    return () => clearInterval(t);
  }, [isOpen, query.length, hasUserActivity]);

  // Scroll active item into view (jsdom-safe).
  useEffect(() => {
    const el = itemRefs.current[activeIndex];
    if (el && typeof el.scrollIntoView === "function") {
      el.scrollIntoView({ block: "nearest" });
    }
  }, [activeIndex]);

  // Run an item: animate, then invoke.
  const runItem = useCallback(
    (item: PaletteItem) => {
      setAnimatingId(item.id);
      window.setTimeout(() => {
        setAnimatingId(null);
        // If this item declares args, enter arg-collection mode instead of
        // calling invoke directly.
        if (item.args && item.args.length > 0 && item.invokeWithArgs) {
          beginArgs(item.id);
          setQuery("");
          return;
        }
        item.invoke();
      }, SCALE_ANIMATION_MS);
    },
    [beginArgs],
  );

  // Section-jump shortcut: focus the first item in the Nth visible section.
  const jumpToSection = useCallback(
    (sectionIndex: number) => {
      const target = groups[sectionIndex];
      if (!target) return;
      const firstItemId = target.items[0]?.id;
      if (!firstItemId) return;
      const flatIdx = flat.findIndex((it) => it.id === firstItemId);
      if (flatIdx >= 0) setActiveIndex(flatIdx);
    },
    [groups, flat],
  );

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
        if (showReleaseNotes) {
          setShowReleaseNotes(false);
          return;
        }
        // In arg-collection mode, Esc backs up one step or cancels at root.
        if (currentArgsItemId) {
          if (currentArgs.length === 0) {
            clearArgs();
          } else {
            popArg();
          }
          return;
        }
        handleClose();
        return;
      }
      if (showShortcuts || showReleaseNotes) return;

      // Cmd+P → toggle pin on highlighted item.
      if ((e.metaKey || e.ctrlKey) && (e.key === "p" || e.key === "P")) {
        e.preventDefault();
        const target = flat[activeIndex];
        if (target) togglePin(target.id);
        return;
      }

      // Cmd+1..6 → section jump.
      if ((e.metaKey || e.ctrlKey) && /^[1-6]$/.test(e.key)) {
        e.preventDefault();
        jumpToSection(Number(e.key) - 1);
        return;
      }

      // ? → keyboard shortcuts modal (when input is empty).
      if (e.key === "?" && query.length === 0) {
        e.preventDefault();
        setShowShortcuts(true);
        return;
      }

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
        if (target) runItem(target);
        return;
      }
      if (e.key === "Tab") {
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
    [
      flat,
      activeIndex,
      handleClose,
      runItem,
      showShortcuts,
      showReleaseNotes,
      currentArgsItemId,
      currentArgs.length,
      clearArgs,
      popArg,
      togglePin,
      jumpToSection,
      query,
    ],
  );

  itemRefs.current = new Array(flat.length).fill(null);

  if (!isOpen) return null;

  // Breadcrumb trail: "Convert / Rule-based" etc.
  const breadcrumbCrumbs: string[] = [];
  if (activeArgItem) {
    breadcrumbCrumbs.push(activeArgItem.primary);
    for (const v of currentArgs) {
      breadcrumbCrumbs.push(v.display);
    }
    if (currentStep) {
      breadcrumbCrumbs.push(currentStep.label);
    }
  }

  // Highlighted item + preview content.
  const highlighted = flat[activeIndex];
  const previewBody = highlighted ? renderPreview(highlighted) : null;

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
        className={`${styles.dialog} ${previewVisible ? styles.dialogWide : ""}`.trim()}
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-label="Command palette"
        data-testid="command-palette"
      >
        <div className={styles.mainColumn}>
          {breadcrumbCrumbs.length > 0 ? (
            <div
              className={styles.breadcrumb}
              data-testid="command-palette-breadcrumb"
              role="navigation"
              aria-label="Command path"
            >
              {breadcrumbCrumbs.map((c, i) => (
                <span key={`${i}-${c}`} className={styles.breadcrumbCrumb}>
                  {i > 0 ? (
                    <span className={styles.breadcrumbSep} aria-hidden>
                      /
                    </span>
                  ) : null}
                  {c}
                </span>
              ))}
            </div>
          ) : null}

          <div className={styles.searchRow}>
            <span className={styles.searchIcon} aria-hidden>
              ⌕
            </span>
            <input
              ref={inputRef}
              type="search"
              className={styles.searchInput}
              placeholder={
                currentStep?.placeholder ??
                "Search recipes, datasets, snippets, or actions… (Cmd+K)"
              }
              value={query}
              onChange={(e) => {
                setQuery(e.target.value);
                setHasUserActivity(true);
              }}
              onFocus={() => setHasUserActivity(true)}
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
            {matchSummary ? (
              <span
                className={styles.matchCount}
                data-testid="command-palette-match-count"
                aria-live="polite"
              >
                {matchSummary}
              </span>
            ) : null}
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
                    <div
                      className={styles.sectionHeader}
                      role="presentation"
                    >
                      <span
                        className={styles.sectionHeaderIcon}
                        aria-hidden
                      >
                        {SECTION_ICONS[g.section] ?? "·"}
                      </span>
                      <span>{g.section}</span>
                    </div>
                    <ul className={styles.list} role="presentation">
                      {g.items.map((item) => {
                        runningIndex += 1;
                        const idx = runningIndex;
                        const active = idx === activeIndex;
                        const isPinned = pinnedIds.includes(item.id);
                        const isAnim = animatingId === item.id;
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
                              className={`${styles.item} ${active ? styles.itemActive : ""} ${isAnim ? styles.itemAnimating : ""}`.trim()}
                              data-testid={`command-palette-item-${item.id}`}
                              onMouseMove={() => setActiveIndex(idx)}
                              onClick={() => runItem(item)}
                            >
                              <span
                                className={styles.itemIcon}
                                aria-hidden
                              >
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
                                {!previewVisible && active && item.description ? (
                                  <span
                                    className={styles.itemSummary}
                                    data-testid={`command-palette-item-summary-${item.id}`}
                                  >
                                    {item.description}
                                  </span>
                                ) : null}
                              </span>
                              <button
                                type="button"
                                className={`${styles.pinBtn} ${isPinned ? styles.pinBtnActive : ""}`.trim()}
                                aria-label={
                                  isPinned ? "Unpin item" : "Pin item"
                                }
                                aria-pressed={isPinned}
                                data-testid={`command-palette-pin-${item.id}`}
                                onClick={(ev) => {
                                  ev.stopPropagation();
                                  togglePin(item.id);
                                }}
                              >
                                {isPinned ? "★" : "☆"}
                              </button>
                              {item.args && item.args.length > 0 ? (
                                <span
                                  className={styles.itemHasArgs}
                                  aria-hidden
                                >
                                  …
                                </span>
                              ) : null}
                              {active ? (
                                <span
                                  className={styles.itemEnter}
                                  aria-hidden
                                >
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
            {query.length === 0 && !hasUserActivity ? (
              <span
                className={styles.tip}
                data-testid="command-palette-tip"
              >
                <span className={styles.tipPrefix}>Tip:</span>{" "}
                {PALETTE_TIPS[tipIndex].label}
              </span>
            ) : (
              <>
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
                  back
                </span>
                <span
                  className={styles.footerHint}
                  style={{ marginLeft: "auto" }}
                >
                  <kbd className={styles.kbd}>⌘</kbd>
                  <kbd className={styles.kbd}>K</kbd>
                  toggle
                </span>
              </>
            )}
          </div>
        </div>

        {previewVisible ? (
          <aside
            className={styles.preview}
            data-testid="command-palette-preview"
            aria-label="Result preview"
          >
            {previewBody ?? (
              <p className={styles.previewEmpty}>
                Highlight an item to preview it here.
              </p>
            )}
          </aside>
        ) : null}
      </div>

      {showShortcuts ? (
        <KeyboardShortcutsHelp onClose={() => setShowShortcuts(false)} />
      ) : null}
      {showReleaseNotes ? (
        <ReleaseNotesModal onClose={() => setShowReleaseNotes(false)} />
      ) : null}
    </div>
  );

  if (props.inlineForTesting || typeof document === "undefined") {
    return dialogTree;
  }
  return createPortal(dialogTree, document.body);
}

/**
 * Render the right-side preview pane for a highlighted item.
 *
 * Recipe → description + canonical name.
 * Dataset → connection type + column count.
 * Snippet → first 10 lines of source.
 * Action / Help → keyboard shortcut + 1-sentence what.
 */
function renderPreview(item: PaletteItem): JSX.Element {
  const sectionLabel = (
    <div className={styles.previewSection}>
      <span className={styles.previewIcon} aria-hidden>
        {SECTION_ICONS[item.section] ?? "·"}
      </span>
      {item.section}
    </div>
  );

  if (item.previewSource) {
    return (
      <div data-testid="command-palette-preview-snippet">
        {sectionLabel}
        <h3 className={styles.previewTitle}>{item.primary}</h3>
        {item.description ? (
          <p className={styles.previewDesc}>{item.description}</p>
        ) : null}
        <pre className={styles.previewCode}>{item.previewSource}</pre>
      </div>
    );
  }

  if (item.section === "Datasets" && item.previewMeta) {
    return (
      <div data-testid="command-palette-preview-dataset">
        {sectionLabel}
        <h3 className={styles.previewTitle}>{item.primary}</h3>
        <dl className={styles.previewMeta}>
          {Object.entries(item.previewMeta).map(([k, v]) => (
            <div key={k} className={styles.previewMetaRow}>
              <dt>{k}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }

  if (item.section === "Recipes" && item.previewMeta) {
    return (
      <div data-testid="command-palette-preview-recipe">
        {sectionLabel}
        <h3 className={styles.previewTitle}>{item.primary}</h3>
        {item.description ? (
          <p className={styles.previewDesc}>{item.description}</p>
        ) : null}
        <dl className={styles.previewMeta}>
          {Object.entries(item.previewMeta).map(([k, v]) => (
            <div key={k} className={styles.previewMetaRow}>
              <dt>{k}</dt>
              <dd>{String(v)}</dd>
            </div>
          ))}
        </dl>
      </div>
    );
  }

  return (
    <div data-testid="command-palette-preview-action">
      {sectionLabel}
      <h3 className={styles.previewTitle}>{item.primary}</h3>
      {item.description ? (
        <p className={styles.previewDesc}>{item.description}</p>
      ) : null}
      {item.shortcut ? (
        <p className={styles.previewShortcut}>
          <span className={styles.previewMetaLabel}>Shortcut:</span>{" "}
          <kbd className={styles.kbd}>{item.shortcut}</kbd>
        </p>
      ) : null}
    </div>
  );
}

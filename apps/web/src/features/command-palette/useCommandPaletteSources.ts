import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { NavigateFunction } from "react-router-dom";
import {
  client,
  type AuditEvent,
  type ExportFormat,
  type RecipeCatalogEntry,
} from "../../api/client";
import { useFlowStore } from "../../state/flowStore";
import { useSettingsStore } from "../../state/settingsStore";
import { SNIPPETS } from "../snippets/snippets";
import type { PaletteItem } from "./types";

const GLOSSARY_URL =
  "https://m-deane.github.io/py-iku/textbook/appendix-a-glossary/";

interface UseCommandPaletteSourcesArgs {
  /** Open state of the palette — gates the network calls. */
  enabled: boolean;
  navigate: NavigateFunction;
  onClose: () => void;
  /** Opens the static "Keyboard shortcuts" help dialog. */
  onOpenShortcutsHelp: () => void;
}

interface UseCommandPaletteSourcesResult {
  items: PaletteItem[];
  /** True while at least one source is still loading. */
  loading: boolean;
}

function triggerJsonDownload(flow: Record<string, unknown>): void {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  const blob = new Blob([JSON.stringify(flow, null, 2)], {
    type: "application/json",
  });
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    const flowName =
      (flow.flow_name as string | undefined) ?? "flow";
    anchor.download = `${flowName}.json`;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}

async function exportThroughApi(
  flow: Record<string, unknown>,
  fmt: ExportFormat,
): Promise<void> {
  const result = await client.export(fmt, flow);
  if (typeof window === "undefined" || typeof document === "undefined") return;
  const url = URL.createObjectURL(result.blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = result.filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}

function formatAuditPrimary(ev: AuditEvent): string {
  return `${ev.action} · ${ev.resource_type}`;
}

function formatAuditSecondary(ev: AuditEvent): string {
  const ts = (() => {
    try {
      return new Date(ev.ts).toLocaleString();
    } catch {
      return ev.ts;
    }
  })();
  return `${ev.actor} • ${ts}`;
}

/**
 * Pulls items from every source the palette knows about and returns a
 * single flat list. Each section is bounded internally; final ranking
 * (recency boost, fuzzy filter, top-5-per-section) happens in the palette
 * component.
 */
export function useCommandPaletteSources(
  args: UseCommandPaletteSourcesArgs,
): UseCommandPaletteSourcesResult {
  const { enabled, navigate, onClose, onOpenShortcutsHelp } = args;

  const currentFlow = useFlowStore((s) => s.currentFlow);
  const setTheme = useSettingsStore((s) => s.setTheme);
  const theme = useSettingsStore((s) => s.theme);

  const recipesQuery = useQuery<RecipeCatalogEntry[]>({
    queryKey: ["catalog", "recipes"],
    queryFn: () => client.listRecipes(),
    // Cache aggressively — catalog rarely changes within a session.
    staleTime: 5 * 60_000,
    enabled,
  });

  const auditQuery = useQuery({
    queryKey: ["audit", "palette-recent"],
    queryFn: () => client.listAuditEvents({ limit: 10 }),
    staleTime: 30_000,
    enabled,
  });

  const items: PaletteItem[] = useMemo(() => {
    const out: PaletteItem[] = [];

    // -----------------------------------------------------------------
    // Recipes (catalog) — every catalog entry becomes a palette item
    // that, when invoked, deep-links into the catalog with that recipe
    // pre-selected via the search query string.
    // -----------------------------------------------------------------
    const recipes = recipesQuery.data ?? [];
    for (const r of recipes) {
      out.push({
        id: `recipe:${r.type}`,
        section: "Recipes",
        primary: r.name,
        secondary: `${r.description.split(".")[0]} • ${r.type}`,
        icon: r.icon,
        keywords: [r.type, r.category, r.name, r.description],
        invoke: () => {
          onClose();
          navigate(`/catalog?tab=recipes&q=${encodeURIComponent(r.name)}`);
        },
      });
    }

    // -----------------------------------------------------------------
    // Datasets — pulled from the in-memory current flow. If nothing is
    // loaded we surface a single placeholder hint instead of an empty
    // section.
    // -----------------------------------------------------------------
    const flowDatasets =
      (currentFlow as { datasets?: Array<Record<string, unknown>> } | null)
        ?.datasets ?? [];
    if (flowDatasets.length === 0) {
      out.push({
        id: "dataset:empty",
        section: "Datasets",
        primary: "Convert a script first",
        secondary: "Load a flow on /convert to see its datasets here",
        icon: "▤",
        keywords: ["dataset", "no flow", "empty"],
        invoke: () => {
          onClose();
          navigate("/convert");
        },
      });
    } else {
      for (const d of flowDatasets) {
        const name = (d.name as string | undefined) ?? "(unnamed)";
        const dtype = (d.type as string | undefined) ?? "dataset";
        const conn = (d.connection_type as string | undefined) ?? "";
        out.push({
          id: `dataset:${name}`,
          section: "Datasets",
          primary: name,
          secondary: conn ? `${dtype} • ${conn}` : dtype,
          icon: "▤",
          keywords: [name, dtype, conn],
          invoke: () => {
            onClose();
            // Datasets live inside the flow viewer on /convert; just route
            // there and let the user click the node.
            navigate("/convert");
          },
        });
      }
    }

    // -----------------------------------------------------------------
    // Snippets — local static data layer, instant.
    // -----------------------------------------------------------------
    for (const s of SNIPPETS) {
      out.push({
        id: `snippet:${s.id}`,
        section: "Snippets",
        primary: s.name,
        secondary: `${s.category} • ${s.description.split(".")[0]}`,
        icon: "✎",
        keywords: [...s.tags, s.category, s.name],
        invoke: () => {
          onClose();
          navigate(`/snippets?id=${encodeURIComponent(s.id)}`);
        },
      });
    }

    // -----------------------------------------------------------------
    // Audit events (last 10) — straight passthrough.
    // -----------------------------------------------------------------
    const auditEvents = auditQuery.data?.events ?? [];
    for (const ev of auditEvents.slice(0, 10)) {
      out.push({
        id: `audit:${ev.ts}:${ev.resource_id}`,
        section: "Audit events",
        primary: formatAuditPrimary(ev),
        secondary: formatAuditSecondary(ev),
        icon: "◷",
        keywords: [ev.action, ev.actor, ev.resource_type, ev.resource_id],
        invoke: () => {
          onClose();
          navigate("/audit");
        },
      });
    }

    // -----------------------------------------------------------------
    // Actions — static, always available. Some are conditional on a
    // flow being loaded.
    // -----------------------------------------------------------------
    const hasFlow = currentFlow !== null;
    const flowAsRecord = (currentFlow as Record<string, unknown> | null) ?? null;

    const actions: PaletteItem[] = [
      {
        id: "action:convert",
        section: "Actions",
        primary: "Convert",
        secondary: "Open the editor and convert Python to a Dataiku flow",
        icon: "→",
        keywords: ["convert", "editor", "paste", "python"],
        invoke: () => {
          onClose();
          navigate("/convert");
        },
      },
      {
        id: "action:new-snippet",
        section: "Actions",
        primary: "New snippet",
        secondary: "Open the snippet gallery in create mode",
        icon: "＋",
        keywords: ["snippet", "create", "new"],
        invoke: () => {
          onClose();
          navigate("/snippets?new=true");
        },
      },
      {
        id: "action:open-diff",
        section: "Actions",
        primary: "Open Diff",
        secondary: "Compare two flows side by side",
        icon: "⇆",
        keywords: ["diff", "compare"],
        invoke: () => {
          onClose();
          navigate("/diff");
        },
      },
      {
        id: "action:open-audit",
        section: "Actions",
        primary: "Open Audit",
        secondary: "View recent flow events and changes",
        icon: "◷",
        keywords: ["audit", "log", "history"],
        invoke: () => {
          onClose();
          navigate("/audit");
        },
      },
      {
        id: "action:open-settings",
        section: "Actions",
        primary: "Open Settings",
        secondary: "Provider, model alias, theme, API base URL",
        icon: "⚙",
        keywords: ["settings", "config", "preferences"],
        invoke: () => {
          onClose();
          navigate("/settings");
        },
      },
      {
        id: "action:toggle-theme",
        section: "Actions",
        primary: "Toggle theme",
        secondary: `Switch to ${theme === "dark" ? "light" : "dark"} mode`,
        icon: theme === "dark" ? "☀" : "☾",
        keywords: ["theme", "dark", "light", "mode"],
        invoke: () => {
          onClose();
          setTheme(theme === "dark" ? "light" : "dark");
        },
      },
    ];

    if (hasFlow && flowAsRecord) {
      actions.push(
        {
          id: "action:export-json",
          section: "Actions",
          primary: "Export current flow as JSON",
          secondary: "Download the active flow as JSON",
          icon: "↓",
          keywords: ["export", "json", "download"],
          invoke: () => {
            onClose();
            triggerJsonDownload(flowAsRecord);
          },
        },
        {
          id: "action:export-pdf",
          section: "Actions",
          primary: "Export as PDF",
          secondary: "Generate a PDF render of the current flow",
          icon: "↓",
          keywords: ["export", "pdf", "download"],
          invoke: () => {
            onClose();
            void exportThroughApi(flowAsRecord, "pdf");
          },
        },
        {
          id: "action:export-png",
          section: "Actions",
          primary: "Export as PNG",
          secondary: "Generate a PNG render of the current flow",
          icon: "↓",
          keywords: ["export", "png", "download", "image"],
          invoke: () => {
            onClose();
            void exportThroughApi(flowAsRecord, "png");
          },
        },
      );
    }

    out.push(...actions);

    // -----------------------------------------------------------------
    // Help — glossary + shortcuts cheat sheet.
    // -----------------------------------------------------------------
    out.push(
      {
        id: "help:glossary",
        section: "Help",
        primary: "Open glossary",
        secondary: "py-iku textbook · Appendix A",
        icon: "?",
        keywords: ["glossary", "help", "docs", "textbook"],
        invoke: () => {
          onClose();
          if (typeof window !== "undefined") {
            window.open(GLOSSARY_URL, "_blank", "noopener,noreferrer");
          }
        },
      },
      {
        id: "help:shortcuts",
        section: "Help",
        primary: "Show keyboard shortcuts",
        secondary: "Cmd+K, Cmd+Enter, Cmd+S, Esc",
        icon: "⌘",
        keywords: ["shortcuts", "keyboard", "hotkeys", "help"],
        invoke: () => {
          onOpenShortcutsHelp();
        },
      },
    );

    return out;
  }, [
    recipesQuery.data,
    auditQuery.data,
    currentFlow,
    theme,
    setTheme,
    navigate,
    onClose,
    onOpenShortcutsHelp,
  ]);

  return {
    items,
    loading: recipesQuery.isLoading || auditQuery.isLoading,
  };
}

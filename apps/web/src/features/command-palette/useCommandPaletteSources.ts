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
import { useRecentsStore } from "../../store/recents";
import { useTabsStore, MAX_TABS } from "../../store/tabs";
import { useCopyShareUrl } from "../../components/ShareUrlButton";
import { useChatStore } from "../chat/chatStore";
import { SNIPPETS } from "../snippets/snippets";
import { TEMPLATES } from "../templates/templates-data";
import {
  buildInsertSnippet,
  GREL_FORMULAS,
} from "../grel-library/formulas-data";
import {
  buildNodeSnippet,
  LMP_NODES,
} from "../lmp-browser/lmp-data";
import type { ArgChoice, PaletteItem } from "./types";

const GLOSSARY_URL =
  "https://m-deane.github.io/py-iku/textbook/appendix-a-glossary/";

/**
 * Template choice list for the multi-step "Open template" action — built
 * from the real ``TEMPLATES`` catalog so the palette and gallery can never
 * disagree on what's available.
 */
const TEMPLATE_CHOICES: ArgChoice[] = TEMPLATES.map((t) => ({
  value: t.id,
  label: t.name,
  description: `${t.category} • ${t.verifiedRecipes.join(" → ")}`,
}));

interface UseCommandPaletteSourcesArgs {
  /** Open state of the palette — gates the network calls. */
  enabled: boolean;
  navigate: NavigateFunction;
  onClose: () => void;
  /** Opens the static "Keyboard shortcuts" help dialog. */
  onOpenShortcutsHelp: () => void;
  /** Opens the lazy-fetched "Release notes" sub-modal. */
  onOpenReleaseNotes: () => void;
  /**
   * Bridge to the convert page — invoked when the user runs the "Convert"
   * arg-driven command from the palette so the page state updates and the
   * router takes them to /convert with the chosen mode/provider applied.
   */
  onRunConvert: (mode: "rule" | "llm", provider?: "anthropic" | "openai") => void;
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
    const flowName = (flow.flow_name as string | undefined) ?? "flow";
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

function snippetPreview(code: string): string {
  return code.split(/\r?\n/).slice(0, 10).join("\n");
}

function datasetColumnCount(d: Record<string, unknown>): number {
  const schema = d.schema as Array<unknown> | undefined;
  if (Array.isArray(schema)) return schema.length;
  return 0;
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
  const {
    enabled,
    navigate,
    onClose,
    onOpenShortcutsHelp,
    onOpenReleaseNotes,
    onRunConvert,
  } = args;

  const currentFlow = useFlowStore((s) => s.currentFlow);
  const setTheme = useSettingsStore((s) => s.setTheme);
  const theme = useSettingsStore((s) => s.theme);
  const recents = useRecentsStore((s) => s.recents);
  const togglePin = useRecentsStore((s) => s.togglePin);
  const newTab = useTabsStore((s) => s.newTab);
  const tabsCount = useTabsStore((s) => s.tabs.length);
  const copyShareUrl = useCopyShareUrl();

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
    // Recipes (catalog)
    // -----------------------------------------------------------------
    const recipes = recipesQuery.data ?? [];
    for (const r of recipes) {
      const oneLineDesc = r.description.split(".")[0];
      out.push({
        id: `recipe:${r.type}`,
        section: "Recipes",
        primary: r.name,
        secondary: `${oneLineDesc} • ${r.type}`,
        icon: r.icon,
        keywords: [r.type, r.category, r.name, r.description],
        description: r.description,
        previewMeta: { canonical: r.type, category: r.category },
        invoke: () => {
          onClose();
          navigate(`/catalog?tab=recipes&q=${encodeURIComponent(r.name)}`);
        },
      });
    }

    // -----------------------------------------------------------------
    // Datasets — pulled from the in-memory current flow.
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
        description:
          "No flow is loaded — convert a Python script to populate this section with datasets.",
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
        const cols = datasetColumnCount(d);
        out.push({
          id: `dataset:${name}`,
          section: "Datasets",
          primary: name,
          secondary: conn ? `${dtype} • ${conn}` : dtype,
          icon: "▤",
          keywords: [name, dtype, conn],
          description: `${dtype} dataset${conn ? ` on ${conn}` : ""} with ${cols} column${cols === 1 ? "" : "s"}.`,
          previewMeta: {
            type: dtype,
            connection: conn || "(none)",
            columns: cols,
          },
          invoke: () => {
            onClose();
            navigate("/convert");
          },
        });
      }
    }

    // -----------------------------------------------------------------
    // Snippets
    // -----------------------------------------------------------------
    for (const s of SNIPPETS) {
      out.push({
        id: `snippet:${s.id}`,
        section: "Snippets",
        primary: s.name,
        secondary: `${s.category} • ${s.description.split(".")[0]}`,
        icon: "❍",
        keywords: [...s.tags, s.category, s.name],
        description: s.description,
        previewSource: snippetPreview(s.code),
        invoke: () => {
          onClose();
          navigate(`/snippets?id=${encodeURIComponent(s.id)}`);
        },
      });
    }

    // -----------------------------------------------------------------
    // Templates — Trade-Blotter Recipe-Template Gallery (Sprint 3).
    // Each template enumerates here so a trader can `Cmd+K, "PJM"` and
    // jump straight to the preview drawer.
    // -----------------------------------------------------------------
    for (const t of TEMPLATES) {
      out.push({
        id: `template:${t.id}`,
        section: "Templates",
        primary: t.name,
        secondary: `${t.category} • ${t.verifiedRecipes.join(" → ")}`,
        icon: "▦",
        keywords: [
          ...t.tags,
          ...t.personas,
          t.category,
          t.name,
          ...t.verifiedRecipes,
        ],
        description: t.summary,
        previewMeta: {
          recipes: t.verifiedRecipes.length,
          datasets: t.verifiedDatasets.length,
          minutesSaved: t.estimatedSavingMinutes,
        },
        invoke: () => {
          onClose();
          navigate(`/templates?id=${encodeURIComponent(t.id)}`);
        },
      });
    }

    // -----------------------------------------------------------------
    // GREL formulas — pre-built crack/heat-rate/basis/freight library.
    // Cmd+K, "crack" jumps straight to the formula preview modal.
    // -----------------------------------------------------------------
    for (const f of GREL_FORMULAS) {
      out.push({
        id: `grel:${f.id}`,
        section: "GREL Formulas",
        primary: f.name,
        secondary: `${f.category} • ${f.relatedInstruments.join(", ")} • ${f.unit}`,
        icon: "ƒ",
        keywords: [
          f.id,
          f.category,
          f.name,
          ...f.relatedInstruments,
          f.unit,
          f.grel,
        ],
        description: f.description,
        previewSource: buildInsertSnippet(f),
        invoke: () => {
          onClose();
          navigate(`/grel?id=${encodeURIComponent(f.id)}`);
        },
      });
    }

    // -----------------------------------------------------------------
    // LMP nodes — six-ISO settlement-point catalog.
    // Cmd+K, "PJM-W" surfaces the Western Hub row.
    // -----------------------------------------------------------------
    for (const n of LMP_NODES) {
      out.push({
        id: `lmp:${n.iso}-${n.node_id}`,
        section: "LMP Nodes",
        primary: `${n.iso} · ${n.node_name}`,
        secondary: `${n.zone} • ${n.region}${n.voltage_kv ? ` • ${n.voltage_kv} kV` : ""}`,
        icon: "⌁",
        keywords: [
          n.iso,
          n.node_id,
          n.node_name,
          n.zone,
          n.region,
        ],
        description: `${n.iso} settlement-point lookup for ${n.node_name}.`,
        previewSource: buildNodeSnippet(n),
        invoke: () => {
          onClose();
          navigate("/lmp");
        },
      });
    }

    // -----------------------------------------------------------------
    // Audit events
    // -----------------------------------------------------------------
    const auditEvents = auditQuery.data?.events ?? [];
    for (const ev of auditEvents.slice(0, 10)) {
      out.push({
        id: `audit:${ev.ts}:${ev.resource_id}`,
        section: "Audit events",
        primary: formatAuditPrimary(ev),
        secondary: formatAuditSecondary(ev),
        icon: "⊙",
        keywords: [ev.action, ev.actor, ev.resource_type, ev.resource_id],
        description: `${ev.actor} ${ev.action} on ${ev.resource_type} (${ev.resource_id}).`,
        invoke: () => {
          onClose();
          navigate("/audit");
        },
      });
    }

    // -----------------------------------------------------------------
    // Actions — including the multi-step args items.
    // -----------------------------------------------------------------
    const hasFlow = currentFlow !== null;
    const flowAsRecord =
      (currentFlow as Record<string, unknown> | null) ?? null;

    const actions: PaletteItem[] = [
      {
        // Multi-step Convert: pick rule|llm, then provider when llm.
        id: "action:convert",
        section: "Actions",
        primary: "Convert",
        secondary: "Choose mode then provider",
        icon: "▶",
        keywords: ["convert", "editor", "paste", "python", "rule", "llm"],
        description:
          "Run a conversion. Step through mode (rule | llm), then provider (only for llm).",
        shortcut: "⌘ Enter",
        invoke: () => {
          // Fallback when the palette skips arg collection (shouldn't happen).
          onClose();
          navigate("/convert");
        },
        args: [
          {
            key: "mode",
            label: "Mode",
            placeholder: "Pick conversion mode…",
            choices: [
              {
                value: "rule",
                label: "Rule-based",
                description: "Offline AST pattern matching. Deterministic.",
              },
              {
                value: "llm",
                label: "LLM",
                description: "AI-assisted. Needs an API key alias.",
              },
            ],
          },
          {
            key: "provider",
            label: "Provider",
            placeholder: "Pick LLM provider…",
            // Only collect provider when mode === "llm".
            when: (vals) => vals[0] === "llm",
            choices: [
              {
                value: "anthropic",
                label: "Anthropic",
                description: "Claude family. Default for py-iku.",
              },
              {
                value: "openai",
                label: "OpenAI",
                description: "GPT family.",
              },
            ],
          },
        ],
        invokeWithArgs: (values) => {
          const [mode, provider] = values as [
            "rule" | "llm",
            "anthropic" | "openai" | undefined,
          ];
          onClose();
          onRunConvert(mode, provider);
        },
      },
      {
        // Multi-step Export.
        id: "action:export-flow",
        section: "Actions",
        primary: "Export current flow",
        secondary: hasFlow
          ? "Pick format (json|yaml|svg|png|pdf)"
          : "Convert a flow first",
        icon: "▶",
        keywords: ["export", "download", "json", "yaml", "svg", "png", "pdf"],
        description: "Download the active flow in the format you choose.",
        invoke: () => {
          onClose();
          if (!hasFlow) navigate("/convert");
        },
        args: hasFlow
          ? [
              {
                key: "format",
                label: "Format",
                placeholder: "Pick export format…",
                choices: [
                  { value: "json", label: "JSON", description: "Plain JSON" },
                  { value: "yaml", label: "YAML", description: "DSS-style YAML" },
                  { value: "svg", label: "SVG", description: "Vector flow render" },
                  { value: "png", label: "PNG", description: "Raster flow render" },
                  { value: "pdf", label: "PDF", description: "Print-ready" },
                ],
              },
            ]
          : undefined,
        invokeWithArgs: (values) => {
          if (!flowAsRecord) return;
          onClose();
          const fmt = values[0] as ExportFormat;
          if (fmt === "json") {
            triggerJsonDownload(flowAsRecord);
          } else {
            void exportThroughApi(flowAsRecord, fmt);
          }
        },
      },
      {
        // Multi-step Open template.
        id: "action:open-template",
        section: "Actions",
        primary: "Open template",
        secondary: "Browse pre-built starter flows",
        icon: "▶",
        keywords: ["template", "starter", "open"],
        description:
          "Pick a template name and Studio opens its preview at /templates.",
        invoke: () => {
          onClose();
          navigate("/templates");
        },
        args: [
          {
            key: "template",
            label: "Template",
            placeholder: "Pick a template…",
            choices: TEMPLATE_CHOICES,
          },
        ],
        invokeWithArgs: (values) => {
          const tpl = values[0] as string;
          onClose();
          navigate(`/templates?id=${encodeURIComponent(tpl)}`);
        },
      },
      {
        // Multi-step Pin flow (pulls choices from recents).
        id: "action:pin-flow",
        section: "Actions",
        primary: "Pin flow",
        secondary: recents.length
          ? "Pick a recent flow to pin"
          : "No recents to pin yet",
        icon: "▶",
        keywords: ["pin", "favourite", "favorite", "star"],
        description: "Promote a recent flow into the persistent Pinned rail.",
        invoke: () => {
          onClose();
          navigate("/");
        },
        args:
          recents.length > 0
            ? [
                {
                  key: "flow",
                  label: "Flow",
                  placeholder: "Pick a recent flow…",
                  choices: recents.map<ArgChoice>((r) => ({
                    value: r.id,
                    label: r.name,
                    description: `${r.recipeCount} recipe${r.recipeCount === 1 ? "" : "s"}`,
                  })),
                },
              ]
            : undefined,
        invokeWithArgs: (values) => {
          const id = values[0] as string;
          togglePin(id);
          onClose();
        },
      },
      {
        id: "action:new-snippet",
        section: "Actions",
        primary: "New snippet",
        secondary: "Open the snippet gallery in create mode",
        icon: "▶",
        keywords: ["snippet", "create", "new"],
        description: "Open the snippet gallery in create mode.",
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
        icon: "▶",
        keywords: ["diff", "compare"],
        description: "Open the Diff view to compare two flows.",
        invoke: () => {
          onClose();
          navigate("/diff");
        },
      },
      {
        id: "action:open-curve-diff",
        section: "Actions",
        primary: "Open Curve Diff",
        secondary: "Compare two counterparty forward curves tenor-by-tenor",
        icon: "▶",
        keywords: ["curve", "diff", "forward", "counterparty", "tenor"],
        description:
          "Open the Counterparty Curve Diff view — side-by-side tenor table with abs/% deltas and threshold highlighting.",
        invoke: () => {
          onClose();
          navigate("/diff/curves");
        },
      },
      {
        id: "action:open-grel-library",
        section: "Actions",
        primary: "Open GREL Formula Library",
        secondary: "Pre-built crack-spread / heat-rate / basis formulas",
        icon: "▶",
        keywords: [
          "grel",
          "formula",
          "crack",
          "heat",
          "basis",
          "freight",
          "library",
        ],
        description:
          "Open the GREL formula library — crack spreads, heat rates, basis trades, freight netbacks.",
        invoke: () => {
          onClose();
          navigate("/grel");
        },
      },
      {
        id: "action:open-lmp-browser",
        section: "Actions",
        primary: "Open LMP Node Browser",
        secondary: "PJM, ERCOT, MISO, CAISO, NYISO, ISO-NE settlement points",
        icon: "▶",
        keywords: [
          "lmp",
          "iso",
          "rto",
          "node",
          "pjm",
          "ercot",
          "miso",
          "caiso",
          "nyiso",
          "isone",
          "settlement",
        ],
        description:
          "Open the ISO/RTO LMP node browser — six markets, ten nodes each.",
        invoke: () => {
          onClose();
          navigate("/lmp");
        },
      },
      {
        id: "action:open-deploy",
        section: "Actions",
        primary: "Open Deploy",
        secondary: "Settle-window-aware deploy gate",
        icon: "▶",
        keywords: ["deploy", "settle", "window", "venue", "calendar"],
        description:
          "Open the Deploy page — Deploy button is gated by major-venue settle windows.",
        invoke: () => {
          onClose();
          navigate("/deploy");
        },
      },
      {
        id: "action:open-audit",
        section: "Actions",
        primary: "Open Audit",
        secondary: "View recent flow events and changes",
        icon: "▶",
        keywords: ["audit", "log", "history"],
        description: "Open the Audit log.",
        invoke: () => {
          onClose();
          navigate("/audit");
        },
      },
      {
        id: "action:open-as-pr",
        section: "Actions",
        primary: "Open as PR",
        secondary: hasFlow
          ? "Push flow.json + SVG to GitHub and open a PR"
          : "Convert a flow first",
        icon: "▶",
        keywords: ["github", "pr", "publish", "branch", "commit", "open"],
        description:
          "Open a GitHub PR with flow.json, flow.svg, and a README. Asks for a PAT — never logged.",
        invoke: () => {
          onClose();
          navigate(hasFlow ? "/export?openPr=1" : "/convert");
        },
      },
      {
        id: "action:share-with-fixtures",
        section: "Actions",
        primary: "Share flow with fixture data",
        secondary: hasFlow
          ? "Embed up to 100 sample rows per input dataset"
          : "Convert a flow first",
        icon: "▶",
        keywords: ["share", "fixture", "sample", "data", "embed"],
        description:
          "Open the Share modal with the 'Include fixture data' option pre-checked.",
        invoke: () => {
          onClose();
          navigate(hasFlow ? "/convert?share=fixtures" : "/convert");
        },
      },
      {
        id: "action:open-settings",
        section: "Actions",
        primary: "Open Settings",
        secondary: "Provider, model alias, theme, API base URL",
        icon: "▶",
        keywords: ["settings", "config", "preferences"],
        description:
          "Configure provider, model alias, theme, and API base URL.",
        invoke: () => {
          onClose();
          navigate("/settings");
        },
      },
      {
        id: "action:open-chat",
        section: "Actions",
        primary: "Chat with flow",
        secondary: "Ask the assistant about the active flow",
        icon: "▶",
        keywords: ["chat", "ask", "explain", "llm", "assistant", "flow"],
        description:
          "Toggle the right-side chat drawer (Cmd+I). Ask questions about the active flow's recipes.",
        shortcut: "⌘ I",
        invoke: () => {
          onClose();
          useChatStore.getState().toggleOpen();
        },
      },
      {
        id: "action:open-llm-history",
        section: "Actions",
        primary: "Open LLM history",
        secondary: "Every LLM call recorded by Studio",
        icon: "▶",
        keywords: ["llm", "history", "spend", "cost", "audit", "prompt"],
        description:
          "Open the prompt-history page — provider/model/cost/status per call.",
        invoke: () => {
          onClose();
          navigate("/llm-history");
        },
      },
      {
        id: "action:open-cost-meter",
        section: "Actions",
        primary: "Show cost meter",
        secondary: "Today + month-to-date LLM spend",
        icon: "▶",
        keywords: ["cost", "meter", "spend", "budget", "money"],
        description:
          "Jump to the LLM history page; the cost meter widget is always visible in the gear bar.",
        invoke: () => {
          onClose();
          navigate("/llm-history");
        },
      },
      {
        id: "action:new-tab",
        section: "Actions",
        primary: "New tab",
        secondary:
          tabsCount >= MAX_TABS
            ? `Tab cap reached (${MAX_TABS})`
            : `Create a new workspace tab (${tabsCount}/${MAX_TABS})`,
        icon: "▶",
        keywords: ["tab", "new", "workspace", "open"],
        description:
          "Create a new workspace tab. Each tab holds its own source code, last flow, and mode/provider settings.",
        shortcut: "⌘ T",
        invoke: () => {
          onClose();
          newTab();
        },
      },
      {
        id: "action:open-replay-timeline",
        section: "Actions",
        primary: "Open replay timeline",
        secondary: "Scrub through recent conversion runs",
        icon: "▶",
        keywords: ["replay", "timeline", "history", "undo", "runs"],
        description:
          "Open the replay timeline at the bottom of the Convert page. Last 20 runs are captured automatically.",
        invoke: () => {
          onClose();
          navigate("/convert");
          // Defer scrolling so the route mounts first.
          setTimeout(() => {
            const el = document.querySelector('[data-testid="replay-timeline"], [data-testid="replay-timeline-empty"]');
            if (el && "scrollIntoView" in el) {
              (el as HTMLElement).scrollIntoView({ behavior: "smooth", block: "center" });
            }
          }, 50);
        },
      },
      {
        id: "action:copy-share-url",
        section: "Actions",
        primary: "Copy share URL",
        secondary: "Encode workspace state into a paste-able URL",
        icon: "▶",
        keywords: ["share", "url", "link", "copy", "state"],
        description:
          "Copy a link with the full workspace state encoded in the URL hash. Falls back to the per-flow share token if the workspace exceeds 32KB.",
        invoke: () => {
          onClose();
          void copyShareUrl();
        },
      },
      {
        id: "action:toggle-theme",
        section: "Actions",
        primary: "Toggle theme",
        secondary: `Switch to ${theme === "dark" ? "light" : "dark"} mode`,
        icon: theme === "dark" ? "☀" : "☾",
        keywords: ["theme", "dark", "light", "mode"],
        description: "Switch between dark and light themes.",
        invoke: () => {
          onClose();
          setTheme(theme === "dark" ? "light" : "dark");
        },
      },
    ];

    out.push(...actions);

    // -----------------------------------------------------------------
    // Help — glossary, shortcuts, release notes.
    // -----------------------------------------------------------------
    out.push(
      {
        id: "help:glossary",
        section: "Help",
        primary: "Open glossary",
        secondary: "py-iku textbook · Appendix A",
        icon: "?",
        keywords: ["glossary", "help", "docs", "textbook"],
        description: "Open the glossary in a new tab.",
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
        icon: "?",
        keywords: ["shortcuts", "keyboard", "hotkeys", "help"],
        description: "Open the full keyboard shortcuts cheat sheet.",
        invoke: () => {
          onOpenShortcutsHelp();
        },
      },
      {
        id: "help:release-notes",
        section: "Help",
        primary: "Show release notes",
        secondary: "Latest version + commit",
        icon: "?",
        keywords: ["release", "notes", "changelog", "version"],
        description:
          "Fetch the latest version + commit message from /api/version and show it inline.",
        invoke: () => {
          onOpenReleaseNotes();
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
    onOpenReleaseNotes,
    onRunConvert,
    recents,
    togglePin,
    newTab,
    tabsCount,
    copyShareUrl,
  ]);

  return {
    items,
    loading: recipesQuery.isLoading || auditQuery.isLoading,
  };
}

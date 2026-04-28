import { useMemo } from "react";
import { useQuery } from "@tanstack/react-query";
import type { NavigateFunction } from "react-router-dom";
import {
  client,
  type RecipeCatalogEntry,
} from "../../api/client";
import { useFlowStore } from "../../state/flowStore";
import { useSettingsStore } from "../../state/settingsStore";
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

function datasetColumnCount(d: Record<string, unknown>): number {
  const schema = d.schema as Array<unknown> | undefined;
  if (Array.isArray(schema)) return schema.length;
  return 0;
}

/**
 * Pulls items from every source the palette knows about and returns a
 * single flat list. Each section is bounded internally; final ranking
 * (fuzzy filter, top-N-per-section) happens in the palette component.
 *
 * After the Studio scope reduction this only surfaces:
 *   - Recipes (catalog)
 *   - Datasets (current flow)
 *   - Actions (Convert, Open Editor, Open Inspector, Open Catalog,
 *     Open Settings, Toggle theme, Show keyboard shortcuts)
 *   - Help (glossary, shortcuts, release notes)
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

  const recipesQuery = useQuery<RecipeCatalogEntry[]>({
    queryKey: ["catalog", "recipes"],
    queryFn: () => client.listRecipes(),
    // Cache aggressively — catalog rarely changes within a session.
    staleTime: 5 * 60_000,
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
    // Actions — minimal set after Studio scope reduction.
    // -----------------------------------------------------------------
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
        id: "action:open-editor",
        section: "Actions",
        primary: "Open Editor",
        secondary: "Pick a recent flow or start a fresh session",
        icon: "▶",
        keywords: ["editor", "open", "code"],
        description: "Open the standalone editor entry.",
        invoke: () => {
          onClose();
          navigate("/editor");
        },
      },
      {
        id: "action:open-inspector",
        section: "Actions",
        primary: "Open Inspector",
        secondary: "Drill into recipes and processors of the active flow",
        icon: "▶",
        keywords: ["inspector", "open", "node", "recipe", "processor"],
        description: "Open the Inspector for the active flow.",
        invoke: () => {
          onClose();
          navigate("/inspector");
        },
      },
      {
        id: "action:open-catalog",
        section: "Actions",
        primary: "Open Catalog",
        secondary: "Browse Dataiku recipe + processor catalog",
        icon: "▶",
        keywords: ["catalog", "open", "library", "recipes", "processors"],
        description: "Open the recipe and processor catalog.",
        invoke: () => {
          onClose();
          navigate("/catalog");
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
      {
        id: "action:show-shortcuts",
        section: "Actions",
        primary: "Show keyboard shortcuts",
        secondary: "Cmd+K, Cmd+Enter, Esc",
        icon: "?",
        keywords: ["shortcuts", "keyboard", "hotkeys", "help"],
        description: "Open the full keyboard shortcuts cheat sheet.",
        invoke: () => {
          onOpenShortcutsHelp();
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
        secondary: "Cmd+K, Cmd+Enter, Esc",
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
    currentFlow,
    theme,
    setTheme,
    navigate,
    onClose,
    onOpenShortcutsHelp,
    onOpenReleaseNotes,
    onRunConvert,
  ]);

  return {
    items,
    loading: recipesQuery.isLoading,
  };
}

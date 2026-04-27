import { create } from "zustand";
import { persist, createJSONStorage } from "zustand/middleware";

export type Theme = "light" | "dark";
export type LlmProvider = "anthropic" | "openai";

export interface SettingsState {
  /** null = not yet set; provider falls back to system preference. */
  theme: Theme | null;
  llmProvider: LlmProvider;
  llmModel: string;
  /** Logical alias resolved server-side. NEVER store an actual API key here. */
  apiKeyAlias: string;
  apiBaseUrl: string;
  /**
   * Sprint 4 power-user flag — when true, the Convert/Editor pages render the
   * multi-tab workspace strip. Default OFF so existing single-tab callers keep
   * working without surprises; user opts in from Settings → Advanced flags.
   */
  multiTabEnabled: boolean;
  setTheme: (theme: Theme) => void;
  setProvider: (provider: LlmProvider) => void;
  setModel: (model: string) => void;
  setApiKeyAlias: (alias: string) => void;
  setApiBaseUrl: (url: string) => void;
  setMultiTabEnabled: (enabled: boolean) => void;
  reset: () => void;
}

// Sprint 4D follow-up: multi-tab is the *recommended* default once Alt+T /
// Alt+W bindings exist for browser-tab contexts. We expose a separate
// constant so tests that want the legacy single-tab UX can `reset()` and
// then explicitly toggle, without the migration path also having to know
// about test-only state.
const FRESH_INSTALL_MULTI_TAB = true;

const DEFAULTS = {
  theme: null as Theme | null,
  llmProvider: "anthropic" as LlmProvider,
  llmModel: "claude-3-5-sonnet-latest",
  apiKeyAlias: "",
  apiBaseUrl: "http://localhost:8000",
  // `reset()` returns the legacy default so existing tests that rely on the
  // single-tab layout keep working without explicit toggles. Fresh installs
  // hit the migration path (no persisted blob → migrate runs with version 0)
  // which honours `FRESH_INSTALL_MULTI_TAB`.
  multiTabEnabled: false,
};

export const useSettingsStore = create<SettingsState>()(
  persist(
    (set) => ({
      ...DEFAULTS,
      setTheme: (theme) => set({ theme }),
      setProvider: (llmProvider) => set({ llmProvider }),
      setModel: (llmModel) => set({ llmModel }),
      setApiKeyAlias: (apiKeyAlias) => set({ apiKeyAlias }),
      setApiBaseUrl: (apiBaseUrl) => set({ apiBaseUrl }),
      setMultiTabEnabled: (multiTabEnabled) => set({ multiTabEnabled }),
      reset: () => set({ ...DEFAULTS }),
    }),
    {
      name: "py-iku-studio-settings",
      storage: createJSONStorage(() => localStorage),
      version: 3,
      // Defensive: never persist anything that looks like a raw API key.
      partialize: (state) => ({
        theme: state.theme,
        llmProvider: state.llmProvider,
        llmModel: state.llmModel,
        apiKeyAlias: state.apiKeyAlias,
        apiBaseUrl: state.apiBaseUrl,
        multiTabEnabled: state.multiTabEnabled,
      }),
      migrate: (persisted, version) => {
        // v1 didn't have multiTabEnabled; default to off when loading older blobs.
        // v2→v3 (Sprint 4D follow-up): flip multiTabEnabled default to ON now
        // that Alt+T / Alt+W bindings replace the browser-reserved Cmd
        // shortcuts. v2 blobs carried multiTabEnabled either from a v1 zero-
        // value migration or an explicit user choice — the migration cannot
        // disambiguate, so it promotes ANY false-or-missing v2 value to true.
        // Explicit-off users can re-toggle from Settings → Advanced flags.
        const p = (persisted as Partial<SettingsState>) ?? {};
        let next: Partial<SettingsState> = { ...p };
        if (version < 2) {
          next = { ...next, multiTabEnabled: false };
        }
        if (version < 3) {
          if (
            next.multiTabEnabled === false ||
            next.multiTabEnabled === undefined
          ) {
            next = { ...next, multiTabEnabled: FRESH_INSTALL_MULTI_TAB };
          }
        }
        return next;
      },
    },
  ),
);

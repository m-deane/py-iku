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
  setTheme: (theme: Theme) => void;
  setProvider: (provider: LlmProvider) => void;
  setModel: (model: string) => void;
  setApiKeyAlias: (alias: string) => void;
  setApiBaseUrl: (url: string) => void;
  reset: () => void;
}

const DEFAULTS = {
  theme: null as Theme | null,
  llmProvider: "anthropic" as LlmProvider,
  llmModel: "claude-3-5-sonnet-latest",
  apiKeyAlias: "",
  apiBaseUrl: "http://localhost:8000",
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
      reset: () => set({ ...DEFAULTS }),
    }),
    {
      name: "py-iku-studio-settings",
      storage: createJSONStorage(() => localStorage),
      version: 1,
      // Defensive: never persist anything that looks like a raw API key.
      partialize: (state) => ({
        theme: state.theme,
        llmProvider: state.llmProvider,
        llmModel: state.llmModel,
        apiKeyAlias: state.apiKeyAlias,
        apiBaseUrl: state.apiBaseUrl,
      }),
    },
  ),
);

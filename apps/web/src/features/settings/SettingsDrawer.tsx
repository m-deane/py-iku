import { useEffect, useState, type FormEvent } from "react";
import {
  useSettingsStore,
  type LlmProvider,
  type Theme,
} from "../../state/settingsStore";
import { useUiStore } from "../../state/uiStore";
import { useFocusTrap } from "../../components/useFocusTrap";

type ThemePref = Theme | "system";

interface DraftSettings {
  theme: ThemePref;
  llmProvider: LlmProvider;
  llmModel: string;
  apiKeyAlias: string;
  apiBaseUrl: string;
}

const MODEL_PLACEHOLDER: Record<LlmProvider, string> = {
  anthropic: "claude-sonnet-4-6",
  openai: "gpt-5",
};

function isValidUrl(value: string): boolean {
  try {
    const u = new URL(value);
    return u.protocol === "http:" || u.protocol === "https:";
  } catch {
    return false;
  }
}

function aliasIsValid(value: string): boolean {
  if (!value) return true; // empty is allowed (no LLM use)
  return /^[a-zA-Z0-9_.-]{1,64}$/.test(value);
}

/**
 * Slide-in settings panel. Triggered by the gear icon in `AppLayout`.
 *
 * Tracks a local `draft` state so users can stage changes and either save or
 * discard. Theme "system" maps back to `null` in the persisted store (matches
 * what `ThemeApplier` already understands).
 */
export function SettingsDrawer(): JSX.Element | null {
  const open = useUiStore((s) => s.settingsDrawerOpen);
  const close = useUiStore((s) => s.closeSettingsDrawer);
  const settings = useSettingsStore();

  const [draft, setDraft] = useState<DraftSettings>(() => ({
    theme: (settings.theme ?? "system") as ThemePref,
    llmProvider: settings.llmProvider,
    llmModel: settings.llmModel,
    apiKeyAlias: settings.apiKeyAlias,
    apiBaseUrl: settings.apiBaseUrl,
  }));

  // Re-sync draft when the drawer is (re)opened — picks up external changes
  // (e.g. ThemeToggle in the header) rather than leaving stale form values.
  useEffect(() => {
    if (open) {
      setDraft({
        theme: (settings.theme ?? "system") as ThemePref,
        llmProvider: settings.llmProvider,
        llmModel: settings.llmModel,
        apiKeyAlias: settings.apiKeyAlias,
        apiBaseUrl: settings.apiBaseUrl,
      });
    }
  }, [
    open,
    settings.theme,
    settings.llmProvider,
    settings.llmModel,
    settings.apiKeyAlias,
    settings.apiBaseUrl,
  ]);

  // Focus trap: ref returned by `useFocusTrap` lives on the <aside>. Only
  // activates while `open === true`. Restores focus to the gear icon (the
  // previously-focused element) when the drawer unmounts.
  const trapRef = useFocusTrap<HTMLElement>(open);

  // Esc closes the drawer (separate from focus trap, which only handles Tab).
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent): void => {
      if (e.key === "Escape") {
        e.stopPropagation();
        close();
      }
    };
    document.addEventListener("keydown", onKey);
    return (): void => document.removeEventListener("keydown", onKey);
  }, [open, close]);

  if (!open) return null;

  const dirty =
    draft.theme !== ((settings.theme ?? "system") as ThemePref) ||
    draft.llmProvider !== settings.llmProvider ||
    draft.llmModel !== settings.llmModel ||
    draft.apiKeyAlias !== settings.apiKeyAlias ||
    draft.apiBaseUrl !== settings.apiBaseUrl;

  const urlValid = isValidUrl(draft.apiBaseUrl);
  const aliasValid = aliasIsValid(draft.apiKeyAlias);
  const canSave = dirty && urlValid && aliasValid;

  const onSave = (e: FormEvent): void => {
    e.preventDefault();
    if (!canSave) return;

    if (draft.theme === "system") {
      // settingsStore allows null, but the typed setter signature is `Theme`,
      // so we route through a direct setState to clear it.
      useSettingsStore.setState({ theme: null });
    } else {
      settings.setTheme(draft.theme);
    }
    settings.setProvider(draft.llmProvider);
    settings.setModel(draft.llmModel);
    settings.setApiKeyAlias(draft.apiKeyAlias);
    settings.setApiBaseUrl(draft.apiBaseUrl);
    close();
  };

  const onDiscard = (): void => {
    setDraft({
      theme: (settings.theme ?? "system") as ThemePref,
      llmProvider: settings.llmProvider,
      llmModel: settings.llmModel,
      apiKeyAlias: settings.apiKeyAlias,
      apiBaseUrl: settings.apiBaseUrl,
    });
    close();
  };

  return (
    <>
      <div
        onClick={onDiscard}
        aria-hidden
        style={{
          position: "fixed",
          inset: 0,
          background: "rgba(0,0,0,0.35)",
          zIndex: 100,
        }}
      />
      <aside
        ref={trapRef}
        role="dialog"
        aria-label="Settings"
        aria-modal="true"
        tabIndex={-1}
        data-testid="settings-drawer"
        style={{
          position: "fixed",
          top: 0,
          right: 0,
          bottom: 0,
          width: "min(420px, 100%)",
          background: "var(--color-background, #fafafa)",
          color: "var(--color-fg, #212121)",
          borderLeft: "1px solid var(--color-grid, #e0e0e0)",
          boxShadow: "-4px 0 16px rgba(0,0,0,0.18)",
          padding: "1.25rem",
          overflowY: "auto",
          zIndex: 101,
        }}
      >
        <header
          style={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            marginBottom: "1rem",
          }}
        >
          <h2 style={{ margin: 0, fontSize: "1.1rem" }}>Settings</h2>
          <button
            type="button"
            onClick={onDiscard}
            aria-label="Close settings"
            style={{
              border: "1px solid var(--color-grid, #e0e0e0)",
              background: "transparent",
              color: "inherit",
              borderRadius: 6,
              width: 28,
              height: 28,
              cursor: "pointer",
            }}
          >
            ×
          </button>
        </header>

        <div
          role="alert"
          style={{
            padding: "0.5rem 0.75rem",
            borderRadius: "var(--radius-md, 6px)",
            background: "var(--info-bg, #eff6ff)",
            color: "var(--info-fg, #1d4ed8)",
            border: "1px solid var(--info-border, #bfdbfe)",
            fontSize: "var(--text-xs, 12px)",
            marginBottom: "1rem",
          }}
        >
          API keys for Anthropic and OpenAI are read from the server
          environment. Save an alias here to identify which provider key the
          server should use — the actual key is never sent from the browser.
        </div>

        <form onSubmit={onSave}>
          <Section title="Appearance">
            <Field label="Theme">
              <select
                value={draft.theme}
                data-testid="settings-theme-select"
                onChange={(e) =>
                  setDraft((d) => ({ ...d, theme: e.target.value as ThemePref }))
                }
                aria-label="Theme"
              >
                <option value="system">System</option>
                <option value="light">Light</option>
                <option value="dark">Dark</option>
              </select>
            </Field>
          </Section>

          <Section title="LLM provider">
            <Field label="Provider">
              <div role="radiogroup" aria-label="LLM provider" style={{ display: "flex", gap: "1rem" }}>
                {(["anthropic", "openai"] as const).map((p) => (
                  <label key={p} style={{ display: "inline-flex", gap: "0.4rem" }}>
                    <input
                      type="radio"
                      name="llmProvider"
                      value={p}
                      checked={draft.llmProvider === p}
                      onChange={() =>
                        setDraft((d) => ({ ...d, llmProvider: p }))
                      }
                    />
                    {p}
                  </label>
                ))}
              </div>
            </Field>
            <Field label="Model">
              <input
                type="text"
                value={draft.llmModel}
                placeholder={MODEL_PLACEHOLDER[draft.llmProvider]}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, llmModel: e.target.value }))
                }
                aria-label="LLM model"
              />
            </Field>
            <Field
              label="API key alias"
              hint="Your key is sent to the API once, never stored in the browser."
              error={!aliasValid ? "Letters, digits, _ . - only (max 64 chars)." : undefined}
            >
              <input
                type="text"
                value={draft.apiKeyAlias}
                placeholder="e.g. anthropic-default"
                onChange={(e) =>
                  setDraft((d) => ({ ...d, apiKeyAlias: e.target.value }))
                }
                aria-label="API key alias"
              />
            </Field>
          </Section>

          <Section title="API connection">
            <Field
              label="API base URL"
              error={!urlValid ? "Must be a valid http(s) URL." : undefined}
            >
              <input
                type="url"
                value={draft.apiBaseUrl}
                onChange={(e) =>
                  setDraft((d) => ({ ...d, apiBaseUrl: e.target.value }))
                }
                aria-label="API base URL"
              />
            </Field>
          </Section>

          <footer
            style={{
              display: "flex",
              gap: "0.5rem",
              justifyContent: "flex-end",
              marginTop: "1rem",
            }}
          >
            <button
              type="button"
              onClick={onDiscard}
              style={{
                padding: "0.45rem 0.9rem",
                borderRadius: 6,
                border: "1px solid var(--color-grid, #e0e0e0)",
                background: "transparent",
                color: "inherit",
                cursor: "pointer",
              }}
            >
              Discard
            </button>
            <button
              type="submit"
              disabled={!canSave}
              aria-disabled={!canSave}
              style={{
                padding: "0.45rem 0.9rem",
                borderRadius: 6,
                border: 0,
                background: canSave
                  ? "var(--color-connectionhover, #1976d2)"
                  : "var(--color-grid, #e0e0e0)",
                color: canSave ? "white" : "var(--color-fg, #212121)",
                cursor: canSave ? "pointer" : "not-allowed",
                opacity: canSave ? 1 : 0.7,
              }}
            >
              Save
            </button>
          </footer>
        </form>
      </aside>
    </>
  );
}

function Section(props: { title: string; children: React.ReactNode }): JSX.Element {
  return (
    <section style={{ marginBottom: "1.25rem" }}>
      <h3 style={{ margin: "0 0 0.6rem 0", fontSize: "0.9rem", color: "var(--fg-muted, #5b6470)" }}>
        {props.title}
      </h3>
      <div style={{ display: "flex", flexDirection: "column", gap: "0.75rem" }}>
        {props.children}
      </div>
    </section>
  );
}

function Field(props: {
  label: string;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: "0.3rem", fontSize: 14 }}>
      <span>{props.label}</span>
      {props.children}
      {props.hint ? (
        <span style={{ fontSize: 12, color: "var(--fg-muted, #5b6470)" }}>{props.hint}</span>
      ) : null}
      {props.error ? (
        <span role="alert" style={{ fontSize: 12, color: "#d32f2f" }}>
          {props.error}
        </span>
      ) : null}
    </label>
  );
}

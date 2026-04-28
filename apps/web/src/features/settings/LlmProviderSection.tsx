import { useEffect, useState } from "react";
import { toast } from "sonner";
import {
  client,
  ApiError,
  type LlmStatusResponse,
} from "../../api/client";
import { useSettingsStore, type LlmProvider } from "../../state/settingsStore";

/**
 * "LLM Provider" section on the Settings page.
 *
 * Spec
 * ----
 *  - Provider select (Anthropic / OpenAI — OpenAI is marked as "not yet
 *    configured server-side" because the server stops dispatching to it on
 *    bootstrap; we still expose the option so users see the surface area).
 *  - ANTHROPIC_API_KEY input (password type, eye toggle).
 *  - 🟢 Configured / 🔴 Not configured status indicator backed by the server's
 *    /api/settings/llm response (NEVER from localStorage).
 *  - "Test connection" button that POSTs a minimal pandas snippet to
 *    /convert?mode=llm and reports success / failure inline + via toast.
 *  - Explanatory copy: "The key is stored server-side via /api/settings/llm/key.
 *    It is never logged and never written to the rendered HTML."
 */
export function LlmProviderSection(): JSX.Element {
  const provider = useSettingsStore((s) => s.llmProvider);
  const setProvider = useSettingsStore((s) => s.setProvider);
  const model = useSettingsStore((s) => s.llmModel);
  const setModel = useSettingsStore((s) => s.setModel);

  const [status, setStatus] = useState<LlmStatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [draftKey, setDraftKey] = useState("");
  const [reveal, setReveal] = useState(false);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [testOutcome, setTestOutcome] = useState<
    | { kind: "ok"; recipeCount: number }
    | { kind: "error"; title: string; detail?: string; status: number }
    | null
  >(null);

  useEffect(() => {
    let alive = true;
    setLoading(true);
    client
      .getLlmStatus()
      .then((s) => {
        if (alive) setStatus(s);
      })
      .catch((err) => {
        if (alive) {
          // Don't toast — the key surface is read-only on first paint and a
          // failed health probe is recoverable.
          setStatus({
            provider,
            has_key: false,
            source: "none",
          } satisfies LlmStatusResponse);
        }
        // eslint-disable-next-line no-console
        console.warn("LLM status probe failed", err);
      })
      .finally(() => {
        if (alive) setLoading(false);
      });
    return (): void => {
      alive = false;
    };
  }, [provider]);

  const onSaveKey = async (): Promise<void> => {
    if (!draftKey.trim()) return;
    setSaving(true);
    try {
      const next = await client.saveLlmKey({ provider, key: draftKey });
      setStatus(next);
      setDraftKey("");
      setReveal(false);
      toast.success("API key saved", {
        description: "Stored server-side. Try a Convert run to verify.",
      });
    } catch (err) {
      const apiErr =
        err instanceof ApiError
          ? err
          : new ApiError({
              type: "about:blank",
              title: "Failed to save key",
              status: 0,
              detail: err instanceof Error ? err.message : String(err),
            });
      toast.error(apiErr.title, { description: apiErr.detail ?? apiErr.title });
    } finally {
      setSaving(false);
    }
  };

  const onClearKey = async (): Promise<void> => {
    setSaving(true);
    try {
      await client.deleteLlmKey(provider);
      const next = await client.getLlmStatus();
      setStatus(next);
      toast.message("API key removed");
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err);
      toast.error("Failed to remove key", { description: detail });
    } finally {
      setSaving(false);
    }
  };

  const onTestConnection = async (): Promise<void> => {
    setTesting(true);
    setTestOutcome(null);
    try {
      // Tiny no-op script — small enough to keep the LLM call cheap, but
      // structured enough that the analyzer always returns at least one
      // recipe. We pass `force=true` so the budget gate doesn't block the
      // probe on a freshly-installed Studio.
      const probeCode =
        "import pandas as pd\n" +
        "df = pd.read_csv('probe.csv')\n" +
        "out = df.groupby('k').agg({'v': 'sum'})\n";
      const result = await client.convert(
        {
          code: probeCode,
          mode: "llm",
          options: { provider, model },
        },
        { force: true },
      );
      const recipeCount = Array.isArray(
        (result.flow as { recipes?: unknown[] }).recipes,
      )
        ? ((result.flow as { recipes: unknown[] }).recipes.length ?? 0)
        : 0;
      setTestOutcome({ kind: "ok", recipeCount });
      toast.success("LLM connection OK", {
        description: `Got ${recipeCount} recipe${recipeCount === 1 ? "" : "s"} back.`,
      });
    } catch (err) {
      const apiErr =
        err instanceof ApiError
          ? err
          : new ApiError({
              type: "about:blank",
              title: "Test failed",
              status: 0,
              detail: err instanceof Error ? err.message : String(err),
            });
      setTestOutcome({
        kind: "error",
        title: apiErr.title,
        detail: apiErr.detail,
        status: apiErr.status,
      });
      toast.error(apiErr.title, { description: apiErr.detail ?? apiErr.title });
    } finally {
      setTesting(false);
    }
  };

  const hasKey = status?.has_key === true;
  const source = status?.source ?? "none";

  return (
    <section
      data-testid="settings-llm-section"
      style={{
        border: "1px solid var(--border, #eaecf0)",
        borderRadius: "var(--radius-lg, 12px)",
        padding: "var(--space-5, 24px)",
        background: "var(--surface, #ffffff)",
        boxShadow: "var(--shadow-sm)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4, 16px)",
      }}
    >
      <header style={{ display: "flex", alignItems: "baseline", gap: "var(--space-3, 12px)" }}>
        <h2 style={{ margin: 0, fontSize: "var(--text-md, 17px)" }}>LLM Provider</h2>
        <StatusPill loading={loading} hasKey={hasKey} source={source} />
      </header>

      <p
        style={{
          margin: 0,
          color: "var(--fg-muted, #5b6470)",
          fontSize: "var(--text-sm, 14px)",
        }}
      >
        The key is stored server-side via{" "}
        <code style={{ fontSize: "var(--text-xs, 12px)" }}>
          /api/settings/llm/key
        </code>
        . It is never logged and never written to the rendered HTML.
      </p>

      <Row label="Provider">
        <select
          data-testid="settings-llm-provider-select"
          value={provider}
          onChange={(e) => setProvider(e.target.value as LlmProvider)}
          aria-label="LLM provider"
        >
          <option value="anthropic">Anthropic (default)</option>
          <option value="openai">OpenAI (not yet configured server-side)</option>
        </select>
      </Row>

      <Row label="Model">
        <input
          data-testid="settings-llm-model-input"
          type="text"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          aria-label="LLM model"
          placeholder={
            provider === "anthropic"
              ? "claude-3-5-sonnet-latest"
              : "gpt-4o-mini"
          }
        />
      </Row>

      <Row
        label={
          provider === "anthropic"
            ? "ANTHROPIC_API_KEY"
            : "OPENAI_API_KEY"
        }
      >
        <div style={{ display: "flex", gap: "var(--space-2, 8px)", flexWrap: "wrap" }}>
          <input
            data-testid="settings-llm-key-input"
            type={reveal ? "text" : "password"}
            value={draftKey}
            onChange={(e) => setDraftKey(e.target.value)}
            placeholder={hasKey ? "•••• already set ••••" : "Paste key here"}
            aria-label="API key"
            autoComplete="off"
            spellCheck={false}
            style={{ flex: 1, minWidth: 240 }}
          />
          <button
            type="button"
            data-testid="settings-llm-key-reveal"
            onClick={() => setReveal((v) => !v)}
            aria-label={reveal ? "Hide key" : "Show key"}
            style={{
              padding: "0.4rem 0.7rem",
              borderRadius: "var(--radius-md, 6px)",
              border: "1px solid var(--border, #eaecf0)",
              background: "transparent",
              cursor: "pointer",
              fontSize: "var(--text-sm, 14px)",
            }}
          >
            {reveal ? "Hide" : "Show"}
          </button>
          <button
            type="button"
            data-testid="settings-llm-key-save"
            onClick={() => {
              void onSaveKey();
            }}
            disabled={saving || !draftKey.trim()}
            aria-disabled={saving || !draftKey.trim()}
            style={{
              padding: "0.4rem 0.9rem",
              borderRadius: "var(--radius-md, 6px)",
              border: 0,
              background:
                saving || !draftKey.trim()
                  ? "var(--color-grid, #e0e0e0)"
                  : "var(--color-connectionhover, #1976d2)",
              color: saving || !draftKey.trim() ? "var(--fg, #212121)" : "white",
              cursor: saving || !draftKey.trim() ? "not-allowed" : "pointer",
              fontSize: "var(--text-sm, 14px)",
              fontWeight: 600,
            }}
          >
            {saving ? "Saving…" : "Save key"}
          </button>
          {hasKey && source === "file" ? (
            <button
              type="button"
              data-testid="settings-llm-key-clear"
              onClick={() => {
                void onClearKey();
              }}
              disabled={saving}
              style={{
                padding: "0.4rem 0.9rem",
                borderRadius: "var(--radius-md, 6px)",
                border: "1px solid var(--border, #eaecf0)",
                background: "transparent",
                color: "inherit",
                cursor: saving ? "not-allowed" : "pointer",
                fontSize: "var(--text-sm, 14px)",
              }}
            >
              Remove
            </button>
          ) : null}
        </div>
      </Row>

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: "var(--space-3, 12px)",
          flexWrap: "wrap",
          paddingTop: "var(--space-2, 8px)",
        }}
      >
        <button
          type="button"
          data-testid="settings-llm-test"
          onClick={() => {
            void onTestConnection();
          }}
          disabled={testing || !hasKey}
          aria-disabled={testing || !hasKey}
          style={{
            padding: "0.45rem 0.9rem",
            borderRadius: "var(--radius-md, 6px)",
            border: "1px solid var(--border, #eaecf0)",
            background: "transparent",
            color: "inherit",
            cursor: testing || !hasKey ? "not-allowed" : "pointer",
            fontSize: "var(--text-sm, 14px)",
          }}
          title={
            hasKey
              ? "Send a tiny pandas script through /convert?mode=llm"
              : "Save a key first"
          }
        >
          {testing ? "Testing…" : "Test connection"}
        </button>
        <span
          style={{
            color: "var(--fg-muted, #5b6470)",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          Sends a 5-line pandas snippet through{" "}
          <code style={{ fontSize: "inherit" }}>/convert?mode=llm</code>.
        </span>
      </div>

      {testOutcome ? (
        <div
          role="status"
          data-testid="settings-llm-test-result"
          style={{
            padding: "0.5rem 0.75rem",
            borderRadius: "var(--radius-md, 6px)",
            background:
              testOutcome.kind === "ok"
                ? "var(--success-bg, #ecfdf5)"
                : "var(--danger-bg, #fef2f2)",
            color:
              testOutcome.kind === "ok"
                ? "var(--success-fg, #047857)"
                : "var(--danger-fg, #b91c1c)",
            border:
              testOutcome.kind === "ok"
                ? "1px solid var(--success-border, #a7f3d0)"
                : "1px solid var(--danger-border, #fecaca)",
            fontSize: "var(--text-xs, 12px)",
          }}
        >
          {testOutcome.kind === "ok" ? (
            <>
              <strong>OK.</strong> Returned {testOutcome.recipeCount} recipe
              {testOutcome.recipeCount === 1 ? "" : "s"}.
            </>
          ) : (
            <>
              <strong>Failed</strong>
              {testOutcome.status > 0 ? ` (HTTP ${testOutcome.status})` : ""}:{" "}
              {testOutcome.title}
              {testOutcome.detail ? ` — ${testOutcome.detail}` : ""}
            </>
          )}
        </div>
      ) : null}
    </section>
  );
}

function StatusPill(props: {
  loading: boolean;
  hasKey: boolean;
  source: "file" | "env" | "none";
}): JSX.Element {
  const { loading, hasKey, source } = props;
  const label = loading
    ? "Checking…"
    : hasKey
      ? source === "file"
        ? "Configured (file)"
        : "Configured (env)"
      : "Not configured";
  const dot = loading ? "⏳" : hasKey ? "🟢" : "🔴";
  return (
    <span
      data-testid="settings-llm-status"
      data-state={loading ? "loading" : hasKey ? "ok" : "missing"}
      style={{
        display: "inline-flex",
        alignItems: "center",
        gap: "0.35rem",
        padding: "0.15rem 0.55rem",
        borderRadius: 999,
        border: "1px solid var(--border, #eaecf0)",
        background: loading
          ? "transparent"
          : hasKey
            ? "var(--success-bg, #ecfdf5)"
            : "var(--danger-bg, #fef2f2)",
        color: loading
          ? "var(--fg-muted, #5b6470)"
          : hasKey
            ? "var(--success-fg, #047857)"
            : "var(--danger-fg, #b91c1c)",
        fontSize: "var(--text-xs, 12px)",
        fontWeight: 600,
      }}
    >
      <span aria-hidden>{dot}</span>
      {label}
    </span>
  );
}

function Row({
  label,
  children,
}: {
  label: React.ReactNode;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <label
      style={{
        display: "grid",
        gridTemplateColumns: "200px 1fr",
        alignItems: "center",
        gap: "var(--space-3, 12px)",
        fontSize: "var(--text-sm, 14px)",
      }}
    >
      <span style={{ color: "var(--fg-muted, #5b6470)" }}>{label}</span>
      <span>{children}</span>
    </label>
  );
}

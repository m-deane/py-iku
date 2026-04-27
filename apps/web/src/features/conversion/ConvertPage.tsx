import { useEffect, useMemo, useRef, useState } from "react";
import { toast } from "sonner";
import { MonacoEditor } from "../editor/MonacoEditor";
import { SnippetPicker } from "../editor/SnippetPicker";
import { JsonView } from "../../components/JsonView";
import { ExportButtons } from "../export/ExportButtons";
import { ValidationPanel } from "../validation/ValidationPanel";
import { NodeInspector } from "../inspector/NodeInspector";
import {
  client,
  ApiError,
  type ConvertResponse,
  type ConversionMode,
} from "../../api/client";
import { useFlowStore } from "../../state/flowStore";
import { useSettingsStore } from "../../state/settingsStore";
import { useUiStore } from "../../state/uiStore";
import {
  useConvertStream,
  type UseConvertStreamResult,
  type UseConvertStreamOptions,
} from "./useConvertStream";

export interface ConvertPageProps {
  /** Test seam — swap in a stub `client.convert` without mocking modules. */
  convertImpl?: typeof client.convert;
  /**
   * Test seam — swap in a stub streaming hook so we can drive the page through
   * the WebSocket code path without a real socket.
   */
  streamConvertImpl?: (options?: UseConvertStreamOptions) => UseConvertStreamResult;
  /** Test seam — Monaco can't render under jsdom. */
  useFallbackEditor?: boolean;
  /** When true, disables the streaming code path (used by REST-only tests). */
  useRestOnly?: boolean;
  /** Test seam — swap in a stub client for the export buttons. */
  exportClientImpl?: typeof client;
  /** Test seam — full client used for save/share calls. */
  shareClientImpl?: typeof client;
}

export function ConvertPage(props: ConvertPageProps): JSX.Element {
  const code = useFlowStore((s) => s.currentCode);
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const mode = useFlowStore((s) => s.conversionMode);
  const setMode = useFlowStore((s) => s.setConversionMode);
  const status = useFlowStore((s) => s.conversionStatus);
  const setStatus = useFlowStore((s) => s.setConversionStatus);
  const setFlow = useFlowStore((s) => s.setFlow);
  const apiKeyAlias = useSettingsStore((s) => s.apiKeyAlias);
  const provider = useSettingsStore((s) => s.llmProvider);
  const model = useSettingsStore((s) => s.llmModel);
  const openSettings = useUiStore((s) => s.openSettingsDrawer);

  const [response, setResponse] = useState<ConvertResponse | null>(null);
  const [error, setError] = useState<{ title: string; detail?: string; status: number } | null>(
    null,
  );
  const [editorValue, setEditorValue] = useState<string | undefined>(undefined);
  const [validationOpen, setValidationOpen] = useState(false);
  const [savedFlowId, setSavedFlowId] = useState<string | null>(null);
  const [sharing, setSharing] = useState(false);

  // Streaming hook (always-on for M5 unless explicitly disabled by tests).
  const useStreamHook = props.streamConvertImpl ?? useConvertStream;
  const stream = useStreamHook();

  const llmDisabled = mode === "llm" && apiKeyAlias.trim() === "";
  const inFlight =
    status === "running" ||
    status === "streaming" ||
    stream.status === "connecting" ||
    stream.status === "streaming";

  // Surface stream completion → flowStore + UI state.
  const lastSeenStreamStatus = useRef(stream.status);
  useEffect(() => {
    if (lastSeenStreamStatus.current === stream.status) return;
    lastSeenStreamStatus.current = stream.status;
    if (stream.status === "done" && stream.flow) {
      const fakeResp: ConvertResponse = {
        flow: stream.flow,
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        score: (stream.score as any) ?? {
          complexity: 0,
          recipe_count: 0,
          dataset_count: 0,
        },
        warnings: stream.warnings ?? [],
      };
      setResponse(fakeResp);
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      setFlow(stream.flow as any);
      setStatus("done");
      if (stream.warnings.length > 0) {
        toast.message(
          `Converted with ${stream.warnings.length} warning${
            stream.warnings.length === 1 ? "" : "s"
          }`,
        );
      }
    } else if (stream.status === "error" && stream.error) {
      setError(stream.error);
      setStatus("error");
      toast.error(stream.error.title, {
        description: stream.error.detail ?? stream.error.title,
      });
    } else if (stream.status === "cancelled") {
      setStatus("idle");
      toast.message("Conversion cancelled");
    } else if (stream.status === "streaming" || stream.status === "connecting") {
      setStatus("streaming");
    }
  }, [stream.status, stream.flow, stream.score, stream.warnings, stream.error, setFlow, setStatus]);

  const onConvert = async (): Promise<void> => {
    if (inFlight) return;
    if (!code || code.trim().length === 0) {
      toast.error("No code to convert", { description: "Paste or pick a snippet first." });
      return;
    }
    setError(null);
    setResponse(null);
    setSavedFlowId(null);

    // REST path (legacy / test compatibility).
    if (props.useRestOnly || props.convertImpl) {
      setStatus("running");
      try {
        const convert = props.convertImpl ?? client.convert;
        const result = await convert({
          code,
          mode,
          options: mode === "llm" ? { provider, model } : undefined,
        });
        setResponse(result);
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        setFlow(result.flow as any);
        setStatus("done");
        if (result.warnings.length > 0) {
          toast.message(
            `Converted with ${result.warnings.length} warning${result.warnings.length === 1 ? "" : "s"}`,
          );
        }
      } catch (err) {
        const apiErr =
          err instanceof ApiError
            ? err
            : new ApiError({
                type: "about:blank",
                title: "Unexpected error",
                status: 0,
                detail: err instanceof Error ? err.message : String(err),
              });
        const friendly = friendlyTitle(apiErr.status, apiErr.title);
        setError({ title: friendly, detail: apiErr.detail, status: apiErr.status });
        setStatus("error");
        toast.error(friendly, { description: apiErr.detail ?? apiErr.title });
      }
      return;
    }

    // Streaming path — default for M5.
    setStatus("streaming");
    stream.start({
      code,
      mode,
      options: mode === "llm" ? { provider, model } : undefined,
    });
  };

  const onCancel = (): void => {
    if (!inFlight) return;
    stream.cancel();
  };

  const cli = props.shareClientImpl ?? client;

  const onShare = async (): Promise<void> => {
    if (!response) return;
    setSharing(true);
    try {
      let flowId = savedFlowId;
      if (!flowId) {
        const saved = await cli.saveFlow({
          flow: response.flow,
          name:
            (response.flow as { flow_name?: string }).flow_name ||
            "shared-flow",
        });
        flowId = saved.id;
        setSavedFlowId(flowId);
      }
      const shared = await cli.shareFlow(flowId, {
        ttl_seconds: 24 * 60 * 60,
        scopes: ["read"],
      });
      try {
        if (typeof navigator !== "undefined" && navigator.clipboard) {
          await navigator.clipboard.writeText(shared.url);
        }
      } catch {
        /* clipboard not available — fall through to toast */
      }
      toast.success("Share link copied", { description: shared.url });
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err);
      toast.error("Could not share flow", { description: msg });
    } finally {
      setSharing(false);
    }
  };

  const progressList = stream.progress;
  const showProgress = progressList.length > 0;

  return (
    <section
      style={{
        display: "grid",
        gridTemplateColumns: "minmax(320px, 1fr) minmax(320px, 1fr)",
        gap: "1rem",
        padding: "1rem 1.25rem",
        maxWidth: 1400,
        margin: "0 auto",
      }}
    >
      <div>
        <header
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            marginBottom: "0.75rem",
          }}
        >
          <h1 style={{ margin: 0, fontSize: "1.25rem" }}>Convert</h1>
          <SnippetPicker
            currentCode={code}
            onSelect={(s) => {
              setEditorValue(s.code);
              setCurrentCode(s.code);
            }}
          />
          {response ? (
            <button
              type="button"
              data-testid="score-badge"
              onClick={() => setValidationOpen((v) => !v)}
              aria-label="Toggle validation panel"
              style={{
                marginLeft: "auto",
                padding: "0.3rem 0.6rem",
                borderRadius: 999,
                border: "1px solid var(--color-grid, #e0e0e0)",
                background: "transparent",
                color: "inherit",
                cursor: "pointer",
                fontSize: 12,
                fontWeight: 600,
              }}
            >
              complexity: {response.score.complexity.toFixed(1)}
            </button>
          ) : null}
        </header>
        <MonacoEditor
          value={editorValue}
          onChange={(v) => setCurrentCode(v)}
          fallbackTextarea={props.useFallbackEditor}
        />
        {showProgress ? (
          <ProgressLog events={progressList} />
        ) : null}
      </div>

      <div style={{ display: "flex", flexDirection: "column", gap: "1rem" }}>
        <div
          style={{
            display: "flex",
            alignItems: "center",
            gap: "0.75rem",
            flexWrap: "wrap",
          }}
        >
          <ModeToggle mode={mode} onChange={setMode} />
          <button
            type="button"
            data-testid="convert-submit"
            onClick={onConvert}
            disabled={inFlight || llmDisabled}
            aria-disabled={inFlight || llmDisabled}
            title={llmDisabled ? "Set LLM credentials in settings" : undefined}
            style={{
              padding: "0.5rem 1rem",
              borderRadius: 6,
              border: 0,
              background:
                inFlight || llmDisabled
                  ? "var(--color-grid, #cccccc)"
                  : "var(--color-connectionhover, #1976d2)",
              color: inFlight || llmDisabled ? "var(--color-fg, #212121)" : "white",
              cursor: inFlight || llmDisabled ? "not-allowed" : "pointer",
              fontWeight: 600,
            }}
          >
            {inFlight ? (
              <span>
                <Spinner /> Converting…
              </span>
            ) : (
              "Convert"
            )}
          </button>
          <button
            type="button"
            data-testid="convert-cancel"
            onClick={onCancel}
            disabled={!inFlight}
            style={{
              padding: "0.5rem 0.9rem",
              borderRadius: 6,
              border: "1px solid var(--color-grid, #e0e0e0)",
              background: "transparent",
              color: "inherit",
              cursor: inFlight ? "pointer" : "not-allowed",
              opacity: inFlight ? 1 : 0.5,
            }}
          >
            Cancel
          </button>
          {llmDisabled ? (
            <button
              type="button"
              onClick={openSettings}
              style={{
                marginLeft: "auto",
                padding: "0.4rem 0.7rem",
                borderRadius: 6,
                border: "1px solid var(--color-grid, #e0e0e0)",
                background: "transparent",
                color: "inherit",
                cursor: "pointer",
                fontSize: 12,
              }}
            >
              Set LLM credentials
            </button>
          ) : null}
        </div>

        <StatusPanel
          status={status}
          mode={mode}
          response={response}
          error={error}
        />

        {response ? (
          <div data-testid="response-panel">
            <h2 style={{ margin: "0 0 0.5rem 0", fontSize: "1rem" }}>
              Flow JSON{" "}
              <span style={{ fontSize: 12, color: "var(--fg-muted, #5b6470)" }}>
                — recipes, datasets, and the DAG payload below
              </span>
            </h2>
            <div
              style={{
                display: "flex",
                gap: "0.5rem",
                alignItems: "center",
                flexWrap: "wrap",
                marginBottom: "0.5rem",
              }}
            >
              <ExportButtons
                flow={response.flow}
                clientImpl={props.exportClientImpl}
              />
              <button
                type="button"
                data-testid="share-flow-button"
                onClick={onShare}
                disabled={sharing}
                aria-disabled={sharing}
                style={{
                  padding: "0.4rem 0.8rem",
                  borderRadius: 6,
                  border: "1px solid var(--color-grid, #e0e0e0)",
                  background: "transparent",
                  color: "inherit",
                  cursor: sharing ? "not-allowed" : "pointer",
                  fontSize: 13,
                  opacity: sharing ? 0.6 : 1,
                }}
              >
                {sharing ? "Sharing…" : "Share this flow"}
              </button>
            </div>
            <ValidationPanel
              flow={response.flow}
              warnings={response.warnings}
              defaultOpen={validationOpen}
              key={validationOpen ? "open" : "closed"}
              clientImpl={cli}
            />
            <NodeList flow={response.flow} />
            <NodeInspector />
            <JsonView value={response.flow} />
          </div>
        ) : null}
      </div>
    </section>
  );
}

/** Compact, accessible list of recipe nodes for click-to-inspect. */
function NodeList(props: { flow: Record<string, unknown> }): JSX.Element | null {
  const setSelectedNodeId = useFlowStore((s) => s.setSelectedNodeId);
  const selectedId = useFlowStore((s) => s.selectedNodeId);
  const recipes = ((props.flow.recipes as Array<{ name: string; type: string }>) ?? []).filter(
    (r) => typeof r?.name === "string",
  );
  if (recipes.length === 0) return null;
  return (
    <nav
      data-testid="node-list"
      aria-label="Flow nodes"
      style={{
        display: "flex",
        flexWrap: "wrap",
        gap: "0.4rem",
        margin: "0.5rem 0",
      }}
    >
      {recipes.map((r) => {
        const active = selectedId === r.name;
        return (
          <button
            key={r.name}
            type="button"
            data-testid={`node-list-item-${r.name}`}
            aria-pressed={active}
            onClick={() => setSelectedNodeId(active ? null : r.name)}
            style={{
              padding: "0.25rem 0.6rem",
              borderRadius: 999,
              border: "1px solid var(--color-grid, #e0e0e0)",
              background: active
                ? "var(--color-connectionhover, #1976d2)"
                : "transparent",
              color: active ? "white" : "inherit",
              cursor: "pointer",
              fontSize: 12,
            }}
          >
            <strong>{r.name}</strong>
            <span style={{ marginLeft: 6, opacity: 0.7 }}>{r.type}</span>
          </button>
        );
      })}
    </nav>
  );
}

function ProgressLog(props: {
  events: { event: string; seq: number; ts: string; payload: Record<string, unknown> }[];
}): JSX.Element {
  return (
    <ol
      data-testid="progress-log"
      style={{
        marginTop: "0.75rem",
        padding: "0.5rem 0.75rem 0.5rem 2rem",
        border: "1px solid var(--color-grid, #e0e0e0)",
        borderRadius: 6,
        fontSize: 12,
        fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace",
        listStyle: "decimal",
        maxHeight: 220,
        overflow: "auto",
      }}
    >
      {props.events.map((e) => (
        <li key={`${e.seq}-${e.event}`} data-testid={`progress-${e.event}`}>
          <span style={{ color: "var(--fg-muted, #5b6470)" }}>{shortTs(e.ts)}</span>{" "}
          <strong>{e.event}</strong>
          {summary(e) ? <span style={{ color: "var(--fg-muted, #5b6470)" }}> — {summary(e)}</span> : null}
        </li>
      ))}
    </ol>
  );
}

function shortTs(ts: string): string {
  // Render only HH:MM:SS.mmm portion if parseable; else passthrough.
  const d = new Date(ts);
  if (Number.isNaN(d.getTime())) return ts;
  return d.toISOString().slice(11, 23);
}

function summary(e: {
  event: string;
  payload: Record<string, unknown>;
}): string | null {
  switch (e.event) {
    case "started":
      return `${e.payload.mode ?? "?"} mode, ${e.payload.code_size_bytes ?? 0} B`;
    case "ast_parsed":
      return `${e.payload.node_count ?? 0} AST nodes`;
    case "recipe_created":
      return `${e.payload.recipe_type ?? "?"}: ${e.payload.recipe_name ?? "?"}`;
    case "processor_added":
      return `${e.payload.recipe_name}: ${e.payload.processor_type} #${e.payload.step_index ?? 0}`;
    case "optimized":
      return `reduction=${e.payload.reduction_count ?? 0}`;
    case "completed":
      return "done";
    case "error":
      return String(e.payload.title ?? "error");
    case "cancelled":
      return "by user";
    case "ping":
      return "keepalive";
    default:
      return null;
  }
}

function ModeToggle(props: {
  mode: ConversionMode;
  onChange: (m: ConversionMode) => void;
}): JSX.Element {
  return (
    <div
      role="radiogroup"
      aria-label="Conversion mode"
      style={{
        display: "inline-flex",
        border: "1px solid var(--color-grid, #e0e0e0)",
        borderRadius: 6,
        overflow: "hidden",
      }}
    >
      {(["rule", "llm"] as const).map((m) => (
        <button
          key={m}
          type="button"
          role="radio"
          aria-checked={props.mode === m}
          onClick={() => props.onChange(m)}
          style={{
            padding: "0.4rem 0.9rem",
            border: 0,
            background:
              props.mode === m
                ? "var(--color-connectionhover, #1976d2)"
                : "transparent",
            color: props.mode === m ? "white" : "inherit",
            cursor: "pointer",
            fontSize: 14,
            textTransform: "uppercase",
          }}
        >
          {m}
        </button>
      ))}
    </div>
  );
}

function StatusPanel(props: {
  status: string;
  mode: ConversionMode;
  response: ConvertResponse | null;
  error: { title: string; detail?: string; status: number } | null;
}): JSX.Element {
  const { status, mode, response, error } = props;
  const card = (label: string, value: string | number, testId?: string) => (
    <div
      key={label}
      data-testid={testId}
      style={{
        padding: "0.6rem 0.8rem",
        borderRadius: 6,
        border: "1px solid var(--color-grid, #e0e0e0)",
        minWidth: 120,
      }}
    >
      <div style={{ fontSize: 11, color: "var(--fg-muted, #5b6470)", textTransform: "uppercase" }}>
        {label}
      </div>
      <div style={{ fontSize: 18, fontWeight: 600 }}>{value}</div>
    </div>
  );

  if (error) {
    return (
      <div
        role="alert"
        data-testid="status-error"
        style={{
          padding: "0.75rem 1rem",
          borderRadius: 6,
          border: "1px solid #d32f2f",
          background: "rgba(211,47,47,0.08)",
          color: "#b71c1c",
        }}
      >
        <div style={{ fontWeight: 600 }}>
          {error.status > 0 ? `HTTP ${error.status} — ` : ""}
          {error.title}
        </div>
        {error.detail ? <div style={{ fontSize: 13 }}>{error.detail}</div> : null}
      </div>
    );
  }

  if (response) {
    return (
      <div
        data-testid="status-success"
        style={{ display: "flex", gap: "0.5rem", flexWrap: "wrap" }}
      >
        {card("Mode", mode)}
        {card("Complexity", response.score.complexity, "stat-complexity")}
        {card("Recipes", response.score.recipe_count)}
        <DatasetsTile
          loading={status === "running" || status === "streaming"}
          count={response.score.dataset_count}
          flow={response.flow as Record<string, unknown>}
        />
        {response.warnings.length > 0 ? card("Warnings", response.warnings.length) : null}
      </div>
    );
  }

  return (
    <div
      data-testid="status-idle"
      style={{
        padding: "0.75rem 1rem",
        borderRadius: 6,
        border: "1px dashed var(--color-grid, #e0e0e0)",
        color: "var(--fg-muted, #5b6470)",
        fontSize: 13,
      }}
    >
      {status === "running" || status === "streaming"
        ? "Converting…"
        : "Pick a snippet or paste Python, then click Convert."}
    </div>
  );
}

/**
 * Dedicated tile for the Datasets metric. Renders three states:
 *  - loading: a skeleton bar while a conversion is in flight.
 *  - empty: explanatory copy when the conversion produced no datasets.
 *  - populated: the count plus a tiny inline bar marker so the tile carries
 *    visual weight even before a real sparkline series is wired up.
 */
function DatasetsTile(props: {
  loading: boolean;
  count: number;
  flow: Record<string, unknown>;
}): JSX.Element {
  const { loading, count } = props;
  const tile: React.CSSProperties = {
    padding: "0.6rem 0.8rem",
    borderRadius: 6,
    border: "1px solid var(--color-grid, #e0e0e0)",
    minWidth: 140,
  };
  const label = (
    <div
      style={{
        fontSize: 11,
        color: "var(--fg-muted, #5b6470)",
        textTransform: "uppercase",
      }}
    >
      Datasets
    </div>
  );

  if (loading) {
    return (
      <div data-testid="stat-datasets" data-state="loading" style={tile}>
        {label}
        <div
          aria-hidden
          style={{
            marginTop: 6,
            height: 18,
            width: 64,
            borderRadius: 3,
            background:
              "linear-gradient(90deg, var(--color-grid, #e0e0e0) 25%, var(--color-bg, #fafafa) 50%, var(--color-grid, #e0e0e0) 75%)",
            backgroundSize: "200% 100%",
            animation: "py-iku-skeleton 1.2s ease-in-out infinite",
          }}
        />
        <span style={{ position: "absolute", left: -9999 }}>Loading datasets…</span>
      </div>
    );
  }

  if (count <= 0) {
    return (
      <div data-testid="stat-datasets" data-state="empty" style={tile}>
        {label}
        <div
          style={{
            fontSize: 13,
            color: "var(--fg-muted, #5b6470)",
            marginTop: 4,
            lineHeight: 1.35,
          }}
        >
          No datasets in this conversion.
        </div>
      </div>
    );
  }

  // Populated: show the count plus a tiny visual marker. We don't have a
  // historical series available client-side, so render a deterministic bar
  // sized to the count (clamped) — a real sparkline plugs in once the API
  // exposes per-conversion history.
  const filled = Math.min(8, Math.max(1, count));
  return (
    <div data-testid="stat-datasets" data-state="populated" style={tile}>
      {label}
      <div
        style={{
          display: "flex",
          alignItems: "baseline",
          gap: "0.5rem",
          marginTop: 2,
        }}
      >
        <div style={{ fontSize: 18, fontWeight: 600 }}>{count}</div>
        <div
          aria-hidden
          style={{
            display: "flex",
            gap: 2,
            height: 14,
            alignItems: "flex-end",
          }}
        >
          {Array.from({ length: 8 }).map((_, i) => (
            <span
              key={i}
              style={{
                display: "inline-block",
                width: 3,
                height: 4 + ((i % 4) + 1) * 2,
                background:
                  i < filled
                    ? "var(--color-connectionhover, #1976d2)"
                    : "var(--color-grid, #e0e0e0)",
                borderRadius: 1,
                opacity: i < filled ? 0.85 : 0.5,
              }}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

function Spinner(): JSX.Element {
  return (
    <span
      aria-hidden
      style={{
        display: "inline-block",
        width: 12,
        height: 12,
        marginRight: 6,
        borderRadius: "50%",
        border: "2px solid currentColor",
        borderTopColor: "transparent",
        animation: "py-iku-spin 0.7s linear infinite",
        verticalAlign: -2,
      }}
    />
  );
}

// Inject keyframes once. CSS-in-JS to keep the page self-contained — no
// extra stylesheet needed for these tiny animations.
if (typeof document !== "undefined" && !document.getElementById("py-iku-spin-keyframes")) {
  const style = document.createElement("style");
  style.id = "py-iku-spin-keyframes";
  style.textContent =
    "@keyframes py-iku-spin { to { transform: rotate(360deg); } } " +
    "@keyframes py-iku-skeleton { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }";
  document.head.appendChild(style);
}

function friendlyTitle(status: number, fallback: string): string {
  switch (status) {
    case 400:
      return "Invalid request";
    case 413:
      return "Code too large";
    case 422:
      return "Could not parse Python";
    case 500:
      return "Server error";
    case 0:
      return "Network error";
    default:
      return fallback;
  }
}

// Suppress unused-suffix warnings: useMemo is intentionally available for future use.
void useMemo;

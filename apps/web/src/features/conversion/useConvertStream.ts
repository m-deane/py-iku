import { useCallback, useEffect, useRef, useState } from "react";
import { useSettingsStore } from "../../state/settingsStore";
import type { ConvertRequest } from "../../api/client";

export type ConvertStreamStatus =
  | "idle"
  | "connecting"
  | "streaming"
  | "done"
  | "error"
  | "cancelled";

/** Subprotocol used to negotiate the WS handshake server-side. */
export const WS_SUBPROTOCOL = "py-iku-studio.v1";

/** Server event envelope: matches `WSEvent` in apps/api/app/schemas/events.py. */
export interface ProgressEvent {
  event: string;
  seq: number;
  ts: string;
  payload: Record<string, unknown>;
}

/** Minimal WebSocket-like surface used for testability. */
export interface WSLike {
  readyState: number;
  send(data: string): void;
  close(code?: number, reason?: string): void;
  onopen: ((ev: Event) => void) | null;
  onclose: ((ev: CloseEvent) => void) | null;
  onerror: ((ev: Event) => void) | null;
  onmessage: ((ev: MessageEvent) => void) | null;
}

/** Factory used by tests to inject a fake WebSocket. */
export type WSFactory = (url: string, protocols?: string | string[]) => WSLike;

export interface UseConvertStreamOptions {
  /** Override `import.meta.env.VITE_API_BASE_URL`. */
  baseUrl?: string;
  /** Test seam — supply a fake WebSocket factory. */
  wsFactory?: WSFactory;
}

/**
 * High-level phase derived from the latest progress event. Drives the visible
 * progress-bar label on `ConvertPage`. Distinct from `status` (lifecycle) and
 * the raw `progress[]` log.
 */
export type ConvertPhase =
  | "idle"
  | "connecting"
  | "analyzing" // ast_parsed
  | "calling_llm" // provider_call_started/completed
  | "building" // recipe_created / processor_added
  | "optimizing" // optimized
  | "done"
  | "error"
  | "cancelled";

export interface UseConvertStreamResult {
  status: ConvertStreamStatus;
  progress: ProgressEvent[];
  /** Coarse phase string suitable for status-line display. */
  phase: ConvertPhase;
  /** Percent complete in [0, 100]. Heuristic — the backend doesn't emit pct. */
  pct: number;
  flow: Record<string, unknown> | null;
  score: Record<string, unknown> | null;
  warnings: string[];
  error: { title: string; detail?: string; status: number } | null;
  start: (req: ConvertRequest) => void;
  cancel: () => void;
  reset: () => void;
}

/**
 * Backend emits 5 ordered milestone events plus optional LLM events. We map
 * each to a coarse percentage so the UI shows monotonic forward progress
 * without needing the backend to emit `pct`. Order:
 *   started → ast_parsed → recipe_created* → processor_added* → optimized → completed
 *
 * These were observed by tailing apps/api/app/services/conversion.py.
 */
const PHASE_FROM_EVENT: Record<string, { phase: ConvertPhase; pct: number }> = {
  started: { phase: "analyzing", pct: 10 },
  ast_parsed: { phase: "analyzing", pct: 25 },
  provider_call_started: { phase: "calling_llm", pct: 35 },
  provider_call_completed: { phase: "calling_llm", pct: 65 },
  recipe_created: { phase: "building", pct: 70 },
  processor_added: { phase: "building", pct: 80 },
  optimized: { phase: "optimizing", pct: 92 },
  completed: { phase: "done", pct: 100 },
  cancelled: { phase: "cancelled", pct: 0 },
  error: { phase: "error", pct: 0 },
};

export function derivePhase(
  events: readonly ProgressEvent[],
  status: ConvertStreamStatus,
): { phase: ConvertPhase; pct: number } {
  if (status === "idle") return { phase: "idle", pct: 0 };
  if (status === "connecting" && events.length === 0)
    return { phase: "connecting", pct: 5 };
  if (status === "error") return { phase: "error", pct: 0 };
  if (status === "cancelled") return { phase: "cancelled", pct: 0 };
  if (status === "done") return { phase: "done", pct: 100 };

  // Walk events in reverse, picking the first known mapping. `recipe_created`
  // and `processor_added` repeat — the heuristic ratchets monotonically since
  // we already filter on the latest known mapping.
  let best: { phase: ConvertPhase; pct: number } = { phase: "connecting", pct: 5 };
  for (const ev of events) {
    const mapped = PHASE_FROM_EVENT[ev.event];
    if (!mapped) continue;
    if (mapped.pct >= best.pct) best = mapped;
  }
  return best;
}

/** Convert an http(s) base URL into a ws(s) URL pointing at /convert/stream. */
export function deriveWsUrl(baseUrl: string): string {
  const trimmed = baseUrl.replace(/\/$/, "");
  if (trimmed.startsWith("https://")) {
    return `wss://${trimmed.slice("https://".length)}/convert/stream`;
  }
  if (trimmed.startsWith("http://")) {
    return `ws://${trimmed.slice("http://".length)}/convert/stream`;
  }
  // Already a ws URL or relative — append path.
  if (trimmed.startsWith("ws://") || trimmed.startsWith("wss://")) {
    return `${trimmed}/convert/stream`;
  }
  return `${trimmed}/convert/stream`;
}

function resolveBaseUrl(override?: string): string {
  if (override) return override;
  // Pull from settings store first; fall back to env then localhost.
  try {
    const fromStore = useSettingsStore.getState().apiBaseUrl;
    if (fromStore) return fromStore;
  } catch {
    /* no-op */
  }
  // Vite env shim: `import.meta.env` is replaced at build time; safe in tests via define.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const env = (import.meta as any).env as Record<string, string | undefined> | undefined;
  return env?.VITE_API_BASE_URL ?? "http://localhost:8000";
}

/**
 * useConvertStream — opens a WebSocket to `/convert/stream`, sends the request,
 * surfaces progress events, the final flow, and a `cancel()` action.
 *
 * The hook is uncontrolled w.r.t. the WS lifecycle: callers invoke `start(req)`
 * which (re)opens the socket, transitions through connecting → streaming → done,
 * and exposes accumulated events via `progress`.
 */
export function useConvertStream(
  options: UseConvertStreamOptions = {},
): UseConvertStreamResult {
  const [status, setStatus] = useState<ConvertStreamStatus>("idle");
  const [progress, setProgress] = useState<ProgressEvent[]>([]);
  const [flow, setFlow] = useState<Record<string, unknown> | null>(null);
  const [score, setScore] = useState<Record<string, unknown> | null>(null);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [error, setError] = useState<{ title: string; detail?: string; status: number } | null>(
    null,
  );

  const socketRef = useRef<WSLike | null>(null);
  const pendingRequestRef = useRef<ConvertRequest | null>(null);

  const cleanupSocket = useCallback(() => {
    const sock = socketRef.current;
    if (sock) {
      sock.onopen = null;
      sock.onclose = null;
      sock.onerror = null;
      sock.onmessage = null;
      try {
        sock.close();
      } catch {
        /* no-op */
      }
    }
    socketRef.current = null;
  }, []);

  const reset = useCallback(() => {
    cleanupSocket();
    pendingRequestRef.current = null;
    setStatus("idle");
    setProgress([]);
    setFlow(null);
    setScore(null);
    setWarnings([]);
    setError(null);
  }, [cleanupSocket]);

  const start = useCallback(
    (req: ConvertRequest) => {
      cleanupSocket();
      setProgress([]);
      setFlow(null);
      setScore(null);
      setWarnings([]);
      setError(null);
      setStatus("connecting");

      const baseUrl = resolveBaseUrl(options.baseUrl);
      const wsUrl = deriveWsUrl(baseUrl);
      const factory: WSFactory =
        options.wsFactory ??
        ((u, p) => new WebSocket(u, p) as unknown as WSLike);

      let sock: WSLike;
      try {
        sock = factory(wsUrl, WS_SUBPROTOCOL);
      } catch (err) {
        setError({
          title: "Failed to open WebSocket",
          detail: err instanceof Error ? err.message : String(err),
          status: 0,
        });
        setStatus("error");
        return;
      }

      socketRef.current = sock;
      pendingRequestRef.current = req;

      sock.onopen = () => {
        try {
          sock.send(JSON.stringify(req));
          setStatus("streaming");
        } catch (err) {
          setError({
            title: "Failed to send request",
            detail: err instanceof Error ? err.message : String(err),
            status: 0,
          });
          setStatus("error");
        }
      };

      sock.onmessage = (ev: MessageEvent) => {
        let parsed: unknown;
        try {
          parsed = typeof ev.data === "string" ? JSON.parse(ev.data) : ev.data;
        } catch {
          return; // malformed frame — drop
        }
        if (typeof parsed !== "object" || parsed === null) return;
        const data = parsed as Partial<ProgressEvent> & {
          type?: string;
          status?: number;
          title?: string;
          detail?: string;
          payload?: Record<string, unknown>;
        };

        // Problem+JSON shape (server sends on validation reject before any envelope)
        if (
          data.event === undefined &&
          typeof data.status === "number" &&
          typeof data.title === "string"
        ) {
          setError({
            title: data.title,
            detail: data.detail,
            status: data.status,
          });
          setStatus("error");
          return;
        }

        if (typeof data.event !== "string") return;

        const evt: ProgressEvent = {
          event: data.event,
          seq: typeof data.seq === "number" ? data.seq : 0,
          ts: typeof data.ts === "string" ? data.ts : new Date().toISOString(),
          payload: (data.payload as Record<string, unknown>) ?? {},
        };

        setProgress((prev) => [...prev, evt]);

        if (evt.event === "completed") {
          const payload = evt.payload as {
            flow?: Record<string, unknown>;
            score?: Record<string, unknown>;
            warnings?: string[];
          };
          if (payload.flow) setFlow(payload.flow);
          if (payload.score) setScore(payload.score);
          if (payload.warnings) setWarnings(payload.warnings);
          setStatus("done");
        } else if (evt.event === "error") {
          const payload = evt.payload as {
            title?: string;
            detail?: string;
            status?: number;
          };
          setError({
            title: payload.title ?? "Conversion failed",
            detail: payload.detail,
            status: payload.status ?? 500,
          });
          setStatus("error");
        } else if (evt.event === "cancelled") {
          setStatus("cancelled");
        }
      };

      sock.onerror = () => {
        // Don't overwrite a more specific status (done/cancelled) the server set.
        setStatus((prev) =>
          prev === "done" || prev === "cancelled" || prev === "error" ? prev : "error",
        );
      };

      sock.onclose = () => {
        // Mark as cancelled if still streaming when the socket closed.
        setStatus((prev) =>
          prev === "streaming" || prev === "connecting" ? "cancelled" : prev,
        );
      };
    },
    [cleanupSocket, options.baseUrl, options.wsFactory],
  );

  const cancel = useCallback(() => {
    const sock = socketRef.current;
    if (sock && sock.readyState === 1) {
      try {
        sock.send(JSON.stringify({ action: "cancel" }));
      } catch {
        /* swallow */
      }
    }
    setStatus((prev) =>
      prev === "streaming" || prev === "connecting" ? "cancelled" : prev,
    );
    cleanupSocket();
  }, [cleanupSocket]);

  // Cleanup on unmount.
  useEffect(() => {
    return () => {
      cleanupSocket();
    };
  }, [cleanupSocket]);

  const { phase, pct } = derivePhase(progress, status);

  return {
    status,
    progress,
    phase,
    pct,
    flow,
    score,
    warnings,
    error,
    start,
    cancel,
    reset,
  };
}

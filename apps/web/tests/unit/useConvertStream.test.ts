import { describe, it, expect, beforeEach } from "vitest";
import { act, renderHook } from "@testing-library/react";
import {
  useConvertStream,
  deriveWsUrl,
  derivePhase,
  WS_SUBPROTOCOL,
  type WSLike,
  type ProgressEvent,
} from "../../src/features/conversion/useConvertStream";
import { useSettingsStore } from "../../src/state/settingsStore";

class FakeSocket implements WSLike {
  readyState = 0; // CONNECTING
  sent: string[] = [];
  closeCalls: { code?: number; reason?: string }[] = [];
  onopen: ((ev: Event) => void) | null = null;
  onclose: ((ev: CloseEvent) => void) | null = null;
  onerror: ((ev: Event) => void) | null = null;
  onmessage: ((ev: MessageEvent) => void) | null = null;
  url: string;
  protocols?: string | string[];

  constructor(url: string, protocols?: string | string[]) {
    this.url = url;
    this.protocols = protocols;
    FakeSocket.last = this;
  }

  send(data: string): void {
    this.sent.push(data);
  }

  close(code?: number, reason?: string): void {
    this.readyState = 3; // CLOSED
    this.closeCalls.push({ code, reason });
  }

  // Test helpers — drive the lifecycle from outside.
  open(): void {
    this.readyState = 1; // OPEN
    this.onopen?.(new Event("open"));
  }

  emit(payload: unknown): void {
    this.onmessage?.(new MessageEvent("message", { data: JSON.stringify(payload) }));
  }

  static last: FakeSocket | null = null;
}

function makeFactory() {
  return (url: string, protocols?: string | string[]) => new FakeSocket(url, protocols);
}

describe("derivePhase", () => {
  function ev(name: string): ProgressEvent {
    return { event: name, seq: 0, ts: "2026-01-01T00:00:00Z", payload: {} };
  }

  it("returns idle/0 for idle status", () => {
    expect(derivePhase([], "idle")).toEqual({ phase: "idle", pct: 0 });
  });

  it("returns connecting at 5% before any event", () => {
    const r = derivePhase([], "connecting");
    expect(r.phase).toBe("connecting");
    expect(r.pct).toBe(5);
  });

  it("ratchets pct monotonically through the rule-mode pipeline", () => {
    expect(derivePhase([ev("started")], "streaming").pct).toBe(10);
    expect(
      derivePhase([ev("started"), ev("ast_parsed")], "streaming").pct,
    ).toBe(25);
    expect(
      derivePhase(
        [ev("started"), ev("ast_parsed"), ev("recipe_created")],
        "streaming",
      ).pct,
    ).toBe(70);
    expect(
      derivePhase(
        [
          ev("started"),
          ev("ast_parsed"),
          ev("recipe_created"),
          ev("processor_added"),
          ev("optimized"),
        ],
        "streaming",
      ).pct,
    ).toBe(92);
  });

  it("locks to done/100 once status is done", () => {
    expect(derivePhase([ev("completed")], "done")).toEqual({
      phase: "done",
      pct: 100,
    });
  });

  it("LLM mode surfaces calling_llm phase between provider events", () => {
    const phase = derivePhase(
      [ev("started"), ev("provider_call_started")],
      "streaming",
    );
    expect(phase.phase).toBe("calling_llm");
  });
});

describe("deriveWsUrl", () => {
  it("converts http base to ws", () => {
    expect(deriveWsUrl("http://localhost:8000")).toBe("ws://localhost:8000/convert/stream");
  });

  it("converts https base to wss", () => {
    expect(deriveWsUrl("https://api.example.com")).toBe(
      "wss://api.example.com/convert/stream",
    );
  });

  it("strips trailing slash before appending the path", () => {
    expect(deriveWsUrl("http://localhost:8000/")).toBe("ws://localhost:8000/convert/stream");
  });
});

describe("useConvertStream", () => {
  beforeEach(() => {
    FakeSocket.last = null;
    act(() => {
      useSettingsStore.getState().reset();
    });
  });

  it("starts in idle and transitions through connecting → streaming → done", () => {
    const factory = makeFactory();
    const { result } = renderHook(() => useConvertStream({ wsFactory: factory }));

    expect(result.current.status).toBe("idle");

    act(() => {
      result.current.start({ code: "x = 1\n", mode: "rule" });
    });
    expect(result.current.status).toBe("connecting");
    expect(FakeSocket.last).not.toBeNull();
    expect(FakeSocket.last!.protocols).toBe(WS_SUBPROTOCOL);

    act(() => {
      FakeSocket.last!.open();
    });
    expect(result.current.status).toBe("streaming");
    expect(FakeSocket.last!.sent[0]).toContain('"code":"x = 1\\n"');

    act(() => {
      FakeSocket.last!.emit({
        event: "started",
        seq: 0,
        ts: "2026-01-01T00:00:00Z",
        payload: { mode: "rule", code_size_bytes: 6 },
      });
    });
    act(() => {
      FakeSocket.last!.emit({
        event: "ast_parsed",
        seq: 1,
        ts: "2026-01-01T00:00:00.100Z",
        payload: { node_count: 3 },
      });
    });
    expect(result.current.progress).toHaveLength(2);
    expect(result.current.progress[0].event).toBe("started");
    expect(result.current.progress[1].event).toBe("ast_parsed");

    const finalFlow = { flow_name: "x", recipes: [], datasets: [], total_recipes: 0, total_datasets: 0 };
    const finalScore = { recipe_count: 0, complexity: 0, max_depth: 0, fan_out_max: 0, processor_count: 0 };
    act(() => {
      FakeSocket.last!.emit({
        event: "completed",
        seq: 2,
        ts: "2026-01-01T00:00:00.200Z",
        payload: { flow: finalFlow, score: finalScore, warnings: [] },
      });
    });

    expect(result.current.status).toBe("done");
    expect(result.current.flow).toEqual(finalFlow);
    expect(result.current.score).toEqual(finalScore);
    expect(result.current.progress).toHaveLength(3);
  });

  it("transitions to error when the server emits an error event", () => {
    const factory = makeFactory();
    const { result } = renderHook(() => useConvertStream({ wsFactory: factory }));

    act(() => {
      result.current.start({ code: "x", mode: "rule" });
    });
    act(() => {
      FakeSocket.last!.open();
    });
    act(() => {
      FakeSocket.last!.emit({
        event: "error",
        seq: 0,
        ts: "2026-01-01T00:00:00Z",
        payload: { title: "Bad code", detail: "SyntaxError", status: 400 },
      });
    });

    expect(result.current.status).toBe("error");
    expect(result.current.error?.title).toBe("Bad code");
    expect(result.current.error?.status).toBe(400);
  });

  it("cancel() sends the cancel action and transitions to cancelled", () => {
    const factory = makeFactory();
    const { result } = renderHook(() => useConvertStream({ wsFactory: factory }));

    act(() => {
      result.current.start({ code: "x", mode: "rule" });
    });
    act(() => {
      FakeSocket.last!.open();
    });
    act(() => {
      result.current.cancel();
    });

    expect(result.current.status).toBe("cancelled");
    expect(FakeSocket.last!.sent.some((s) => s.includes('"cancel"'))).toBe(true);
  });

  it("reset() clears state back to idle", () => {
    const factory = makeFactory();
    const { result } = renderHook(() => useConvertStream({ wsFactory: factory }));
    act(() => {
      result.current.start({ code: "x", mode: "rule" });
    });
    act(() => {
      FakeSocket.last!.open();
    });
    act(() => {
      FakeSocket.last!.emit({
        event: "started",
        seq: 0,
        ts: "2026-01-01T00:00:00Z",
        payload: { mode: "rule", code_size_bytes: 1 },
      });
    });
    expect(result.current.progress).toHaveLength(1);
    act(() => {
      result.current.reset();
    });
    expect(result.current.status).toBe("idle");
    expect(result.current.progress).toHaveLength(0);
  });

  it("handles a problem+json frame received before any envelope", () => {
    const factory = makeFactory();
    const { result } = renderHook(() => useConvertStream({ wsFactory: factory }));
    act(() => {
      result.current.start({ code: "x", mode: "rule" });
    });
    act(() => {
      FakeSocket.last!.open();
    });
    act(() => {
      FakeSocket.last!.emit({
        type: "https://py-iku.dev/errors/ValidationError",
        title: "Validation Error",
        status: 422,
        detail: "code must not be empty",
      });
    });
    expect(result.current.status).toBe("error");
    expect(result.current.error?.status).toBe(422);
  });
});

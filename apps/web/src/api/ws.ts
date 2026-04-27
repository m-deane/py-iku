/**
 * WSClient — minimal websocket wrapper for the streaming conversion endpoint.
 *
 * Not wired to the UI yet (M5 will integrate with `flowStore`). This file ships now so the
 * shell can reference `import("@/api/ws")` without breaking typechecking.
 */

export interface WSEnvelope<T = unknown> {
  event: string;
  seq: number;
  ts: string;
  payload: T;
}

export type WSStatus = "idle" | "connecting" | "open" | "closed" | "error";

export interface WSClientOptions {
  url: string;
  onMessage?: (env: WSEnvelope) => void;
  onStatus?: (status: WSStatus) => void;
  /** TODO M5: real backoff strategy. Set false to disable auto-reconnect. */
  reconnect?: boolean;
}

export class WSClient {
  private socket: WebSocket | null = null;
  private status: WSStatus = "idle";
  private readonly opts: WSClientOptions;

  constructor(opts: WSClientOptions) {
    this.opts = opts;
  }

  open(): void {
    if (this.socket && this.status === "open") return;
    this.setStatus("connecting");
    const sock = new WebSocket(this.opts.url);
    sock.onopen = () => this.setStatus("open");
    sock.onclose = () => this.setStatus("closed");
    sock.onerror = () => this.setStatus("error");
    sock.onmessage = (ev: MessageEvent<string>) => {
      try {
        const data = JSON.parse(ev.data) as WSEnvelope;
        this.opts.onMessage?.(data);
      } catch {
        // malformed frame — ignore in skeleton; M5 surfaces via toast.
      }
    };
    this.socket = sock;
  }

  send(payload: unknown): void {
    if (!this.socket || this.status !== "open") {
      throw new Error("WSClient: socket not open");
    }
    this.socket.send(JSON.stringify(payload));
  }

  close(): void {
    this.socket?.close();
    this.socket = null;
    this.setStatus("closed");
  }

  getStatus(): WSStatus {
    return this.status;
  }

  private setStatus(status: WSStatus): void {
    this.status = status;
    this.opts.onStatus?.(status);
  }
}

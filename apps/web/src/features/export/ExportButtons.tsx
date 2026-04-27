import { toast } from "sonner";
import {
  client as defaultClient,
  type ExportFormat,
  type ExportResult,
} from "../../api/client";

const FORMATS: ExportFormat[] = ["zip", "json", "yaml", "svg", "png", "pdf"];

export interface ExportButtonsProps {
  /** The flow to export — typically the current flow from flowStore. */
  flow: Record<string, unknown> | null;
  /** Test seam — swap in a stub client without mocking modules. */
  clientImpl?: typeof defaultClient;
  /** Test seam — override the post-download side-effect (e.g. toast/anchor). */
  onExported?: (format: ExportFormat, result: ExportResult) => void;
}

function triggerDownload(blob: Blob, filename: string): void {
  if (typeof window === "undefined" || typeof document === "undefined") return;
  const url = URL.createObjectURL(blob);
  try {
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = filename;
    document.body.appendChild(anchor);
    anchor.click();
    anchor.remove();
  } finally {
    // Defer revoke to next tick so the click is observed first.
    setTimeout(() => URL.revokeObjectURL(url), 0);
  }
}

export function ExportButtons(props: ExportButtonsProps): JSX.Element {
  const apiClient = props.clientImpl ?? defaultClient;
  const disabled = !props.flow;

  const onExport = async (fmt: ExportFormat): Promise<void> => {
    if (!props.flow) return;
    try {
      const result = await apiClient.export(fmt, props.flow);
      if (props.onExported) {
        props.onExported(fmt, result);
      } else {
        triggerDownload(result.blob, result.filename);
        try {
          toast.success(`Exported ${result.filename}`);
        } catch {
          /* toast harness not mounted in tests */
        }
      }
    } catch (err) {
      const detail = err instanceof Error ? err.message : String(err);
      try {
        toast.error(`Export failed (${fmt})`, { description: detail });
      } catch {
        /* swallow */
      }
    }
  };

  return (
    <div
      role="group"
      aria-label="Export flow"
      data-testid="export-buttons"
      style={{ display: "flex", gap: "0.4rem", flexWrap: "wrap" }}
    >
      <span style={{ fontSize: 12, color: "var(--color-grid, #888)", alignSelf: "center" }}>
        Export:
      </span>
      {FORMATS.map((fmt) => (
        <button
          key={fmt}
          type="button"
          onClick={() => onExport(fmt)}
          disabled={disabled}
          aria-disabled={disabled}
          data-testid={`export-${fmt}`}
          style={{
            padding: "0.35rem 0.7rem",
            borderRadius: 6,
            border: "1px solid var(--color-grid, #e0e0e0)",
            background: "transparent",
            color: "inherit",
            cursor: disabled ? "not-allowed" : "pointer",
            opacity: disabled ? 0.5 : 1,
            fontSize: 12,
            textTransform: "uppercase",
            letterSpacing: "0.04em",
          }}
        >
          {fmt}
        </button>
      ))}
    </div>
  );
}

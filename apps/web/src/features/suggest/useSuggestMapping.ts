import { useCallback, useState } from "react";
import {
  client as defaultClient,
  type SuggestMappingRequest,
  type SuggestMappingResponse,
} from "../../api/client";

/**
 * Suggest-mapping for PYTHON-recipe banner. Unlike explain, we don't cache
 * locally — the LLM is consulted per click and the response sits in the
 * banner until the user dismisses or accepts. The server-side audit log
 * captures the call so the LLM-history page surfaces it alongside chat /
 * convert / explain.
 */

export type SuggestStatus = "idle" | "loading" | "ready" | "error";

export interface UseSuggestOptions {
  /** Test seam — swap in a stub `client.suggestMapping`. */
  clientImpl?: { suggestMapping: typeof defaultClient.suggestMapping };
}

export interface UseSuggestResult {
  status: SuggestStatus;
  data: SuggestMappingResponse | null;
  error: { title: string; detail?: string } | null;
  request: (req: SuggestMappingRequest) => Promise<void>;
  reset: () => void;
}

export function useSuggestMapping(
  options: UseSuggestOptions = {},
): UseSuggestResult {
  const client = options.clientImpl ?? {
    suggestMapping: defaultClient.suggestMapping,
  };
  const [status, setStatus] = useState<SuggestStatus>("idle");
  const [data, setData] = useState<SuggestMappingResponse | null>(null);
  const [error, setError] = useState<
    { title: string; detail?: string } | null
  >(null);

  const request = useCallback(
    async (req: SuggestMappingRequest): Promise<void> => {
      setError(null);
      setStatus("loading");
      try {
        const resp = await client.suggestMapping(req);
        setData(resp);
        setStatus("ready");
      } catch (e) {
        const err = e as { title?: string; detail?: string; message?: string };
        setError({
          title: err.title ?? "Suggest failed",
          detail: err.detail ?? err.message,
        });
        setStatus("error");
      }
    },
    [client],
  );

  const reset = useCallback(() => {
    setStatus("idle");
    setData(null);
    setError(null);
  }, []);

  return { status, data, error, request, reset };
}

/** Confidence threshold above which the "Apply" CTA is enabled. */
export const APPLY_CONFIDENCE_THRESHOLD = 0.7;

/**
 * Apply the suggestion to a Monaco editor instance. The function is exported
 * separately from the React component so unit tests can drive it with a
 * stub editor that records ``executeEdits`` calls. The Monaco type is
 * intentionally minimal — we only need the methods the runtime exposes.
 */
export interface MonacoLikeEditor {
  getModel: () => {
    getValue: () => string;
    findMatches: (
      searchString: string,
      searchOnlyEditableRange: boolean,
      isRegex: boolean,
      matchCase: boolean,
      wordSeparators: string | null,
      captureMatches: boolean,
    ) => Array<{
      range: {
        startLineNumber: number;
        startColumn: number;
        endLineNumber: number;
        endColumn: number;
      };
    }>;
    getFullModelRange: () => {
      startLineNumber: number;
      startColumn: number;
      endLineNumber: number;
      endColumn: number;
    };
  } | null;
  executeEdits: (
    source: string,
    edits: Array<{
      range: {
        startLineNumber: number;
        startColumn: number;
        endLineNumber: number;
        endColumn: number;
      };
      text: string;
      forceMoveMarkers?: boolean;
    }>,
  ) => boolean;
}

/**
 * Replace ``original`` with ``replacement`` inside the editor. Falls back to
 * a full-model swap if the original snippet isn't found exactly — that keeps
 * the Apply CTA functional even when the user has edited the source after
 * the suggestion fetched.
 */
export function applySuggestionToEditor(
  editor: MonacoLikeEditor,
  original: string,
  replacement: string,
): { applied: boolean; mode: "exact" | "full-replace" | "noop" } {
  const model = editor.getModel();
  if (!model) return { applied: false, mode: "noop" };

  const matches = model.findMatches(
    original,
    /* searchOnlyEditableRange */ true,
    /* isRegex */ false,
    /* matchCase */ true,
    /* wordSeparators */ null,
    /* captureMatches */ false,
  );

  if (matches.length > 0) {
    const range = matches[0].range;
    const ok = editor.executeEdits("py-iku-suggest-mapping", [
      { range, text: replacement, forceMoveMarkers: true },
    ]);
    return { applied: ok, mode: "exact" };
  }

  // Fallback: replace the whole model.
  const range = model.getFullModelRange();
  const ok = editor.executeEdits("py-iku-suggest-mapping", [
    { range, text: replacement, forceMoveMarkers: true },
  ]);
  return { applied: ok, mode: "full-replace" };
}

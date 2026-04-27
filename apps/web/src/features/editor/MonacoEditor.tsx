import { Suspense, lazy, useEffect, useMemo, useRef, useState } from "react";
import { useFlowStore } from "../../state/flowStore";
import { getDefaultCode } from "./snippets";

export interface MonacoEditorProps {
  /** Controlled value. When omitted, falls back to the default snippet. */
  value?: string;
  /** Called after the debounce window (default 250ms). */
  onChange?: (value: string) => void;
  /** Editor height (any CSS value). Default `60vh`. */
  height?: string;
  /** Disable editing (used during conversion). */
  readOnly?: boolean;
  /** Test hook so we can render in jsdom without spinning up real Monaco. */
  fallbackTextarea?: boolean;
}

const DEBOUNCE_MS = 250;

/**
 * Lazy-loaded inner Monaco editor.
 *
 * `@monaco-editor/react` AND the `monaco-editor` worker setup are both
 * deferred behind this `React.lazy()` boundary. On a cold load of `/convert`,
 * the user sees a `<textarea>` fallback first; the moment they focus the
 * editor we trigger the dynamic import, swap the chunks in, and re-render
 * with the real Monaco surface. This keeps Monaco out of the initial
 * navigation waterfall — the chunk only ships when the user actually edits.
 *
 * The split point is `./MonacoEditorInner.tsx` so the bundler can carve
 * `@monaco-editor/react` into its own JS chunk.
 */
const MonacoEditorInner = lazy(() =>
  import("./MonacoEditorInner").then((m) => ({ default: m.MonacoEditorInner })),
);

/**
 * Public Monaco editor wrapper used across the app.
 *
 * Behaviour:
 *   1. Renders a styled `<textarea>` fallback for first paint — the user can
 *      already type, so the editor is interactive from millisecond one.
 *   2. On the first `focus` event we set `boost=true`, which causes the
 *      `Suspense` boundary below to start loading the `@monaco-editor/react`
 *      chunk + worker. Once it resolves, the inner component takes over and
 *      preserves the in-progress text via the `value` prop.
 *   3. The `fallbackTextarea` prop forces the textarea path forever. jsdom
 *      and visual regression tests rely on it.
 */
export function MonacoEditor(props: MonacoEditorProps): JSX.Element {
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const initial = useMemo(() => props.value ?? getDefaultCode(), [props.value]);
  const [localValue, setLocalValue] = useState<string>(initial);
  const [boosted, setBoosted] = useState<boolean>(false);
  const debounceRef = useRef<number | null>(null);

  // Push initial value into the store on first mount so consumers (Convert
  // button, etc.) see something even before the user types.
  useEffect(() => {
    setCurrentCode(initial);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // External `value` prop changes win over local state (e.g. snippet picker).
  useEffect(() => {
    if (props.value !== undefined && props.value !== localValue) {
      setLocalValue(props.value);
      setCurrentCode(props.value);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.value]);

  const handleChange = (next: string): void => {
    setLocalValue(next);
    if (debounceRef.current !== null) {
      window.clearTimeout(debounceRef.current);
    }
    debounceRef.current = window.setTimeout(() => {
      setCurrentCode(next);
      props.onChange?.(next);
    }, DEBOUNCE_MS);
  };

  // jsdom + visual-regression suites pin the textarea forever.
  if (props.fallbackTextarea) {
    return (
      <textarea
        aria-label="Python code"
        value={localValue}
        readOnly={props.readOnly}
        onChange={(e) => handleChange(e.target.value)}
        style={textareaStyle(props.height)}
      />
    );
  }

  // Cold-load path. We render a textarea until the user focuses it; on focus
  // we set `boosted` and the Suspense boundary kicks in to fetch the Monaco
  // chunks. The Suspense fallback continues to show the textarea so the
  // typing surface never disappears mid-load.
  if (!boosted) {
    return (
      <textarea
        data-testid="monaco-fallback"
        aria-label="Python code"
        value={localValue}
        readOnly={props.readOnly}
        onFocus={() => setBoosted(true)}
        onChange={(e) => handleChange(e.target.value)}
        style={textareaStyle(props.height)}
      />
    );
  }

  return (
    <Suspense
      fallback={
        <textarea
          data-testid="monaco-fallback-loading"
          aria-label="Python code"
          aria-busy="true"
          value={localValue}
          readOnly={props.readOnly}
          onChange={(e) => handleChange(e.target.value)}
          style={textareaStyle(props.height)}
        />
      }
    >
      <MonacoEditorInner
        value={localValue}
        height={props.height}
        readOnly={props.readOnly}
        onChange={handleChange}
      />
    </Suspense>
  );
}

function textareaStyle(height: string | undefined): React.CSSProperties {
  return {
    width: "100%",
    height: height ?? "60vh",
    fontFamily: "var(--font-mono, ui-monospace, SFMono-Regular, Menlo, Monaco, monospace)",
    fontSize: 14,
    padding: 12,
    border: "1px solid var(--border, #eaecf0)",
    borderRadius: "var(--radius-md, 6px)",
    background: "var(--surface, #fafafa)",
    color: "var(--fg, #212121)",
    resize: "vertical",
  };
}

import { useEffect, useMemo, useRef, useState } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";
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

function readDataTheme(): "vs" | "vs-dark" {
  if (typeof document === "undefined") return "vs";
  const t = document.documentElement.dataset.theme;
  return t === "dark" ? "vs-dark" : "vs";
}

/**
 * Thin wrapper around `@monaco-editor/react`'s `<Editor>` configured for
 * Python. The component owns local state for snappy keystroke updates and
 * debounces writes back to `flowStore.currentCode` so the rest of the app
 * doesn't re-render on every keypress.
 *
 * Theme tracks `<html data-theme>` (toggled by `ThemeApplier` in `providers.tsx`)
 * via a MutationObserver, so light/dark switching is fully reactive.
 */
export function MonacoEditor(props: MonacoEditorProps): JSX.Element {
  const setCurrentCode = useFlowStore((s) => s.setCurrentCode);
  const initial = useMemo(() => props.value ?? getDefaultCode(), [props.value]);
  const [localValue, setLocalValue] = useState<string>(initial);
  const [theme, setTheme] = useState<"vs" | "vs-dark">(() => readDataTheme());
  const debounceRef = useRef<number | null>(null);

  // Push initial value into the store on first mount so consumers (Convert
  // button, etc.) see something even before the user types.
  useEffect(() => {
    setCurrentCode(initial);
    // Intentionally only on mount — subsequent updates are debounced below.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Reactive theme: watch the `data-theme` attribute on <html>.
  useEffect(() => {
    if (typeof document === "undefined") return;
    const html = document.documentElement;
    const apply = (): void => setTheme(readDataTheme());
    apply();
    const observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        if (m.type === "attributes" && m.attributeName === "data-theme") {
          apply();
          return;
        }
      }
    });
    observer.observe(html, { attributes: true, attributeFilter: ["data-theme"] });
    return () => observer.disconnect();
  }, []);

  // External `value` prop changes win over local state (e.g. snippet picker).
  useEffect(() => {
    if (props.value !== undefined && props.value !== localValue) {
      setLocalValue(props.value);
      setCurrentCode(props.value);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [props.value]);

  const handleChange = (v: string | undefined): void => {
    const next = v ?? "";
    setLocalValue(next);
    if (debounceRef.current !== null) {
      window.clearTimeout(debounceRef.current);
    }
    debounceRef.current = window.setTimeout(() => {
      setCurrentCode(next);
      props.onChange?.(next);
    }, DEBOUNCE_MS);
  };

  const handleMount: OnMount = (_editor, _monaco) => {
    // Reserved for future M5 hooks (cursor position, decorations, etc.).
  };

  // jsdom can't render Monaco; tests pass `fallbackTextarea` to swap in a
  // plain textarea so component tests don't need to mock the editor module.
  if (props.fallbackTextarea) {
    return (
      <textarea
        aria-label="Python code"
        value={localValue}
        readOnly={props.readOnly}
        onChange={(e) => handleChange(e.target.value)}
        style={{
          width: "100%",
          height: props.height ?? "60vh",
          fontFamily: "ui-monospace, SFMono-Regular, Menlo, Monaco, monospace",
          fontSize: 14,
          padding: 12,
          border: "1px solid var(--color-grid, #e0e0e0)",
          borderRadius: 6,
          background: "var(--color-background, #fafafa)",
          color: "var(--color-fg, #212121)",
        }}
      />
    );
  }

  return (
    <div data-testid="monaco-editor">
      <Editor
        height={props.height ?? "60vh"}
        defaultLanguage="python"
        language="python"
        value={localValue}
        theme={theme}
        onMount={handleMount}
        onChange={handleChange}
        options={{
          minimap: { enabled: false },
          fontSize: 14,
          tabSize: 4,
          automaticLayout: true,
          wordWrap: "on",
          scrollBeyondLastLine: false,
          readOnly: props.readOnly ?? false,
          renderWhitespace: "selection",
          fixedOverflowWidgets: true,
        }}
      />
    </div>
  );
}

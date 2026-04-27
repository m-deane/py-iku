import { useEffect, useState } from "react";
import Editor, { type OnMount } from "@monaco-editor/react";

/**
 * Inner Monaco surface. Imported via `React.lazy` from `MonacoEditor.tsx`.
 *
 * Lives in its own module so Vite/Rollup can carve `@monaco-editor/react`
 * (and via its dynamic worker imports, the Monaco core JS) into a chunk
 * that's NOT pulled into the initial navigation waterfall on `/convert`.
 *
 * Importing this module also pulls in `monacoWorkers.ts` for its side-effect
 * (wiring `window.MonacoEnvironment.getWorker`), so the worker glue ships
 * with the same lazy chunk rather than from `main.tsx`.
 */
import "./monacoWorkers";

export interface MonacoEditorInnerProps {
  value: string;
  height?: string;
  readOnly?: boolean;
  onChange: (next: string) => void;
}

function readDataTheme(): "vs" | "vs-dark" {
  if (typeof document === "undefined") return "vs";
  const t = document.documentElement.dataset.theme;
  return t === "dark" ? "vs-dark" : "vs";
}

export function MonacoEditorInner(props: MonacoEditorInnerProps): JSX.Element {
  const [theme, setTheme] = useState<"vs" | "vs-dark">(() => readDataTheme());

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

  const handleMount: OnMount = (_editor, _monaco) => {
    // Reserved for future M5 hooks (cursor position, decorations, etc.).
  };

  return (
    <div data-testid="monaco-editor">
      <Editor
        height={props.height ?? "60vh"}
        defaultLanguage="python"
        language="python"
        value={props.value}
        theme={theme}
        onMount={handleMount}
        onChange={(v) => props.onChange(v ?? "")}
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

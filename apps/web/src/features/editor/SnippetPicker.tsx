import { useMemo, useRef, useState, type FormEvent } from "react";
import { SNIPPETS, type Snippet } from "./snippets";

export interface SnippetPickerProps {
  /** Called with the chosen snippet's code. */
  onSelect: (snippet: Snippet) => void;
  /**
   * The current editor content. When non-empty AND not equal to one of the
   * known snippet bodies, the picker prompts for confirmation before clobbering it.
   */
  currentCode?: string;
  /** Optional confirm impl — tests inject a stub. Defaults to `window.confirm`. */
  confirmImpl?: (msg: string) => boolean;
}

function isKnownSnippetBody(code: string | undefined): boolean {
  if (!code) return true;
  const trimmed = code.trim();
  if (trimmed === "") return true;
  return SNIPPETS.some((s) => s.code.trim() === trimmed);
}

/**
 * Searchable popover. Click the trigger button to expand, type to filter,
 * click an entry to load it. We deliberately do not use a portal — the
 * popover sits inline below the trigger and closes on outside click.
 */
export function SnippetPicker(props: SnippetPickerProps): JSX.Element {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const triggerRef = useRef<HTMLButtonElement>(null);

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return SNIPPETS;
    return SNIPPETS.filter((s) => {
      if (s.name.toLowerCase().includes(q)) return true;
      if (s.description.toLowerCase().includes(q)) return true;
      return s.tags.some((t) => t.toLowerCase().includes(q));
    });
  }, [query]);

  const choose = (snippet: Snippet): void => {
    const confirmFn = props.confirmImpl ?? ((msg: string) => window.confirm(msg));
    if (!isKnownSnippetBody(props.currentCode)) {
      const ok = confirmFn(
        `Replace the current editor content with the "${snippet.name}" snippet?`,
      );
      if (!ok) return;
    }
    props.onSelect(snippet);
    setOpen(false);
    setQuery("");
  };

  const onSubmit = (e: FormEvent): void => {
    e.preventDefault();
    const first = filtered[0];
    if (first) choose(first);
  };

  return (
    <div style={{ position: "relative", display: "inline-block" }}>
      <button
        ref={triggerRef}
        type="button"
        data-testid="snippet-picker-trigger"
        onClick={() => setOpen((o) => !o)}
        aria-haspopup="listbox"
        aria-expanded={open}
        style={{
          padding: "0.4rem 0.75rem",
          borderRadius: 6,
          border: "1px solid var(--color-grid, #e0e0e0)",
          background: "var(--color-background, #fafafa)",
          color: "inherit",
          cursor: "pointer",
          fontSize: 14,
        }}
      >
        Snippets ▾
      </button>
      {open ? (
        <div
          role="dialog"
          aria-label="Snippet gallery"
          style={{
            position: "absolute",
            top: "calc(100% + 4px)",
            left: 0,
            zIndex: 50,
            width: 360,
            maxHeight: 400,
            overflow: "auto",
            background: "var(--color-background, #fafafa)",
            border: "1px solid var(--color-grid, #e0e0e0)",
            borderRadius: 6,
            boxShadow: "0 4px 16px rgba(0,0,0,0.12)",
          }}
        >
          <form onSubmit={onSubmit} style={{ padding: 8, borderBottom: "1px solid var(--color-grid, #e0e0e0)" }}>
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search snippets…"
              autoFocus
              aria-label="Search snippets"
              style={{
                width: "100%",
                padding: "0.4rem 0.5rem",
                fontSize: 14,
                borderRadius: 4,
                border: "1px solid var(--color-grid, #e0e0e0)",
                background: "transparent",
                color: "inherit",
              }}
            />
          </form>
          <ul role="listbox" style={{ listStyle: "none", margin: 0, padding: 0 }}>
            {filtered.length === 0 ? (
              <li style={{ padding: "0.75rem", color: "var(--color-grid, #888)" }}>
                No snippets match.
              </li>
            ) : (
              filtered.map((s, idx) => (
                <li key={s.id} role="option" aria-selected={false}>
                  <button
                    type="button"
                    data-testid={idx === 0 ? "snippet-picker-first-item" : undefined}
                    onClick={() => choose(s)}
                    style={{
                      width: "100%",
                      textAlign: "left",
                      padding: "0.6rem 0.75rem",
                      background: "transparent",
                      border: 0,
                      color: "inherit",
                      cursor: "pointer",
                      borderBottom: "1px solid var(--color-grid, #f0f0f0)",
                    }}
                  >
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{s.name}</div>
                    <div style={{ fontSize: 12, color: "var(--color-grid, #666)" }}>
                      {s.description}
                    </div>
                  </button>
                </li>
              ))
            )}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

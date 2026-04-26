import { useSettingsStore } from "../state/settingsStore";

export function ThemeToggle(): JSX.Element {
  const theme = useSettingsStore((s) => s.theme) ?? "light";
  const setTheme = useSettingsStore((s) => s.setTheme);
  const next = theme === "dark" ? "light" : "dark";

  return (
    <button
      type="button"
      onClick={() => setTheme(next)}
      aria-label={`Switch to ${next} theme`}
      title={`Switch to ${next} theme`}
      style={{
        width: 32,
        height: 32,
        borderRadius: 6,
        border: "1px solid var(--color-grid, #e0e0e0)",
        background: "transparent",
        color: "inherit",
        cursor: "pointer",
      }}
    >
      {theme === "dark" ? "☾" : "☀"}
    </button>
  );
}

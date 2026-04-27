import { describe, it, expect, beforeEach } from "vitest";
import { render, screen, fireEvent, act } from "@testing-library/react";
import { SettingsDrawer } from "../../src/features/settings/SettingsDrawer";
import { useSettingsStore } from "../../src/state/settingsStore";
import { useUiStore } from "../../src/state/uiStore";

function openDrawer(): void {
  act(() => {
    useUiStore.getState().openSettingsDrawer();
  });
}

describe("<SettingsDrawer />", () => {
  beforeEach(() => {
    act(() => {
      useSettingsStore.getState().reset();
      useUiStore.getState().closeSettingsDrawer();
    });
  });

  it("does not render when closed", () => {
    const { container } = render(<SettingsDrawer />);
    expect(container.firstChild).toBeNull();
  });

  it("opens, edits provider/model, saves, persists to settingsStore", () => {
    render(<SettingsDrawer />);
    openDrawer();

    expect(screen.getByRole("dialog", { name: /settings/i })).toBeInTheDocument();

    // Switch provider to openai
    const openaiRadio = screen.getByRole("radio", { name: /openai/i });
    fireEvent.click(openaiRadio);

    // Edit the model name
    const modelInput = screen.getByLabelText(/llm model/i);
    fireEvent.change(modelInput, { target: { value: "gpt-4o" } });

    // Set the alias
    const aliasInput = screen.getByLabelText(/api key alias/i);
    fireEvent.change(aliasInput, { target: { value: "openai-prod" } });

    // Save
    const saveBtn = screen.getByRole("button", { name: /^save$/i });
    expect(saveBtn).not.toBeDisabled();
    fireEvent.click(saveBtn);

    const state = useSettingsStore.getState();
    expect(state.llmProvider).toBe("openai");
    expect(state.llmModel).toBe("gpt-4o");
    expect(state.apiKeyAlias).toBe("openai-prod");
    // Drawer closes on save
    expect(useUiStore.getState().settingsDrawerOpen).toBe(false);
  });

  it("discard reverts changes and closes the drawer", () => {
    // Pre-set known state.
    act(() => {
      useSettingsStore.getState().setProvider("anthropic");
      useSettingsStore.getState().setModel("claude-3-5-sonnet-latest");
    });
    render(<SettingsDrawer />);
    openDrawer();

    const modelInput = screen.getByLabelText(/llm model/i) as HTMLInputElement;
    fireEvent.change(modelInput, { target: { value: "trash-value" } });
    expect(modelInput.value).toBe("trash-value");

    fireEvent.click(screen.getByRole("button", { name: /discard/i }));

    expect(useSettingsStore.getState().llmModel).toBe("claude-3-5-sonnet-latest");
    expect(useUiStore.getState().settingsDrawerOpen).toBe(false);
  });

  it("save button is disabled until the form is dirty", () => {
    render(<SettingsDrawer />);
    openDrawer();
    const saveBtn = screen.getByRole("button", { name: /^save$/i });
    expect(saveBtn).toBeDisabled();
  });

  it("rejects an invalid API base URL", () => {
    render(<SettingsDrawer />);
    openDrawer();

    const urlInput = screen.getByLabelText(/api base url/i);
    fireEvent.change(urlInput, { target: { value: "not-a-url" } });

    expect(screen.getByText(/must be a valid http/i)).toBeInTheDocument();
    const saveBtn = screen.getByRole("button", { name: /^save$/i });
    expect(saveBtn).toBeDisabled();
  });

  it("shows the API-key provenance banner for key registration", () => {
    render(<SettingsDrawer />);
    openDrawer();
    expect(
      screen.getByText(/api keys for anthropic and openai are read from the server/i),
    ).toBeInTheDocument();
  });

  it("focuses the first focusable element on open and traps Tab inside", () => {
    render(<SettingsDrawer />);
    openDrawer();

    // First focusable is the close-X button. The trap is applied via
    // requestAnimationFrame in some environments; in jsdom it's synchronous.
    const dialog = screen.getByTestId("settings-drawer");
    expect(dialog).toBeInTheDocument();

    // The drawer pulls focus inside; after opening, document.activeElement
    // should be inside the dialog.
    expect(dialog.contains(document.activeElement)).toBe(true);

    // Find the last focusable inside the dialog.
    const focusables = dialog.querySelectorAll<HTMLElement>(
      'a[href], button:not([disabled]), input:not([disabled]):not([type="hidden"]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])',
    );
    const last = focusables[focusables.length - 1];
    last.focus();
    expect(document.activeElement).toBe(last);

    // Tab from last → wraps to first.
    fireEvent.keyDown(document, { key: "Tab" });
    expect(dialog.contains(document.activeElement)).toBe(true);
    expect(document.activeElement).toBe(focusables[0]);
  });

  it("Esc closes the drawer", () => {
    render(<SettingsDrawer />);
    openDrawer();
    expect(useUiStore.getState().settingsDrawerOpen).toBe(true);
    fireEvent.keyDown(document, { key: "Escape" });
    expect(useUiStore.getState().settingsDrawerOpen).toBe(false);
  });
});

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

  it("shows the M7-pending banner for key registration", () => {
    render(<SettingsDrawer />);
    openDrawer();
    expect(screen.getByText(/key registration backend pending/i)).toBeInTheDocument();
  });
});

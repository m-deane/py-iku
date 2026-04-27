import { describe, it, expect } from "vitest";
import { render, fireEvent, act } from "@testing-library/react";
import { useState } from "react";
import { useFocusTrap } from "../../src/components/useFocusTrap";

function Harness({ initialOpen }: { initialOpen: boolean }): JSX.Element {
  const [open, setOpen] = useState(initialOpen);
  const trapRef = useFocusTrap<HTMLDivElement>(open);
  return (
    <div>
      <button data-testid="trigger" onClick={() => setOpen(true)}>
        Open
      </button>
      {open ? (
        <div ref={trapRef} tabIndex={-1} data-testid="dialog">
          <button data-testid="first">First</button>
          <input data-testid="middle" />
          <button data-testid="last">Last</button>
          <button data-testid="close" onClick={() => setOpen(false)}>
            Close
          </button>
        </div>
      ) : null}
    </div>
  );
}

describe("useFocusTrap", () => {
  it("focuses the first focusable on open", () => {
    const { getByTestId } = render(<Harness initialOpen={false} />);
    const trigger = getByTestId("trigger") as HTMLButtonElement;
    trigger.focus();
    expect(document.activeElement).toBe(trigger);
    fireEvent.click(trigger);
    const first = getByTestId("first");
    expect(document.activeElement).toBe(first);
  });

  it("Tab from the last element wraps to the first", () => {
    const { getByTestId } = render(<Harness initialOpen={true} />);
    const last = getByTestId("close"); // last focusable
    (last as HTMLButtonElement).focus();
    expect(document.activeElement).toBe(last);
    fireEvent.keyDown(document, { key: "Tab" });
    const first = getByTestId("first");
    expect(document.activeElement).toBe(first);
  });

  it("Shift+Tab from the first element wraps to the last", () => {
    const { getByTestId } = render(<Harness initialOpen={true} />);
    const first = getByTestId("first") as HTMLButtonElement;
    first.focus();
    fireEvent.keyDown(document, { key: "Tab", shiftKey: true });
    expect(document.activeElement).toBe(getByTestId("close"));
  });

  it("restores focus to the trigger on deactivation", () => {
    const { getByTestId } = render(<Harness initialOpen={false} />);
    const trigger = getByTestId("trigger") as HTMLButtonElement;
    trigger.focus();
    fireEvent.click(trigger);
    // Now click Close — the harness flips `open` back to false.
    act(() => {
      fireEvent.click(getByTestId("close"));
    });
    expect(document.activeElement).toBe(trigger);
  });
});

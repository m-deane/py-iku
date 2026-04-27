import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { useChatStore, flowIdFromCode } from "../../src/features/chat/chatStore";

beforeEach(() => {
  // Reset to known defaults before each test.
  useChatStore.setState({
    drawerOpen: false,
    drawerWidth: 0.3,
    historyByFlow: {},
    highlightedRecipeId: null,
  });
});

afterEach(() => {
  useChatStore.setState({ historyByFlow: {} });
});

describe("chatStore", () => {
  it("toggleOpen flips drawerOpen", () => {
    expect(useChatStore.getState().drawerOpen).toBe(false);
    useChatStore.getState().toggleOpen();
    expect(useChatStore.getState().drawerOpen).toBe(true);
    useChatStore.getState().toggleOpen();
    expect(useChatStore.getState().drawerOpen).toBe(false);
  });

  it("setWidth clamps between 0.25 and 0.5", () => {
    useChatStore.getState().setWidth(0.1);
    expect(useChatStore.getState().drawerWidth).toBe(0.25);
    useChatStore.getState().setWidth(0.7);
    expect(useChatStore.getState().drawerWidth).toBe(0.5);
    useChatStore.getState().setWidth(0.4);
    expect(useChatStore.getState().drawerWidth).toBe(0.4);
  });

  it("appendTurn / patchAssistantTurn / clearHistory round-trip", () => {
    const flowId = "flow-test";
    useChatStore.getState().appendTurn(flowId, {
      id: "u1",
      role: "user",
      content: "hi",
      ts: 1,
    });
    useChatStore.getState().appendTurn(flowId, {
      id: "a1",
      role: "assistant",
      content: "",
      pending: true,
      ts: 2,
    });
    useChatStore.getState().patchAssistantTurn(flowId, "a1", {
      content: "hello",
      pending: false,
    });
    let list = useChatStore.getState().historyByFlow[flowId];
    expect(list.map((t) => t.content)).toEqual(["hi", "hello"]);
    useChatStore.getState().clearHistory(flowId);
    list = useChatStore.getState().historyByFlow[flowId];
    expect(list).toBeUndefined();
  });

  it("flowIdFromCode is deterministic for the same input", () => {
    expect(flowIdFromCode("import pandas")).toBe(flowIdFromCode("import pandas"));
    expect(flowIdFromCode("a")).not.toBe(flowIdFromCode("b"));
  });
});

import { describe, expect, it } from "vitest";
import { render, screen } from "@testing-library/react";
import { ChatMessage, splitWithCitations } from "../../src/features/chat/ChatMessage";

describe("splitWithCitations", () => {
  it("splits text and citation chips", () => {
    const segs = splitWithCitations("Hello [recipe:foo] and [recipe:bar].");
    expect(segs.map((s) => s.kind)).toEqual([
      "text",
      "citation",
      "text",
      "citation",
      "text",
    ]);
  });

  it("returns a single text segment when no citations are present", () => {
    const segs = splitWithCitations("plain text only");
    expect(segs.length).toBe(1);
    expect(segs[0].kind).toBe("text");
  });
});

describe("<ChatMessage />", () => {
  it("renders citation chips for each recipe marker", () => {
    render(
      <ChatMessage
        turn={{
          id: "t1",
          role: "assistant",
          content: "See [recipe:prep_raw] then [recipe:agg].",
          ts: Date.now(),
        }}
      />,
    );
    expect(screen.getByTestId("chat-citation-prep_raw")).toBeInTheDocument();
    expect(screen.getByTestId("chat-citation-agg")).toBeInTheDocument();
  });

  it("renders user turns aligned right", () => {
    render(
      <ChatMessage
        turn={{
          id: "t1",
          role: "user",
          content: "what does prep_raw do?",
          ts: Date.now(),
        }}
      />,
    );
    expect(screen.getByTestId("chat-turn-user")).toHaveTextContent(
      "what does prep_raw do?",
    );
  });

  it("renders a streaming cursor while pending", () => {
    render(
      <ChatMessage
        turn={{
          id: "t1",
          role: "assistant",
          content: "thinking",
          pending: true,
          ts: Date.now(),
        }}
      />,
    );
    expect(screen.getByTestId("chat-streaming-cursor")).toBeInTheDocument();
  });
});

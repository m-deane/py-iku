import { describe, it, expect } from "vitest";
import {
  encodeShareUrl,
  decodeShareUrl,
  tabToShared,
  sharedToTab,
  MAX_URL_BYTES,
  SHARE_HASH_KEY,
  type SharedAppState,
} from "../../src/store/shareState";
import type { WorkspaceTab } from "../../src/store/tabs";

/**
 * Sprint 4 — URL-as-state codec.
 *
 * Coverage:
 *   - encode/decode round-trip preserves the payload byte-for-byte
 *   - non-ASCII source survives the base64url path
 *   - tooLarge fires above MAX_URL_BYTES
 *   - decodeShareUrl tolerates garbage and returns null instead of throwing
 *   - tabToShared/sharedToTab round-trip
 */
function makeState(tabs: SharedAppState["tabs"], theme: "light" | "dark" | null = null): SharedAppState {
  return {
    v: 1,
    tabs,
    activeTabId: tabs[0]?.id ?? null,
    theme,
    panels: { replay: true },
  };
}

describe("shareState codec", () => {
  it("round-trips a small workspace through hash encoding", () => {
    const tabs = [
      {
        id: "t1",
        title: "Trade capture",
        code: "import pandas as pd\ndf = pd.DataFrame()",
        lastFlow: null,
        mode: "rule" as const,
        provider: "anthropic" as const,
        scrollTop: 12,
      },
    ];
    const state = makeState(tabs, "dark");
    const encoded = encodeShareUrl(state, "https://studio.example.com/convert");
    expect(encoded.tooLarge).toBe(false);
    expect(encoded.url).toContain(`#${SHARE_HASH_KEY}=`);
    expect(encoded.bytes).toBeGreaterThan(0);

    const decoded = decodeShareUrl(encoded.url);
    expect(decoded).not.toBeNull();
    expect(decoded?.v).toBe(1);
    expect(decoded?.activeTabId).toBe("t1");
    expect(decoded?.tabs).toHaveLength(1);
    expect(decoded?.tabs[0].code).toBe("import pandas as pd\ndf = pd.DataFrame()");
    expect(decoded?.theme).toBe("dark");
    expect(decoded?.panels.replay).toBe(true);
  });

  it("survives non-ASCII source code (UTF-8 in base64url)", () => {
    const code = "# façade — résumé naïve\nx = 'π'";
    const tabs = [
      {
        id: "t1",
        title: "Δflow",
        code,
        lastFlow: null,
        mode: "rule" as const,
        provider: "anthropic" as const,
        scrollTop: 0,
      },
    ];
    const encoded = encodeShareUrl(makeState(tabs), "https://x.test/");
    const decoded = decodeShareUrl(encoded.url);
    expect(decoded?.tabs[0].code).toBe(code);
    expect(decoded?.tabs[0].title).toBe("Δflow");
  });

  it("strips an existing hash before appending state=", () => {
    const tabs = [
      {
        id: "t1",
        title: "x",
        code: "",
        lastFlow: null,
        mode: "rule" as const,
        provider: "anthropic" as const,
        scrollTop: 0,
      },
    ];
    const encoded = encodeShareUrl(makeState(tabs), "https://x.test/#existing-hash");
    expect(encoded.url.startsWith("https://x.test/#")).toBe(true);
    // Only one '#' in the URL.
    expect(encoded.url.split("#").length).toBe(2);
  });

  it("flags tooLarge when the payload exceeds MAX_URL_BYTES", () => {
    // Build a code blob big enough to push the encoded URL over 32KB.
    const huge = "x".repeat(MAX_URL_BYTES + 5_000);
    const tabs = [
      {
        id: "t1",
        title: "Huge",
        code: huge,
        lastFlow: null,
        mode: "rule" as const,
        provider: "anthropic" as const,
        scrollTop: 0,
      },
    ];
    const encoded = encodeShareUrl(makeState(tabs), "https://x.test/");
    expect(encoded.tooLarge).toBe(true);
    expect(encoded.bytes).toBeGreaterThan(MAX_URL_BYTES);
  });

  it("decodeShareUrl returns null for malformed input", () => {
    expect(decodeShareUrl("https://x.test/")).toBeNull();
    expect(decodeShareUrl("https://x.test/#")).toBeNull();
    expect(decodeShareUrl("https://x.test/#state=not-base64-json!!")).toBeNull();
    // Wrong schema version.
    const badJson = btoa(JSON.stringify({ v: 99, tabs: [] }));
    expect(decodeShareUrl(`https://x.test/#${SHARE_HASH_KEY}=${badJson}`)).toBeNull();
  });

  it("tabToShared / sharedToTab round-trip drops/regenerates updatedAt", () => {
    const live: WorkspaceTab = {
      id: "t1",
      title: "Persistable",
      code: "y = 1",
      lastFlow: { recipes: [] },
      mode: "llm",
      provider: "openai",
      model: "gpt-4o",
      scrollTop: 99,
      updatedAt: 12345,
    };
    const shared = tabToShared(live);
    expect("updatedAt" in shared).toBe(false);
    const back = sharedToTab(shared);
    expect(back.id).toBe("t1");
    expect(back.title).toBe("Persistable");
    expect(back.code).toBe("y = 1");
    expect(back.mode).toBe("llm");
    expect(back.provider).toBe("openai");
    expect(back.model).toBe("gpt-4o");
    expect(back.scrollTop).toBe(99);
    expect(back.updatedAt).toBeGreaterThan(0); // freshly stamped
  });
});

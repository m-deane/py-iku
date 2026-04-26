import { describe, it, expect, vi } from "vitest";
import { ApiError, client } from "../../src/api/client";

function makeFetch(response: { status: number; body: unknown; contentType?: string }): typeof fetch {
  return vi.fn(async () => {
    const headers = new Headers({
      "content-type": response.contentType ?? "application/json",
    });
    const body = typeof response.body === "string" ? response.body : JSON.stringify(response.body);
    return new Response(body, { status: response.status, headers });
  }) as unknown as typeof fetch;
}

describe("api client — health()", () => {
  it("returns the parsed health payload on 200", async () => {
    const fetchImpl = makeFetch({
      status: 200,
      body: { status: "ok", version: "0.0.0", py_iku_version: "0.3.0" },
    });
    const result = await client.health({
      baseUrl: "http://example.test",
      fetchImpl,
    });
    expect(result).toEqual({ status: "ok", version: "0.0.0", py_iku_version: "0.3.0" });
    expect(fetchImpl).toHaveBeenCalledOnce();
    const [url, init] = (fetchImpl as unknown as { mock: { calls: [string, RequestInit][] } })
      .mock.calls[0]!;
    expect(url).toBe("http://example.test/health");
    const headers = new Headers(init.headers);
    expect(headers.get("X-Request-ID")).toMatch(/[0-9a-f-]{8,}/);
  });

  it("throws ApiError with parsed problem+json on 500", async () => {
    const fetchImpl = makeFetch({
      status: 500,
      contentType: "application/problem+json",
      body: {
        type: "https://py-iku.dev/problems/internal-error",
        title: "Internal Server Error",
        status: 500,
        detail: "boom",
      },
    });
    await expect(
      client.health({ baseUrl: "http://example.test", fetchImpl }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 500,
      title: "Internal Server Error",
      detail: "boom",
      type: "https://py-iku.dev/problems/internal-error",
    });
  });

  it("ApiError is an instance of Error and ApiError", async () => {
    const fetchImpl = makeFetch({
      status: 500,
      body: { type: "about:blank", title: "oops", status: 500 },
    });
    let caught: unknown;
    try {
      await client.health({ baseUrl: "http://example.test", fetchImpl });
    } catch (err) {
      caught = err;
    }
    expect(caught).toBeInstanceOf(ApiError);
    expect(caught).toBeInstanceOf(Error);
  });

  it("wraps network failures as ApiError with status 0", async () => {
    const fetchImpl = vi.fn(async () => {
      throw new TypeError("network down");
    }) as unknown as typeof fetch;
    await expect(
      client.health({ baseUrl: "http://example.test", fetchImpl }),
    ).rejects.toMatchObject({
      name: "ApiError",
      status: 0,
      title: "Network error",
    });
  });
});

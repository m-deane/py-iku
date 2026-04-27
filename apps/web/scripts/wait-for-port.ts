#!/usr/bin/env tsx
/**
 * wait-for-port.ts
 *
 * Polls a URL until it returns HTTP 200 (or any 2xx) or the timeout elapses.
 * Exits 0 on success, 1 on timeout.
 *
 * Usage:
 *   tsx scripts/wait-for-port.ts [url] [timeout_seconds]
 *
 * Defaults:
 *   url     = http://localhost:8000/health
 *   timeout = 60 (seconds)
 *
 * Example (from repo root):
 *   pnpm --filter apps-web exec tsx scripts/wait-for-port.ts http://localhost:8000/health 30
 */

const url = process.argv[2] ?? "http://localhost:8000/health";
const timeoutSec = parseInt(process.argv[3] ?? "60", 10);
const intervalMs = 1_000;
const deadline = Date.now() + timeoutSec * 1_000;

process.stdout.write(`Waiting for ${url} (timeout ${timeoutSec}s)...\n`);

async function poll(): Promise<void> {
  while (Date.now() < deadline) {
    try {
      const res = await fetch(url, { signal: AbortSignal.timeout(3_000) });
      if (res.ok) {
        process.stdout.write(`\nReady: ${url} responded ${res.status}\n`);
        process.exit(0);
      }
      process.stdout.write(".");
    } catch {
      process.stdout.write(".");
    }
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }

  process.stdout.write(`\nTimeout after ${timeoutSec}s — ${url} not reachable\n`);
  process.exit(1);
}

poll();

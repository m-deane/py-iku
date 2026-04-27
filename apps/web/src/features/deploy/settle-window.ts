/**
 * Pure helpers for the Deploy settle-window guard.
 *
 * Given a venue with an HH:MM venue-local close + a half-window in minutes,
 * return whether a given UTC instant ("now") falls inside that window. The
 * conversion uses Intl.DateTimeFormat with a timeZone option so we don't
 * pull in luxon / date-fns-tz just for one call.
 */

import type { MarketSession } from "../../api/client";

export interface InWindowResult {
  inWindow: boolean;
  /** Minutes until close (negative when past close). */
  minutesToClose: number;
  /** "HH:MM" venue-local time of `now`. */
  venueLocal: string;
  /** Window start/end as HH:MM venue-local strings. */
  windowStart: string;
  windowEnd: string;
}

/**
 * Convert a UTC Date to "HH:MM" in the venue-local timezone, using the
 * platform Intl APIs.
 */
export function utcToVenueLocalHHMM(now: Date, timezone: string): string {
  const fmt = new Intl.DateTimeFormat("en-GB", {
    timeZone: timezone,
    hour12: false,
    hour: "2-digit",
    minute: "2-digit",
  });
  // en-GB returns "HH:MM" already.
  return fmt.format(now);
}

function hhmmToMinutes(hhmm: string): number {
  const [h, m] = hhmm.split(":").map((s) => Number.parseInt(s, 10));
  return (h ?? 0) * 60 + (m ?? 0);
}

function minutesToHHMM(total: number): string {
  // Wrap into a single calendar day for display.
  const wrapped = ((total % (24 * 60)) + 24 * 60) % (24 * 60);
  const h = Math.floor(wrapped / 60);
  const m = wrapped % 60;
  return `${h.toString().padStart(2, "0")}:${m.toString().padStart(2, "0")}`;
}

/**
 * Decide whether `now` falls inside the venue's settle window.
 *
 * Pure function — no global Date.now() call. Tests pass an explicit `now`
 * so they don't depend on wall-clock time.
 */
export function inSettleWindow(
  session: MarketSession,
  now: Date,
): InWindowResult {
  const venueLocal = utcToVenueLocalHHMM(now, session.timezone);
  const nowMin = hhmmToMinutes(venueLocal);
  const closeMin = hhmmToMinutes(session.close_time);
  const half = session.settle_window_minutes;

  const startMin = closeMin - half;
  const endMin = closeMin + half;

  // Compute "minutes-to-close" on a [-12h, +12h] axis so a window that
  // straddles midnight still gives sensible numbers.
  let minutesToClose = closeMin - nowMin;
  if (minutesToClose > 12 * 60) minutesToClose -= 24 * 60;
  if (minutesToClose < -12 * 60) minutesToClose += 24 * 60;

  const inWindow = Math.abs(minutesToClose) <= half;

  return {
    inWindow,
    minutesToClose,
    venueLocal,
    windowStart: minutesToHHMM(startMin),
    windowEnd: minutesToHHMM(endMin),
  };
}

export interface ActiveWindow {
  session: MarketSession;
  result: InWindowResult;
}

/**
 * Return all venues whose window currently contains `now`. The Deploy
 * page disables the deploy button when this list is non-empty and uses
 * the first entry to populate the tooltip.
 */
export function findActiveWindows(
  sessions: readonly MarketSession[],
  now: Date,
): ActiveWindow[] {
  const out: ActiveWindow[] = [];
  for (const s of sessions) {
    const result = inSettleWindow(s, now);
    if (result.inWindow) {
      out.push({ session: s, result });
    }
  }
  return out;
}

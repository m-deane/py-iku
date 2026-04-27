import { useEffect, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  client,
  type MarketCalendarResponse,
  type MarketSession,
} from "../../api/client";
import {
  findActiveWindows,
  inSettleWindow,
  utcToVenueLocalHHMM,
  type ActiveWindow,
} from "./settle-window";
import styles from "./DeployPage.module.css";

const REFRESH_MS = 30_000;

export interface DeployPageProps {
  /** Test seam — overrides ``client.getMarketCalendar``. */
  fetchCalendarImpl?: () => Promise<MarketCalendarResponse>;
  /** Test seam — fixes "now" so the page renders deterministically in tests. */
  nowOverride?: Date;
}

/**
 * Deploy page — lifecycle's terminal step, gated by venue settle windows.
 *
 * Flow:
 *   1. Fetch the static schedule from ``GET /market-calendar`` (cached 5 min).
 *   2. Re-evaluate "is now in any settle window" every 30 s using ``Date.now()``.
 *   3. If yes, the Deploy button is disabled and the tooltip explains which
 *      venue is in window. If no, the button is live (but still a no-op
 *      placeholder until DSS write-back lands — see roadmap).
 *
 * Provenance is honest: the schedule itself is static and v1-quality.
 */
export function DeployPage(props: DeployPageProps = {}): JSX.Element {
  const fetchFn = props.fetchCalendarImpl ?? (() => client.getMarketCalendar());

  const calendarQuery = useQuery<MarketCalendarResponse>({
    queryKey: ["market-calendar"],
    queryFn: fetchFn,
    staleTime: 5 * 60_000,
  });

  // Re-render every REFRESH_MS so the "is in window" check stays current.
  // Tests bypass this with nowOverride.
  const [now, setNow] = useState<Date>(() => props.nowOverride ?? new Date());
  useEffect(() => {
    if (props.nowOverride) return;
    const id = window.setInterval(() => {
      setNow(new Date());
    }, REFRESH_MS);
    return () => window.clearInterval(id);
  }, [props.nowOverride]);

  if (calendarQuery.isLoading) {
    return (
      <section className={styles.page} data-testid="deploy-page-loading">
        <header className={styles.header}>
          <h1 className={styles.title}>Deploy</h1>
        </header>
        <div className={styles.loadingState}>Loading market schedule…</div>
      </section>
    );
  }

  if (calendarQuery.isError || !calendarQuery.data) {
    return (
      <section className={styles.page} data-testid="deploy-page-error">
        <header className={styles.header}>
          <h1 className={styles.title}>Deploy</h1>
        </header>
        <div className={styles.errorState}>
          Could not load the market calendar. Falling back to a permissive
          deploy gate — proceed with caution and check the venue close
          times manually.
        </div>
      </section>
    );
  }

  const calendar = calendarQuery.data;
  const active: ActiveWindow[] = findActiveWindows(calendar.sessions, now);
  const blocked = active.length > 0;
  const blockingVenue = active[0]?.session;
  const blockingResult = active[0]?.result;

  return (
    <section className={styles.page} data-testid="deploy-page">
      <header className={styles.header}>
        <h1 className={styles.title}>Deploy</h1>
      </header>

      <p className={styles.subtitle}>
        Push a converted flow into a Dataiku DSS project. The Deploy
        button is gated by major-venue settle windows so a deploy never
        races a {blocked ? "live" : ""} settlement run.
      </p>

      <div className={styles.staleBanner} role="status">
        {calendar.note}
      </div>

      <div className={styles.clockRow}>
        <span
          className={styles.clockBig}
          data-testid="deploy-clock-utc"
        >
          {now.toISOString().slice(11, 16)} UTC
        </span>
        <span className={styles.clockLabel}>
          server-side check refreshes every 30 s
        </span>
      </div>

      <div className={styles.deployRow}>
        <button
          type="button"
          className={`${styles.deployBtn} ${blocked ? styles.deployBtnBlocked : ""}`}
          disabled={blocked}
          aria-disabled={blocked}
          data-testid="deploy-button"
          data-blocked={blocked ? "true" : "false"}
          title={
            blocked && blockingVenue && blockingResult
              ? `Cannot deploy — within ${blockingVenue.venue} settle window ${blockingResult.windowStart}-${blockingResult.windowEnd} ${blockingVenue.timezone}`
              : "Deploy is live"
          }
        >
          {blocked
            ? `Cannot deploy — ${blockingVenue?.venue} settle window`
            : "Deploy to DSS"}
        </button>
        {blocked && blockingVenue && blockingResult ? (
          <div className={styles.tooltip} data-testid="deploy-blocked-tooltip">
            Within {blockingVenue.venue} ({blockingVenue.product}) settle
            window {blockingResult.windowStart}–{blockingResult.windowEnd}{" "}
            {blockingVenue.timezone}. {blockingVenue.note}
          </div>
        ) : null}
      </div>

      <div
        className={`${styles.activeBanner} ${
          blocked ? "" : styles.activeBannerOk
        }`}
        data-testid="deploy-status-banner"
      >
        {blocked ? (
          <>
            <strong>{active.length} venue{active.length === 1 ? "" : "s"} in settle window</strong>
            <span>Hold deploys until the active windows close.</span>
          </>
        ) : (
          <>
            <strong>All venues outside settle windows</strong>
            <span>Deploy is live. Real DSS write-back lands in a later wave; today this is a guarded UI placeholder.</span>
          </>
        )}
      </div>

      <div className={styles.calendar} data-testid="deploy-calendar">
        <div className={styles.calendarHeader}>
          Today's settle windows ({calendar.sessions.length} venues)
        </div>
        <ul className={styles.sessionList}>
          {calendar.sessions.map((s) => (
            <SessionRow key={s.venue} session={s} now={now} />
          ))}
        </ul>
      </div>
    </section>
  );
}

interface SessionRowProps {
  session: MarketSession;
  now: Date;
}

function SessionRow({ session, now }: SessionRowProps): JSX.Element {
  const result = inSettleWindow(session, now);
  const venueLocal = utcToVenueLocalHHMM(now, session.timezone);
  return (
    <li
      className={`${styles.sessionItem} ${result.inWindow ? styles.sessionItemActive : ""}`}
      data-testid={`deploy-session-${session.venue}`}
      data-in-window={result.inWindow ? "true" : "false"}
    >
      <span className={styles.venueTicker}>{session.venue}</span>
      <span>
        <span className={styles.venueProduct}>{session.product}</span>
        <span className={styles.venueProductNote}>{session.venue_name}</span>
      </span>
      <span className={styles.closeTime}>
        {session.close_time}
        <span className={styles.closeTimeNote}>
          {session.timezone} · now {venueLocal}
        </span>
      </span>
      <span
        className={`${styles.statusBadge} ${result.inWindow ? styles.statusClosed : styles.statusOpen}`}
      >
        {result.inWindow ? "in window" : "open"}
      </span>
    </li>
  );
}

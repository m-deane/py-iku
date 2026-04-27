import { useEffect, useState } from "react";
import {
  client as defaultClient,
  type PluginsInstalledResponse,
} from "../../api/client";

export interface UseInstalledPluginsResult {
  data: PluginsInstalledResponse | null;
  loading: boolean;
  error: string | null;
  refresh: () => void;
}

interface UseInstalledPluginsOptions {
  /** Test seam — swap in a stub fetcher. */
  clientImpl?: { listPluginsInstalled: typeof defaultClient.listPluginsInstalled };
  /** Set false to skip the network call (e.g. when the panel is closed). */
  enabled?: boolean;
}

/**
 * Hook that snapshots the live ``PluginRegistry`` via ``GET /plugins/installed``.
 * Returns the introspection response plus loading / error / manual-refresh
 * controls so the marketplace can display the active mappings tab.
 */
export function useInstalledPlugins(
  opts: UseInstalledPluginsOptions = {},
): UseInstalledPluginsResult {
  const cli = opts.clientImpl ?? defaultClient;
  const enabled = opts.enabled ?? true;
  const [data, setData] = useState<PluginsInstalledResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    if (!enabled) return;
    let cancelled = false;
    setLoading(true);
    setError(null);
    cli
      .listPluginsInstalled()
      .then((res) => {
        if (!cancelled) setData(res);
      })
      .catch((err: unknown) => {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : String(err));
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [cli, enabled, tick]);

  return {
    data,
    loading,
    error,
    refresh: () => setTick((n) => n + 1),
  };
}

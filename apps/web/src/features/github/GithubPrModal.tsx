import { useEffect, useMemo, useRef, useState } from "react";
import {
  collabClient as defaultCollab,
  client as defaultClient,
  type CollabClient,
  type Client,
  type GithubPublishResponse,
} from "../../api/client";
import { useSettingsStore } from "../../state/settingsStore";

export interface GithubPrModalProps {
  /** The flow being committed — modal is hidden when null. */
  flow: Record<string, unknown> | null;
  /** Closes the modal. */
  onClose: () => void;
  /** Test seam — collab API client. */
  collabImpl?: CollabClient;
  /** Test seam — main client (used for SVG export). */
  clientImpl?: Client;
}

type Step = "creating-branch" | "committing-files" | "opening-pr" | "done" | "error";

interface StepState {
  status: "pending" | "active" | "ok" | "error";
  message?: string;
}

interface ProgressState {
  branch: StepState;
  files: StepState;
  pr: StepState;
}

const INITIAL_PROGRESS: ProgressState = {
  branch: { status: "pending" },
  files: { status: "pending" },
  pr: { status: "pending" },
};

/** Map of error-codes to user-facing messages. */
const ERROR_COPY: Record<string, string> = {
  BAD_PAT:
    "GitHub rejected the personal access token. Check the token in Settings — it may be revoked or mistyped.",
  INSUFFICIENT_SCOPE:
    "The PAT doesn't grant the 'repo' scope. Re-create the token with full repo access.",
  REPO_NOT_FOUND:
    "Repository not found, or the PAT can't see it. Verify owner/name and that the token has access.",
  BASE_NOT_FOUND:
    "The base branch doesn't exist. Pick an existing branch (e.g. 'main' or 'master').",
  BRANCH_EXISTS:
    "A branch with that name already exists. Pick a unique name and try again.",
  PATH_CONFLICT:
    "A file at the target path already exists on the branch. Use a different flow name or branch.",
  RATE_LIMITED:
    "GitHub returned a rate-limit error. Wait a few minutes and try again.",
  NETWORK_ERROR:
    "Could not reach GitHub. Check your network or the API server's egress.",
  UNKNOWN: "GitHub returned an unexpected error. See toast for details.",
};

/**
 * "Open as PR" modal — collects the PAT + repo + branch + PR title,
 * then POSTs to the backend which performs the actual GitHub REST calls.
 *
 * The PAT never lingers on the frontend after submit. We hold it only in
 * local state for the duration of the modal — `useState` is reset when
 * the modal closes.
 */
export function GithubPrModal(props: GithubPrModalProps): JSX.Element | null {
  const { flow, onClose } = props;
  const collab = props.collabImpl ?? defaultCollab;
  const cli = props.clientImpl ?? defaultClient;

  const flowName =
    (flow?.flow_name as string | undefined) ?? "py-iku-flow";

  // Form state
  const [pat, setPat] = useState("");
  const [repo, setRepo] = useState("");
  const [base, setBase] = useState("main");
  const [branch, setBranch] = useState(
    `studio/${flowName.replace(/[^a-z0-9-]/gi, "-")}-${Date.now().toString(36)}`,
  );
  const [prTitle, setPrTitle] = useState(`Add ${flowName} flow`);

  // Submission state
  const [submitting, setSubmitting] = useState(false);
  const [progress, setProgress] = useState<ProgressState>(INITIAL_PROGRESS);
  const [result, setResult] = useState<GithubPublishResponse | null>(null);
  const [error, setError] = useState<{ code: string; message: string } | null>(
    null,
  );

  // Persist PAT in memory only — never serialize to localStorage.
  const patRef = useRef("");
  useEffect(() => {
    patRef.current = pat;
  }, [pat]);

  useEffect(() => {
    return () => {
      // Defensive: clear pat from refs on unmount.
      patRef.current = "";
    };
  }, []);

  const onSubmit = async (): Promise<void> => {
    if (!flow) return;
    if (!pat || !repo || !branch || !prTitle) {
      setError({ code: "UNKNOWN", message: "All fields are required." });
      return;
    }
    setSubmitting(true);
    setError(null);
    setProgress({
      branch: { status: "active" },
      files: { status: "pending" },
      pr: { status: "pending" },
    });

    // Render the flow as SVG via the existing /export/svg endpoint.
    let flowSvg = "<svg/>";
    try {
      const svgResult = await cli.export("svg", flow);
      flowSvg = await svgResult.blob.text();
    } catch (err) {
      // Non-fatal — fall back to a placeholder SVG so the PR still opens.
      // eslint-disable-next-line no-console
      console.warn("svg export failed, using placeholder", err);
    }

    try {
      // Optimistic UI — flip steps as we go.  The backend doesn't currently
      // stream progress, so we advance by stage based on completion.
      setProgress((p) => ({
        ...p,
        branch: { status: "active" },
      }));

      const res = await collab.githubPublish({
        pat,
        repo,
        base,
        branch,
        flow_name: flowName,
        pr_title: prTitle,
        flow_json: flow,
        flow_svg: flowSvg,
      });

      setProgress({
        branch: { status: "ok" },
        files: { status: "ok" },
        pr: { status: "ok" },
      });
      setResult(res);
      // Clear the PAT now that it's done its job.
      setPat("");
    } catch (err) {
      const detail = err as { detail?: { code?: string; message?: string }; message?: string };
      const code = detail?.detail?.code ?? "UNKNOWN";
      const msg =
        detail?.detail?.message ??
        detail?.message ??
        (err instanceof Error ? err.message : "GitHub publish failed");
      setError({ code, message: msg });
      setProgress((p) => ({
        ...p,
        branch: p.branch.status === "ok" ? p.branch : { status: "error", message: msg },
      }));
    } finally {
      setSubmitting(false);
    }
  };

  const summary = useMemo(() => {
    if (result) return "done" as Step;
    if (error) return "error" as Step;
    if (progress.pr.status === "active") return "opening-pr" as Step;
    if (progress.files.status === "active") return "committing-files" as Step;
    if (progress.branch.status === "active") return "creating-branch" as Step;
    return "creating-branch" as Step;
  }, [progress, result, error]);

  if (!flow) return null;

  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-label="Open as GitHub PR"
      data-testid="github-pr-modal"
      style={{
        position: "fixed",
        inset: 0,
        background: "rgba(16,24,40,0.5)",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        zIndex: 60,
      }}
      onClick={(e) => {
        if (e.target === e.currentTarget && !submitting) onClose();
      }}
    >
      <div
        style={{
          background: "var(--surface)",
          color: "var(--fg)",
          borderRadius: "var(--radius-lg)",
          boxShadow: "var(--shadow-lg)",
          width: "min(560px, 92vw)",
          maxHeight: "92vh",
          overflow: "auto",
          fontFamily: "var(--font-sans)",
        }}
      >
        <header
          style={{
            padding: "var(--space-4) var(--space-5)",
            borderBottom: "1px solid var(--border)",
            display: "flex",
            alignItems: "center",
            gap: "var(--space-3)",
          }}
        >
          <h2
            style={{
              margin: 0,
              fontSize: "var(--text-md)",
              fontWeight: "var(--font-weight-semibold)",
              flex: 1,
            }}
          >
            Open as GitHub PR
          </h2>
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            aria-label="Close"
            data-testid="github-pr-close"
            style={{
              border: 0,
              background: "transparent",
              cursor: submitting ? "not-allowed" : "pointer",
              fontSize: "1.2rem",
              color: "var(--fg-muted)",
            }}
          >
            ×
          </button>
        </header>

        {result ? (
          <ResultView result={result} onClose={onClose} />
        ) : (
          <div style={{ padding: "var(--space-5)" }}>
            <FormField label="GitHub PAT" hint="Stored in memory only — never logged.">
              <input
                type="password"
                value={pat}
                onChange={(e) => setPat(e.target.value)}
                disabled={submitting}
                data-testid="github-pat-input"
                autoComplete="off"
                spellCheck={false}
                placeholder="ghp_..."
                style={inputStyle}
              />
            </FormField>
            <FormField label="Target repo" hint="owner/name (e.g. acme/data-flows)">
              <input
                type="text"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                disabled={submitting}
                data-testid="github-repo-input"
                placeholder="owner/name"
                style={inputStyle}
              />
            </FormField>
            <div
              style={{
                display: "grid",
                gridTemplateColumns: "1fr 1fr",
                gap: "var(--space-3)",
              }}
            >
              <FormField label="Base branch">
                <input
                  type="text"
                  value={base}
                  onChange={(e) => setBase(e.target.value)}
                  disabled={submitting}
                  data-testid="github-base-input"
                  style={inputStyle}
                />
              </FormField>
              <FormField label="New branch">
                <input
                  type="text"
                  value={branch}
                  onChange={(e) => setBranch(e.target.value)}
                  disabled={submitting}
                  data-testid="github-branch-input"
                  style={inputStyle}
                />
              </FormField>
            </div>
            <FormField label="PR title">
              <input
                type="text"
                value={prTitle}
                onChange={(e) => setPrTitle(e.target.value)}
                disabled={submitting}
                data-testid="github-pr-title-input"
                style={inputStyle}
              />
            </FormField>

            {submitting || error ? (
              <ProgressList progress={progress} step={summary} />
            ) : null}

            {error ? (
              <div
                role="alert"
                data-testid="github-pr-error"
                data-error-code={error.code}
                style={{
                  marginTop: "var(--space-3)",
                  padding: "var(--space-3)",
                  borderRadius: "var(--radius-md)",
                  background: "var(--danger-bg)",
                  border: "1px solid var(--danger-border)",
                  color: "var(--danger-fg)",
                  fontSize: "var(--text-sm)",
                }}
              >
                <strong>{error.code}</strong>
                <div style={{ marginTop: 4 }}>
                  {ERROR_COPY[error.code] ?? error.message}
                </div>
              </div>
            ) : null}

            <div
              style={{
                marginTop: "var(--space-4)",
                display: "flex",
                gap: "var(--space-2)",
                justifyContent: "flex-end",
              }}
            >
              <button
                type="button"
                onClick={onClose}
                disabled={submitting}
                data-testid="github-pr-cancel"
                style={secondaryBtn}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => void onSubmit()}
                disabled={submitting || !pat || !repo || !branch || !prTitle}
                data-testid="github-pr-submit"
                style={primaryBtn(submitting)}
              >
                {submitting ? "Publishing…" : "Open PR"}
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function FormField(props: {
  label: string;
  hint?: string;
  children: React.ReactNode;
}): JSX.Element {
  return (
    <div style={{ marginBottom: "var(--space-3)" }}>
      <label
        style={{
          display: "block",
          fontSize: "var(--text-sm)",
          color: "var(--fg-muted)",
          marginBottom: "var(--space-1)",
        }}
      >
        {props.label}
      </label>
      {props.children}
      {props.hint ? (
        <div
          style={{
            fontSize: "var(--text-xs)",
            color: "var(--fg-subtle)",
            marginTop: "var(--space-1)",
          }}
        >
          {props.hint}
        </div>
      ) : null}
    </div>
  );
}

function ProgressList(props: {
  progress: ProgressState;
  step: Step;
}): JSX.Element {
  const { progress } = props;
  return (
    <ol
      data-testid="github-pr-progress"
      style={{
        listStyle: "none",
        padding: 0,
        margin: "var(--space-3) 0 0",
        fontSize: "var(--text-sm)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-1)",
      }}
    >
      <ProgressItem label="Creating branch" state={progress.branch} testId="step-branch" />
      <ProgressItem label="Committing files" state={progress.files} testId="step-files" />
      <ProgressItem label="Opening PR" state={progress.pr} testId="step-pr" />
    </ol>
  );
}

function ProgressItem(props: {
  label: string;
  state: StepState;
  testId: string;
}): JSX.Element {
  const { state, label, testId } = props;
  const symbol =
    state.status === "ok"
      ? "✓"
      : state.status === "active"
        ? "…"
        : state.status === "error"
          ? "✗"
          : "·";
  const color =
    state.status === "ok"
      ? "var(--success-fg)"
      : state.status === "error"
        ? "var(--danger-fg)"
        : state.status === "active"
          ? "var(--accent)"
          : "var(--fg-subtle)";
  return (
    <li
      data-testid={testId}
      data-status={state.status}
      style={{
        display: "flex",
        alignItems: "center",
        gap: "var(--space-2)",
        color,
      }}
    >
      <span aria-hidden="true" style={{ fontFamily: "var(--font-mono)", width: 16 }}>
        {symbol}
      </span>
      <span>{label}</span>
    </li>
  );
}

function ResultView(props: {
  result: GithubPublishResponse;
  onClose: () => void;
}): JSX.Element {
  const { result, onClose } = props;
  return (
    <div
      style={{
        padding: "var(--space-5)",
        display: "flex",
        flexDirection: "column",
        gap: "var(--space-4)",
      }}
    >
      <div
        data-testid="github-pr-success"
        style={{
          padding: "var(--space-3)",
          borderRadius: "var(--radius-md)",
          background: "var(--success-bg)",
          border: "1px solid var(--success-border)",
          color: "var(--success-fg)",
          fontSize: "var(--text-sm)",
        }}
      >
        PR #{result.pr_number} opened on branch <code>{result.branch}</code>.
      </div>
      <a
        href={result.pr_url}
        target="_blank"
        rel="noopener noreferrer"
        data-testid="github-pr-link"
        style={{
          display: "inline-block",
          padding: "var(--space-2) var(--space-4)",
          background: "var(--accent)",
          color: "var(--accent-fg)",
          textDecoration: "none",
          borderRadius: "var(--radius-md)",
          fontWeight: "var(--font-weight-semibold)",
          textAlign: "center",
        }}
      >
        Open PR on GitHub →
      </a>
      <button type="button" onClick={onClose} style={secondaryBtn}>
        Close
      </button>
    </div>
  );
}

const inputStyle: React.CSSProperties = {
  width: "100%",
  padding: "var(--space-2) var(--space-3)",
  border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius-md)",
  background: "var(--surface)",
  color: "var(--fg)",
  fontFamily: "inherit",
  fontSize: "var(--text-sm)",
};

const secondaryBtn: React.CSSProperties = {
  padding: "var(--space-2) var(--space-4)",
  border: "1px solid var(--border-strong)",
  borderRadius: "var(--radius-md)",
  background: "transparent",
  color: "inherit",
  cursor: "pointer",
  fontSize: "var(--text-sm)",
};

function primaryBtn(busy: boolean): React.CSSProperties {
  return {
    padding: "var(--space-2) var(--space-4)",
    border: 0,
    borderRadius: "var(--radius-md)",
    background: "var(--accent)",
    color: "var(--accent-fg)",
    cursor: busy ? "not-allowed" : "pointer",
    fontSize: "var(--text-sm)",
    fontWeight: "var(--font-weight-semibold)",
    opacity: busy ? 0.6 : 1,
  };
}

// Avoid ESLint "useSettingsStore unused" — reserved for a future "remember
// last repo" enhancement when we ship a settings-secret store.
void useSettingsStore;

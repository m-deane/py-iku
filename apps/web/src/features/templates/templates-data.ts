/**
 * Trade-Blotter Recipe-Template Gallery — front-office commodity-trading templates.
 *
 * Single source of truth: per-category ``templates-<category>.json`` files
 * next to this file. The FastAPI backend reads the same JSON; the frontend
 * imports them directly so we don't drift. Every entry has been round-tripped
 * through ``convert(...)`` and the actual produced
 * ``[recipe.recipe_type.value for r in flow.recipes]`` is captured under
 * ``verifiedRecipes`` — round-trip tests assert that list.
 *
 * Sprint 5 grew the catalog from 10 → 25 templates. The combined payload
 * exceeded the 30 KB single-file budget, so the catalog is split into one
 * JSON per category. The backend concatenates them at serve time; the
 * frontend imports + concatenates them here in canonical category order.
 *
 * To add a new template: write the pandas script, run it through
 * ``apps/api/.venv/bin/python -c "from py2dataiku import convert; ..."``, copy
 * the produced recipe list into ``verifiedRecipes``, and add an entry to the
 * appropriate ``templates-<category>.json``. NEVER hand-write a
 * verifiedRecipes list — capture it from a real conversion.
 */
import tradeCaptureJson from "./templates-trade-capture.json";
import positionPnlJson from "./templates-position-pnl.json";
import curvesJson from "./templates-curves.json";
import counterpartyJson from "./templates-counterparty.json";
import powerJson from "./templates-power.json";

export type TemplateCategory =
  | "trade-capture"
  | "position-pnl"
  | "curves"
  | "counterparty"
  | "power";

export type TemplatePersona =
  | "trader"
  | "risk"
  | "middle-office"
  | "data-eng"
  | "quant";

/**
 * Sprint 5 — parametric templates. A template's ``pythonSource`` may contain
 * ``${PLACEHOLDER}`` markers; the Open-in-Editor flow prompts the user to
 * fill them via ``ParameterForm``. Substitution is plain string-replace, no
 * eval — every value is rendered as-typed (or ISO-formatted for dates).
 */
export type ParameterType = "text" | "date" | "number" | "select";

export interface ParameterSpec {
  name: string;
  label: string;
  type: ParameterType;
  defaultValue: string;
  /** Required for ``type === "select"``. */
  choices?: string[];
  description?: string;
}

export interface FlowTemplate {
  id: string;
  name: string;
  category: TemplateCategory;
  summary: string;
  personas: TemplatePersona[];
  tags: string[];
  pythonSource: string;
  verifiedRecipes: string[];
  verifiedDatasets: string[];
  estimatedSavingMinutes: number;
  /** Optional — present only on parametric templates. */
  parameters?: ParameterSpec[];
}

/**
 * Substitute ``${NAME}`` placeholders in *source* using a name -> value map.
 * Plain string replacement only — no eval, no shell interpretation. Unknown
 * placeholders are left as-is so a template-author error doesn't silently
 * lose information.
 */
export function applyTemplateParameters(
  source: string,
  values: Record<string, string>,
): string {
  let out = source;
  for (const [name, value] of Object.entries(values)) {
    // Use a literal find-replace rather than RegExp so values that happen to
    // contain regex metacharacters are still inserted verbatim.
    const needle = "${" + name + "}";
    out = out.split(needle).join(value);
  }
  return out;
}

/** Today's ISO date in UTC — exposed as a helper so tests can stub it. */
export function isoToday(now: Date = new Date()): string {
  const yyyy = now.getUTCFullYear();
  const mm = String(now.getUTCMonth() + 1).padStart(2, "0");
  const dd = String(now.getUTCDate()).padStart(2, "0");
  return `${yyyy}-${mm}-${dd}`;
}

/**
 * Build the initial form values for a template's parameters. Honours the
 * ``${TODAY}`` convention by injecting today's ISO date as the default for
 * any date-type parameter named ``TODAY``.
 */
export function defaultParameterValues(
  template: Pick<FlowTemplate, "parameters">,
): Record<string, string> {
  const out: Record<string, string> = {};
  if (!template.parameters) return out;
  for (const p of template.parameters) {
    if (p.type === "date" && p.name === "TODAY") {
      out[p.name] = p.defaultValue || isoToday();
    } else {
      out[p.name] = p.defaultValue;
    }
  }
  return out;
}

// Concatenate per-category files in the canonical category order. The
// resulting array order is stable and deterministic, so UI tests that
// rely on index can still rely on it.
export const TEMPLATES: readonly FlowTemplate[] = [
  ...(tradeCaptureJson as FlowTemplate[]),
  ...(positionPnlJson as FlowTemplate[]),
  ...(curvesJson as FlowTemplate[]),
  ...(counterpartyJson as FlowTemplate[]),
  ...(powerJson as FlowTemplate[]),
];

export const TEMPLATE_CATEGORIES: ReadonlyArray<{
  value: TemplateCategory;
  label: string;
}> = [
  { value: "trade-capture", label: "Trade Capture" },
  { value: "position-pnl", label: "Position & P&L" },
  { value: "curves", label: "Curves" },
  { value: "counterparty", label: "Counterparty" },
  { value: "power", label: "Power" },
];

export function getTemplate(id: string): FlowTemplate | undefined {
  return TEMPLATES.find((t) => t.id === id);
}

export function getTemplatesByCategory(
  category: TemplateCategory,
): readonly FlowTemplate[] {
  return TEMPLATES.filter((t) => t.category === category);
}

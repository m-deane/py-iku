/**
 * Trade-Blotter Recipe-Template Gallery — front-office commodity-trading templates.
 *
 * Single source of truth: ``templates.json`` next to this file. The FastAPI
 * backend reads the same JSON; the frontend imports it directly so we don't
 * drift. Every entry has been round-tripped through ``convert(...)`` and the
 * actual produced ``[recipe.recipe_type.value for r in flow.recipes]`` is
 * captured under ``verifiedRecipes`` — round-trip tests assert that list.
 *
 * To add a new template: write the pandas script, run it through
 * ``apps/api/.venv/bin/python -c "from py2dataiku import convert; ..."``, copy
 * the produced recipe list into ``verifiedRecipes``, and add an entry to
 * ``templates.json``. NEVER hand-write a verifiedRecipes list — capture it
 * from a real conversion.
 */
import templatesJson from "./templates.json";

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
}

export const TEMPLATES: readonly FlowTemplate[] = templatesJson as FlowTemplate[];

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

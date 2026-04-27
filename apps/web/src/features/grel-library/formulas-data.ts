/**
 * Pre-built GREL formula library — front-office trading accelerators.
 *
 * Each entry pairs a Dataiku DSS GREL expression (the exact string a desk
 * analyst would paste into a CREATE_COLUMN_WITH_GREL processor) with the
 * pandas equivalent that a quant would write in a notebook.
 *
 * Conventions:
 *   - Heat rate is in MMBtu/MWh (US convention). A "10 heat rate" market
 *     means the implied burn at the gas-power crossover.
 *   - Crack spread sign convention follows NYMEX: $/bbl positive = refiner
 *     margin. 3:2:1 = (2*RBOB + 1*HO - 3*WTI) / 3 in $/bbl.
 *   - All commodity codes are real venue tickers (CL, RB, HO, NG, B, TTF,
 *     JKM, PJM-W, AEP-DAYTON-HUB, TC2, TC5).
 *   - The pandas snippet is "one-line so a trader can drop it into the
 *     editor without restructuring their script". Multi-step computations
 *     read columns that already exist in the trader's DataFrame.
 */

export type GrelFormulaCategory =
  | "crack-spread"
  | "heat-rate"
  | "basis"
  | "freight"
  | "custom";

export interface GrelFormula {
  id: string;
  name: string;
  category: GrelFormulaCategory;
  description: string;
  /** GREL expression — exactly what goes into a DSS prepare-step formula. */
  grel: string;
  /** pandas one-liner equivalent. Assumes a DataFrame named ``df``. */
  pandas: string;
  /** Unit semantics for the output column. */
  unit: string;
  /** Real venue / instrument tickers this formula touches. */
  relatedInstruments: string[];
  /** Worked numeric example so a trader can sanity-check the result. */
  example: {
    inputs: Record<string, number>;
    output: number;
    notes: string;
  };
}

export const GREL_FORMULAS: readonly GrelFormula[] = [
  // -------------------------------------------------------------------------
  // Crack spreads
  // -------------------------------------------------------------------------
  {
    id: "crack-3-2-1",
    name: "3:2:1 Crack Spread",
    category: "crack-spread",
    description:
      "Industry-standard refiner margin — 3 barrels of WTI yield 2 of gasoline (RBOB) and 1 of heating oil (HO). Quoted in $/bbl on NYMEX.",
    grel: "(2 * val(\"rbob_price\") * 42 + 1 * val(\"ho_price\") * 42 - 3 * val(\"wti_price\")) / 3",
    pandas:
      "df[\"crack_3_2_1\"] = (2 * df[\"rbob_price\"] * 42 + 1 * df[\"ho_price\"] * 42 - 3 * df[\"wti_price\"]) / 3",
    unit: "$/bbl",
    relatedInstruments: ["CL", "RB", "HO"],
    example: {
      inputs: { wti_price: 78.5, rbob_price: 2.45, ho_price: 2.62 },
      output: 23.43,
      notes:
        "RBOB and HO trade in $/gal — multiply by 42 gal/bbl to align with WTI's $/bbl quote.",
    },
  },
  {
    id: "crack-2-1-1",
    name: "2:1:1 Crack Spread",
    category: "crack-spread",
    description:
      "Simpler refiner-margin proxy — 2 bbl crude yield 1 bbl gasoline + 1 bbl distillate. Used when the desk does not split RBOB/HO unevenly.",
    grel: "(val(\"rbob_price\") * 42 + val(\"ho_price\") * 42 - 2 * val(\"wti_price\")) / 2",
    pandas:
      "df[\"crack_2_1_1\"] = (df[\"rbob_price\"] * 42 + df[\"ho_price\"] * 42 - 2 * df[\"wti_price\"]) / 2",
    unit: "$/bbl",
    relatedInstruments: ["CL", "RB", "HO"],
    example: {
      inputs: { wti_price: 78.5, rbob_price: 2.45, ho_price: 2.62 },
      output: 27.22,
      notes: "Equal-weight gasoline and distillate yield.",
    },
  },
  {
    id: "crack-gasoline",
    name: "Gasoline Crack (RBOB-WTI)",
    category: "crack-spread",
    description:
      "Single-product RBOB-vs-WTI margin. Quote convention: $/bbl. Common summer-driving-season hedge.",
    grel: "val(\"rbob_price\") * 42 - val(\"wti_price\")",
    pandas: "df[\"gasoline_crack\"] = df[\"rbob_price\"] * 42 - df[\"wti_price\"]",
    unit: "$/bbl",
    relatedInstruments: ["RB", "CL"],
    example: {
      inputs: { wti_price: 78.5, rbob_price: 2.45 },
      output: 24.4,
      notes: "RBOB at $2.45/gal -> $102.90/bbl, minus $78.50 WTI = $24.40 crack.",
    },
  },
  {
    id: "crack-distillate",
    name: "Distillate Crack (HO-WTI)",
    category: "crack-spread",
    description:
      "Single-product heating-oil-vs-WTI margin. Quote convention: $/bbl. Winter-demand hedge.",
    grel: "val(\"ho_price\") * 42 - val(\"wti_price\")",
    pandas: "df[\"distillate_crack\"] = df[\"ho_price\"] * 42 - df[\"wti_price\"]",
    unit: "$/bbl",
    relatedInstruments: ["HO", "CL"],
    example: {
      inputs: { wti_price: 78.5, ho_price: 2.62 },
      output: 31.54,
      notes: "HO at $2.62/gal -> $110.04/bbl, minus $78.50 WTI = $31.54 crack.",
    },
  },

  // -------------------------------------------------------------------------
  // Heat rates
  // -------------------------------------------------------------------------
  {
    id: "heat-rate-market",
    name: "Market Heat Rate (Power/Gas)",
    category: "heat-rate",
    description:
      "Implied burn that equates power to gas at current prices. >gen heat rate means CCGT is in the money.",
    grel: "val(\"power_price\") / val(\"gas_price\")",
    pandas: "df[\"market_heat_rate\"] = df[\"power_price\"] / df[\"gas_price\"]",
    unit: "MMBtu/MWh",
    relatedInstruments: ["PJM-W", "AEP-DAYTON-HUB", "Henry Hub"],
    example: {
      inputs: { power_price: 42.5, gas_price: 3.4 },
      output: 12.5,
      notes: "$42.50/MWh vs $3.40/MMBtu = 12.5 implied heat rate.",
    },
  },
  {
    id: "heat-rate-implied",
    name: "Implied Spark Spread Heat Rate",
    category: "heat-rate",
    description:
      "Spark spread expressed as the heat rate that zeros it out. Useful when comparing assets with different fixed efficiencies.",
    grel:
      "(val(\"power_price\") - val(\"vom\") - val(\"emissions_cost\")) / val(\"gas_price\")",
    pandas:
      "df[\"implied_hr\"] = (df[\"power_price\"] - df[\"vom\"] - df[\"emissions_cost\"]) / df[\"gas_price\"]",
    unit: "MMBtu/MWh",
    relatedInstruments: ["PJM-W", "Henry Hub", "EUA"],
    example: {
      inputs: { power_price: 42.5, gas_price: 3.4, vom: 3.0, emissions_cost: 1.2 },
      output: 11.26,
      notes: "Same desk gas/power but net of variable O&M and emissions cost.",
    },
  },

  // -------------------------------------------------------------------------
  // Basis
  // -------------------------------------------------------------------------
  {
    id: "basis-pjm-hh",
    name: "Gas-Power Basis (PJM-W vs Henry Hub)",
    category: "basis",
    description:
      "Power-side basis trade — how much PJM Western Hub clears above the gas benchmark on a heat-rate-adjusted basis.",
    grel:
      "val(\"pjm_w_price\") - val(\"henry_hub_price\") * val(\"reference_heat_rate\")",
    pandas:
      "df[\"basis_pjm_hh\"] = df[\"pjm_w_price\"] - df[\"henry_hub_price\"] * df[\"reference_heat_rate\"]",
    unit: "$/MWh",
    relatedInstruments: ["PJM-W", "Henry Hub"],
    example: {
      inputs: { pjm_w_price: 42.5, henry_hub_price: 3.4, reference_heat_rate: 10.0 },
      output: 8.5,
      notes: "$42.50 - 3.4 * 10 = $8.50 basis (CCGT margin at 10 HR).",
    },
  },
  {
    id: "basis-ttf-nbp",
    name: "TTF-NBP Basis",
    category: "basis",
    description:
      "European cross-hub gas basis. TTF (NL) is the continental benchmark; NBP (UK) settles in p/therm and must be unit-converted.",
    grel: "val(\"ttf_price\") - val(\"nbp_price\") * 0.0341",
    pandas: "df[\"ttf_nbp_basis\"] = df[\"ttf_price\"] - df[\"nbp_price\"] * 0.0341",
    unit: "EUR/MWh",
    relatedInstruments: ["TTF", "NBP"],
    example: {
      inputs: { ttf_price: 32.4, nbp_price: 92.5 },
      output: 28.85,
      notes:
        "NBP p/th * 0.0341 ≈ EUR/MWh assuming 1 GBP = 1.17 EUR; refresh the FX scalar from the curve set.",
    },
  },
  {
    id: "basis-jkm-ttf",
    name: "JKM-TTF Basis",
    category: "basis",
    description:
      "Asia-Europe LNG arb proxy. Positive JKM-TTF means a cargo points at Asia after freight + reload costs.",
    grel: "val(\"jkm_price\") - val(\"ttf_price\")",
    pandas: "df[\"jkm_ttf_basis\"] = df[\"jkm_price\"] - df[\"ttf_price\"]",
    unit: "$/MMBtu",
    relatedInstruments: ["JKM", "TTF"],
    example: {
      inputs: { jkm_price: 11.45, ttf_price: 9.8 },
      output: 1.65,
      notes:
        "Compare against the headline freight (TC2/TC5) + reload spread to see if the arb is open.",
    },
  },

  // -------------------------------------------------------------------------
  // Freight
  // -------------------------------------------------------------------------
  {
    id: "freight-netback",
    name: "Freight Netback (TC2/TC5)",
    category: "freight",
    description:
      "Delivered-cargo netback after freight charter — TC2 (UK-USAC) or TC5 (Mideast-Japan) Worldscale rates.",
    grel:
      "val(\"delivered_price\") - val(\"ws_rate\") * val(\"flat_rate\") / 100",
    pandas:
      "df[\"freight_netback\"] = df[\"delivered_price\"] - df[\"ws_rate\"] * df[\"flat_rate\"] / 100",
    unit: "$/bbl",
    relatedInstruments: ["TC2", "TC5"],
    example: {
      inputs: { delivered_price: 78.5, ws_rate: 145, flat_rate: 18.5 },
      output: 51.67,
      notes:
        "WS 145 on TC2 flat-rate $18.50 = $26.83/bbl freight; netback = delivered - freight.",
    },
  },

  // -------------------------------------------------------------------------
  // Grade / location differentials
  // -------------------------------------------------------------------------
  {
    id: "grade-diff-wti-brent",
    name: "WTI-Brent Grade Differential",
    category: "custom",
    description:
      "Atlantic-basin sweet-grade arb. Negative WTI-Brent means Brent is rich; the global proxy for US crude exports.",
    grel: "val(\"wti_price\") - val(\"brent_price\")",
    pandas: "df[\"wti_brent\"] = df[\"wti_price\"] - df[\"brent_price\"]",
    unit: "$/bbl",
    relatedInstruments: ["CL", "B"],
    example: {
      inputs: { wti_price: 78.5, brent_price: 82.1 },
      output: -3.6,
      notes: "Brent rich by $3.60 — supports US crude exports.",
    },
  },
  {
    id: "loc-diff-pjm-w-aep",
    name: "PJM-W vs AEP-Dayton-Hub Location Diff",
    category: "custom",
    description:
      "Internal PJM congestion proxy — Western Hub vs AEP-Dayton-Hub. Used for FTR-style locational hedges.",
    grel: "val(\"pjm_w_price\") - val(\"aep_dayton_price\")",
    pandas: "df[\"pjm_w_aep\"] = df[\"pjm_w_price\"] - df[\"aep_dayton_price\"]",
    unit: "$/MWh",
    relatedInstruments: ["PJM-W", "AEP-DAYTON-HUB"],
    example: {
      inputs: { pjm_w_price: 42.5, aep_dayton_price: 39.1 },
      output: 3.4,
      notes: "$3.40/MWh PJM-W premium over AEP-Dayton — congestion towards the east.",
    },
  },
];

export const GREL_CATEGORIES: ReadonlyArray<{
  value: GrelFormulaCategory;
  label: string;
}> = [
  { value: "crack-spread", label: "Crack Spread" },
  { value: "heat-rate", label: "Heat Rate" },
  { value: "basis", label: "Basis" },
  { value: "freight", label: "Freight" },
  { value: "custom", label: "Differential" },
];

export function getFormula(id: string): GrelFormula | undefined {
  return GREL_FORMULAS.find((f) => f.id === id);
}

export function getFormulasByCategory(
  category: GrelFormulaCategory,
): readonly GrelFormula[] {
  return GREL_FORMULAS.filter((f) => f.category === category);
}

/**
 * Build the comment+pandas snippet that the "Insert into editor" button
 * prepends to the active code buffer. Kept here so the test suite and the
 * page agree on the exact shape.
 */
export function buildInsertSnippet(formula: GrelFormula): string {
  const header =
    `# ${formula.name} — ${formula.category}\n` +
    `# ${formula.description}\n` +
    `# unit: ${formula.unit} | instruments: ${formula.relatedInstruments.join(", ")}\n` +
    `# GREL: ${formula.grel}\n`;
  return `${header}${formula.pandas}\n`;
}

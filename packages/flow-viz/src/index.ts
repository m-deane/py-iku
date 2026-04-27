/**
 * @py-iku-studio/flow-viz — public API.
 *
 * M3a surface: FlowCanvas, RecipeNode, DatasetNode, FlowEdge, ELK layout
 * helper, token loader and lookup helpers, type re-exports.
 *
 * M3b additions: 37 RecipeType node coverage (via category-based design),
 * zone overlays, focus mode, animated execution simulation, and
 * SVG/PNG/PDF export.
 */

export { FlowCanvas } from "./FlowCanvas";
export type { FlowCanvasProps, FlowCanvasSimulationProps } from "./FlowCanvas";

export { RecipeNode, bandFor } from "./nodes/RecipeNode";
export type { ConfidenceBand } from "./nodes/RecipeNode";
export { DatasetNode } from "./nodes/DatasetNode";
export {
  nodeTypes,
  REPRESENTATIVE_RECIPE_TYPES,
  ALL_RECIPE_TYPES,
  categoryFor,
  subLabelFor,
  getSvgGlyph,
  SVG_GLYPH_TYPES,
} from "./nodes";
export type { RecipeCategory } from "./nodes";

export { FlowEdge, edgeTypes } from "./edges/FlowEdge";

export { layoutFlow } from "./layout/elkLayout";
export type { ElkLayoutOptions } from "./layout/elkLayout";

export {
  loadTokens,
  getRecipeColor,
  getDatasetColor,
  getConnectionColor,
  getDatasetShape,
  SPACING,
  NODE_SIZES,
} from "./theme/tokens";
export type { Tokens, DatasetShape } from "./theme/tokens";

export { getRecipeGlyph } from "./theme/icons";

// M3b: zones
export {
  Zone,
  ZoneLayer,
  autoAssignZones,
  getZoneColor,
  ZONE_LABELS,
  ZONE_ORDER,
  ZONE_PALETTE_INDEX,
  ZONE_PALETTE_SIZE,
  ZONE_PADDING,
  ZONE_RADIUS,
} from "./zones";
export type { ZoneId, ZoneProps, ZoneRect, ZoneLayerProps } from "./zones";

// M3b: focus mode
export { useFocusMode, computeFocus } from "./focus";
export type { FocusModeResult } from "./focus";

// M3b: simulation
export { useExecutionSim, topologicalSort } from "./sim";
export type {
  SimNodeStatus,
  UseExecutionSimOptions,
  UseExecutionSimResult,
} from "./sim";

// M3b: export to SVG / PNG / PDF
export { toSvg, toPng, toPdf } from "./export";
export type {
  ExportOptions,
  PngExportOptions,
  PdfExportOptions,
  PdfNodeRow,
} from "./export";

export type {
  RecipeType,
  DatasetType,
  DatasetConnectionType,
  ThemeName,
  NodeStatus,
  RecipeNodeData,
  DatasetNodeData,
  FlowNode,
  FlowEdge as FlowEdgeModel,
  MinimalFlow,
} from "./types";

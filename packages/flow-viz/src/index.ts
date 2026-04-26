/**
 * @py-iku-studio/flow-viz — public API.
 *
 * M3a surface: FlowCanvas, RecipeNode, DatasetNode, FlowEdge, ELK layout
 * helper, token loader and lookup helpers, type re-exports.
 *
 * M3b will add: focus-mode controls, animated execution simulation, zone
 * overlays, full 37-RecipeType node coverage, and SVG/PNG/PDF export.
 */

export { FlowCanvas } from "./FlowCanvas";
export type { FlowCanvasProps } from "./FlowCanvas";

export { RecipeNode } from "./nodes/RecipeNode";
export { DatasetNode } from "./nodes/DatasetNode";
export { nodeTypes, REPRESENTATIVE_RECIPE_TYPES } from "./nodes";

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

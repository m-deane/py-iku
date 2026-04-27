import { memo, type CSSProperties } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import clsx from "clsx";
import type { NodeStatus, RecipeNodeData, RecipeType, ThemeName } from "../types";
import { getRecipeColor } from "../theme/tokens";
import { getRecipeGlyph } from "../theme/icons";
import { categoryFor, subLabelFor, type RecipeCategory } from "./categories";
import { getSvgGlyph } from "./glyphs";
import styles from "./RecipeNode.module.css";

interface RecipeNodeProps extends NodeProps<RecipeNodeData> {
  /** Optional theme override; defaults to reading the closest `data-theme` attr. */
  theme?: ThemeName;
  /** Override the auto-derived category. Used by tests / stories. */
  category?: RecipeCategory;
}

function readTheme(): ThemeName {
  if (typeof document === "undefined") return "light";
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "dark" ? "dark" : "light";
}

/**
 * Base recipe node. Renders the rounded tile with category-color stripe,
 * SVG or Unicode glyph, label, optional sub-label badge (code recipes get a
 * monospace language tag), IO badges, status badge, and category-specific
 * decorations. Colors are read from `tokens.json` per RecipeType + theme;
 * no hard-coded hex.
 *
 * Supports the M3b interaction states:
 *   - `data.dimmed === true` → focus-mode dim
 *   - `data.status === "executing"` → shimmer overlay
 *   - `data.status === "done"` → solid filled status badge
 */
function RecipeNodeImpl(props: RecipeNodeProps): JSX.Element {
  const { data, selected, theme: themeProp, category: categoryProp } = props;
  const theme: ThemeName = themeProp ?? readTheme();
  const colors = getRecipeColor(data.type, theme);
  const status: NodeStatus = data.status ?? "none";
  const category = categoryProp ?? categoryFor(data.type);
  const SvgGlyph = getSvgGlyph(data.type);
  const subLabel = subLabelFor(data.type);
  const dimmed = data.dimmed === true;

  const styleVars: CSSProperties = {
    ["--node-bg" as string]: colors.bg,
    ["--node-border" as string]: colors.border,
    ["--node-text" as string]: colors.text,
  };

  return (
    <div
      className={clsx(
        styles.recipeNode,
        styles[`category-${category}`],
        selected && styles.selected,
        status === "error" && styles.error,
        status === "executing" && styles.executing,
        status === "done" && styles.done,
        dimmed && styles.dimmed,
      )}
      style={styleVars}
      data-recipe-type={data.type}
      data-category={category}
      data-status={status}
      data-theme={theme}
      data-dimmed={dimmed ? "true" : undefined}
    >
      <Handle type="target" position={Position.Left} />
      <span className={styles.icon} aria-hidden="true">
        {SvgGlyph ? <SvgGlyph color={colors.text} size={20} /> : getRecipeGlyph(data.type)}
      </span>
      <span className={styles.label}>{data.name}</span>
      {subLabel && (
        <span className={styles.subLabel} aria-hidden="true">
          {subLabel}
        </span>
      )}
      <span className={styles.ioRow}>
        <span className={styles.ioBadge} aria-label={`${data.inputs} inputs`}>
          ◀{data.inputs}
        </span>
        <span className={styles.ioBadge} aria-label={`${data.outputs} outputs`}>
          {data.outputs}▶
        </span>
      </span>
      {status !== "none" && (
        <span
          className={clsx(
            styles.statusBadge,
            status === "deployed" && styles.deployed,
            status === "deploying" && styles.deploying,
            status === "error" && styles.errorBadge,
            status === "done" && styles.doneBadge,
            status === "executing" && styles.executingBadge,
          )}
          aria-label={`status ${status}`}
        />
      )}
      {status === "executing" && <span className={styles.shimmer} aria-hidden="true" />}
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export const RecipeNode = memo(RecipeNodeImpl);
RecipeNode.displayName = "RecipeNode";

/** Helper used by `nodeTypes` map below to bind a fixed RecipeType. */
export function makeRecipeNodeForType(
  type: RecipeType,
): (props: NodeProps<RecipeNodeData>) => JSX.Element {
  const Bound = (props: NodeProps<RecipeNodeData>): JSX.Element => {
    const data: RecipeNodeData = { ...props.data, type };
    return <RecipeNode {...props} data={data} />;
  };
  Bound.displayName = `RecipeNode(${type})`;
  return Bound;
}

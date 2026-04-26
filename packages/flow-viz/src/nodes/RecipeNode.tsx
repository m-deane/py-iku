import { memo, type CSSProperties } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import clsx from "clsx";
import type { NodeStatus, RecipeNodeData, RecipeType, ThemeName } from "../types";
import { getRecipeColor } from "../theme/tokens";
import { getRecipeGlyph } from "../theme/icons";
import styles from "./RecipeNode.module.css";

interface RecipeNodeProps extends NodeProps<RecipeNodeData> {
  /** Optional theme override; defaults to reading the closest `data-theme` attr. */
  theme?: ThemeName;
}

function readTheme(): ThemeName {
  if (typeof document === "undefined") return "light";
  const attr = document.documentElement.getAttribute("data-theme");
  return attr === "dark" ? "dark" : "light";
}

/**
 * Base recipe node. Renders the rounded tile with category-color stripe,
 * Unicode glyph, label, IO badges, and a status-badge slot. Colors are read
 * from `tokens.json` per RecipeType + theme; no hard-coded hex.
 */
function RecipeNodeImpl(props: RecipeNodeProps): JSX.Element {
  const { data, selected, theme: themeProp } = props;
  const theme: ThemeName = themeProp ?? readTheme();
  const colors = getRecipeColor(data.type, theme);
  const glyph = getRecipeGlyph(data.type);
  const status: NodeStatus = data.status ?? "none";

  const styleVars: CSSProperties = {
    ["--node-bg" as string]: colors.bg,
    ["--node-border" as string]: colors.border,
    ["--node-text" as string]: colors.text,
  };

  return (
    <div
      className={clsx(styles.recipeNode, selected && styles.selected, status === "error" && styles.error)}
      style={styleVars}
      data-recipe-type={data.type}
      data-status={status}
      data-theme={theme}
    >
      <Handle type="target" position={Position.Left} />
      <span className={styles.icon} aria-hidden="true">
        {glyph}
      </span>
      <span className={styles.label}>{data.name}</span>
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
            status === "error" && styles.error,
          )}
          aria-label={`status ${status}`}
        />
      )}
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

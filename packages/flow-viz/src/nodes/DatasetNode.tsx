import { memo, type CSSProperties } from "react";
import { Handle, Position, type NodeProps } from "reactflow";
import clsx from "clsx";
import type { DatasetNodeData, ThemeName } from "../types";
import { getDatasetColor, getDatasetShape, type DatasetShape } from "../theme/tokens";
import styles from "./DatasetNode.module.css";

interface DatasetNodeProps extends NodeProps<DatasetNodeData> {
  theme?: ThemeName;
}

function readTheme(): ThemeName {
  if (typeof document === "undefined") return "light";
  return document.documentElement.getAttribute("data-theme") === "dark" ? "dark" : "light";
}

function ShapeSvg(props: { shape: DatasetShape; color: string }): JSX.Element {
  const { shape, color } = props;
  if (shape === "cylinder") {
    return (
      <svg viewBox="0 0 24 28" width="24" height="28" aria-hidden="true">
        <ellipse cx="12" cy="5" rx="10" ry="3" fill="none" stroke={color} strokeWidth="1.5" />
        <path d="M2 5 V23 A10 3 0 0 0 22 23 V5" fill="none" stroke={color} strokeWidth="1.5" />
        <ellipse cx="12" cy="23" rx="10" ry="3" fill="none" stroke={color} strokeWidth="1.5" />
      </svg>
    );
  }
  if (shape === "folder") {
    return (
      <svg viewBox="0 0 24 28" width="24" height="28" aria-hidden="true">
        <path
          d="M2 8 V23 H22 V10 H12 L9 7 H2 Z"
          fill="none"
          stroke={color}
          strokeWidth="1.5"
          strokeLinejoin="round"
        />
      </svg>
    );
  }
  // document
  return (
    <svg viewBox="0 0 24 28" width="24" height="28" aria-hidden="true">
      <path
        d="M5 3 H15 L19 7 V25 H5 Z"
        fill="none"
        stroke={color}
        strokeWidth="1.5"
        strokeLinejoin="round"
      />
      <path d="M15 3 V7 H19" fill="none" stroke={color} strokeWidth="1.5" />
      <line x1="8" y1="13" x2="16" y2="13" stroke={color} strokeWidth="1" />
      <line x1="8" y1="17" x2="16" y2="17" stroke={color} strokeWidth="1" />
      <line x1="8" y1="21" x2="13" y2="21" stroke={color} strokeWidth="1" />
    </svg>
  );
}

function DatasetNodeImpl(props: DatasetNodeProps): JSX.Element {
  const { data, selected, theme: themeProp } = props;
  const theme: ThemeName = themeProp ?? readTheme();
  const colors = getDatasetColor(data.datasetType, theme);
  const shape = getDatasetShape(data.connectionType);
  const dimmed = data.dimmed === true;

  const styleVars: CSSProperties = {
    ["--ds-bg" as string]: colors.bg,
    ["--ds-border" as string]: colors.border,
    ["--ds-text" as string]: colors.text,
  };

  return (
    <div
      className={clsx(styles.datasetNode, selected && styles.selected, dimmed && styles.dimmed)}
      style={styleVars}
      data-dataset-type={data.datasetType}
      data-connection-type={data.connectionType}
      data-theme={theme}
      data-dimmed={dimmed ? "true" : undefined}
    >
      <Handle type="target" position={Position.Left} />
      <span className={styles.shape}>
        <ShapeSvg shape={shape} color={colors.border} />
      </span>
      <span className={styles.body}>
        <span className={styles.name}>{data.name}</span>
        <span className={styles.tag}>{data.connectionType.replace(/_/g, " ").toLowerCase()}</span>
      </span>
      <Handle type="source" position={Position.Right} />
    </div>
  );
}

export const DatasetNode = memo(DatasetNodeImpl);
DatasetNode.displayName = "DatasetNode";

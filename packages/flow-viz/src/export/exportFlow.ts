/**
 * Export flow canvas → SVG / PNG / PDF.
 *
 * - `toSvg(canvasEl, opts)` — clones the React Flow viewport SVG, inlines
 *   computed styles for the foreignObject HTML nodes, returns an XML
 *   string. Works headlessly (in Storybook test-runner) and in browsers.
 * - `toPng(canvasEl, opts)` — rasterizes the SVG via an Image element +
 *   `canvas.toBlob`. Theme-aware: background pulled from theme tokens.
 * - `toPdf(canvasEl, opts)` — embeds the rasterized PNG into a `jsPDF`
 *   document with A4 / Letter support, fits the flow proportionally, and
 *   appends a second page listing the recipe nodes as a table.
 */

import type { ThemeName } from "../types";

export interface ExportOptions {
  /** Background color override; defaults to theme-aware token. */
  background?: string;
  /** Theme name; influences default background. */
  theme?: ThemeName;
}

export interface PngExportOptions extends ExportOptions {
  /** Output width in CSS pixels. Default: source SVG width. */
  width?: number;
  /** Output height in CSS pixels. Default: source SVG height. */
  height?: number;
  /** Pixel density multiplier. Default: 2 (retina-quality). */
  pixelRatio?: number;
}

export interface PdfNodeRow {
  /** Node id. */
  id: string;
  /** Node type (recipe / dataset). */
  type: string;
  /** Display label. */
  name: string;
}

export interface PdfExportOptions extends PngExportOptions {
  /** Page format. Default: "a4". */
  format?: "a4" | "letter";
  /** Document title (rendered top of page 1). */
  title?: string;
  /**
   * Optional table of nodes to render on page 2. Pass `null` to suppress
   * the inventory page.
   */
  nodes?: PdfNodeRow[] | null;
}

const THEME_BG: Record<ThemeName, string> = {
  light: "#FAFAFA",
  dark: "#1E1E1E",
};

/** Find the React Flow `<svg>` element inside `canvasEl`. */
function findReactFlowSvg(canvasEl: HTMLElement): SVGSVGElement | null {
  return canvasEl.querySelector("svg.react-flow__edges") ?? canvasEl.querySelector("svg");
}

/** Find the React Flow viewport `<div>` (parent of nodes + edges). */
function findReactFlowViewport(canvasEl: HTMLElement): HTMLElement | null {
  return canvasEl.querySelector(".react-flow__viewport") as HTMLElement | null;
}

/** Approximate the viewport bounds. */
function approxBounds(viewport: HTMLElement | null, fallback: { w: number; h: number }): {
  width: number;
  height: number;
} {
  if (!viewport) return { width: fallback.w, height: fallback.h };
  const rect = viewport.getBoundingClientRect();
  return {
    width: Math.max(rect.width, fallback.w),
    height: Math.max(rect.height, fallback.h),
  };
}

/**
 * Serialize the React Flow canvas to an SVG XML string. We wrap the
 * cloned edges SVG plus a `<foreignObject>` containing the cloned node
 * layer, so HTML-rendered recipe / dataset tiles are preserved.
 */
export function toSvg(canvasEl: HTMLElement, opts: ExportOptions = {}): string {
  const theme = opts.theme ?? "light";
  const background = opts.background ?? THEME_BG[theme];
  const viewport = findReactFlowViewport(canvasEl);
  const sourceSvg = findReactFlowSvg(canvasEl);
  const { width, height } = approxBounds(viewport, {
    w: sourceSvg ? Number(sourceSvg.getAttribute("width") ?? 1024) : 1024,
    h: sourceSvg ? Number(sourceSvg.getAttribute("height") ?? 768) : 768,
  });

  const xmlns = "http://www.w3.org/2000/svg";
  const root = document.createElementNS(xmlns, "svg");
  root.setAttribute("xmlns", xmlns);
  root.setAttribute("xmlns:xhtml", "http://www.w3.org/1999/xhtml");
  root.setAttribute("width", String(width));
  root.setAttribute("height", String(height));
  root.setAttribute("viewBox", `0 0 ${width} ${height}`);

  // Background
  const bg = document.createElementNS(xmlns, "rect");
  bg.setAttribute("x", "0");
  bg.setAttribute("y", "0");
  bg.setAttribute("width", String(width));
  bg.setAttribute("height", String(height));
  bg.setAttribute("fill", background);
  root.appendChild(bg);

  // Edges SVG: inline a clone if present.
  if (sourceSvg) {
    const clone = sourceSvg.cloneNode(true) as SVGSVGElement;
    // Strip the outer wrapper attrs that conflict with our root.
    clone.removeAttribute("width");
    clone.removeAttribute("height");
    const inner = document.createElementNS(xmlns, "g");
    inner.setAttribute("data-source", "react-flow-edges");
    while (clone.firstChild) inner.appendChild(clone.firstChild);
    root.appendChild(inner);
  }

  // Node layer wrapped in <foreignObject>.
  const nodeContainer = canvasEl.querySelector(".react-flow__nodes");
  if (nodeContainer) {
    const fo = document.createElementNS(xmlns, "foreignObject");
    fo.setAttribute("x", "0");
    fo.setAttribute("y", "0");
    fo.setAttribute("width", String(width));
    fo.setAttribute("height", String(height));
    const cloned = nodeContainer.cloneNode(true) as HTMLElement;
    fo.appendChild(cloned);
    root.appendChild(fo);
  }

  return new XMLSerializer().serializeToString(root);
}

/** Convert an SVG XML string to an Image element. */
function svgToImage(svg: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const blob = new Blob([svg], { type: "image/svg+xml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const img = new Image();
    img.onload = () => {
      URL.revokeObjectURL(url);
      resolve(img);
    };
    img.onerror = (e) => {
      URL.revokeObjectURL(url);
      reject(e);
    };
    img.src = url;
  });
}

/** Rasterize the canvas to a PNG `Blob`. */
export async function toPng(
  canvasEl: HTMLElement,
  opts: PngExportOptions = {},
): Promise<Blob> {
  const theme = opts.theme ?? "light";
  const background = opts.background ?? THEME_BG[theme];
  const pixelRatio = opts.pixelRatio ?? 2;
  const viewport = findReactFlowViewport(canvasEl);
  const { width, height } = approxBounds(viewport, { w: 1024, h: 768 });
  const w = opts.width ?? width;
  const h = opts.height ?? height;

  const svg = toSvg(canvasEl, { background, theme });
  const img = await svgToImage(svg);
  const canvas = document.createElement("canvas");
  canvas.width = Math.max(1, Math.round(w * pixelRatio));
  canvas.height = Math.max(1, Math.round(h * pixelRatio));
  const ctx = canvas.getContext("2d");
  if (!ctx) throw new Error("[flow-viz/export] 2D canvas context unavailable");
  ctx.fillStyle = background;
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
  return await new Promise<Blob>((resolve, reject) => {
    canvas.toBlob((blob) => {
      if (blob) resolve(blob);
      else reject(new Error("[flow-viz/export] canvas.toBlob returned null"));
    }, "image/png");
  });
}

/** Page dimensions in millimeters (jsPDF "mm" unit). */
const PAGE_DIMS: Record<NonNullable<PdfExportOptions["format"]>, { w: number; h: number }> = {
  a4: { w: 210, h: 297 },
  letter: { w: 215.9, h: 279.4 },
};

/**
 * Render the canvas as a PDF. Uses `jspdf` (browser-native, ~150kb).
 * The PDF is two pages: page 1 is the rasterized flow, page 2 is a
 * tabular inventory of the nodes (when `nodes` is provided).
 */
export async function toPdf(
  canvasEl: HTMLElement,
  opts: PdfExportOptions = {},
): Promise<Blob> {
  const format = opts.format ?? "a4";
  const dims = PAGE_DIMS[format];
  const title = opts.title ?? "Dataiku Flow";
  const theme = opts.theme ?? "light";

  const png = await toPng(canvasEl, {
    background: opts.background,
    theme,
    pixelRatio: opts.pixelRatio ?? 2,
    width: opts.width,
    height: opts.height,
  });
  const dataUrl = await blobToDataUrl(png);

  // Lazy-import jsPDF so it's tree-shakable for callers that only use SVG/PNG.
  const { jsPDF } = await import("jspdf");
  const doc = new jsPDF({ unit: "mm", format, orientation: "landscape" });

  const pageW = dims.h; // landscape: swap w/h
  const pageH = dims.w;
  const margin = 12;
  const innerW = pageW - 2 * margin;
  const innerH = pageH - 2 * margin - 16;

  doc.setFontSize(14);
  doc.text(title, margin, margin + 6);

  // Fit the PNG proportionally to the page's inner box.
  const img = await loadImage(dataUrl);
  const ratio = Math.min(innerW / img.width, innerH / img.height);
  const drawW = img.width * ratio;
  const drawH = img.height * ratio;
  const x = margin + (innerW - drawW) / 2;
  const y = margin + 12 + (innerH - drawH) / 2;
  doc.addImage(dataUrl, "PNG", x, y, drawW, drawH);

  if (opts.nodes !== null && opts.nodes && opts.nodes.length > 0) {
    doc.addPage();
    doc.setFontSize(14);
    doc.text(`${title} — Nodes (${opts.nodes.length})`, margin, margin + 6);
    doc.setFontSize(10);
    let yCursor = margin + 14;
    const rowHeight = 6;
    doc.text("ID", margin, yCursor);
    doc.text("Type", margin + 50, yCursor);
    doc.text("Name", margin + 100, yCursor);
    yCursor += rowHeight;
    doc.line(margin, yCursor - 4, pageW - margin, yCursor - 4);
    for (const row of opts.nodes) {
      if (yCursor > pageH - margin) {
        doc.addPage();
        yCursor = margin + 6;
      }
      doc.text(row.id.slice(0, 30), margin, yCursor);
      doc.text(row.type.slice(0, 30), margin + 50, yCursor);
      doc.text(row.name.slice(0, 60), margin + 100, yCursor);
      yCursor += rowHeight;
    }
  }

  const blobOut = doc.output("blob") as Blob;
  return blobOut;
}

function blobToDataUrl(blob: Blob): Promise<string> {
  return new Promise((resolve, reject) => {
    const r = new FileReader();
    r.onload = () => resolve(r.result as string);
    r.onerror = (e) => reject(e);
    r.readAsDataURL(blob);
  });
}

function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = (e) => reject(e);
    img.src = src;
  });
}

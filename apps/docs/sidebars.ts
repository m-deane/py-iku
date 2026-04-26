import type { SidebarsConfig } from "@docusaurus/plugin-content-docs";

const sidebars: SidebarsConfig = {
  gettingStartedSidebar: [
    {
      type: "category",
      label: "Getting Started",
      collapsed: false,
      items: [
        "getting-started/introduction",
        "getting-started/quickstart",
        "getting-started/architecture",
      ],
    },
  ],

  userGuideSidebar: [
    {
      type: "category",
      label: "User Guide",
      collapsed: false,
      items: [
        "user-guide/convert-page",
        "user-guide/catalog-browser",
        "user-guide/diff-view",
        "user-guide/inspector",
        "user-guide/validation-panel",
        "user-guide/export",
        "user-guide/snippets",
        "user-guide/share-links",
        "user-guide/audit-log",
      ],
    },
  ],

  apiReferenceSidebar: [
    {
      type: "category",
      label: "API Reference",
      collapsed: false,
      items: [
        "api-reference/overview",
        "api-reference/convert",
        "api-reference/catalog",
        "api-reference/diff",
        "api-reference/score",
        "api-reference/export",
        "api-reference/flows",
        "api-reference/share",
        "api-reference/audit",
        "api-reference/health",
      ],
    },
  ],

  flowVizSidebar: [
    {
      type: "category",
      label: "Visualization (flow-viz)",
      collapsed: false,
      items: [
        "flow-viz/overview",
        "flow-viz/components",
        "flow-viz/theme-tokens",
        "flow-viz/layout",
        "flow-viz/node-categories",
        "flow-viz/zone-overlays",
        "flow-viz/focus-mode",
        "flow-viz/execution-sim",
        "flow-viz/export",
      ],
    },
    {
      type: "category",
      label: "Types (packages/types)",
      collapsed: false,
      items: [
        "types/overview",
        "types/codegen",
        "types/runtime-validation",
      ],
    },
  ],

  operationsSidebar: [
    {
      type: "category",
      label: "Operations",
      collapsed: false,
      items: [
        "operations/deployment",
        "operations/ci-matrix",
        "operations/env-vars",
      ],
    },
    {
      type: "category",
      label: "Contributing",
      collapsed: false,
      items: [
        "contributing/overview",
        "contributing/new-recipe-type",
        "contributing/commit-conventions",
      ],
    },
    "roadmap",
  ],
};

export default sidebars;

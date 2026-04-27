import { themes as prismThemes } from "prism-react-renderer";
import type { Config } from "@docusaurus/types";
import type * as Preset from "@docusaurus/preset-classic";

// Brand primary colors from docs/design/tokens.json
// Light: dataset input border #4A90D9, dark: recipe join #2196F3
const PRIMARY_COLOR = "#2196F3";
const PRIMARY_DARK = "#1565C0";

const config: Config = {
  title: "py-iku Studio Docs",
  tagline:
    "Documentation for py-iku Studio — the visual Dataiku flow builder powered by py2dataiku.",
  favicon: "img/favicon.ico",

  url: "https://m-deane.github.io",
  baseUrl: "/py-iku/studio/",

  organizationName: "m-deane",
  projectName: "py-iku",

  onBrokenLinks: "warn",
  markdown: {
    hooks: {
      onBrokenMarkdownLinks: "warn",
    },
  },

  i18n: {
    defaultLocale: "en",
    locales: ["en"],
  },

  // Serve the built Storybook static site under /storybook/
  staticDirectories: ["static", "public"],

  plugins: [
    [
      "@docusaurus/plugin-content-docs",
      {
        id: "default",
        path: "docs",
        routeBasePath: "/",
        sidebarPath: "./sidebars.ts",
        editUrl:
          "https://github.com/m-deane/py-iku/edit/main/apps/docs/",
      },
    ],
  ],

  presets: [
    [
      "classic",
      {
        docs: false, // handled by plugin above
        blog: false,
        theme: {
          customCss: "./src/css/custom.css",
        },
        sitemap: {
          changefreq: "weekly",
          priority: 0.5,
        },
      } satisfies Preset.Options,
    ],
  ],

  themeConfig: {
    image: "img/social-card.png",
    colorMode: {
      defaultMode: "light",
      disableSwitch: false,
      respectPrefersColorScheme: true,
    },
    navbar: {
      title: "py-iku Studio",
      logo: {
        alt: "py-iku Studio Logo",
        src: "img/logo.svg",
      },
      items: [
        {
          type: "docSidebar",
          sidebarId: "gettingStartedSidebar",
          position: "left",
          label: "Getting Started",
        },
        {
          type: "docSidebar",
          sidebarId: "userGuideSidebar",
          position: "left",
          label: "User Guide",
        },
        {
          type: "docSidebar",
          sidebarId: "apiReferenceSidebar",
          position: "left",
          label: "API Reference",
        },
        {
          type: "docSidebar",
          sidebarId: "flowVizSidebar",
          position: "left",
          label: "flow-viz",
        },
        {
          type: "docSidebar",
          sidebarId: "operationsSidebar",
          position: "left",
          label: "Operations",
        },
        {
          href: "https://m-deane.github.io/py-iku/",
          label: "Library Docs",
          position: "right",
        },
        {
          href: "https://github.com/m-deane/py-iku",
          label: "GitHub",
          position: "right",
        },
      ],
    },
    footer: {
      style: "dark",
      links: [
        {
          title: "Docs",
          items: [
            { label: "Getting Started", to: "/getting-started/introduction" },
            { label: "API Reference", to: "/api-reference/overview" },
            { label: "Library Docs (py2dataiku)", href: "https://m-deane.github.io/py-iku/" },
          ],
        },
        {
          title: "More",
          items: [
            { label: "GitHub", href: "https://github.com/m-deane/py-iku" },
            { label: "Studio Plan", href: "https://github.com/m-deane/py-iku/blob/main/.claude_plans/py-iku-studio.md" },
            { label: "Roadmap", to: "/roadmap" },
          ],
        },
      ],
      copyright: `Copyright © ${new Date().getFullYear()} py-iku contributors. Built with Docusaurus.`,
    },
    prism: {
      theme: prismThemes.github,
      darkTheme: prismThemes.dracula,
      additionalLanguages: ["python", "bash", "json", "typescript", "yaml"],
    },
    // Future: Algolia search configuration
    // algolia: { appId: '', apiKey: '', indexName: '' },
  } satisfies Preset.ThemeConfig,
};

export default config;

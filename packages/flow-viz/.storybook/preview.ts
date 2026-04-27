import type { Preview, Decorator } from "@storybook/react";
import { createElement, useEffect } from "react";
import "../src/theme/tokens.css";
import "reactflow/dist/style.css";

const withTheme: Decorator = (Story, context) => {
  const theme = context.globals.theme === "dark" ? "dark" : "light";
  useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    return () => {
      document.documentElement.removeAttribute("data-theme");
    };
  }, [theme]);
  return createElement(
    "div",
    {
      "data-theme": theme,
      style: {
        background: theme === "dark" ? "#1E1E1E" : "#FAFAFA",
        color: theme === "dark" ? "#EEE" : "#212121",
        padding: 16,
        minHeight: "100vh",
      },
    },
    createElement(Story, null),
  );
};

const preview: Preview = {
  decorators: [withTheme],
  globalTypes: {
    theme: {
      name: "Theme",
      description: "Light/dark theme toggle",
      defaultValue: "light",
      toolbar: {
        icon: "circlehollow",
        items: [
          { value: "light", title: "Light" },
          { value: "dark", title: "Dark" },
        ],
        showName: true,
      },
    },
  },
  parameters: {
    controls: {
      matchers: { color: /(background|color)$/i },
    },
    layout: "centered",
  },
};

export default preview;

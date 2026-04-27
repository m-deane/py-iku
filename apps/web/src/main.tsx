import React from "react";
import ReactDOM from "react-dom/client";
import { Providers } from "./app/providers";
import { AppRouter } from "./app/router";
import "./features/editor/monacoWorkers";
import "./styles/tokens.css";
import "./styles/ui-tokens.css";
import "./styles/global.css";

const rootElement = document.getElementById("root");
if (!rootElement) {
  throw new Error("Root element #root not found in index.html");
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <Providers>
      <AppRouter />
    </Providers>
  </React.StrictMode>,
);

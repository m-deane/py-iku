import React from "react";
import ReactDOM from "react-dom/client";
import { Providers } from "./app/providers";
import { AppRouter } from "./app/router";
// Monaco worker glue is now imported lazily from MonacoEditorInner.tsx so it
// only ships when the user actually focuses a code editor — see
// features/editor/MonacoEditor.tsx for the lazy boundary.
import "./styles/tokens.css";
import "./styles/ui-tokens.css";
import "./styles/global.css";
import "./styles/responsive.css";

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

import React from "react";
import { createRoot } from "react-dom/client";
import App from "./App.jsx";
import "./index.css";

// React Grab: dev only. Loads the overlay so you can grab any component and
// point the agent at it. Never bundled into the production build.
if (import.meta.env.DEV) {
  import("react-grab").catch(() => {});
}

createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);

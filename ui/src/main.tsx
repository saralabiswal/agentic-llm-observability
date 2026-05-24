/**
 * React frontend entry point, styling, or type support for the observability app.
 *
 * Author: Sarala Biswal
 */
import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App";
import "./style.css";

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

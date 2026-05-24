/**
 * Frontend build, test, or HTML shell configuration for the React app.
 *
 * Author: Sarala Biswal
 */
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";
export default defineConfig({
    plugins: [react()],
    server: {
        port: 5173,
    },
});

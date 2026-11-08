import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

// In development, Vite serves the app and forwards API calls to uvicorn on :8000.
const api = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: { proxy: { "/v1": api, "/health": api, "/ready": api } },
  test: { environment: "jsdom" },
});

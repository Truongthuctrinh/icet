import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    // Mọi request /api/... được chuyển sang FastAPI -> không cần lo CORS khi dev
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
    },
  },
});

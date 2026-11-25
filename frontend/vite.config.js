import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";

// Header bảo mật cho chính trang web (backend đã tự gắn cho API)
const securityHeaders = {
  "X-Frame-Options": "DENY", // không cho trang khác nhúng ICeT bằng iframe
  "Content-Security-Policy": "frame-ancestors 'none'",
  "X-Content-Type-Options": "nosniff",
  "Referrer-Policy": "same-origin",
};

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 5173,
    headers: securityHeaders,
    // Mọi request /api/... được chuyển sang FastAPI -> không cần lo CORS khi dev.
    // xfwd: gửi kèm X-Forwarded-For để backend biết IP thật của người dùng.
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true, xfwd: true },
      "/media": { target: "http://localhost:8000", changeOrigin: true }, // ảnh bìa, ảnh đại diện
    },
  },
  preview: { headers: securityHeaders },
});

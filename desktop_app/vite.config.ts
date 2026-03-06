import tailwindcss from '@tailwindcss/vite';
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [react(), tailwindcss()],

  server: {
    port: 1420,
    strictPort: true,
    host: '0.0.0.0',
    watch: {
      ignored: ["**/src-tauri/**"],
    },
    proxy: {
      '/api/v1': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        ws: true,  // 启用 WebSocket 代理
        rewrite: (path) => path,
      },
    },
  },
}));

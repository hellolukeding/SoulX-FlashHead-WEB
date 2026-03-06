import tailwindcss from '@tailwindcss/vite';
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// @ts-expect-error process is a nodejs global
const host = process.env.TAURI_DEV_HOST;

// https://vite.dev/config/
export default defineConfig(async () => ({
  plugins: [react(), tailwindcss()],

  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent Vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    // 当 TAURI_DEV_HOST 未设置时，将 host 设为 true 以绑定到 0.0.0.0（允许通过 IP 访问）
    host: host || true,
    hmr: host
      ? {
        protocol: "ws",
        host,
        port: 1421,
      }
      : undefined,
    watch: {
      // 3. tell Vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"],
    },
    proxy: {
      '/offer': 'http://localhost:8010',
      '/human': 'http://localhost:8010',
      '/record': 'http://localhost:8010',
      '/is_speaking': 'http://localhost:8010',
    },
  },
}));

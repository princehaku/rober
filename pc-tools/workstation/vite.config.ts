import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [vue()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      // 本地开发时 API 仍由 Node 进程提供，避免 UI 假造机器人状态。
      "/api": "http://127.0.0.1:8787",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    exclude: ["node_modules/**", "dist/**", "dist-server/**", "coverage/**"],
  },
});

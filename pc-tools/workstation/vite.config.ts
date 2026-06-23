import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

const host = process.env.HOST ?? "127.0.0.1";
const parsedPort = Number(process.env.PORT ?? 5173);
const port = Number.isFinite(parsedPort) ? parsedPort : 5173;

export default defineConfig({
  plugins: [vue()],
  server: {
    host,
    port,
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

import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";

const DEFAULT_PUBLIC_HOST = "0.0.0.0";
const DEFAULT_PUBLIC_PORT = 7001;
const host = process.env.HOST ?? DEFAULT_PUBLIC_HOST;
const parsedPort = Number(process.env.PORT ?? DEFAULT_PUBLIC_PORT);
const port = Number.isFinite(parsedPort) ? parsedPort : DEFAULT_PUBLIC_PORT;

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

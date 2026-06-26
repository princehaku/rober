import vue from "@vitejs/plugin-vue";
import { defineConfig } from "vite";
import { WORKSTATION_DEV_API_PROXY_TARGET, WORKSTATION_DEV_PORT, WORKSTATION_PUBLIC_HOST } from "./src/shared/workstationDefaults";

const host = process.env.HOST ?? WORKSTATION_PUBLIC_HOST;
const parsedPort = Number(process.env.PORT ?? WORKSTATION_DEV_PORT);
const port = Number.isFinite(parsedPort) ? parsedPort : WORKSTATION_DEV_PORT;
const apiProxyTarget = process.env.API_PROXY_TARGET ?? WORKSTATION_DEV_API_PROXY_TARGET;

export default defineConfig({
  plugins: [vue()],
  server: {
    host,
    port,
    proxy: {
      // 本地开发时 API 仍由 7001 的 Node 工作站提供，避免前端直连上位机或撞 Clash 端口。
      "/api": apiProxyTarget,
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    exclude: ["node_modules/**", "dist/**", "dist-server/**", "coverage/**"],
  },
});

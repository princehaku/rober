import vue from "@vitejs/plugin-vue";
import type { IncomingMessage, ServerResponse } from "node:http";
import { defineConfig, type Plugin } from "vite";
import { createWorkstationApp } from "./src/server/index";

function workstationApiDevPlugin(): Plugin {
  const apiApp = createWorkstationApp();

  return {
    name: "rober-workstation-api-dev",
    configureServer(server) {
      server.middlewares.use((req: IncomingMessage, res: ServerResponse, next) => {
        // Vite dev 必须和 Express 共用同一套 API handler，避免 5173 单独启动时把接口代理到空端口。
        if (!req.url?.startsWith("/api/")) {
          next();
          return;
        }

        // Express app 只处理 /api/*；非 API 继续交给 Vite，确保 UI 热更新和 API fail-closed 互不绕开。
        apiApp(req, res, next);
      });
    },
  };
}

export default defineConfig({
  plugins: [workstationApiDevPlugin(), vue()],
  server: {
    host: "127.0.0.1",
    port: 5173,
  },
  test: {
    environment: "jsdom",
    globals: true,
    exclude: ["node_modules/**", "dist/**", "dist-server/**", "coverage/**"],
  },
});

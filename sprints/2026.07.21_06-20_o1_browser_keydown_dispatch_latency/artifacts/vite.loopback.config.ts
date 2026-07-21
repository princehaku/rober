import vue from "/Users/m1/apps/rober/pc-tools/workstation/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { defineConfig } from "/Users/m1/apps/rober/pc-tools/workstation/node_modules/vite/dist/node/index.js";

const workstationRoot = "/Users/m1/apps/rober/pc-tools/workstation";
const loopbackDefaults = "/Users/m1/apps/rober/sprints/2026.07.21_06-20_o1_browser_keydown_dispatch_latency/artifacts/robotDefaults.loopback.ts";

export default defineConfig({
  // 本轮通过只读 resolve hook 覆盖默认地址，避免页面挂载阶段碰到现场 IP。
  plugins: [
    {
      name: "latency-loopback-defaults",
      enforce: "pre",
      resolveId(source) {
        // 产品代码仍保持原样；仅本轮 Vite 进程把共享默认地址模块换成 loopback fixture。
        return source === "../shared/robotDefaults" || source.endsWith("/shared/robotDefaults")
          ? loopbackDefaults
          : null;
      },
    },
    vue(),
  ],
  root: workstationRoot,
  server: {
    // 三个 fixture 端口都固定到 127.0.0.1，不能被局域网其它主机访问。
    host: "127.0.0.1",
    port: 15173,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:17001",
    },
  },
});

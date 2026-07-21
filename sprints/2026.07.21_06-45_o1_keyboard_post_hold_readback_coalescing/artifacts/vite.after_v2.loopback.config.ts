import vue from "/Users/m1/apps/rober/pc-tools/workstation/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { defineConfig } from "/Users/m1/apps/rober/pc-tools/workstation/node_modules/vite/dist/node/index.js";

const workstationRoot = "/Users/m1/apps/rober/pc-tools/workstation";
const loopbackDefaults = "/Users/m1/apps/rober/sprints/2026.07.21_06-45_o1_keyboard_post_hold_readback_coalescing/artifacts/robotDefaults.after_v2.loopback.ts";

export default defineConfig({
  // resolve hook 只影响隔离 Vite 进程，不修改产品默认地址或正式构建产物。
  plugins: [
    {
      name: "post-hold-after-v2-loopback-defaults",
      enforce: "pre",
      resolveId(source) {
        // 独立 18082 mock 确保浏览器测试不能接触现场 Upper。
        return source === "../shared/robotDefaults" || source.endsWith("/shared/robotDefaults")
          ? loopbackDefaults
          : null;
      },
    },
    vue(),
  ],
  root: workstationRoot,
  server: {
    // 新端口避开旧标签页自动重连，采样前可保持 raw/guard 真正为零行。
    host: "127.0.0.1",
    port: 15174,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:17002",
    },
  },
});

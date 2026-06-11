import vue from "../../../pc-tools/workstation/node_modules/@vitejs/plugin-vue/dist/index.mjs";
import { defineConfig } from "../../../pc-tools/workstation/node_modules/vite/dist/node/index.js";
import { resolve } from "node:path";

const workstationRoot = resolve(__dirname, "../../../pc-tools/workstation");

export default defineConfig({
  plugins: [vue()],
  resolve: {
    alias: {
      vue: resolve(workstationRoot, "node_modules/vue/dist/vue.runtime.esm-bundler.js"),
      "@vue/test-utils": resolve(workstationRoot, "node_modules/@vue/test-utils/dist/vue-test-utils.esm-bundler.mjs"),
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    include: ["sprints/2026.06.11_13-50_pc_map_lifecycle_real_proxy_smoke/artifacts/**/*.test.ts"],
    exclude: ["node_modules/**", "pc-tools/workstation/dist/**", "pc-tools/workstation/dist-server/**"],
  },
});

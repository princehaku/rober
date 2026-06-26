# PC free-roam 地图记录 gate 所见即所得

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `free_roam_autonomy_gates[].mapping_active` 优先使用当前 `/api/free-roam/autonomy/latest` runtime gate。
  - 当 runtime 已明确提供 `mapping_active` 时，不再用旧 `map/proof` 的 `managed_runtime_started=true` 覆盖成 ready。
  - 仅在旧 runtime 缺少 `mapping_active` gate 时，保留 map proof 兼容补行。
- `pc-tools/workstation/test/catalog.test.ts`
  - 修改回归测试：runtime 明确 `mapping_active=blocked` 时，summary 必须照实显示 blocked。
  - 新增旧 runtime 无 mapping gate 时的兼容补行测试。
- `docs/product/pc_tools_workstation.md`
  - 同步记录自动扫图准备里地图记录 gate 的当前事实口径。

## 验证结果

- 已通过：
  - `npm test -- --run test/catalog.test.ts --testNamePattern "free-roam mapping gate|free-roam autonomy runtime"`
- `npm test -- --run test/catalog.test.ts`
  - 通过：`Tests 115 passed (115)`。
- `npm run lint`
  - 通过：`eslint .` 无报错。
- `npm run build`
  - 通过：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json`。
  - Vite 仍提示产物 chunk 大于 500 kB，这是既有体积提示。
- PC Node 已重启到 `0.0.0.0:7001`，`node` 监听 `*:7001`。
- live 只读验证：
  - `free_roam_autonomy_label=自由移动（勾确认后可启动）`
  - `free_roam_autonomy_start_ready=true`
  - `mapping_active.state=not_proven`
  - `mapping_active.evidence=地图记录未启动`
  - `free_roam_autonomy_runtime.state=stopping`
  - `cmd_vel_publish_enabled=false`

## 剩余风险

- 本轮只修 PC summary/readiness 的状态一致性，不启动真实 free-roam 或 Nav2。
- live 已证明 PC summary 不再把旧 map proof 覆盖成 `mapping_active=ready`。

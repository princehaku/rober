# PC 送达成功地图 Caption 同步

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当当前 Nav2 execution 已完整到达且本轮 `deliverySuccessReady` 对齐 route/map ref 时，普通首屏地图 caption 从 `已到达，准备送达材料` 升级为 `已送达，delivery gate 已确认`。
  - 未送达但 Nav2 已到达的场景仍保持 `准备送达材料`，避免提前宣称 delivery success。
- `pc-tools/workstation/test/App.test.ts`
  - 更新 delivery success 对齐当前 Nav2 route 的地图用例，断言 marker 与 caption 都显示 `已送达`。
- `docs/product/pc_tools_workstation.md`
  - 同步记录 delivery success 后地图 caption 的 WYSIWYG 口径和控制边界。

## 验证结果

- 已通过：
  - `npm test -- -t "marks the map goal as delivered only when delivery success matches the current Nav2 route"`
  - 结果：`Test Files 1 passed | 1 skipped (2)`，`Tests 1 passed | 184 skipped (185)`。
  - `npm run lint`
  - 结果：ESLint 通过。
  - `npm run build`
  - 结果：`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 通过。
  - `npm test`
  - 结果：`Test Files 2 passed (2)`，`Tests 185 passed (185)`。
  - `git diff --check`
  - 结果：通过，无 whitespace error。
  - `lsof -nP -iTCP:7001 -sTCP:LISTEN`
  - 结果：本机已有 `node` 监听 `*:7001`，未改 Clash 或系统代理配置。

## 剩余风险

- 本轮是 PC 前端 mock 验证，没有连接真实上位机读取真实 delivery latest 或 Nav2 execution latest。
- 该改动只同步地图 caption，不改变 delivery gate、Nav2 execute、manual、keyboard、stop 或 `/cmd_vel` 的后端行为。
- 未触发真实 manual、keyboard pulse、Nav2 execute、delivery complete、stop 或 `/cmd_vel`；未修改 Clash 或系统代理配置。

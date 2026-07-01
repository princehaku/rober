# tech-done

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：雷达贴图恢复链从两步/旧顺序统一为 `radar scan proof -> radar status -> map preview -> summary`，并同步 field acceptance 的 `refresh_radar_map_overlay` sequence、labels 和只读说明。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：PC 首屏“刷新雷达贴图”改为执行 summary 声明的 no-motion sequence，DOM 补充 `data-refreshes-summary=true`。
- `pc-tools/workstation/src/shared/contracts.ts` 与相关测试：把 live WYSIWYG 雷达地图刷新 sequence 类型和断言同步为四步。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`：同步记录当前雷达贴图只读复验链路；PC 地图仍优先使用 `/map` 大屏，ROS2 配套为 RViz2/Foxglove 旁路观察。

## 验证结果

- `git diff --check`：通过。
- `npm test -- robotControlSummary.test.ts`：10 passed。
- `npm test -- App.test.ts`：236 passed。
- `npm test -- robotControlSummary.test.ts App.test.ts catalog.test.ts`：427 passed。
- `npm run lint`：通过。
- `npm run build`：通过；仅保留 Vite chunk size warning。

## 剩余风险

- 本轮未执行实车运动、Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`；雷达贴图链路仅做 PC/Node 合同和本地测试验证。
- 真实雷达点是否成功贴到当前地图仍需现场点击只读刷新后，以 `/api/robot-control/summary` 和 PC 地图画面确认。

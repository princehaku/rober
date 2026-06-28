# PC Radar Stop No Live Sweep WYSIWYG Micro Sprint

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：雷达停止请求 pending 时，地图仍显示“雷达停止请求中”marker，但不再把该状态当作 live radar，不再显示扫描范围占位或距离读数，避免停止中看起来还在实时扫描。
- `pc-tools/workstation/test/App.test.ts`：补充 radar stop pending 回归断言，锁定停止中不渲染 `plain-map-radar-sweep`，并继续断言不会触发 manual、free-roam、Nav2 或 `/cmd_vel`。
- `docs/product/pc_free_roam_mapping_design.md`、`pc-tools/README.md`：同步记录雷达停止 pending 的地图所见即所得边界。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- --run test/App.test.ts -t "radar stop pending"`，结果 `1 passed | 204 skipped (205)`。
- 通过：`cd pc-tools/workstation && npm test`，结果 `2 passed (2)`，`354 passed (354)`。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`；Vite 仍提示既有 chunk size warning。
- 通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC 地图展示，不触发真实雷达 stop、不发送底盘 manual、free-roam、Nav2、delivery、stop 或 `/cmd_vel`。
- 真实雷达停止是否完成仍以上位机 stop 回包和下一次只读雷达状态为准。

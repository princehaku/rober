# 2026-06-26 05:50 PC 行程执行等待地图刷新

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 地图画面 `mapPreviewPending` 时，即使旧画面仍有当前路线，普通首屏 `执行图上路线` 也会临时显示 `等待地图刷新` 并禁用。
  - 同步行程状态、路线 WYSIWYG 提示、本轮进度下一步和验收卡点，明确“刷新完成后再执行”。
  - 该 gate 只等待只读 `/api/robot-control/map/preview` 返回，不新增 endpoint，不执行 Nav2，不发送 manual、keyboard、delivery、stop 或 `/cmd_vel`。
- `pc-tools/workstation/test/App.test.ts`
  - 新增延迟 map preview 的 route execution 测试：路线仍可见但执行按钮禁用，并断言点击时不会调用 Nav2 execute、manual 或 `/cmd_vel`；preview 返回后按钮恢复。
- `docs/product/pc_tools_workstation.md`
  - 同步地图刷新中不能按旧图执行路线的产品口径。

## 验证结果

- 通过：`cd pc-tools/workstation && npm test -- -t "map preview is refreshing|visible-route"`，2 passed / 188 skipped。
- 通过：`cd pc-tools/workstation && npm run lint`。
- 通过：`cd pc-tools/workstation && npm run build`。
- 通过：`cd pc-tools/workstation && npm test`，2 files / 190 passed。
- 通过：`git diff --check`。
- 确认：`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 PC node 监听 `*:7001`，未改 Clash/系统代理。

## 剩余风险

- 本轮只覆盖 PC 前端 route/map preview pending gate 和 mock 回归；没有在真实小车上执行 Nav2 路线或做 HIL。

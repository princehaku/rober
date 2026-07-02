# Camera WYSIWYG Recovery Boundaries

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层 `camera_wysiwyg_recovery_*` 补齐只读边界，新增 `starts_nav2/manual/keyboard/free_roam=false`、`submits_delivery=false`、`stops_motion=false`。
- `pc-tools/workstation/src/shared/contracts.ts`：同步 `RobotControlSummaryResponse` 类型，固定相机 WYSIWYG recovery 读回不触发控制链。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-live-closure-summary` DOM 暴露相机 recovery 的完整只读 flags。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁住 API 和 DOM 的相机 WYSIWYG recovery 边界。
- `docs/product/pc_tools_workstation.md`：同步产品合同，明确首帧复测/共享预览状态读回不启动 Nav2、manual、keyboard、free-roam、建图 runtime、delivery、stop 或 `/cmd_vel`。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍保留既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮只补 PC/API/DOM 验收证据，不复测真实相机首帧，不发送 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 真实画面 WYSIWYG 仍需现场 USB/供电/known-good UVC 处理后复测。

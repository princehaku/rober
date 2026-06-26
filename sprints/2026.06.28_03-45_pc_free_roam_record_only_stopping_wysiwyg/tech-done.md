# PC Free Roam Record-only Stopping WYSIWYG

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当上车端 free-roam latest 为 `state=stopping`、`artifact_only=true`、`cmd_vel_publish_enabled=false` 时，普通首屏 runtime 文案从当前动作口径改为“上次记录停在停止请求”。
  - 地图 runtime marker 从“自动扫图：停止中”改为“自由移动记录：上次停止请求”，并在 aria 中明确“当前未发布运动”。
- `pc-tools/workstation/test/App.test.ts`
  - 补充 start-ready artifact-only stopping 和 camera/radar degraded free movement 两条 WYSIWYG 断言。
- `docs/product/pc_tools_workstation.md`
  - 记录 record-only stopping 的普通地图和状态解释口径。

## 验证结果

- 已通过：`cd pc-tools/workstation && npm test -- --testNamePattern "start-ready free-roam autonomy|free movement from mapping acceptance"`，`Tests 2 passed | 258 skipped (260)`。
- 已通过：`cd pc-tools/workstation && npm test`，`Tests 260 passed (260)`。
- 已通过：`cd pc-tools/workstation && npm run lint`。
- 已通过：`cd pc-tools/workstation && npm run build`。
  - 保留既有 Vite chunk size warning：`Some chunks are larger than 500 kB after minification`。
- 已通过：`git diff --check`。

## 剩余风险

- 本轮只修 PC WYSIWYG，不改变上车端 free-roam runtime artifact，也不执行真实自由移动。
- 当前 live latest 没有时间戳；PC 只能从 `artifact_only=true` 和 `cmd_vel_publish_enabled=false` 判断这不是当前运动发布状态。

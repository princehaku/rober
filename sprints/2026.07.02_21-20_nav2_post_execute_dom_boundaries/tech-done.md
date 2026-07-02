# Nav2 Post Execute DOM Boundaries

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 Nav2 行程执行区、执行按钮和闭环读回区同步暴露 `nav2_post_execute_readback_starts_manual=false`、`starts_keyboard=false`、`starts_free_roam=false`、`starts_map_runtime=false`、`stops_motion=false`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`：锁住 summary 顶层 Nav2 post-execute 完整只读边界。
- `pc-tools/workstation/test/App.test.ts`：补齐 fixture 和 `plain-trip-closure-readback` DOM 断言，确保现场 DOM 不只暴露部分边界。
- `docs/product/pc_tools_workstation.md`：同步产品合同，说明 `/api/robot-control/nav2/goal/execute` 成功后的复验链只读，不启动 manual、keyboard、free-roam、建图 runtime 或 stop。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍保留既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮只补 PC/API/DOM 验收证据，不执行真实 Nav2 goal，不发送 manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 真实完整路线、wheel L/R 非零和送达确认仍需现场勾安全确认后实车复验。

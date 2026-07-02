# Free Move Post Start Free Roam Boundary

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：summary 顶层和当前自由移动动作新增 `*_post_start_readback_starts_free_roam=false`，补齐自由移动启动后复验链的只读边界。
- `pc-tools/workstation/src/shared/contracts.ts`：同步 `RobotControlSummaryResponse` 类型，避免前端和现场脚本猜字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：`plain-free-move-acceptance-proof` DOM 增加 `data-post-start-readback-starts-free-roam=false`，并补齐 `PlainFreeMoveAcceptanceProof` 的 post-start 字段类型。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`：锁住 API、fixture 和 DOM 的自由移动 post-start `starts_free_roam=false`。
- `docs/product/pc_tools_workstation.md`：同步产品合同，强调自由移动启动成功后的读回链只读，不再次启动 free-roam。

## 验证结果

- `cd pc-tools/workstation && npm test -- --run robotControlSummary.test.ts App.test.ts`：通过，`2 passed`，`247 passed`。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍保留既有 large chunk warning。
- `cd pc-tools/workstation && npm run lint`：通过。
- `git diff --check`：通过，无空白错误。

## 剩余风险

- 本轮只补 PC/API/DOM 验收证据，不执行真实自由移动 start，不发送 Nav2/manual/keyboard/free-roam/建图/delivery/stop 或 `/cmd_vel`。
- 真实自由移动运行态、wheel L/R 和建图 readiness 仍需现场勾安全确认后实车复验。

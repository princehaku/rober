# PC 四项目标审计合同

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：新增 `RobotControlLiveObjectiveAuditItem` 与四项目标审计字段，挂到 `RobotControlLiveClosureSummary`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`：从 live readback 和 goal checklist 派生 `motion`、`wysiwyg`、`precheck`、`mapping` 四项目标审计，严格区分 ready 和 completed；可启动不等于完成。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通首屏 `plain-objective-overview` 优先使用 `live_closure_summary.objective_audit_items`，并暴露 `data-objective-audit-*` 机器可读字段。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：覆盖 API 本体和 DOM 目标审计字段，确保可见文案不泄漏 `operator report`、`camera_first_frame`、`raw` 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步四项目标审计合同。

## 验证结果

- 已通过：`npm test -- --run test/robotControlSummary.test.ts`，1 file / 6 tests。
- 已通过：`npm test -- --run test/App.test.ts -t "renders Robot Control V1 by default with Robot API proxy and locked command boundary"`，1 matched test。
- 已通过：`npm run build`，`tsc` + Vite build + server `tsc` 通过；Vite 仍提示单 chunk 超过 500 kB，这是既有体积 warning。
- 已通过：`npm test -- --run`，3 files / 413 tests。
- 已通过：`npm run lint`，0 error；仍有 `RobotControlConsolePanel.vue` 4 个既有 `vue/multiline-html-element-content-newline` warning。
- 已通过：`git diff --check`。
- 已通过：重启 PC Node 到 `0.0.0.0:7001`，实际监听进程 `node` PID `78004`；只读 `GET http://127.0.0.1:7001/api/robot-control/summary` 返回 `live_closure_summary.status=needs_wheel_rerun`、`objective_audit_status=in_progress`、`objective_audit_done_count=1`、`objective_audit_remaining_count=3`、`objective_audit_next_objective_id=motion`、`objective_audit_missing_objective_ids=motion,wysiwyg,mapping`、`objective_audit_sends_motion_when_clicked=false`。
- 已通过：live motion 子项严格口径复核。当前 `motion.summary_plain=图上行程：待轮速复验；键盘：可验证；自由移动：可启动。`、`motion.missing_count=3`、`motion.source_card_id=nav2_route`，没有把 Nav2 goal success、free-roam start-ready 或 keyboard-ready 误报为完成；当前主卡点仍聚焦图上行程轮速复验。

## 剩余风险

- 该 sprint 只把四项目标的当前完成度做成稳定 API/DOM 合同，不替代真实运动验收。
- 当前 live 目标仍需现场安全确认后重跑 Nav2 并证明同窗口 wheel L/R 非零；摄像头首帧仍受真实 UVC/USB 传输错误影响。

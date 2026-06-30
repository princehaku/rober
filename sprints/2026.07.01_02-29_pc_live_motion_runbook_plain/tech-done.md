# PC Live Motion Runbook Plain Micro Sprint

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 增加动作清单普通用户汇总字段：
    - `live_motion_runbook_summary_plain`
    - `live_motion_runbook_ready_plain`
    - `live_motion_runbook_blocked_plain`
    - `live_motion_runbook_primary_action_plain`
    - `live_motion_runbook_minimal_precheck_plain`
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 基于现有 `live_motion_runbook_items` 生成可执行动作、阻塞动作、主推荐动作和最小预检中文短句。
  - 最小预检固定表达：执行运动只需现场安全确认；相机、雷达和 operator report 不作为额外发车前置。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 当前卡点动作清单展示 API 汇总句，并在 `plain-live-motion-runbook` 暴露 `data-summary-plain`、`data-ready-plain`、`data-blocked-plain`、`data-primary-action-plain`、`data-minimal-precheck-plain`。
  - 发车前预检行优先使用 API 下发的中文最小预检口径。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖 summary 合同和 DOM 展示，不允许普通用户继续从结构化 item 手工拼结论。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`
  - 同步记录 PC 当前卡点动作清单口径。

## 验证结果

- 通过：`npm test -- test/robotControlSummary.test.ts --run`，6 tests OK。
- 通过：`npm test -- test/App.test.ts -t "live closure|motion runbook|当前卡点|动作清单" --run`，1 test OK / 228 skipped。
- 通过：`npm test -- --run`，3 files / 413 tests OK。
- 通过：`npm run build`。
- 通过：`npm run lint`，0 errors / 4 warnings（既有 Vue 模板换行 warning，未阻塞）。
- 通过：`git diff --check`。
- 通过：PC Node 重启到 `0.0.0.0:7001`，PID `90384`。
- 通过：live 只读 GET `/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：
  - `live_motion_runbook_primary_action_id=run_nav2_route`
  - `live_motion_runbook_primary_action_plain=完整行程执行`
  - `live_motion_runbook_ready_action_ids=run_nav2_route,hold_keyboard,start_free_move`
  - `live_motion_runbook_blocked_action_ids=start_mapping_when_sensors_ready`
  - `live_motion_runbook_ready_plain=可先执行：完整行程执行、键盘连续手控、自由自助移动。`
  - `live_motion_runbook_minimal_precheck_plain=发车前预检已精简：执行运动只需勾现场安全确认；相机、雷达和 operator report 不作为额外发车前置。`

## 剩余风险

- 本轮只提升只读 API/DOM 和普通用户文案；没有发送 Nav2、manual、keyboard、free-roam、delivery、stop 或 `/cmd_vel`。
- 完整 Nav2 路线闭环仍需要现场勾安全确认后重跑图上路线，并在同窗口读到轮速 L/R 非零。
- 真实画面仍受 UVC/USB 传输错误阻塞；雷达地图点仍需要 fresh scan proof 后刷新地图预览。

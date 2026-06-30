# live closure 旁路缺口 API 合同

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`
  - `RobotControlLiveClosureSummary` 新增 `side_blocker_ids`、`side_blocker_count`、`ready_action_count`、`side_gap_summary_plain`。
- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - `live_closure_summary` API 直接输出当前主卡点之外的 blocker 清单，以及当前 ready action 数和普通文案。
  - `side_gap_summary_plain` 复用 goal checklist summary，不新增控制 gate。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-side-gaps` 优先消费 API 字段；旧 summary 缺字段时继续用本地 checklist 推导。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖 API 字段和页面 DOM 一致性。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录 API/DOM 对齐后的只读验收口径。

## 验证结果

- `npm test -- robotControlSummary.test.ts`：通过，3 passed。
- `npm test -- App.test.ts`：通过，225 passed。
- `npm test -- --run`：通过，3 files / 402 tests passed。
- `npm run lint`：通过，0 errors；保留既有 4 个 Vue multiline warning。
- `npm run build`：通过；保留 Vite chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 node PID `39561` 监听 `TCP *:7001`。
- 只读 `GET /api/health`：通过，`pc_only=true`、`mode=pc_only_readonly_workstation`。
- 只读 live summary：通过，`live_status=needs_wheel_rerun`、`primary=nav2_route_execution`、`side_blocker_ids=camera_wysiwyg,radar_map_points_wysiwyg,mapping_start`、`ready_action_ids=free_move,keyboard_continuous_control,nav2_route_execution`、`side_gap_summary_plain=其它缺口：画面所见即所得、雷达点贴到地图、传感器就绪后建图；可先做：自由自助移动、键盘连续手控、完整行程执行。`
- 只读 bundle 检查：通过，`index-BF2S1GkQ.js` 包含 `side_gap_summary_plain`、`side_blocker_ids`、`plain-live-closure-side-gaps`。

## 剩余风险

- 本轮只改 summary API 和 PC DOM 合同，未发 live motion POST。
- 当前真实闭环仍需要现场安全确认后复验 Nav2 wheel raw L/R 非零；相机首帧和雷达新鲜扫描仍是建图/WYSIWYG 缺口。

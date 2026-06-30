# PC 当前卡点旁路缺口展示

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - `plain-live-closure-summary` 新增 blocker/ready action DOM 字段：`data-blocker-ids`、`data-ready-action-ids`、`data-side-blocker-ids`、`data-side-blocker-count`、`data-ready-action-count`。
  - 新增 `plain-live-closure-side-gaps` 短行，用已有 goal checklist 展示当前主卡点之外仍未完成的缺口，以及现场可先执行的动作。
  - 展示顺序跟随后端 `ready_action_ids`，避免普通首屏和 summary 优先级不一致。
- `pc-tools/workstation/test/App.test.ts`
  - 扩展普通首屏默认测试，覆盖旁路缺口、ready action、WYSIWYG 缺口和 no-motion DOM 合同。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录“当前卡点 + 旁路缺口 + 可先做动作”的普通用户口径。

## 验证结果

- `npm test -- App.test.ts`：通过，225 passed。
- `npm test -- --run`：通过，3 files / 402 tests passed。
- `npm run lint`：通过，0 errors；保留既有 4 个 Vue multiline warning。
- `npm run build`：通过；保留 Vite chunk size warning。
- `git diff --check`：通过。
- PC Node 已重启到 `0.0.0.0:7001`，`lsof` 显示 node PID `28366` 监听 `TCP *:7001`。
- 只读 `GET /api/health`：通过，`pc_only=true`、`mode=pc_only_readonly_workstation`。
- 只读首页 bundle 检查：通过，`index-BpvSIwo4.js` 包含 `plain-live-closure-side-gaps`、`data-side-blocker-ids`、`data-ready-action-ids`。
- 只读 live summary：通过，`live_status=needs_wheel_rerun`、`primary=nav2_route_execution`、`blocker_ids=camera_wysiwyg,radar_map_points_wysiwyg,mapping_start`、`ready_action_ids=free_move,keyboard_continuous_control,nav2_route_execution`、`wysiwyg_missing=camera,radar_map_points`。

## 剩余风险

- 本轮未发送 live motion POST；真实 Nav2 重跑、wheel raw L/R 非零、键盘手控、自由移动和送达仍需要现场安全确认后复验。
- 只读 live 当前仍显示：主卡点为 wheel raw L/R 复验，旁路缺口为 camera 和 radar_map_points WYSIWYG；本轮只让 PC 端更清楚地展示这些事实。

# 2026-07-02 05:35 完整路线验收顶层别名

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`
  - 新增 summary 顶层只读 alias：
    `trip_execution_ready`、`trip_execution_complete`、`trip_execution_missing_evidence`、
    `trip_execution_required_success_markers`、`wheel_feedback_same_window_complete`、
    `same_window_wheel_lr_nonzero_complete`、`delivery_success_current`。
  - 这些字段全部复用 `nav2_route_acceptance_packet`，不新增第二套判断，不新增控制入口。
- `pc-tools/workstation/src/shared/contracts.ts`
  - 补齐上述字段类型。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 在普通首屏 `plain-live-closure-summary` 和 `plain-field-acceptance-packet` DOM 暴露同名验收字段，缺 packet 时输出明确 `false` / `none`。
- `pc-tools/workstation/test/robotControlSummary.test.ts`、`pc-tools/workstation/test/App.test.ts`
  - 增加 API 和 DOM 断言，覆盖完整路线、同窗口 wheel L/R、当前送达确认的短 alias。
- `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`
  - 同步说明字段只读且与 `nav2_route_acceptance_packet` 同源。

## 验证结果

- `git diff --check`：通过。
- `cd pc-tools/workstation && npm test -- --run App.test.ts robotControlSummary.test.ts`：通过，2 个测试文件、246 个测试通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过；Vite 仍提示单个 bundle 超过 500kB，这是既有体积提醒，不影响本轮只读别名。
- 重启 PC API 后，`lsof -nP -iTCP:7001 -sTCP:LISTEN` 显示 `node` 监听 `TCP *:7001`，PID `59665`。
- `curl http://127.0.0.1:7001/` 读到当前 bundle `index--4XQAMx-.js`。
- `curl http://127.0.0.1:7001/assets/index--4XQAMx-.js | rg -o ... | sort | uniq -c`：
  - `data-delivery-success-current`：4 处。
  - `data-same-window-wheel-lr-nonzero-complete`：2 处。
  - `data-trip-execution-complete`：4 处。
  - `data-trip-execution-missing-evidence`：4 处。
  - `data-trip-execution-ready`：4 处。
  - `data-wheel-feedback-same-window-complete`：4 处。
- `curl 'http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http://192.168.1.11:8787' | jq ...` 现场读回：
  - `status=needs_wheel_rerun`
  - `trip_execution_ready=true`
  - `trip_execution_complete=false`
  - `trip_execution_missing_evidence=["same_window_wheel_lr_nonzero","delivery_success"]`
  - `trip_execution_required_success_markers=["map_route_visible","nav2_goal_succeeded","same_window_wheel_lr_nonzero","delivery_success"]`
  - `wheel_feedback_same_window_complete=false`
  - `same_window_wheel_lr_nonzero_complete=false`
  - `delivery_success_current=false`
  - `field_acceptance_primary_missing_id=same_window_wheel_lr_nonzero`
  - `live_wysiwyg_missing_reasons=["camera"]`
  - `radar_overlay_wysiwyg_complete=true`
  - `mapping_start_missing_evidence=["camera_first_frame"]`

## 剩余风险

- 本轮只补完整路线验收读回口径，没有执行 Nav2、键盘、自由移动、送达确认、stop 或 `/cmd_vel`。
- 当前 motion 目标仍需要现场安全确认后的真实运动窗口读回，才能把 `same_window_wheel_lr_nonzero` 和 delivery success 变成完成证据。

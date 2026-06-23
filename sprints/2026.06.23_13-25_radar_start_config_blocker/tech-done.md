# Radar start config blocker

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：从上位机只读 `/api/radar/status` 的 `controls.start.command.configured` 提取 `readback_summary.lidar.radar_start_configured`。
- `pc-tools/workstation/src/shared/contracts.ts`：同步 Robot Control summary 合同字段。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：当 `radar_start_configured=false` 时，普通首屏显示“上位机雷达启动命令未配置”，禁用普通 `启动雷达` 按钮并把行程、送达、键盘 LiDAR delta 的下一步改为“先配置雷达启动命令”。
- `pc-tools/workstation/test/App.test.ts`：新增未配置场景测试，确认不会调用 radar start、Nav2 execute、delivery complete 或 `/cmd_vel`。
- `docs/product/pc_tools_workstation.md`：同步 PC 工作站最新用户路径口径。

## 只读上位机证据

- `ssh root@192.168.1.11 -p 37878` 后使用 Python 标准库只读 GET。
- `/api/base/status`：`/dev/ttyS5 @ 115200` 可读，`T1001=true`，13 帧，`latest_L=0.0`、`latest_R=0.0`、`nonzero_frames=0`、`wheel_feedback_lr_nonzero_proven=false`。
- `/api/radar/status`：`lifecycle_running=false`、`lifecycle_state=stopped`、`continuous_scan_status=lifecycle_not_running`、`latest_scan_proof_state=missing`、blocked 为 `latest_scan_proof_missing` 和 `lidar_lifecycle_not_running`，且 `controls.start.command.configured=false`。
- `/api/nav2/goal/execution/latest`：最近结果 `result_status=succeeded`、`evidence_ref=o11-nav2-goal-execution-1782099547218`、`feedback_sample_count=8`，但顶层仍 `status=not_proven` / `proof_state=not_proven`，`delivery_success=false`。
- `/api/delivery/latest`：`status=blocked_missing_delivery_material`、`delivery_success=false`。
- `/api/operator/report`：材料仍是 `site_state=delivery_material_draft_not_operator_confirmed`，`visible_content_proven=true`、`real_route_map_proven=true`，但 `wheel_feedback_lr_nonzero_proven=false`、`physical_motion_lidar_delta_proven=false`、`delivery_success=false`。

## 验证结果

- `cd pc-tools/workstation && npm test -- -t "radar start"`：通过，3 个 radar start 相关用例通过。
- `cd pc-tools/workstation && npm test`：通过，2 个 test files / 148 个 tests 全部通过。
- `cd pc-tools/workstation && npm run lint`：通过。
- `cd pc-tools/workstation && npm run build`：通过，Vite production build 和 server TypeScript build 完成。

## 剩余风险

- 本轮没有触发真实小车运动，没有 POST 上位机控制接口；只做 SSH GET 状态读取和本地 PC 代码验证。
- 真实收口仍卡在现场/上位机状态：wheel L/R 仍为 `0/0`，LiDAR lifecycle 未运行且 radar start command 未配置，delivery 仍未确认成功。

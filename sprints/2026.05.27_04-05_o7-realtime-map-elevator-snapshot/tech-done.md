# O7 realtime map/elevator snapshot micro sprint

## sprint_type

micro

## 实际改动

- 在 cloud-relay O7 operator console 契约中新增 `realtime_map_snapshot` 与 `elevator_state_snapshot`，固定保持 `source=software_proof`、`snapshot_status=blocked_not_proven`、`safe_to_control=false`、`primary_actions_enabled=false`。
- 在 PC workstation 共享类型、后端 builder 和 O7 Console 面板中展示 map_ref、map frame、pose freshness、route membership、电梯状态链、楼层证据和人工接管原因。
- 更新 O7 Console API/UI 测试，覆盖新增 snapshot 字段和 fail-closed 状态。
- 更新 `docs/interfaces/o7_realtime_operator_console.md` 与 `docs/product/pc_tools_workstation.md`，明确 snapshot 不证明真实 ROS2 `/tf`、真实地图、真实电梯或 <2s 延迟。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过。关键输出：`✓ 29 modules transformed.`、`✓ built in 1.90s`。
- `cd pc-tools/workstation && npm run test`：通过。关键输出：`Test Files  2 passed (2)`、`Tests  16 passed (16)`。
- `cd pc-tools/workstation && npm run lint`：通过，最终无 warning/error 输出。
- `python3 -m py_compile cloud-relay/src/ros2_trashbot_cloud_relay/remote_cloud_relay.py`：通过，无输出。
- `git diff --check -- cloud-relay pc-tools docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md sprints/2026.05.27_04-05_o7-realtime-map-elevator-snapshot`：通过，无输出。

中途 `npm run lint` 曾提示 `O7OperatorConsolePanel.vue` 一处 Vue 模板缩进 warning，已修复并重跑通过。

## 剩余风险

- 当前只完成软件契约和 PC 展示，仍未连接真实 O6 cloud realtime API、ROS2 `/tf`、地图 artifact、真实电梯事件归档或现场证据。
- 本轮不修改 `OKR.md`，不提升 O7 完成度。

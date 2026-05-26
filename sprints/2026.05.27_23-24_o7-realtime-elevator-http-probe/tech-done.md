# O7 Realtime/Elevator HTTP Probe Tech Done

## sprint_type

micro

## 实际改动

- `remote_cloud_relay.py` 新增公开只读 `GET /api/o7/realtime-elevator/snapshot`，返回 `trashbot.o7.realtime_elevator_snapshot.v1` fail-closed contract。
- PC workstation 新增 `GET /api/o7/realtime-elevator-probe?baseUrl=<local-loopback-url>`，只允许 `http://127.0.0.1`、`http://localhost`、`http://[::1]` 回环 URL，拉取远端 snapshot 并扫描危险 true 字段。
- O7 Previews 新增 `Realtime/elevator cloud probe` 区块，默认不自动请求；点击后展示 remote schema、realtime/snapshot status、map ref/frame、pose freshness、route membership false fields、电梯状态、楼层证据、人工接管、dangerous true fields、blocked/not_proven。
- 更新 `docs/interfaces/o7_realtime_operator_console.md`、`docs/product/pc_tools_workstation.md`、`pc-tools/README.md`，明确该 contract 不等于真实 ROS2 `/tf`、真实地图、真实电梯、真实楼层识别、真实人工接管或真实控制。

## 验证结果

- `cd pc-tools/workstation && npm run build`：通过，Vite 输出 `✓ built in 2.11s`。
- `cd pc-tools/workstation && npm run test`：通过，`Test Files 2 passed (2)`、`Tests 35 passed (35)`。
- `cd pc-tools/workstation && npm run lint`：通过，无 ESLint 输出。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`：首轮失败于新测试误把 archive inspector 断言放进 realtime snapshot 测试；已定位并修复。最终复跑通过，`Ran 106 tests in 31.988s`、`OK`。
- `git diff --check -- onboard/src/ros2_trashbot_behavior pc-tools/workstation docs/product/pc_tools_workstation.md docs/interfaces/o7_realtime_operator_console.md pc-tools/README.md sprints/2026.05.27_23-24_o7-realtime-elevator-http-probe`：通过，无输出。

## 剩余风险

- 本轮只证明 cloud relay HTTP contract 和 PC loopback probe 的软件链路，不连接真实 ROS2 `/tf`、真实地图、真实实时 API、真实电梯状态链、真实楼层识别或真实机器人控制。
- O7-KR1/KR2 仍需要后续 Robot/Algorithm/O6 提供真实 pose/map/elevator stream contract 与上车证据后才能提升完成度。

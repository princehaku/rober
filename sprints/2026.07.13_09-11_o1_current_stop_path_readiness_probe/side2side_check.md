# Side2Side Check - O1 Current Stop Path Readiness Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Sprint time: 2026-07-13 09:11 CST
- Product check time: 2026-07-13 09:36 CST
- Product status: accepted
- Proof boundary: `software_proof_o1_o3_current_stop_path_readiness_probe_only`

## 用户价值和产品北极星

北极星仍是普通用户交付垃圾后，小车能沿固定路线安全送达并随时可停。本轮用户价值不是发车，而是把下一轮受控 route execution 前必须具备的 current stop path 做成可机读 readiness 证据，降低真实发车前的安全歧义。

## Product 验收结论

Product 接受本轮为 O1/O3 no-motion current stop path readiness probe only。Hardware artifact `artifacts/hardware/stop_path_readiness.json` 明确：

- `schema=trashbot.o1.current_stop_path_readiness.v1`
- `current_stop_path_readiness_status=ready_for_mock_stop_only_probe_not_hil`
- `stop_endpoint=/api/base/stop`
- zero-stop command plan 覆盖 `T=1`、`T=11`、`T=13`
- `mock_virtual_serial_validation.frame_count=3`
- `mock_virtual_serial_validation.all_frames_newline_terminated=true`
- `mock_virtual_serial_validation.all_frames_json_objects=true`
- `mock_virtual_serial_validation.all_motion_axes_zero=true`
- `safe_to_control=false`
- `hil_pass=false`
- `route_execution_success=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `nonzero_motion_command_sent=false`
- `uses_real_uart=false`

保守拒绝：本轮不是 current live HIL、真实 UART ACK、safe-to-control、route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、delivery/operator acceptance 或 O5 production/external evidence。

## Side2Side 验收矩阵

| 验收项 | 期望 | 实际 | Product 判断 |
| --- | --- | --- | --- |
| 机器可读 artifact | 产出 `stop_path_readiness.json` | JSON 可解析，schema 为 `trashbot.o1.current_stop_path_readiness.v1` | 通过 |
| stop endpoint | 明确 `/api/base/stop`，不走 manual | `stop_endpoint=/api/base/stop`，`manual_endpoint_called=false` | 通过 |
| zero-stop plan | 覆盖 `T=1`、`T=11`、`T=13` 全零帧 | `{"T":1,"L":0,"R":0}`、`{"T":11,"L":0,"R":0}`、`{"T":13,"X":0,"Z":0}` | 通过 |
| mock/虚拟串口 | 只验证 newline JSON zero frames | `frame_count=3`，newline/json/zero 全部 true | 通过 |
| safety fields | 必须 fail closed | `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false` | 通过 |
| 范围边界 | 不触发真实控制或路线执行 | `uses_real_uart=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false` | 通过 |
| 文档同步 | 硬件文档和 `tech-done.md` 同步 | `docs/hardware/wave_rover_stop_path_readiness.md` 与 `tech-done.md` 已记录来源、验证和风险 | 通过 |

## 验证偏差

`tech-plan.md` 中要求的裸命令 `python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness` 在当前 macOS conda Python 中失败于 `ModuleNotFoundError`，原因是源码 package 没有安装或 sourced。Hardware 没有扩大范围去改 packaging，而是用 `PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware"` 重新执行同一个 module entry 并通过。

Product 判定：这是环境 import-path 偏差，不是 helper 代码、artifact JSON 或 stop-only 逻辑失败；closeout 必须保留该偏差，不能写成完全无偏差。

## OKR 映射和方向判断

- O5：继续约 `85%`。本轮没有真实 external production evidence，不消费 O5 blocker。
- O1：继续约 `94%`。本轮只补 no-motion mock stop path readiness，不证明 current live HIL、safe-to-control、route execution 或 delivery。
- O3 现场验证 lane：继续但不单独计分。本轮补上 08:09 bounded route command plan 后的 stop path readiness 前置项。
- O6/O7：继续约 `93%`。本轮不做 readback-only wrapper。
- 方向判断：继续 O1/O3 安全准入链路；不调整、不暂停、不替换 Objective。
- KR 归档：本轮 `不归档` KR，主百分比不调整。

## 剩余风险和下一轮建议

剩余风险：没有真实 WAVE ROVER UART capture、没有 ESP32 ACK、没有 current live `T=1001` feedback、没有真实 heartbeat observation、没有 operator approval、没有 HIL acceptance，也没有 route execution 或 delivery/operator acceptance。

下一轮建议由 `rober-hardware-engineer` 负责 current live stop HIL：在 explicit operator approval 后记录 `/api/base/stop` 调用、同窗口 UART zero-stop frame capture 和 stop 后 `T=1001` L/R 归零；再由 `robot-algorithm-engineer` 在同窗口 LiDAR/localization/TF readiness 和 Nav2/controller result 可记录后接受控 route execution evidence。

# Final - O1 Current Stop Path Readiness Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Final status: accepted
- Sprint time: 2026-07-13 09:11 CST
- Closeout time: 2026-07-13 09:36 CST
- Proof boundary: `software_proof_o1_o3_current_stop_path_readiness_probe_only`

## Product 验收结论

Product 接受本轮为 O1/O3 no-motion current stop path readiness probe only。Hardware 已实现纯离线 `trashbot.o1.current_stop_path_readiness.v1` artifact，关键事实为：

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

保守拒绝：本轮不是 HIL、真实 UART ACK、safe-to-control、route execution、fixed-route movement、NavigateToPose、controller/BT、`/cmd_vel`、`/api/base/manual`、delivery/operator acceptance 或 O5 production/external evidence。

## 用户价值和产品北极星

北极星仍是让普通用户把垃圾交给小车后，小车沿固定路线安全送达并能随时停下。本轮的产品价值是补齐下一轮受控 route execution 前的停车路径可核验证据：`/api/base/stop` 对应 WAVE ROVER zero-stop command plan，并由 mock/虚拟串口证明所有 frame 都是 newline-delimited JSON zero frame。

## OKR 映射和方向判断

- O5：继续约 `85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `94%`。本轮只补 no-motion current stop path readiness，不证明 current live HIL、safe-to-control、Nav2 route execution success、delivery/operator acceptance、真实 UART ACK、轮速方向或 IMU/battery 标定。
- O3 现场验证 lane：继续但不单独计分。本轮接在 08:09 bounded route command plan 后，补齐 current stop path readiness 这个前置安全项。
- O6/O7：继续约 `93%`。本轮不做 O6/O7 readback-only wrapper。
- 方向判断：继续 O1/O3 安全准入链路；不调整、不暂停、不替换 Objective。
- KR 归档：本轮 `不归档` KR，主百分比不调整。

## 实际改动

Implementation 由 `rober-hardware-engineer` 完成：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py`
- `docs/hardware/wave_rover_stop_path_readiness.md`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/tech-done.md`

Product closeout 新增或更新：

- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/side2side_check.md`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/final.md`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/product_acceptance_stop_path_readiness.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Implementation 验证证据来自 `tech-done.md`：

```text
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py
exit 0
```

```text
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py
Ran 5 tests in 0.006s
OK
```

```text
PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware" python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness \
  --output sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
{"artifact": "sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json", "schema": "trashbot.o1.current_stop_path_readiness.v1", "status": "ready_for_mock_stop_only_probe_not_hil"}
exit 0
```

Product 主节点验收命令通过：

```text
python3 -m json.tool .../artifacts/hardware/stop_path_readiness.json
exit 0
```

```text
python3 -m json.tool .../artifacts/product_acceptance_stop_path_readiness.json
exit 0
```

```text
product_stop_path_readiness_acceptance_ok
```

```text
rg anchors matched: 2026-07-13 09:11, current stop path, stop_path_readiness,
ready_for_mock_stop_only_probe_not_hil, /api/base/stop, T=1, T=11, T=13,
mock_virtual_serial, safe_to_control=false, hil_pass=false,
route_execution_success=false, 不归档, O5, O1
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe
exit 0
```

## 验证偏差和失败定位

`tech-plan.md` 要求的裸命令 `python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness` 在当前 macOS conda Python 中失败于 `ModuleNotFoundError`，因为源码 package 没有安装或 sourced。Hardware 未修改范围外 packaging，也未写入本机 site-packages，而是用 `PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware"` 复跑同一 module entry 并通过。

Product 判定：这是环境 import-path 偏差，不是代码语法、测试、artifact JSON 或 stop-only 逻辑失败；本轮接受时保留该偏差，不写成完全无偏差。

## 剩余风险和下一轮建议

剩余风险：

- 本轮仍是 `software_proof_o1_o3_current_stop_path_readiness_probe_only`。
- 不证明真实 `/api/base/stop` 已在上车环境执行。
- 不证明真实 WAVE ROVER UART ACK、真实 ESP32 heartbeat、current live `T=1001` feedback 或 HIL acceptance。
- 不证明 safe-to-control、route execution、fixed-route movement、delivery/operator acceptance 或 O5 production/external evidence。

下一轮 owner/action：`rober-hardware-engineer` 先在 explicit operator approval 下做 current live stop HIL，记录 `/api/base/stop` 调用、同窗口 UART zero-stop frame capture、stop 后 `T=1001` L/R 归零和 HIL acceptance。之后 `robot-algorithm-engineer` 只有在 current live HIL/stop path、同窗口 `/scan` / `/amcl_pose` / `/tf` / `/map` readiness 与 Nav2/controller result 可记录后，才用同一 route packet 继续受控 route execution evidence。

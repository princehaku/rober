# Final - O1 Live Stop HIL Capture Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`
- Product owner: `product-okr-owner`
- Implementation owner: `rober-hardware-engineer`
- Final status: accepted
- Sprint time: 2026-07-13 10:12 CST
- Proof boundary: `software_proof_o1_live_stop_hil_capture_gate_mock_only`

## Product 验收结论

Product 接受本轮为 O1/O3 mock-only operator-gated current stop HIL capture gate。Hardware artifact `artifacts/hardware/stop_hil_capture_gate.json` 明确：

- `schema=trashbot.o1.current_stop_hil_capture_gate.v1`
- `capture_gate_status=ready_for_mock_stop_hil_capture_gate_not_hil`
- `mock_http_stop_called=true`
- `mock_http_stop_call.method=POST`
- `mock_http_stop_call.path=/api/base/stop`
- `mock_http_stop_call.network_transport=mock_in_memory_no_socket`
- `mock_t1001_feedback_fixture_used=true`
- `t1001_feedback_zero_after_stop_fixture=true`
- `observed_t1001_count=1`
- `hil_pass=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `nonzero_motion_command_sent=false`
- `uses_real_uart=false`

保守拒绝：本轮不是 current live HIL、真实 `/api/base/stop`、真实 UART zero-stop frame、ESP32 ACK、safe-to-control、route execution、delivery/operator acceptance 或 O5 production/external evidence。

## 用户价值和产品北极星

北极星仍是普通用户把垃圾交给小车后，小车沿固定路线安全送达并能随时停下。本轮把下一次现场 current live stop HIL 的采集入口做成可复验 gate，但当前 run 没有 explicit operator approval，所以只接受 mock/local pipeline readiness。

## OKR 映射和方向判断

- O5：继续约 `85%`。本轮没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `94%`。本轮只证明 mock-only operator-gated stop HIL capture gate，不证明 current live HIL、safe-to-control、真实 UART ACK、ESP32 ACK、Nav2 route execution success、delivery/operator acceptance、轮速方向或 IMU/battery 标定。
- O3 现场验证 lane：继续但不单独计分。本轮接在 09:11 stop path readiness 后，进一步准备 stop HIL capture gate；后续 route execution 必须等待 explicit operator approval、current live HIL、同窗口 LiDAR/localization/TF readiness 和 Nav2/controller result。
- O6/O7：继续约 `93%`。本轮不做 O6/O7 readback-only wrapper。
- 方向判断：继续 O1/O3 安全准入链路；不调整、不暂停、不替换 Objective。
- KR 归档：本轮 KR `不归档`，主百分比不调整。

## KR 拆解和历史归档

O1 current live HIL 仍拆成四个未完成材料项：

1. explicit operator approval。
2. current live `/api/base/stop` 调用记录。
3. 同窗口 UART zero-stop frame capture。
4. stop 后 current live `T=1001` feedback L/R 归零和 HIL acceptance。

本轮只完成第 0 步 mock/local capture gate，不归档 KR。历史记录位置为本 sprint `side2side_check.md`、本 `final.md`、`artifacts/product_acceptance_stop_hil_capture_gate.json`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 实际改动

Implementation 由 `rober-hardware-engineer` 完成：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py`
- `docs/hardware/wave_rover_stop_hil_capture_gate.md`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/mock_t1001_feedback.json`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/tech-done.md`

Product closeout 新增或更新：

- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/side2side_check.md`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/final.md`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/product_acceptance_stop_hil_capture_gate.json`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Implementation 验证证据来自 `tech-done.md`：

```text
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py
exit 0
```

```text
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py
Ran 6 tests in 0.009s
OK
```

```text
PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware" python3 -m ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate \
  --mock \
  --operator-approval-token MOCK_APPROVED_STOP_ONLY \
  --output sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json
{"artifact": "sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json", "schema": "trashbot.o1.current_stop_hil_capture_gate.v1", "status": "ready_for_mock_stop_hil_capture_gate_not_hil"}
exit 0
```

Product closeout 验收命令通过：

```text
python3 -m json.tool .../artifacts/hardware/stop_hil_capture_gate.json
exit 0
```

```text
python3 -m json.tool .../artifacts/product_acceptance_stop_hil_capture_gate.json
exit 0
```

```text
product_stop_hil_capture_gate_acceptance_ok
```

```text
rg anchors matched: 2026-07-13 10:12, stop HIL capture gate,
ready_for_mock_stop_hil_capture_gate_not_hil, mock_in_memory_no_socket,
t1001_feedback_zero_after_stop_fixture, hil_pass=false, safe_to_control=false,
route_execution_success=false, delivery_success=false, 不归档, O5, O1
```

```text
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate
exit 0
```

## 失败定位

Product closeout 验收命令均通过，没有新增失败需要修复。Hardware implementation 已在 `tech-done.md` 覆盖缺 token、错 token、非 mock mode 和 after_stop `T=1001` L/R 非零等 fail-closed 负例。

## 剩余风险和下一轮建议

剩余风险：

- 本轮仍是 `software_proof_o1_live_stop_hil_capture_gate_mock_only`。
- 不证明真实 `/api/base/stop` 已在机器人上执行。
- 不证明真实 UART zero-stop frame、ESP32 ACK、current live `T=1001` feedback 或 HIL acceptance。
- 不证明 safe-to-control、route execution、fixed-route movement、delivery/operator acceptance 或 O5 production/external evidence。

下一轮 owner/action：`rober-hardware-engineer` 只有在 explicit operator approval 后，才采 current live `/api/base/stop` 调用、同窗口 UART zero-stop frame capture、stop 后 `T=1001` L/R 归零和 HIL acceptance。之后 `robot-algorithm-engineer` 只有在同窗口 LiDAR/localization/TF readiness 与 Nav2/controller result 可记录时，才推进 controlled route execution evidence。

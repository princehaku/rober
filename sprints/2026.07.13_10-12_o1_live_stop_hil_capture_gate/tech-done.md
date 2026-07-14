# Tech Done - O1 Live Stop HIL Capture Gate

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/`
- Owner: `rober-hardware-engineer`
- Implementation status: complete
- Completed at: 2026-07-13 10:29 CST
- Proof boundary: `software_proof_o1_live_stop_hil_capture_gate_mock_only`

## 已读资料

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/tech-plan.md`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/final.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`

## 已证实的硬件结论

- Vendor 上位机 `base_ctrl.py` 使用 `json.dumps(data) + "\n"` 发送 UTF-8 UART JSON 帧。
- Vendor 固件 `uart_ctrl.h` 以 newline 作为完整 JSON 指令解析边界。
- Vendor 固件 `json_cmd.h` 定义 `FEEDBACK_BASE_INFO` 为 `T=1001`，本轮 fixture 只验证该反馈帧的解析路径。
- Vendor Raspberry Pi 示例是 `/dev/ttyAMA0`、`115200`，另有 `/dev/serial0` 注释；本轮没有推断或写死 Orange Pi 真实 UART 设备。

## 实际改动

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py`
  - 新增 `python3 -m ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate` module entry。
  - 支持 `--mock`、`--operator-approval-token MOCK_APPROVED_STOP_ONLY`、`--feedback-fixture`、`--output`。
  - token 缺失、错误 token 或非 mock mode 均 fail-closed，且不会调用 mock stop。
  - 通过内存 mock client 验证 `POST /api/base/stop` 调用形状，不发起真实网络请求。
  - 复用 `wave_rover_feedback.parse_feedback_line` 解析 mock fixture 的 `T=1001` stop 后 L/R 归零路径。
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py`
  - 覆盖 ready artifact、缺 token、错 token、非 mock mode、T=1001 非零负例和 CLI 写 artifact。
- `docs/hardware/wave_rover_stop_hil_capture_gate.md`
  - 新增 operator-gated stop HIL capture gate 文档，写明 vendor 来源、mock 边界、禁止项和 live 履约证据。
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/mock_t1001_feedback.json`
  - 新增 mock-only `T=1001` after_stop L/R=0 fixture。
- `sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json`
  - 写出 schema `trashbot.o1.current_stop_hil_capture_gate.v1` artifact。

## Artifact 关键结果

- `capture_gate_status=ready_for_mock_stop_hil_capture_gate_not_hil`
- `mock_http_stop_called=true`
- `mock_http_stop_call_shape_valid=true`
- `mock_http_stop_call.method=POST`
- `mock_http_stop_call.path=/api/base/stop`
- `mock_http_stop_call.network_transport=mock_in_memory_no_socket`
- `mock_t1001_feedback_fixture_used=true`
- `t1001_feedback_zero_after_stop_fixture=true`
- `mock_t1001_feedback.observed_t1001_count=1`
- 固定 false 字段全部保持：
  - `hil_pass=false`
  - `safe_to_control=false`
  - `route_execution_success=false`
  - `delivery_success=false`
  - `robot_control_executed=false`
  - `nonzero_motion_command_sent=false`
  - `uses_real_uart=false`

## 验证结果

```text
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py
exit 0
```

```text
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py
......
----------------------------------------------------------------------
Ran 6 tests in 0.009s

OK
```

```text
PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware" \
python3 -m ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate \
  --mock \
  --operator-approval-token MOCK_APPROVED_STOP_ONLY \
  --output sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json
{"artifact": "sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json", "schema": "trashbot.o1.current_stop_hil_capture_gate.v1", "status": "ready_for_mock_stop_hil_capture_gate_not_hil"}
exit 0
```

```text
python3 -m json.tool sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json
exit 0
```

```text
structured assertion:
stop_hil_capture_gate_assertions_ok
```

断言覆盖：

- schema 为 `trashbot.o1.current_stop_hil_capture_gate.v1`
- status 为 `ready_for_mock_stop_hil_capture_gate_not_hil`
- mock stop called 且 shape 为 `POST /api/base/stop`
- network transport 为 `mock_in_memory_no_socket`
- mock `T=1001` fixture 被消费
- after_stop sample 的 `left_speed=0`、`right_speed=0`
- 七个 required safety/control 字段全部为 false

```text
comment ratio self-check:
wave_rover_stop_hil_capture_gate.py comment_like ratio=20.79%
test_wave_rover_stop_hil_capture_gate.py comment_like ratio=21.26%
```

```text
git diff --check -- \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_hil_capture_gate.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_hil_capture_gate.py \
  docs/hardware/wave_rover_stop_hil_capture_gate.md \
  sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate
exit 0
```

## 失败定位

本轮指定验收命令均一次通过，没有需要修复后复验的失败。

实现内已覆盖以下 fail-closed 负例：

- 缺 `MOCK_APPROVED_STOP_ONLY` token：blocked，且 mock stop 不调用。
- 错 token：blocked，且 mock stop 不调用。
- 非 `--mock` mode：blocked，且不调用真实 stop、不打开 UART。
- after_stop `T=1001` L/R 非零：blocked，且 HIL/safety/control 字段继续 false。

## 剩余风险

- 本轮仍是 `software_proof_o1_live_stop_hil_capture_gate_mock_only`。
- 不证明真实 `/api/base/stop` 已在机器人上执行。
- 不证明真实 UART zero-stop frame、真实 ESP32 ACK、真实 current live `T=1001` feedback 或 HIL acceptance。
- 不证明 `safe_to_control`、route execution、fixed-route movement、delivery/operator acceptance 或 O5 production/external evidence。

下一步必须在 explicit operator approval 后，由 Hardware owner 采集 current live stop call、同窗口 UART zero-stop frame capture、post-stop `T=1001` L/R 归零和 HIL acceptance，再交由 Product closeout 判断是否改变 O1 证据等级。

# WAVE ROVER Stop HIL Capture Gate

## 目的

本 helper 为下一步 current live stop HIL 做 operator-gated capture gate。当前自动化没有现场 operator approval，所以只允许 `--mock` 路径：验证本地 mock HTTP `POST /api/base/stop` 调用形状，并用 fixture 证明 stop 后 `T=1001` feedback 的 L/R 归零解析路径可机读。

本轮结果不是 HIL pass，不证明真实 `/api/base/stop` 已执行，不证明真实 WAVE ROVER UART frame、ESP32 ACK、safe-to-control、route execution 或 delivery success。

## Vendor 来源

已采用本地资料来源：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`

关键硬件结论：

- `base_ctrl.py` 使用 `json.dumps(data) + "\n"` 发送 UTF-8 JSON 串口帧。
- `uart_ctrl.h` 在接收到 newline 后解析完整 JSON 指令。
- `json_cmd.h` 定义 `FEEDBACK_BASE_INFO` 为 `T=1001`，这是底盘 feedback 帧。
- `base_ctrl.py` 的 Raspberry Pi 示例是 `/dev/ttyAMA0`、`115200`，另有 `/dev/serial0` 注释；Orange Pi 真实设备名不能由本 helper 猜测或写死。

## 使用方式

当前 automation 只能运行 mock：

```bash
PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware" \
python3 -m ros2_trashbot_hardware.wave_rover_stop_hil_capture_gate \
  --mock \
  --operator-approval-token MOCK_APPROVED_STOP_ONLY \
  --output sprints/2026.07.13_10-12_o1_live_stop_hil_capture_gate/artifacts/hardware/stop_hil_capture_gate.json
```

缺少 `--operator-approval-token MOCK_APPROVED_STOP_ONLY` 或 token 错误时，helper 必须 fail-closed，且不会调用 mock stop。

## Artifact 合同

输出 schema：

```text
trashbot.o1.current_stop_hil_capture_gate.v1
```

当前 mock-only ready 状态：

```text
ready_for_mock_stop_hil_capture_gate_not_hil
```

固定 false 字段：

- `hil_pass=false`
- `safe_to_control=false`
- `route_execution_success=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `nonzero_motion_command_sent=false`
- `uses_real_uart=false`

## 禁止项

本 helper 不做以下事情：

- 不调用真实 `/api/base/stop`
- 不调用 `/api/base/manual`
- 不发布 `/cmd_vel`
- 不发送 NavigateToPose
- 不打开 WAVE ROVER UART
- 不发送非零运动命令

## 下一步 live 履约

只有在现场 explicit operator approval 后，下一轮才可以采集 current live stop HIL evidence：

- 真实 `/api/base/stop` 调用记录
- 同窗口 UART zero-stop frame capture
- stop 后真实 `T=1001` L/R 归零
- HIL acceptance 记录
- 同窗口 LiDAR/localization/TF readiness

在这些证据出现前，artifact 只能作为 mock/local capture gate readiness，不得提升为 HIL 或 safe-to-control。

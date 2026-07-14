# Tech Done - O1 Current Stop Path Readiness Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- Implementation owner: `rober-hardware-engineer`
- Completed at: 2026-07-13 09:26 CST
- Proof boundary: `software_proof_o1_o3_current_stop_path_readiness_probe_only`
- Status: implementation complete, ready for Product acceptance

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- `sprints/2026.07.13_08-09_o3_bounded_route_command_plan/final.md`

## 实际改动

- 新增 `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py`：生成 `trashbot.o1.current_stop_path_readiness.v1` 离线 artifact，复用 vendor UART JSON 编码纯函数，mock/虚拟串口校验 `T=1`、`T=11`、`T=13` zero-stop command plan。
- 新增 `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py`：覆盖固定 false safety fields、zero-stop command plan、newline-delimited JSON frame、vendor source/heartbeat 摘要、非零命令 fail-closed 和 CLI 写出。
- 新增 `docs/hardware/wave_rover_stop_path_readiness.md`：同步 `/api/base/stop` readiness 合同、vendor 来源、heartbeat/zero-stop 资料边界和下一步 HIL 履约动作。
- 新增 `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json`：可机读 artifact，包含 `/api/base/stop`、no `/api/base/manual`、no `/cmd_vel`、no NavigateToPose、vendor refs、mock frame validation 和固定 false 字段。

未修改 `OKR.md`、launch 参数、真实串口设备配置、production cloud、`pc-tools/` 或范围外 sprint。

## 已证实的硬件结论

- Vendor 上位机 `base_ctrl.py` 使用 UTF-8 JSON 加 `\n` 写串口；固件 `uart_ctrl.h` 收到 `\n` 后解析完整 JSON object。
- Vendor RPi 示例串口为 `/dev/ttyAMA0` at `115200`，另有 `/dev/serial0` 注释；本轮未硬编码 Orange Pi 串口设备。
- `T=1` / `T=11` / `T=13` 的 zero-stop 计划分别是 `{"T":1,"L":0,"R":0}`、`{"T":11,"L":0,"R":0}`、`{"T":13,"X":0,"Z":0}`。
- heartbeat 资料来自 vendor source：`T=1`、`T=11`、`T=13` 会刷新 `lastCmdRecvTime`，`HEART_BEAT_DELAY=3000`，`heartBeatCtrl()` 超时后调用 `setGoalSpeed(0,0)`。
- 以上是 source-readback + mock/虚拟串口软件证明，不是当前 live ESP32 heartbeat observation。

## 验证结果

```text
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py
exit 0
```

```text
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py
.....
----------------------------------------------------------------------
Ran 5 tests in 0.006s

OK
```

```text
python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness \
  --output sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
exit 1
/opt/homebrew/Caskroom/miniconda/base/bin/python3: Error while finding module specification for 'ros2_trashbot_hardware.wave_rover_stop_path_readiness' (ModuleNotFoundError: No module named 'ros2_trashbot_hardware')
```

失败定位：当前 macOS conda Python 没有安装/sourced `onboard/src/ros2_trashbot_hardware` 包；为避免修改范围外 `setup.py` 或本机 site-packages，本轮使用源码 `PYTHONPATH` 作为本地验收前置重新执行同一 module entry。

```text
PYTHONPATH="$PWD/onboard/src/ros2_trashbot_hardware" python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness \
  --output sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
{"artifact": "sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json", "schema": "trashbot.o1.current_stop_path_readiness.v1", "status": "ready_for_mock_stop_only_probe_not_hil"}
exit 0
```

```text
python3 -m json.tool sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json >/tmp/o1_stop_path_readiness.pretty.json
exit 0
```

```text
python3 - <<'PY'
...
print("current_stop_path_readiness_acceptance_ok")
PY
current_stop_path_readiness_acceptance_ok
exit 0
```

```text
rg -n "current_stop_path_readiness|current stop path|/api/base/stop|T=1|T=11|T=13|heartbeat|safe_to_control=false|hil_pass=false|route_execution_success=false|no /api/base/manual" \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py \
  docs/hardware/wave_rover_stop_path_readiness.md \
  sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/tech-done.md \
  sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
exit 0
key hits: current_stop_path_readiness, current stop path, /api/base/stop, T=1, T=11, T=13, heartbeat, safe_to_control=false, hil_pass=false, route_execution_success=false, no /api/base/manual
```

```text
git diff --check -- \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py \
  docs/hardware/wave_rover_stop_path_readiness.md \
  sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe
exit 0
```

## Artifact 关键字段

- `schema=trashbot.o1.current_stop_path_readiness.v1`
- `current_stop_path_readiness_status=ready_for_mock_stop_only_probe_not_hil`
- `stop_endpoint=/api/base/stop`
- `manual_endpoint_called=false`
- `safe_to_control=false`
- `hil_pass=false`
- `route_execution_success=false`
- `delivery_success=false`
- `robot_control_executed=false`
- `nonzero_motion_command_sent=false`
- `uses_real_uart=false`
- `zero_stop_command_plan` 包含 `T=1`、`T=11`、`T=13` 三条全零命令。

## 失败定位

- 裸 `python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness` 在当前 conda 环境失败于 `ModuleNotFoundError`。根因是本地 Python 没有 package install/source；不是 helper 代码语法、测试或 artifact 逻辑失败。
- `rg` 首轮失败于 `tech-done.md` 尚未存在；本文件补齐后已重新运行并通过。

## 剩余风险和下一步

剩余风险：

- 本轮仍是 `software_proof_o1_o3_current_stop_path_readiness_probe_only`。
- 没有打开真实 UART，没有 WAVE ROVER ESP32 ACK，没有当前 live `T=1001` feedback，没有真实 heartbeat observation。
- 没有调用 `/api/base/manual`，没有发布 `/cmd_vel`，没有 NavigateToPose/Nav2 controller/BT，没有 route execution 或 delivery。
- `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false` 必须保持到真实 HIL/route execution 证据出现。

下一步履约动作：

1. 现场 explicit operator approval 后，记录 current live `/api/base/stop` 调用和同窗口 UART zero-stop frame capture。
2. 在真实 WAVE ROVER 上采集 stop 前后 `T=1001` feedback，确认 stop 后 L/R 归零。
3. 与同窗口 `/scan`、`/amcl_pose`、`/tf`、`/map` readiness 合并成 HIL 准入记录。
4. 只有 stop path、HIL 准入、Nav2/controller result 和 operator acceptance 同时存在后，才推进 route execution 或 delivery 证据。

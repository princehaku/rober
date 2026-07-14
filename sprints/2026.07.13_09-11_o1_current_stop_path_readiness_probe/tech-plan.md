# Tech Plan - O1 Current Stop Path Readiness Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/`
- Product owner: `product-okr-owner`
- Planned implementation owner: `rober-hardware-engineer`
- Implementation model: single owner closed loop
- Proof boundary: `software_proof_o1_o3_current_stop_path_readiness_probe_only`

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字完成度最低 Objective 是 O5，约 `85%`。
2. 本 sprint 不针对 O5；本 sprint 转向 O1/O3 current stop path / emergency stop readiness。
3. 不针对 O5 的理由：O5 下一步只有真实 external production evidence 才可计增量；最近 production cutover readiness packet 已经是 support-only，继续 O5 readiness / packet / handoff 会重复消费同一 blocker。
4. O1 当前约 `94%`，缺 current live HIL、current stop path、safe-to-control、Nav2 route execution success、delivery/operator acceptance、轮速方向和 IMU/battery 标定。
5. 本轮针对 O1 的理由：上一轮 bounded route command plan 已把下一步收敛到 explicit operator approval、current live HIL/stop path、同窗口 LiDAR/localization/TF readiness 与 Nav2/controller result；stop path readiness 是当前环境可用 mock/虚拟串口验证、且不重复 route/gate packaging 的最窄前置项。
6. 收口要求：若本轮只产出 no-motion current stop path readiness，OKR 主百分比预计不调整，KR `不归档`；所有 safety fields 继续固定 `safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`。

## 后续允许文件范围

允许 `rober-hardware-engineer` 修改：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py`
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py` 仅当需要新增纯函数时可改
- `docs/hardware/wave_rover_stop_path_readiness.md`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json`
- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/tech-done.md`

不允许修改：

- `OKR.md`
- `docs/` 下其它文件
- `onboard/` 下范围外文件
- `pc-tools/`
- 其它 sprint 目录
- launch 参数、硬件配置、真实串口设备配置或 production cloud

## 输入和来源

本轮必须把以下来源写入 artifact 或文档：

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_config.h`
- 上轮 Product closeout：`sprints/2026.07.13_08-09_o3_bounded_route_command_plan/final.md`

必须保留的事实：

- UART framing：vendor upper computer 使用 newline-delimited UTF-8 JSON。
- Vendor RPi default UART：`/dev/ttyAMA0` at `115200`，Orange Pi 实际设备名不得硬编码。
- `T=1`：speed control，zero-stop 形态为 `{"T":1,"L":0,"R":0}`。
- `T=11`：PWM input，zero-stop 形态为 `{"T":11,"L":0,"R":0}`。
- `T=13`：ROS linear/angular control，zero-stop 形态为 `{"T":13,"X":0,"Z":0}`。
- heartbeat：`T=1`、`T=11`、`T=13` 会刷新 `lastCmdRecvTime`；固件 `heartBeatCtrl` 超过 `HEART_BEAT_DELAY=3000` 后执行 `setGoalSpeed(0, 0)`。
- `/api/base/stop` 是 stop endpoint；本轮只做 readiness，不调用 `/api/base/manual`。

## 技术方案

`rober-hardware-engineer` 新增一个纯离线 Hardware readiness helper：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py`

建议 schema：

- `trashbot.o1.current_stop_path_readiness.v1`

建议输出 artifact：

- `sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json`

核心逻辑：

1. 构造 stop-only contract，包含 `stop_endpoint=/api/base/stop` 和 no `/api/base/manual`。
2. 从 `wave_rover_protocol.py` 复用或新增纯函数生成 newline-delimited UART JSON bytes；不得打开串口。
3. 生成 zero-stop command plan，必须覆盖 `T=1`、`T=11`、`T=13`，且 `L/R/X/Z` 全为 0。
4. 用 mock/虚拟串口对象记录 bytes，验证每条 frame 是 JSON object + `\n`。
5. 扫描写出的 frame，任何非零 `L/R/X/Z`、任何 `/api/base/manual`、任何 `/cmd_vel`、任何 NavigateToPose 字样都必须 fail closed。
6. 输出 heartbeat vendor source summary，但不得宣称真实 ESP32 heartbeat 已触发。
7. 输出固定 false fields：`safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`、`nonzero_motion_command_sent=false`、`uses_real_uart=false`。
8. 输出 `current_stop_path_readiness_status=ready_for_mock_stop_only_probe_not_hil` 或更保守状态。

## 接口影响

- 只新增离线 Hardware artifact contract 和文档。
- 不新增 ROS2 topic/action/service。
- 不打开真实 UART。
- 不调用 `/api/base/manual`。
- 不触发 `/cmd_vel`、NavigateToPose、Nav2 controller/BT 或 route execution。
- 不改变 `/api/base/stop` 现有行为；本轮只把它作为 stop path readiness contract 的 endpoint 字段。
- 不改变 O6/O7 consumer API 或 production cloud。

## 验收命令

`rober-hardware-engineer` 必须运行并在 `tech-done.md` 记录：

```bash
python3 -m py_compile \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py
python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py
python3 -m ros2_trashbot_hardware.wave_rover_stop_path_readiness \
  --output sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
python3 -m json.tool sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json >/tmp/o1_stop_path_readiness.pretty.json
python3 - <<'PY'
import json
from pathlib import Path

path = Path("sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json")
data = json.loads(path.read_text())
assert data["schema"] == "trashbot.o1.current_stop_path_readiness.v1"
assert data["stop_endpoint"] == "/api/base/stop"
assert data["manual_endpoint_called"] is False
assert data["safe_to_control"] is False
assert data["hil_pass"] is False
assert data["route_execution_success"] is False
assert data["delivery_success"] is False
assert data["robot_control_executed"] is False
assert data["nonzero_motion_command_sent"] is False
commands = data["zero_stop_command_plan"]
assert {"T": 1, "L": 0, "R": 0} in commands
assert {"T": 11, "L": 0, "R": 0} in commands
assert {"T": 13, "X": 0, "Z": 0} in commands
guards = " ".join(data["no_motion_control_guard"])
assert "no /api/base/manual" in guards
assert "no /cmd_vel" in guards
assert "no NavigateToPose" in guards
print("current_stop_path_readiness_acceptance_ok")
PY
rg -n "current_stop_path_readiness|current stop path|/api/base/stop|T=1|T=11|T=13|heartbeat|safe_to_control=false|hil_pass=false|route_execution_success=false|no /api/base/manual" \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py \
  docs/hardware/wave_rover_stop_path_readiness.md \
  sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/tech-done.md \
  sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/artifacts/hardware/stop_path_readiness.json
git diff --check -- \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/test/test_wave_rover_stop_path_readiness.py \
  onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_protocol.py \
  docs/hardware/wave_rover_stop_path_readiness.md \
  sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe
```

Product 计划验收命令：

```bash
rg -n "sprint_type: epic|OKR 最低优先级核对|O5|O1|current stop path|/api/base/stop|T=1|T=11|T=13|heartbeat|safe_to_control=false|hil_pass=false|route_execution_success=false|no /api/base/manual" sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/pre_start.md sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/prd.md sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe/tech-plan.md
git diff --check -- sprints/2026.07.13_09-11_o1_current_stop_path_readiness_probe
```

## 验收标准

通过标准：

- `stop_path_readiness.json` 可被 `json.tool` 解析。
- artifact 明确 `current_stop_path_readiness_status`，且不使用 success-like route execution/HIL 状态。
- artifact 包含 `/api/base/stop`、no `/api/base/manual`、`T=1`、`T=11`、`T=13`、heartbeat 和 vendor refs。
- mock/虚拟串口证明所有 JSON frames 都是 zero-stop，且以 `\n` 结尾。
- 所有 safety/control/mission fields 固定 false：`safe_to_control=false`、`hil_pass=false`、`route_execution_success=false`、`delivery_success=false`、`robot_control_executed=false`。
- `docs/hardware/wave_rover_stop_path_readiness.md` 和 `tech-done.md` 完成同步。

不通过标准：

- 触发真实非零运动，或调用 `/api/base/manual`。
- 把 readiness 写成 current live HIL pass、safe-to-control、route execution success 或 delivery success。
- 未引用 vendor UART/JSON/heartbeat/zero-stop 来源。
- 只做 checklist，不产出可机读 artifact。
- 修改范围外文件或覆盖上一轮 route packet / bounded plan artifact。

## 风险和回滚边界

- 本轮仍是 `software_proof_o1_o3_current_stop_path_readiness_probe_only`，不是 HIL、真实串口 ACK、route execution 或 delivery。
- 虚拟串口只能证明编码和 fail-closed 逻辑，不能证明真实 WAVE ROVER 接收、执行或停车距离。
- heartbeat 来源来自 vendor 固件代码；本轮不证明加载固件版本与本地源码完全一致。
- 回滚边界是新增 helper/test、必要 protocol pure function、hardware doc、本 sprint artifact 和 `tech-done.md`。

## 后续收口要求

实现完成后，`tech-done.md` 必须写清实际改动、验证输出、失败定位和剩余风险。Product closeout 后再决定是否更新 `OKR.md`、`side2side_check.md` 和 `final.md`；本计划阶段不修改 `OKR.md`。

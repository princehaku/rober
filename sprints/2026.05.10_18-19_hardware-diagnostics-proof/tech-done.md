# Sprint 2026.05.10 18-19 Hardware Diagnostics Proof - Tech Done

## 状态

- 阶段：implementation completed。
- 时间：2026-05-10 18:28 Asia/Shanghai。
- Owner：`hardware-engineer`。
- 范围：Objective 1 软件侧 hardware diagnostics proof helper/CLI；未做真实 UART/WAVE ROVER HIL。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/pre_start.md`
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/prd.md`
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-plan.md`

## 已证实的硬件结论

- 软件侧协议事实来自本地 vendor 资料：WAVE ROVER ESP32 下位机通过 UART 接收 UTF-8 JSON line，`base_ctrl.py` 发送 `json.dumps(data) + "\n"`。
- `json_cmd.h` 定义 `T=1` 为左右轮 speed control，`T=13` 为 ROS X/Z control，`T=131` 为 base feedback flow，`T=142` 为 feedback interval，`T=143` 为 UART echo mode，`T=1001` 为 base info feedback。
- `movtion_module.h` 显示 `T=1` 会进入 `setGoalSpeed(L, R)`，`T=13` 会进入 `rosCtrl(X, Z)`；本轮只证明命令结构和软件复用路径，不证明实车运动表现。
- 当前 `/odom` 仍按项目驱动说明标记为 ROS-side command integration，不能当作实测轮速/里程计。
- Orange Pi 实际 UART 设备名、真实接线、电气、轮向、速度单位、反馈频率、IMU/电池读数仍未上车验证。

## 实际改动

- `src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`
  - 新增 `build_hardware_diagnostics_proof(config=None, feedback_sample=None, output_file=None)`。
  - 复用 `esp32_bridge.py` 的 `validate_startup_config`、`build_startup_config_commands`、`build_cmd_vel_command`、`parse_feedback_line`、`encode_json_command`。
  - 输出 `vendor_sources`、`config`、`startup_commands`、`cmd_vel_examples`、`feedback_sample`、`risk_flags`、`hil_recipe`。
  - `invalid_config` 和 `feedback_parse_failed` 都输出结构化 JSON，不打开串口、不启动 ROS2 node。
- `src/ros2_trashbot_hardware/setup.py`
  - 新增 console script：`hardware_diagnostics_proof = ros2_trashbot_hardware.hardware_diagnostics_proof:main`。
- `src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
  - 新增 focused unittest，覆盖默认 proof、CLI 写文件、非法配置、坏 feedback、T=13/HIL 风险标记和 startup command IDs。
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md`
  - 记录本轮来源、实现、验证和 HIL 风险。

## Proof artifact 字段

- `status`
  - `software_proof_ready`
  - `invalid_config`
  - `feedback_parse_failed`
- `vendor_sources`
- `config`
- `config_validation`
- `startup_commands`
- `cmd_vel_examples`
- `feedback_sample`
- `risk_flags`
- `hil_recipe`

## 接口影响

- 新增 Python 模块和 console script。
- 不修改 `esp32_bridge` 运行时行为。
- 不修改 ROS2 msg/srv/action。
- 不修改 launch 默认参数、UART 默认值、vendor 文件或 factory firmware。
- 不打开 serial、不连接真实硬件。

## 验证结果

已运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_hardware/test -p 'test_hardware_diagnostics_proof.py'
```

结果：9 tests OK。

```bash
python3 -m py_compile src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py
```

结果：通过，无语法错误。

```bash
git diff --check -- src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py src/ros2_trashbot_hardware/setup.py src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md
```

结果：通过，无 whitespace error。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_hardware/test
```

结果：23 tests OK。

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

结果：通过，覆盖 interfaces 6 tests、hardware 23 tests、nav 39 tests、bringup 9 tests、behavior 111 tests、vision 13 tests。

## 失败定位

- 暂无失败；focused unittest、hardware 包测试、py_compile、diff check 和完整 smoke 均通过。

## 剩余风险和下一步履约

- 真实 WAVE ROVER UART 未打开，不能声明实机连接成功。
- Orange Pi 实际串口设备名仍需在目标硬件上确认，不能把 Raspberry Pi vendor 路径当默认事实。
- `T=1` 左右轮方向、速度单位、限速响应和停车路径仍需低速 HIL。
- `T=13` ROS mode 仍仅作为 vendor-defined unverified 示例，不能切成默认 `/cmd_vel` 映射。
- `T=1001` 的反馈频率、字段稳定性、IMU 姿态、电池电压和轮速读数仍需实测。
- 下一步：在有车环境运行 `scripts/hardware_smoke_wave_rover.py` 的 no-motion、low-speed T=1、T=13 专项 recipe，并把结果接入 `side2side_check.md` / `final.md`。

## 小修记录 2026-05-10 18:41 Asia/Shanghai

- 修复：`_merge_config()` 不再在结构化校验前直接转换数值字段，避免 `config={"max_wheel_speed_mps": "bad"}` 这类输入直接抛异常。
- 实现：数值 coercion 下沉到 `_validate_config()`，`serial_baudrate`、`track_width_m`、`max_wheel_speed_mps`、`feedback_interval_ms`、`odom_publish_hz` 无法转换或非 finite 时统一返回结构化 `invalid_config`。
- 测试：新增 focused unittest 覆盖 5 个非数值配置字段，确认输出 `invalid_config`、不生成 startup commands、不生成 cmd_vel examples。
- 验证：
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_hardware/test -p 'test_hardware_diagnostics_proof.py'`：10 tests OK。
  - `python3 -m py_compile src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`：通过。
  - `git diff --check -- src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md`：通过。
  - `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_hardware/test`：24 tests OK。
- 剩余风险：本次只修复离线 proof 配置失败边界，不新增任何真实 UART/WAVE ROVER HIL 证据。

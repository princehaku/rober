# Sprint 2026.05.10 18-19 Hardware Diagnostics Proof - Tech Plan

## 状态

- 阶段：tech-plan completed，可进入 implementation。
- 时间：2026-05-10 18:09 Asia/Shanghai。
- 主责：Hardware Infra Engineer。
- 执行方式：1 owner 单线闭环，必须由 `hardware-engineer` 子 agent 实现、验证并更新 `tech-done.md`。Coordinator/Product Owner 不直接写产品代码、测试代码或硬件配置。

## 文件范围

Hardware Engineer 可改：

- `src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`
- `src/ros2_trashbot_hardware/setup.py`
- `src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md`

允许只读：

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/pre_start.md`
- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/prd.md`
- `sprints/2026.05.10_17-18_visual-gate-proof/*`
- `.codex/agents/hardware-engineer.toml`
- `src/ros2_trashbot_hardware/ros2_trashbot_hardware/esp32_bridge.py`
- `src/ros2_trashbot_hardware/test/test_waveshare_json_bridge.py`
- `scripts/hardware_smoke_wave_rover.py`
- `scripts/run_smoke_tests.sh`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

禁止改动：

- `OKR.md`
- `AGENTS.md`
- `.codex/agents/`
- `docs/vendor/`
- `docs/hardware/`，除非 coordinator 后续另开文档范围
- `src/ros2_trashbot_behavior/`
- `src/ros2_trashbot_nav/`
- `src/ros2_trashbot_vision/`
- `src/ros2_trashbot_interfaces/`
- `src/ros2_trashbot_bringup/`
- launch 硬件参数、UART 设备默认值、WAVE ROVER/ESP32/Orange Pi 配置
- factory firmware 或 vendor 二进制

## 接口影响

- 新增 CLI 建议入口：`hardware_diagnostics_proof = ros2_trashbot_hardware.hardware_diagnostics_proof:main`。
- 不改现有 `esp32_bridge` console script 行为。
- 不改 ROS2 msg/srv/action。
- 不改 launch 参数默认值。
- 不打开串口、不发真实硬件命令。
- 新增 proof JSON artifact contract，建议字段：

```json
{
  "status": "software_proof_ready",
  "vendor_sources": [
    "docs/vendor/VENDOR_INDEX.md",
    "docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py",
    "docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h"
  ],
  "config": {
    "serial_port": "/dev/ttyUSB0",
    "serial_baudrate": 115200,
    "command_mode": "speed",
    "track_width_m": 0.172,
    "max_wheel_speed_mps": 1.3,
    "feedback_interval_ms": 100,
    "odom_source": "ROS-side command integration until measured wheel odometry is validated"
  },
  "startup_commands": [
    {"T": 143, "cmd": 0},
    {"T": 142, "cmd": 100},
    {"T": 131, "cmd": 1}
  ],
  "cmd_vel_examples": {
    "speed_mode_forward": {"T": 1, "L": 0.5, "R": 0.5},
    "ros_mode_forward": {"T": 13, "X": 0.1, "Z": 0.0}
  },
  "feedback_sample": {
    "raw": {"T": 1001, "L": 0.2, "R": 0.3, "r": 1.0, "p": 2.0, "y": 3.0, "v": 11.7},
    "parsed": {"left_speed": 0.2, "right_speed": 0.3, "roll": 1.0, "pitch": 2.0, "yaw": 3.0, "voltage": 11.7},
    "status": "parsed"
  },
  "risk_flags": [
    {"id": "hil_required", "severity": "high", "detail": "T=13 ROS mode and real UART feedback still require WAVE ROVER HIL"}
  ],
  "hil_recipe": {
    "no_motion": "python3 scripts/hardware_smoke_wave_rover.py --serial-port <target_uart>",
    "low_speed": "python3 scripts/hardware_smoke_wave_rover.py --serial-port <target_uart> --move-test --reverse-test"
  }
}
```

- Artifact 字段后续可被 operator diagnostics/HIL runbook 消费；本轮先保持稳定、简单、明确标注风险。

## 实施任务

### Task 1：新增 diagnostics proof 模块

文件：

- `src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`

要求：

1. 提供纯函数入口，例如 `build_hardware_diagnostics_proof(config=None, feedback_sample=None, output_file=None)`。
2. 复用 `esp32_bridge.py` 的纯函数，不复制协议计算逻辑：
   - `validate_startup_config`
   - `build_startup_config_commands`
   - `build_cmd_vel_command`
   - `parse_feedback_line`
   - `encode_json_command`
3. 默认 config 使用当前 driver 默认值，但必须在 proof 中标注 Orange Pi 实际 UART 仍需上车确认。
4. 默认 feedback sample 使用 `T=1001` vendor-shaped JSON，并输出 raw、parsed、status。
5. 配置非法时输出结构化 `invalid_config`，包含 error message，不应打开串口。
6. 反馈解析失败时输出 `feedback_parse_failed`，并保留 raw 样例。
7. 风险标记必须包含：
   - `hil_required`
   - `orange_pi_uart_unconfirmed`
   - `ros_mode_t13_unverified`
   - `odom_is_command_integration`
8. 不启动 ROS2 node，不创建 `serial.Serial`，不订阅 topic。

### Task 2：新增 CLI

文件：

- `src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py`
- `src/ros2_trashbot_hardware/setup.py`

要求：

1. CLI 参数建议：
   - `--serial-port`
   - `--serial-baudrate`
   - `--command-mode`
   - `--track-width-m`
   - `--max-wheel-speed-mps`
   - `--feedback-interval-ms`
   - `--feedback-sample-json`
   - `--output`
2. 正常生成 proof 时退出码为 0。
3. 配置非法或 feedback sample 解析失败时仍输出结构化 JSON；退出码可为 0 或非 0，但单测必须锁定行为。
4. 不新增外部服务、前端构建或真实硬件依赖。

### Task 3：新增 focused 单测

文件：

- `src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py`

要求：

1. 使用标准库 `unittest`。
2. 复用现有 ROS/serial stubs 模式，避免真实 ROS2 和 pyserial 环境依赖。
3. 至少覆盖：
   - 默认 proof artifact。
   - CLI 写出 JSON 文件。
   - invalid command mode 或非法速度/尺寸配置。
   - bad feedback sample。
   - `T=13` risk flag 存在。
   - startup commands 包含 `T=143`、`T=142`、`T=131`。
4. 断言 proof JSON 包含 `vendor_sources`、`config`、`startup_commands`、`cmd_vel_examples`、`feedback_sample`、`risk_flags`、`hil_recipe`。

### Task 4：写 tech-done

文件：

- `sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md`

记录：

- 已读 vendor 来源。
- 已证实的硬件结论必须限定为软件侧/vendor 资料事实，不写成实车验证。
- 实际改动文件。
- proof artifact 示例字段。
- 接口影响。
- 验证命令和结果。
- 失败定位。
- 剩余风险，尤其是真实 UART、轮向、速度、反馈频率、IMU/电池和 WAVE ROVER HIL 未完成。

## 验收命令

Hardware Engineer 必须至少运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_hardware/test -p 'test_hardware_diagnostics_proof.py'
python3 -m py_compile src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py
git diff --check -- src/ros2_trashbot_hardware/ros2_trashbot_hardware/hardware_diagnostics_proof.py src/ros2_trashbot_hardware/setup.py src/ros2_trashbot_hardware/test/test_hardware_diagnostics_proof.py sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-done.md
```

如果改动影响 hardware 包通用测试，还应运行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s src/ros2_trashbot_hardware/test
```

如果本地耗时可接受，继续运行完整护栏：

```bash
PYTHONDONTWRITEBYTECODE=1 bash scripts/run_smoke_tests.sh
```

本 planning 子 agent 只运行只读/文档检查：

```bash
grep -n "文件范围\|验收命令\|接口影响\|风险\|主责" sprints/2026.05.10_18-19_hardware-diagnostics-proof/tech-plan.md
```

## 风险边界

- 本轮 proof artifact 不证明真实 WAVE ROVER HIL、真实 UART、电气接线、轮向、速度单位、反馈频率、IMU/电池实测或 Orange Pi 串口设备名。
- 本轮必须读取 `docs/vendor/VENDOR_INDEX.md` 和具体 vendor 文件后才能写任何协议事实；`tech-done.md` 必须列出采用的 vendor 来源。
- `T=13` 只能作为 proof 中的待验证示例，不能改成默认控制路径。
- CLI 输出 contract 一旦被 operator diagnostics 或 HIL runbook 消费，后续字段变更需要迁移策略；本轮先保持 artifact 明确、简单、可替换。

## 子 Agent 启动建议

下阶段 implementation 应派发 1 个 `hardware-engineer` worker，prompt 必须包含：

- 角色 System Prompt：从 `.codex/agents/hardware-engineer.toml` 的 `prompt` 字段完整复制。
- 本轮任务：实现 hardware diagnostics proof helper/CLI，生成/验证 WAVE ROVER JSON 协议离线证据。
- 文件范围：使用本 tech-plan 的“文件范围”。
- 验收命令：使用本 tech-plan 的“验收命令”。
- 输出要求：实际改动文件、验证命令输出、失败定位、剩余风险。

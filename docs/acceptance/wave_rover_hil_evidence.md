# WAVE ROVER Hardware-In-Loop Evidence

Use this file as the evidence checklist for the first real robot run.
Default fields below follow `source=software_proof` and must be replaced/补齐为
`source=hil_pass` 才可把硬件验收推进到闭环。

## Run Metadata

- Date/time:
- Operator:
- Robot:
- Orange Pi OS:
- Serial device:
- Baudrate:
- Git branch/commit:
- Launch command:
- Smoke command:

## Vendor Sources Used

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/ugv_advance.h`

## Evidence Source

- `source=software_proof`（脚本模板/离线检查、参数、风险声明）
- `source=hil_pass`（真实硬件运行结果）

## Required Evidence

| Check | Evidence Source | Evidence |
| --- | --- | --- |
| `source=software_proof` baseline captured | `software_proof` | `python3 scripts/hardware_smoke_wave_rover.py --status` 输出及脚本版本 |
| Smoke command template可复用 | `software_proof` | 运行命令行记录：`python3 scripts/hardware_smoke_wave_rover.py --help` |
| Script 访问前后参数与串口约定确认 | `software_proof` | `docs/acceptance/robot_bringup_checklist.md` 与 `docs/acceptance/hil_runbook.md` |
| 真实设备串口打开（115200 或记录覆盖值） | `hil_pass` | `HIL Smoke` 终端日志中的 `Opened <serial> @ <baud>` |
| 停止命令覆盖运动并前后成立 | `hil_pass` | 运动段前后 `T=1,L=0,R=0` 命令与小车静止照片/视频 |
| 下发启动命令（`T=143`,`T=142`,`T=131`） | `hil_pass` | 启动日志含三条 startup frame |
| `T=1001` 反馈收到且完整字段存在 | `hil_pass` | 至少一条 `T=1001` 样本含 `L,R,r,p,y,v` |
| `T=1001` 反馈采样频率 | `hil_pass` | 连续>=2帧间隔估算（目标接近 `feedback_interval_ms`） |
| 正向低速 `T=1` 方向正确 | `hil_pass` | 行驶轨迹/照片/视频 |
| 反向低速 `T=1` 方向正确 | `hil_pass` | 行驶轨迹/照片/视频 |
| 低速原地转向 `T=1`/`T=13` 方向正确 | `hil_pass` | 行驶轨迹/照片/视频 |
| `T=13` 测试（如启用） | `hil_pass` | `--ros-mode-test`/`--turn-test` 终端与安全评估 |
| `/battery` 电压语义记录 | `hil_pass` | `ros2 topic echo /battery --once` 与 `T=1001.v` 对照 |
| `/imu/data` yaw 语义记录 | `hil_pass` | `/imu/data` 与 `T=1001.y` 采样记录 |
| `/odom` 来源声明（命令积分 vs 实测里程） | `hil_pass` | `/odom` 样本并标注 `source=command_integration` |
| 紧急停机路径演示 | `hil_pass` | 停止按钮/服务触发日志与最终停止确认 |

## Attached Artifacts

- `source=software_proof`：
  - 采样模板：`docs/acceptance/hil_runbook.md`
  - 脚本说明：`docs/hardware/wave_rover_json_bridge.md`
- Hardware smoke terminal output:
- ROS log path:
- Task record JSON:
- Route debug status JSON:
- Photos/video:

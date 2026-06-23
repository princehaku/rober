# Upper radar default lifecycle

sprint_type: micro

## 实际改动

- `onboard/scripts/upper_robot_api.py`：新增 `DEFAULT_RADAR_START_COMMAND` / `DEFAULT_RADAR_STOP_COMMAND`，CLI 默认值从空 env 改成受管 `o1_lidar_lifecycle.sh` 命令。`ROBER_RADAR_START_COMMAND` / `ROBER_RADAR_STOP_COMMAND` 仍可覆盖。
- `onboard/tests/test_upper_robot_api.py`：新增默认 radar status 与默认 radar start 合同测试，确认未显式传命令时也会走默认 LiDAR-only lifecycle，且 `safe_to_control=false`、`sends_base_motion_commands=false`。
- `docs/hardware/board_sensor_stack_smoke.md`、`docs/product/pc_tools_workstation.md`：同步默认 lifecycle 命令口径。

## 采用资料来源

- `docs/vendor/VENDOR_INDEX.md`：硬件事实入口，确认 WAVE ROVER 底盘 UART 与 LiDAR 串口必须隔离。
- `onboard/scripts/o1_lidar_lifecycle.sh`：受管 LiDAR lifecycle 脚本；默认 `/dev/ttyACM0 @ 150000`，显式拒绝 `/dev/ttyS5`，不发送 `/cmd_vel`、`/api/base/manual` 或 WAVE ROVER `T=1/T=13/T=130/T=131`。
- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`：LiDAR driver 启动字节 `A5 60`、停止字节 `A5 00 A5 65 A5 65`，默认 `/dev/ttyACM0 @ 150000`。
- `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`：LiDAR launch 参数默认 `/dev/ttyACM0 @ 150000`，LiDAR 默认关闭，现场显式启用。

## 验证结果

- `python3 -m unittest onboard.tests.test_upper_robot_api -k radar`：通过，14 个 radar 相关测试。
- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py`：通过。
- `python3 -m unittest onboard.tests.test_upper_robot_api`：通过，38 个测试。
- `git diff --check`：通过。
- 上位机部署：已上传 `onboard/scripts/upper_robot_api.py` 到 `root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py`，原文件备份为 `/root/rober/onboard/scripts/upper_robot_api.py.bak_codex_20260623_133149`，并用原参数重启 `upper_robot_api.py`，新 PID 为 `65398`。
- 上位机只读确认 `/api/radar/status`：`controls.start.command.configured=true`、`mode=command`、argv 为 `bash /root/rober/onboard/scripts/o1_lidar_lifecycle.sh start --serial-port /dev/ttyACM0 --serial-baudrate 150000 --frame-id laser_frame`；`lifecycle_running=false`、`continuous_scan_status=lifecycle_not_running`、`sends_motion_commands=false`、`calls_base_manual=false`、`publishes_cmd_vel=false`、`safe_to_control=false`、`delivery_success=false`。
- 上位机只读确认 `/api/base/status`：`/dev/ttyS5 @ 115200` 可读，`T1001=true`，13 帧，`latest_L=0.0`、`latest_R=0.0`、`nonzero_frames=0`、`wheel_feedback_lr_nonzero_proven=false`、`sends_motion_commands=false`。

## 剩余风险

- 本轮已部署上位机默认 radar lifecycle 命令，但尚未执行 `/api/radar/start`，也未启动 LiDAR、Nav2、manual、keyboard pulse、stop、delivery complete 或 `/cmd_vel`。
- 真实收口仍未完成：LiDAR lifecycle 仍 stopped，wheel L/R 仍为 `0/0`，delivery success 仍未确认。

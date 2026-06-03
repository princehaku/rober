# O1 LiDAR Runtime Bootstrap Micro Sprint

## sprint_type

sprint_type: micro

## 实际改动

- `onboard/scripts/o1_upper_computer_readiness_probe.py`
  - 新增 `lidar_ros2_bootstrap`，把 LiDAR ROS2 `/scan` 前置条件拆成 `runtime_missing`、`repo_missing`、`install_missing`、`driver_missing`、`lidar_device_missing`、`ready_for_scan_bootstrap`。
  - 新增 `ros2_runtime_remediation_plan`，输出 `docker_arm64_unavailable`、`topics_not_running` 等更细 blocker 和下一条可执行动作。
  - 所有新增检查只运行本地只读命令或路径检查；不打开串口、不启动 ROS2 driver、不发送 `A5 60`、不发送 WAVE ROVER `T=1/T=13/T=130/T=131`、不调用 `/api/base/manual`、不发布 `/cmd_vel`。
- `onboard/scripts/test_o1_upper_computer_readiness_probe.py`
  - 覆盖新增 bootstrap 分类、fail-closed 安全字段、ready 命令不含底盘控制入口。
- `docs/hardware/o1_upper_computer_readiness_probe.md`
  - 记录新增字段 contract、vendor 来源和本轮 bootstrap 分类边界。
- `docs/interfaces/lidar_ros2_closed_loop.md`
  - 补充 runtime/bootstrap status 的 evidence boundary。
- `OKR.md`、`docs/process/okr_progress_log.md`
  - 记录本轮 O1 进展，O1 百分比不调整。

## 验证结果

本地验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_upper_computer_readiness_probe.py
# Ran 6 tests in 0.752s
# OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py
# Ran 9 tests in 3.066s
# OK

python3 -m py_compile onboard/scripts/o1_upper_computer_readiness_probe.py onboard/scripts/test_o1_upper_computer_readiness_probe.py
# passed

python3 onboard/scripts/o1_upper_computer_readiness_probe.py --once-json
# boundary.safe_to_control=false
# boundary.sends_commands=false
# boundary.opens_serial_devices=false
# lidar_ros2_bootstrap.status=runtime_missing
# ros2_runtime_remediation_plan.next_action=install_or_provide_ros2_humble_runtime
```

远端只读/no-motion SSH 检查：

```bash
timeout 25 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

摘要：

- host：`op-z3-b6.home`，`aarch64`。
- boundary：`safe_to_control=false`、`sends_commands=false`、`opens_serial_devices=false`、`starts_ros2_control=false`、`robot_control_executed=false`。
- `lidar_ros2_bootstrap.status=runtime_missing`。
- `lidar_ros2_bootstrap.blocker_codes=[runtime_missing, install_missing, driver_missing]`。
- `ros2_runtime_remediation_plan.status=blocked`。
- `ros2_runtime_remediation_plan.primary_blocker=runtime_missing`。
- `ros2_runtime_remediation_plan.next_action=install_or_provide_ros2_humble_runtime`。

未执行动作：

- 未调用 `/api/base/manual`。
- 未发送 WAVE ROVER `T=1/T=13/T=130/T=131`。
- 未发布 `/cmd_vel`。
- 未打开 `/dev/ttyS5` 或 LiDAR 串口。
- 未启动 ROS2 driver。

## 剩余风险

- 真实 ROS2 `/scan`、`/lidar/raw_packet` topic、TF、SLAM/Nav2 消费仍未证明。
- 上位机仍缺 ROS2 Humble runtime、当前 `/root/rober/onboard/install` 和可运行 `lidar_driver` install entrypoint。
- 本轮只是把 blocker 从泛化 runtime 缺口拆成可执行分类，不是 HIL、ACK、`safe_to_control=true`、真实手控或 delivery success。
- 后续要么在 aarch64 上安装/提供 ROS2 Humble runtime 并重建 onboard workspace，要么预置可用 arm64 Humble Docker 镜像，再采集 `/scan` once/hz、`/lidar/raw_packet` 和 TF 证据。

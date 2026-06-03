# 2026.06.03 17-18 O1 LiDAR scan proof artifact tech-done

## sprint_type

micro

## 已读资料与 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/README.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/launch/lidar.launch.py`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`

已采用硬件事实：

- 当前 LiDAR source-of-truth 是 `docs/vendor/lidar_pkg_ros2-main/` ROS2 Humble snapshot。
- 参考 LiDAR 串口波特率是 `150000`。
- 参考 driver 启动字节是 `A5 60`，退出停止序列是 `A5 00 A5 65 A5 65`。
- 数据包同步头是 `0xAA 0x55`。
- 目标 ROS2 topic 是 `/scan`，raw packet topic 是 `/lidar/raw_packet`。
- vendor udev 目标是 `/dev/lidar`；当前现场观察候选是 `/dev/ttyACM0` 与 STC by-id。

## 实际改动

- `onboard/scripts/o1_lidar_scan_proof_collector.py`
  - 新增 O1 LiDAR `/scan` proof collector。
  - 默认只读 ROS2 setup/install、LiDAR 设备候选、8787 `/health` 与 `/api/radar/status`。
  - 支持 `--output` 原子写入 `trashbot.o1.lidar_scan_proof.v1` artifact。
  - 支持 `--expect-existing-topics` 在 ROS2 runtime ready 后只读观察 `/scan`、`/lidar/raw_packet` 和 `/scan` hz。
  - 固定 fail-closed：不启动 LiDAR driver，不发送 `A5 60`，不打开 LiDAR 串口，不发送 `T=1/T=13/T=130/T=131` 或 `/cmd_vel`。
- `onboard/scripts/test_o1_lidar_scan_proof_collector.py`
  - 覆盖 blocker 输出、默认不读 topic、runtime blocker 下不运行 `ros2 topic`、topic read-only 模式、artifact 原子写入。
- `onboard/scripts/upper_robot_api.py`
  - 新增 `ROBER_LIDAR_SCAN_PROOF_ARTIFACT_PATH` / `--lidar-scan-proof-artifact-path`。
  - 新增只读 `GET /api/radar/scan-proof/latest`。
  - `GET /api/radar/status` 增加 `scan_proof_latest` 摘要。
  - readback 只做 artifact `read_text/json.loads`，不启动 ROS2、不打开串口、不发送命令。
- `onboard/scripts/test_upper_robot_api.py`
  - 覆盖 LiDAR proof latest missing/loaded/bad-json readback，断言不打开 fake serial、不发送命令。
- `docs/hardware/o1_upper_computer_readiness_probe.md`
  - 补充 LiDAR proof collector 用法、contract 和本轮远端 no-motion 检查结果。
- `docs/hardware/o1_lidar_scan_proof_artifact.md`
  - 新增 LiDAR scan proof artifact/readback contract。
- `docs/interfaces/o7_upper_robot_api.md`
  - 补充 `/api/radar/scan-proof/latest` 和 `radar.scan_proof_latest` 边界。

本轮未更新 `OKR.md`，未提交 git。

## 远端 no-motion 检查结果

执行只读 SSH 检查：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'set -u; ...'
```

关键日志摘要：

- host：`op-z3-b6.home`，Linux `aarch64`。
- `/opt/ros/humble/setup.bash`：不存在。
- `/root/rober/onboard/install/setup.bash`：不存在。
- `ros2`：不可用。
- `/dev/ttyACM0`：存在，`crw-rw---- root dialout`。
- `/dev/lidar`：不存在。
- `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> ../../ttyACM0`：存在。
- 8787 `/health`：`status=ready`。
- 8787 `/api/radar/status`：`scan_status=not_proven`，`observed_lidar_port=/dev/ttyACM0`，`baudrate=150000`。
- `trashbot-upper-robot-api.service`：`active`，启动命令含 `--base-port /dev/ttyS5 --base-baudrate 115200`。

因为 ROS2 runtime/install 缺失，本轮未启动 LiDAR driver，未执行 `ros2 topic echo`，未采到真实 `/scan` 或 `/lidar/raw_packet`。

远端运行 no-motion collector：

```bash
ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json --output /tmp/o1_lidar_scan_proof_latest.json --timeout-s 3' < onboard/scripts/o1_lidar_scan_proof_collector.py
```

关键日志摘要：

- artifact 写入 `/tmp/o1_lidar_scan_proof_latest.json`，`bytes_written=7217`，`method=atomic_replace`。
- `proof.status=blocked_or_not_observed`。
- `proof.scan_once_observed=false`。
- `proof.raw_packet_once_observed=false`。
- `proof.driver_started_by_collector=false`。
- `proof.lidar_start_command_sent_by_collector=false`。
- `topic_reads.attempted=false`。
- `blockers=[ros2_humble_setup_missing, rober_install_setup_missing, ros2_command_unavailable, upper_api_scan_not_proven]`。
- `safe_to_control=false`、`sends_commands=false`、`sends_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。

## 本地验证结果

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_o1_lidar_scan_proof_collector.py
```

结果：`Ran 4 tests in 0.420s`，`OK`。

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/scripts/test_upper_robot_api.py
```

结果：`Ran 15 tests in 1.207s`，`OK`。

```bash
python3 -m py_compile onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
```

结果：exit 0，无输出。

```bash
git diff --check -- onboard/scripts/o1_lidar_scan_proof_collector.py onboard/scripts/test_o1_lidar_scan_proof_collector.py onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py docs/hardware/o1_upper_computer_readiness_probe.md docs/hardware/o1_lidar_scan_proof_artifact.md docs/interfaces/o7_upper_robot_api.md sprints/2026.06.03_17-18_o1-lidar-scan-proof-artifact/tech-done.md
```

结果：exit 0，无输出。

## 剩余风险

- 远端仍缺 `/opt/ros/humble/setup.bash` 和 `/root/rober/onboard/install/setup.bash`，真实 ROS2 `/scan` 未证明。
- 本轮没有启动 LiDAR driver，没有发送 `A5 60`，没有执行 topic echo/hz，所以 `/lidar/raw_packet` 也未证明。
- 本轮没有部署更新后的 8787 脚本，远端当前没有 `/api/radar/scan-proof/latest` readback endpoint。
- `/dev/ttyACM0` 与 STC by-id 只能证明当前 LiDAR 候选存在，不证明 topic 连续输出、TF、SLAM/Nav2 消费链路或 150000 长稳。
- 本轮不证明 WAVE ROVER HIL、底盘 ACK、`safe_to_control=true`、真实 `/odom`、`/imu/data`、`/battery`、manual control 或 delivery success。

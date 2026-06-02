# O1 LiDAR ttyACM0 ROS2 接入 Tech Done

## Sprint Type

sprint_type: micro

## Actual Changes

- 将 ROS2 LiDAR 默认串口从历史 `/dev/ttyUSB0` 收敛为现场确认的 `/dev/ttyACM0 @150000`：
  - `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/lidar_driver.py`
  - `onboard/src/ros2_trashbot_bringup/launch/learn.launch.py`
  - `onboard/src/ros2_trashbot_bringup/launch/bringup.launch.py`
- `onboard/scripts/upper_robot_api.py` 的 `/api/radar/status` 返回雷达口、波特率、启动/停止字节和 ROS2 launch 命令；该接口只读，不打开雷达串口，不发送底盘命令。
- 增加静态/单元测试约束：
  - launch 默认必须包含 `lidar_serial_port=/dev/ttyACM0` 和 `lidar_serial_baudrate=150000`。
  - 8787 radar 状态必须公开 `a5 60`、`a5 00 a5 65 a5 65`、`/scan` 和 `/lidar/raw_packet` 合同，同时保持 `sends_commands=false`。
- 文档同步：
  - `docs/interfaces/lidar_ros2_closed_loop.md`
  - `docs/hardware/lidar_ros_reference.md`
  - `docs/interfaces/o7_upper_robot_api.md`
  - `docs/interfaces/o7_realtime_hardware_sources.md`
  - `docs/interfaces/o7_live_operator_panel.md`
- PC 首屏同步：
  - `pc-tools/workstation/src/server/o7LiveOperatorPanel.ts`
  - `pc-tools/workstation/src/server/index.ts`
  - `pc-tools/workstation/src/shared/contracts.ts`
  - `pc-tools/workstation/test/App.test.ts`
  - `pc-tools/workstation/test/catalog.test.ts`
  - `GET /api/o7/live-operator-panel` 现在只读消费 `ROBER_UPPER_API_BASE_URL/api/status`，展示 8787 ready、camera ready、LiDAR `/dev/ttyACM0` 和 base `/dev/ttyS5`，仍保持控制 fail-closed。

## Adopted Sources

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`
- `docs/vendor/lidar_pkg_ros2-main/config/lidar_params.yaml`
- `docs/vendor/lidar_pkg_ros2-main/scripts/99-lidar.rules`
- CEO 现场手动 smoke：`/dev/ttyACM0`、`150000`、`A5 60` 启动，退出发送 `A5 00 A5 65 A5 65`。

## Verification

本地软件验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'
# Ran 11 tests in 0.001s
# OK

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'
# Ran 11 tests in 0.085s
# OK

PYTHONDONTWRITEBYTECODE=1 python3 onboard/scripts/test_upper_robot_api.py
# Ran 5 tests in 0.803s
# OK

python3 -m compileall -q onboard/src/ros2_trashbot_hardware onboard/src/ros2_trashbot_bringup onboard/scripts/upper_robot_api.py onboard/scripts/test_upper_robot_api.py
# passed, no output

cd pc-tools/workstation && npm run test -- test/App.test.ts
# Test Files 1 passed (1)
# Tests 6 passed (6)

cd pc-tools/workstation && npx vitest run test/catalog.test.ts -t "O7 live operator panel"
# Test Files 1 passed (1)
# Tests 1 passed, 62 skipped

cd pc-tools/workstation && npm run build
# tsc + vite build passed
```

上位机部署与只读验证：

```bash
scp -P 37878 onboard/scripts/upper_robot_api.py root@192.168.1.11:/root/rober/onboard/scripts/upper_robot_api.py
ssh -p 37878 root@192.168.1.11 'ls -l /dev/ttyACM0 /dev/lidar 2>/dev/null || true; lsmod | grep -E "ch341|cp210x|ftdi_sio|pl2303|cdc_acm" || true'
```

关键结果：

- `/dev/ttyACM0` exists，权限 `crw-rw---- root:dialout`。
- 已加载 `pl2303`、`ftdi_sio`、`cp210x`、`ch341`、`cdc_acm`。

8787 服务修正：

```bash
ssh -p 37878 root@192.168.1.11 'systemctl stop trashbot-upper-robot-api.service || true; for pid in $(ss -ltnp | sed -n "s/.*:8787.*pid=\\([0-9][0-9]*\\).*/\\1/p" | sort -u); do kill "$pid"; done; sleep 0.5; systemctl start trashbot-upper-robot-api.service'
curl -fsS http://192.168.1.11:8787/api/radar/status
curl -fsS http://192.168.1.11:8787/api/status
```

关键结果：

- `trashbot-upper-robot-api.service` active/running，MainPID 为 `25470`。
- `0.0.0.0:8787` 由 `python3 pid=25470` 监听；旧占端口进程已清理。
- `/api/radar/status` 返回：
  - `observed_lidar_port="/dev/ttyACM0"`
  - `baudrate=150000`
  - `start_command_hex="a5 60"`
  - `stop_command_hex="a5 00 a5 65 a5 65"`
  - `ros2.driver="ros2_trashbot_hardware lidar_driver"`
  - `ros2.scan_topic="/scan"`
  - `ros2.raw_packet_topic="/lidar/raw_packet"`
  - `scan_status="not_proven"`
- `/api/status` 同时返回 camera ready、base `/dev/ttyS5 @115200` 和 radar `/dev/ttyACM0 @150000`。

PC 本机验证：

```bash
TMPDIR=/tmp ROBER_UPPER_API_BASE_URL=http://192.168.1.11:8787 npm run dev -- --host 127.0.0.1 --port 5173
curl -fsS http://127.0.0.1:5173/api/o7/live-operator-panel
curl -fsS http://127.0.0.1:5173/api/o7/local-webrtc-camera
```

关键结果：

- 本机 `http://127.0.0.1:5173/` dev server ready。
- `live-operator-panel.ssh.workstation_api_8787_status="ready"`。
- `live-operator-panel.lidar_radar.dev_lidar="/dev/ttyACM0"`。
- `live-operator-panel.lidar_radar.stc_by_id="resolved_to_ttyACM0"`。
- `live-operator-panel.camera.health_status="ready"`。
- `live-operator-panel.control.base_boundary.observed_write_device="/dev/ttyS5"`。
- `local-webrtc-camera.base_url="http://192.168.1.11:8787"`，说明 PC 已通过统一 API 读取 camera proxy。

## Remaining Risks

- 当前改动证明 ROS2 driver/launch/API 合同已对齐 `/dev/ttyACM0`，但还没有在上位机运行 ROS2 并采到真实 `/scan`。
- `/dev/lidar` udev 稳定命名仍需安装/验证；现在默认先使用现场确认的 `/dev/ttyACM0`。
- `laser_frame -> base_link` 安装位姿、角度方向、点云质量、SLAM/Nav2 消费链路和 `150000` 长时间稳定性仍未验收。

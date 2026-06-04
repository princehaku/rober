# LiDAR ROS2 Closed-loop Interface

## Package Ownership

- Driver executable: `ros2_trashbot_hardware lidar_driver`
- Parser module: `ros2_trashbot_hardware.lidar_packets`
- Launch owners: `ros2_trashbot_bringup/launch/bringup.launch.py` and `ros2_trashbot_bringup/launch/learn.launch.py`

LiDAR 当前作为传感器硬件接入和串口 reader 管理，因此 driver/parser 归属
`ros2_trashbot_hardware`。`ros2_trashbot_nav` 后续只消费 `/scan`、TF 和
SLAM/Nav2 结果，不放置重复 LiDAR driver 或 packet parser。

当前 ROS2/STC vendor 来源是 `docs/vendor/lidar_pkg_ros2-main/`。历史
`docs/vendor/lidar_ros/` 保留为 ROS1/protocol reference，用于对比老 packet
parser 和 topic 形态，不作为当前 ROS2 driver source of truth。

## Launch Contract

- `bringup.launch.py` 和 `learn.launch.py` 通过 `lidar_enabled` gate 启动 LiDAR，默认 `false`。
- `lidar_enabled:=true` 时启动 `ros2_trashbot_hardware/lidar_driver`。
- `lidar_enabled:=true` 时同步启动 `tf2_ros/static_transform_publisher`，提供 `base_link -> laser_frame` 占位 TF。
- `lidar_serial_port`、`lidar_serial_baudrate`、`lidar_frame_id`、`lidar_scan_topic`、`lidar_raw_packet_topic`、`lidar_publish_raw_packets`、range 和 timing 参数保持 launch 可配置。
- `learn.launch.py` 的参数名与 `bringup.launch.py` 对齐，真机建图 smoke 可以直接复用同一套 LiDAR/TF CLI 覆盖参数。
- `learn.launch.py` 只在显式 `lidar_enabled:=true` 时暴露 `/scan` 和 `laser_frame`，避免无雷达或未测 TF 时让 SLAM 学习阶段误消费占位输入。

## Driver Runtime Contract

- `mock_scan=true`：使用内置 mock packet 发布 `/scan`，不打开串口，不发送 LiDAR 启动命令。
- `mock_packets` 非空：按 `|` 分隔的 hex packet 回放 `/scan`，不打开串口，不发送 LiDAR 启动命令。
- `mock_scan=false` 且 `mock_packets` 为空：进入真实串口模式，打开 `serial_port`、`serial_baudrate`，发送 `A5 60` 启动命令，然后读取 bytes，经 `find_packets` 和 `scan_dict_from_packet` 转为 `sensor_msgs/msg/LaserScan`；若启动命令写入失败，driver 会先关闭刚打开的句柄再抛出错误。
- `publish_raw_packets=true`：每个完整 packet 同步发布到 `raw_packet_topic`，类型为 `std_msgs/msg/UInt8MultiArray`，用于真机 bringup 时保留 parser 前的原始证据。
- 节点销毁时会 best-effort 写入 `A5 00 A5 65 A5 65` 并关闭串口；停止写入失败不能阻止 close，该动作也不能替代真实电机停转观察。
- 用户手动 Python 串口测试已确认 `/dev/ttyACM0`、`150000` baud、`A5 60` 可启动 STC USB Serial LiDAR 电机；因此项目 ROS2 LiDAR driver 和 `bringup`/`learn` launch 的默认 `lidar_serial_port` 已改为 `/dev/ttyACM0`。稳定部署时仍建议安装 vendor udev 规则，把 STC `34bf:ff0a` 映射为 `/dev/lidar`，然后显式传入 `lidar_serial_port:=/dev/lidar`。

## Orange Pi Direct Bringup

在上位机上，雷达 USB 串口应先确认内核驱动和设备节点。CEO 本轮提供的现场入口如下：

```bash
modprobe ch341
modprobe cp210x
modprobe ftdi_sio
modprobe pl2303
modprobe cdc_acm
```

当前已确认雷达设备是 `/dev/ttyACM0`，串口参数和启动/停止字节来自 `docs/vendor/lidar_pkg_ros2-main/src/lidar_node.cpp`：

```bash
source /opt/ros/humble/setup.bash
source /root/rober/onboard/install/setup.bash
ros2 launch ros2_trashbot_bringup learn.launch.py \
  lidar_enabled:=true \
  lidar_serial_port:=/dev/ttyACM0 \
  lidar_serial_baudrate:=150000 \
  lidar_frame_id:=laser_frame \
  lidar_publish_raw_packets:=true
```

等价手动串口 smoke 只用于验证电机和原始 bytes，不替代 ROS2 验收：

```bash
python3 - <<'PY'
import serial, time

ser = serial.Serial("/dev/ttyACM0", 150000, timeout=1)
ser.write(bytes([0xA5, 0x60]))
ser.flush()
time.sleep(1)
print(ser.read(64).hex(" "))
ser.write(bytes([0xA5, 0x00, 0xA5, 0x65, 0xA5, 0x65]))
ser.flush()
ser.close()
PY
```

### 2026-06-03 Raw Packet Evidence

Hardware Infra Engineer 在上位机 `ssh root@192.168.1.11 -p 37878` 做了真实
LiDAR 原始串口 smoke：`/dev/ttyACM0 @150000` 可打开，写入 vendor 启动命令
`a5 60` 后 3 秒读到 `4246` bytes，其中 `0xaa55` sync header 数量为 `127`，
退出时发送停止序列 `a5 00 a5 65 a5 65`。

该结果证明 LiDAR 原始串口数据真实可读，但仍不等于 ROS2 `/scan` 已通过。
本轮 ROS2 smoke 被上位机环境阻塞：host 缺 `/opt/ros/humble/setup.bash`，`ros2`
command 不存在，`/root/rober/onboard/install` 不存在；远端 repo 仍是旧
`setup.py`，没有 `lidar_driver` entry point；临时 Docker 路径先遇到
`amd64` 镜像在 Orange Pi `arm64` 上 `exec format error`，随后拉取 arm64 ROS
base 镜像超时。

### 2026-06-04 ROS2 Scan Smoke Evidence

Hardware Infra Engineer 继续通过 `ssh root@192.168.1.11 -p 37878` 推进 O1：
远端 apt/dpkg/locales 已自然结束，ROS2 Humble runtime 已可用；同步当前
`onboard/src` 与 `onboard/scripts` 后，执行：

```bash
bash /root/rober/onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh --skip-apt-install
```

结果为 `Summary: 6 packages finished [2min 8s]`，并确认：

```text
/opt/ros/humble/setup.bash: exists
/root/rober/onboard/install/setup.bash: exists
ros2=/opt/ros/humble/bin/ros2
```

随后执行 LiDAR-only smoke：

```bash
bash /root/rober/onboard/scripts/o1_lidar_ros2_scan_smoke.sh \
  --serial-port /dev/ttyACM0 \
  --serial-baudrate 150000 \
  --frame-id laser_frame \
  --output-dir /tmp/o1_lidar_ros2_scan_smoke
```

`/tmp/o1_lidar_ros2_scan_smoke/summary.json` 摘要：

```json
{
  "scan_once_observed": true,
  "scan_hz_observed": true,
  "raw_packet_once_observed": true,
  "tf_observed": true,
  "safe_to_control": false,
  "sends_base_motion_commands": false,
  "calls_base_manual": false,
  "publishes_cmd_vel": false
}
```

证据片段：

- `/scan` once 输出 `frame_id=laser_frame`、`range_min=0.05`、`range_max=8.0`
  和真实 `ranges` 数值。
- `/scan` hz 输出 `average rate`，观察窗口约 `295-300 Hz`。
- `/lidar/raw_packet` once 的 `data` 以 `170, 85` 开头，即 `0xAA,0x55`。
- `tf2_echo base_link laser_frame` 输出零位姿静态 TF。
- topic list 包含 `/scan`、`/lidar/raw_packet`、`/tf_static`。

安全边界：该 smoke 只向 LiDAR 串口发送 `A5 60` 和退出停止序列；未写
`/dev/ttyS5`，未调用 `/api/base/manual`，未发送 WAVE ROVER
`T=1/T=13/T=130/T=131`，未发布 `/cmd_vel`。

已知 caveat：smoke 退出阶段 `lidar_driver.log` 出现 ROS context shutdown error。
该错误发生在 `/scan`、raw packet 和 TF evidence 已采集之后；它不撤销本轮
topic 观察，但说明 driver 优雅退出仍需单独修复或复验。

## Evidence Boundary

- Vendor source: `docs/vendor/VENDOR_INDEX.md`, `docs/vendor/lidar_pkg_ros2-main/`, and historical comparison snapshot `docs/vendor/lidar_ros/`.
- Current evidence level: `source=software_reference + user_manual_serial_observed_start + upper_api_observed_lidar_port + raw_serial_packet_observed + ros2_scan_smoke_observed`.
- Hardware status: real raw bytes and `0xaa55` packet sync headers are observed on `/dev/ttyACM0 @150000`; first ROS2 `/scan` once/hz, `/lidar/raw_packet` once, and static TF smoke are observed on the upper computer.
- Still not proven: Nav2/SLAM consumption, mapping quality, long-run `150000` stability, physical LiDAR motor stop observation, production udev `/dev/lidar`, WAVE ROVER HIL, ACK, `/odom`, `/imu/data`, `/battery`, and `safe_to_control=true`.
- Mock status: `lidar_mock_scan` and `lidar_mock_packets` can prove software conversion and no-serial safety only; they are not HIL and cannot be marked `source=hil_pass`.
- Runtime/bootstrap status: `onboard/scripts/o1_upper_computer_readiness_probe.py`
  现在输出 `lidar_ros2_bootstrap.status`，用于区分 `runtime_missing`、
  `repo_missing`、`install_missing`、`driver_missing`、`lidar_device_missing`
  和 `ready_for_scan_bootstrap`。该字段只证明前置条件分类更细，不证明真实
  `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2、HIL 或 `safe_to_control=true`。
- `ready_for_scan_bootstrap` 只表示可以进入只读 topic proof 或由现场人员手动启动
  LiDAR driver；probe 本身仍固定 `opens_serial_devices=false`、`starts_ros2_driver=false`、
  `publishes_cmd_vel=false`、`calls_base_manual=false`，且不发送 WAVE ROVER
  `T=1/T=13/T=130/T=131`。
- `o1_lidar_scan_proof_collector.py --expect-existing-topics` 的 ROS2 CLI readiness
  只使用 `command -v ros2 && ros2 --help`；不能使用 `ros2 --version`，因为 Humble
  目标机上该参数会返回非零并造成 `ros2_command_unavailable` false blocker。该修复
  只允许 collector 继续做只读 topic/TF readback，不会启动 driver、打开 LiDAR 串口、
  写 `/dev/ttyS5`、调用 `/api/base/manual` 或发布 `/cmd_vel`。
- 2026-06-05 API-managed runtime hook 复核口径：`GET /api/radar/scan-proof/latest` 只能回放
  `runtime/lidar_scan_proof_latest.json`，不得启动 driver、打开 `/dev/ttyS5`、发送
  WAVE ROVER `T=1/T=13/T=130/T=131` 或发布 `/cmd_vel`。`POST
  /api/radar/scan-proof/refresh` 默认仍只运行同目录只读
  `o1_lidar_scan_proof_collector.py --expect-existing-topics --output
  runtime/lidar_scan_proof_latest.json`，用于刷新 artifact、`command_result` 和
  `blockers_summary`；默认不启动 LiDAR driver、不打开 `/dev/ttyACM0` 或
  `/dev/lidar`、不发送 `A5 60`。只有显式配置
  `ROBER_LIDAR_SCAN_PROOF_RUNTIME_COMMAND` 为
  `o1_lidar_ros2_scan_smoke.sh` 时，refresh 可先启动 LiDAR-only runtime，再读取
  `/scan`、`/lidar/raw_packet` 和 `base_link -> laser_frame` TF；该 runtime 只允许
  LiDAR 串口 `/dev/lidar`、`/dev/ttyACM*` 或 STC `/dev/serial/by-*` 路径，并必须拒绝
  `/dev/ttyS5`、`/api/base/manual`、`/cmd_vel`、WAVE ROVER
  `T=1/T=13/T=130/T=131` 和 shell 控制符。响应固定保留
  `safe_to_control=false`、`sends_motion_commands=false`、
  `sends_base_motion_commands=false`、`robot_control_executed=false`。refresh/readback
  即使观察到 `/scan` 或 `/lidar/raw_packet`，也不能外推为 WAVE ROVER ACK、HIL、
  Nav2/SLAM 可消费、`safe_to_control=true` 或 delivery success。
- `onboard/scripts/o1_ros2_humble_arm64_bootstrap.sh` 是当前上位机 runtime/build
  remediation 入口：只安装 ROS2 Humble arm64 runtime 并构建 onboard，不启动
  driver、不打开串口、不写底盘 UART。
- `onboard/scripts/o1_lidar_ros2_scan_smoke.sh` 是 runtime 就绪后的 LiDAR-only
  证据入口：只允许 LiDAR 串口，显式拒绝 `/dev/ttyS5`，采集 `/scan` once/hz、
  `/lidar/raw_packet` once 和 `tf2_echo base_link laser_frame`。该脚本会让 LiDAR
  driver 向 LiDAR 串口发送 `A5 60` 和退出停止序列，但不发送任何 WAVE ROVER
  底盘命令，不发布 `/cmd_vel`，不调用 `/api/base/manual`。

## Verification Commands

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_lidar*.py'
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_hardware/test/test_o1_wave_rover_serial_feedback_probe.py
python3 -m compileall -q onboard/src/ros2_trashbot_hardware onboard/scripts/o1_wave_rover_serial_feedback_probe.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_bringup/test -p 'test_launch_contract_static.py'
PYTHONDONTWRITEBYTECODE=1 python3 onboard/scripts/test_upper_robot_api.py
```

真机建图 smoke 的推荐入口：

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py lidar_enabled:=true lidar_serial_port:=/dev/ttyACM0 lidar_serial_baudrate:=150000 lidar_frame_id:=laser_frame lidar_publish_raw_packets:=true
```

2026-06-04 已补到首个 LiDAR-only ROS2 smoke：`ros2 topic echo --once /scan`、
`ros2 topic hz /scan`、`ros2 topic echo --once /lidar/raw_packet` 和
`tf2_echo base_link laser_frame` 均观察到输出。真实上车前仍必须补充长稳运行、
生产 udev `/dev/lidar`、SLAM/Nav2 订阅和建图质量证据。Robot Software 静态验证
只能证明 launch contract 可复用，不能声明完整建图或导航已通过。

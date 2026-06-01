# O1 LiDAR Upper Runtime Readiness Micro Sprint

## sprint_type

micro

## 实际改动

- 更新 `onboard/scripts/o1_upper_computer_readiness_probe.py`：
  - 新增 `lidar_runtime_readiness` 机器可读 gate。
  - gate 只根据 ROS2 Humble setup、pyserial、rober workspace、LiDAR 串口候选判断是否允许进入 no-motion LiDAR smoke。
  - 缺条件时输出 `blocked_by_readiness` 与 blocker code；满足条件时只给出 LiDAR driver、`/scan`、`/lidar/raw_packet` 观察命令。
  - 固定声明 `sends_base_motion_commands=false`、`sends_cmd_vel=false`、`writes_wave_rover_uart=false`，避免把 LiDAR smoke 误解成底盘控制许可。
- 更新 `onboard/src/ros2_trashbot_hardware/test/test_o1_upper_computer_readiness_probe.py`：
  - 覆盖缺 ROS2/pyserial/workspace/候选串口时必须 blocked。
  - 覆盖条件齐备时也只能进入 no-motion LiDAR smoke，不能包含 WAVE ROVER 底盘运动或 `/cmd_vel`。
- 更新 `docs/hardware/o1_upper_computer_readiness_probe.md`：
  - 修正 SSH stdin 命令示例为 `python3 -s - --once-json`。
  - 记录本轮远端 SSH `No route to host`，明确没有新的远端 JSON artifact。
  - 写入下一轮 SSH 恢复后的最小 runbook。
- 更新 `docs/hardware/lidar_ros_reference.md`：
  - 增补 `lidar_runtime_readiness` gate 作为真实 `/scan` 前置检查。
  - 记录本轮未进入上位机、未采到真实 `/scan` 或 LiDAR runtime 证据。

## 验证结果

远端只读 readiness probe：

```bash
timeout 20 ssh -o BatchMode=yes -o ConnectTimeout=8 -p 37878 root@192.168.1.11 'python3 -s - --once-json' < onboard/scripts/o1_upper_computer_readiness_probe.py
```

结果：

```text
ssh: connect to host 192.168.1.11 port 37878: No route to host
```

本地 target test 已运行一次：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p 'test_o1_upper_computer_readiness_probe.py'
```

结果：

```text
Ran 9 tests in 0.250s
OK
```

## 失败定位

- SSH 在网络层不可达，错误为 `No route to host`。
- 因为未进入上位机，本轮无法确认当前小时的 ROS2 Humble runtime、workspace、pyserial、LiDAR 串口候选，也无法运行 LiDAR driver。
- 该失败不是 ROS2 driver、pyserial 或 LiDAR parser 的运行时失败；根因当前定位在访问 `192.168.1.11:37878` 的网络路径不可达。

## 是否采到真实 ROS2 /scan 或 LiDAR runtime 证据

没有。

本轮没有进入上位机，没有启动 ROS2 LiDAR driver，没有打开 LiDAR 串口，没有采到真实 `/scan`，也没有采到 `/lidar/raw_packet`。本轮新增的是 readiness/runbook 护栏，便于下一轮 SSH 恢复后直接判断缺哪个条件。

## 剩余风险

- 真实 ROS2 Humble runtime 仍未确认。
- 真实 rober onboard workspace / install setup 仍未确认。
- 真实 pyserial 可用性仍未确认。
- 真实 LiDAR USB path、`/dev/lidar` udev、STC by-id 路径、`150000` 稳定性仍未确认。
- 真实 ROS2 `/scan`、`/lidar/raw_packet`、TF、SLAM/Nav2 消费链路仍为 `not_proven`。
- 本轮未触碰 WAVE ROVER feedback probe 文件，未改运动控制默认值，未发送任何底盘运动命令。

## 协同需求

- Product：暂不需要，任务边界清楚且 O1 当前最低优先级未改变。
- Hardware：需要现场确认上位机网络/供电/SSH 可达性，以及 LiDAR 真实 USB 路径或 udev 映射。
- Autonomy：暂不需要；待 `/scan` 可采后再联动 TF、SLAM/Nav2 消费验证。
- Full-Stack：暂不需要。

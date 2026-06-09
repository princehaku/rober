# ROS2 Motion Mainline Smoke Tech Plan

## 目标

用真实上位机验证 ROS2 `/cmd_vel` 到 WAVE ROVER ESP32 UART 的最小运动主链路。优先产出可复核证据，不在本轮改动产品代码。

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低的活跃 Objective 是 O7 `~12%`，其次 O6 `~30%`。本 sprint 不直接针对最低 O7，而是针对 O1 真实硬件协议可信底盘。

理由：CEO 本轮明确要求“雷达、摄像头、建图、运动，都走一圈”。上一轮已经给 O7/O6 提供 no-motion route/keyframe/map 输入；当前最大缺口是 ROS2 运动主链路没有真实上车 smoke。如果不先证明 `/cmd_vel` 和底盘串口可控，O7 的手控/寻路与真实路线回放后续也无法闭环。

## 文件范围

允许改动：

- `sprints/2026.06.10_00-35_ros2-motion-mainline-smoke/**`

默认不改动产品代码。如必须修复 ROS2 bridge 或 launch 问题，硬件 agent 需先在输出中说明根因，再由主节点派 `robot-software-engineer` 接手代码修复。

## 远端执行计划

目标主机：

```bash
ssh root@192.168.1.11 -p 37878
```

### 1. 基线记录

在真实上位机记录：

```bash
date
hostname
ps -ef | grep -E 'upper_robot_api|esp32_bridge|bringup.launch|ros2' | grep -v grep || true
curl -sS http://127.0.0.1:8787/api/base/status || true
fuser -v /dev/ttyS5 || true
ls -l /dev/ttyS5
```

### 2. 释放底盘串口

只停止 `upper_robot_api.py`，保留原 command line：

```bash
ps -ef | grep '[u]pper_robot_api.py'
kill <upper_robot_api_pid>
sleep 1
fuser -v /dev/ttyS5 || true
```

如未能释放，禁止继续发布 `/cmd_vel`，必须记录失败并恢复 API。

### 3. 启动 ROS2 base-only bringup

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 launch ros2_trashbot_bringup bringup.launch.py \
  base_enabled:=true \
  serial_port:=/dev/ttyS5 \
  serial_baudrate:=115200 \
  command_mode:=speed \
  lidar_enabled:=false \
  camera_enabled:=false \
  operator_gateway:=false \
  remote_bridge:=false
```

### 4. Topic/service smoke

```bash
ros2 node list
ros2 topic info /cmd_vel
ros2 topic echo /odom --once
timeout 5 ros2 topic echo /battery --once || true
timeout 5 ros2 topic echo /imu/data --once || true
ros2 service list | grep /trashbot/stop
```

### 5. 低速短脉冲

低速命令：

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.03, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
sleep 0.3
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}"
ros2 topic echo /odom --once
```

### 6. 收尾恢复

```bash
ros2 topic pub --once /cmd_vel geometry_msgs/msg/Twist \
  "{linear: {x: 0.0, y: 0.0, z: 0.0}, angular: {x: 0.0, y: 0.0, z: 0.0}}"
ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" || true
```

停止 launch 后恢复 API：

```bash
nohup python3 /root/rober/onboard/scripts/upper_robot_api.py \
  --host 0.0.0.0 \
  --port 8787 \
  --camera-base-url http://127.0.0.1:8088 \
  --base-port /dev/ttyS5 \
  --base-baudrate 115200 \
  --max-speed 0.12 \
  >/tmp/upper_robot_api_restore.log 2>&1 &
sleep 2
curl -sS http://127.0.0.1:8787/api/base/status
fuser -v /dev/ttyS5 || true
```

## 本地 artifact

硬件 agent 必须把证据写入：

- `sprints/2026.06.10_00-35_ros2-motion-mainline-smoke/artifacts/ros2_motion_mainline_smoke.md`
- 如有日志，放入 `sprints/2026.06.10_00-35_ros2-motion-mainline-smoke/artifacts/`

## 验证命令

子 agent 必须执行并记录结果：

```bash
ssh root@192.168.1.11 -p 37878 'true'
ssh root@192.168.1.11 -p 37878 'curl -sS http://127.0.0.1:8787/api/base/status || true'
ssh root@192.168.1.11 -p 37878 'source /opt/ros/humble/setup.bash && source /root/rober/onboard/install/setup.bash && ros2 launch ros2_trashbot_bringup bringup.launch.py --show-args'
```

运动 smoke 的实际命令按上方步骤执行，所有输出写入 artifact。

## 完成标准

- `tech-done.md` 写明实际执行步骤、是否运动、topic/service 结果、API 恢复状态。
- `side2side_check.md` 写明本轮与“雷达/摄像头/建图/运动都走一圈”的差距。
- `final.md` 写明 OKR 影响、剩余风险和下一轮动作。

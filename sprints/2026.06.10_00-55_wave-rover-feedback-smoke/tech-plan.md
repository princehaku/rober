# WAVE ROVER Feedback Smoke Tech Plan

## 目标

补齐真实上车 evidence capture 中最弱的一环：WAVE ROVER `T=1001` 新鲜 feedback。先做 raw UART，再做 ROS2 topic。

## OKR 最低优先级核对

`OKR.md` 4.1 当前最低活跃 Objective 是 O7 `~12%`，其次 O6 `~30%`。本 sprint 仍然先补 O1 feedback，因为 O7 的手控、状态展示和历史回放需要可信底盘状态作为数据源。上一轮 integrated capture 已给 O7 提供 route/map/keyframe；本轮补 feedback 能提升整包证据可信度。

## 文件范围

允许改动：

- `sprints/2026.06.10_00-55_wave-rover-feedback-smoke/**`

禁止改动产品代码、launch、driver、API 脚本。若 raw feedback 和 ROS topic 证据显示需要修代码，硬件 agent 只记录根因。

## 远端执行设计

目标主机：

```bash
ssh root@192.168.1.11 -p 37878
```

### 1. 基线

```bash
date
hostname
ps -ef | grep -E 'upper_robot_api|esp32_bridge|ros2' | grep -v grep || true
curl -sS http://127.0.0.1:8787/api/base/status || true
fuser -v /dev/ttyS5 || true
ls -l /dev/ttyS5
```

### 2. 停 API 释放串口

```bash
ps -ef | grep '[u]pper_robot_api.py'
kill <upper_robot_api_pid>
sleep 1
fuser -v /dev/ttyS5 || true
```

### 3. raw UART feedback probe

在远端临时执行 Python，不修改产品文件：

```python
import json
import serial
import time

port = "/dev/ttyS5"
baudrate = 115200
commands = [
    {"T": 143, "cmd": 0},
    {"T": 142, "cmd": 100},
    {"T": 131, "cmd": 1},
    {"T": 130},
]

with serial.Serial(port, baudrate, timeout=0.2) as ser:
    ser.reset_input_buffer()
    for command in commands:
        frame = (json.dumps(command, separators=(",", ":")) + "\\n").encode("utf-8")
        ser.write(frame)
        print("TX", frame.decode("utf-8").strip(), flush=True)
        time.sleep(0.2)
    deadline = time.time() + 10.0
    while time.time() < deadline:
        line = ser.readline()
        if line:
            print("RX", line.decode("utf-8", errors="replace").strip(), flush=True)
```

把 stdout 保存为：

- `artifacts/raw_feedback_probe.log`

### 4. ROS2 bridge topic probe

仅当 raw probe 有 `T=1001` 时执行；如果 raw 无 `T=1001`，可以跳过 ROS topic probe 或执行并记录空结果。

```bash
cd /root/rober/onboard
source /opt/ros/humble/setup.bash
source install/setup.bash
ros2 run ros2_trashbot_hardware esp32_bridge --ros-args \
  -p serial_port:=/dev/ttyS5 \
  -p serial_baudrate:=115200 \
  -p command_mode:=speed \
  -p feedback_interval_ms:=100
```

另一个 shell 采集：

```bash
timeout 10 ros2 topic echo /battery --once || true
timeout 10 ros2 topic echo /imu/data --once || true
timeout 10 ros2 topic echo /odom --once || true
```

停止 bridge 前调用：

```bash
ros2 service call /trashbot/stop std_srvs/srv/Trigger "{}" || true
```

### 5. 恢复 API

```bash
pkill -f 'ros2_trashbot_hardware.*esp32_bridge|esp32_bridge' || true
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

## 输出文件

硬件 agent 必须写：

- `artifacts/wave_rover_feedback_smoke.md`
- `artifacts/raw_feedback_probe.log`
- 如执行 ROS2 probe：
  - `artifacts/esp32_bridge_feedback.log`
  - `artifacts/battery_once.txt`
  - `artifacts/imu_once.txt`
  - `artifacts/odom_once.txt`
- `tech-done.md`
- `side2side_check.md`
- `final.md`

## 完成标准

`final.md` 必须明确：

- raw UART 是否打开成功。
- 是否有 `T=1001`。
- `T=1001` 是否包含 `L/R/r/p/y/v`。
- ROS2 `/battery` 是否发布。
- ROS2 `/imu/data` 是否发布。
- API 是否恢复。

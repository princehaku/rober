# ros_rbs - Autonomous Trash Collection Robot

ROS2 自主导航扔垃圾小车。**Orange Pi (Ubuntu) + ESP32** 上下位机架构。

## 硬件拓扑

```
┌──────────────────────────────────────────────────────────────────┐
│                     Orange Pi (Ubuntu 22.04)                      │
│  ┌─────────┐  ┌──────────┐  ┌───────────┐  ┌─────────────────┐  │
│  │  Nav2   │  │  SLAM   │  │  Vision   │  │  Behavior Tree  │  │
│  │ 路径规划│  │ Toolbox │  │ cv_bridge │  │  任务编排/状态机  │  │
│  └────┬────┘  └────┬─────┘  └─────┬─────┘  └────────┬────────┘  │
│       └────────────┴──────────────┴─────────────────┘            │
│                          │ /cmd_vel, /odom                        │
│                     ┌────┴─────┐                                  │
│                     │ esp32_   │  ROS2 ↔ 二进制串口协议            │
│                     │ bridge   │  115200 baud /dev/ttyUSB0        │
│                     └────┬─────┘                                  │
└──────────────────────────┼───────────────────────────────────────┘
                           │ UART (TX/RX)
                           │
┌──────────────────────────┼───────────────────────────────────────┐
│                     ESP32 (下位机)                                │
│                     ┌────┴─────┐                                  │
│                     │ main.cpp │                                  │
│                     └────┬─────┘                                  │
│        ┌───────────┬──────┴──────┬───────────────┐                │
│        │           │             │               │                │
│   ┌────┴────┐ ┌────┴────┐  ┌────┴────┐    ┌────┴────┐           │
│   │ 左电机   │ │ 右电机   │  │ 轮式编码  │    │ 超声波x3│           │
│   │ TB6612  │ │ TB6612  │  │ 11PPR   │    │ 前左右   │           │
│   └─────────┘ └─────────┘  └─────────┘    └─────────┘           │
│                                                                   │
│   ┌─────────────────┐  ┌─────────────┐  ┌─────────────┐          │
│   │ IMU (BNO055)   │  │ 蜂鸣器       │  │ 摄像头(USB)  │          │
│   │ 航向角         │  │ 状态提示      │  │ 直连Orange Pi│          │
│   └─────────────────┘  └─────────────┘  └─────────────┘          │
└───────────────────────────────────────────────────────────────────┘
```

## 串口通信协议

ESP32 ↔ Orange Pi 使用二进制协议，115200 baud：

```
[0xAA 0x55] [seq] [type/cmd] [len] [payload...] [checksum]
```

| 方向 | 类型 | 说明 |
|------|------|------|
| ESP32 → Pi | 0x01 ODOM | 里程计 (x, y, theta, enc_l, enc_r) |
| ESP32 → Pi | 0x02 ULTRASONIC | 超声波 (front, left, right) |
| ESP32 → Pi | 0x03 IMU | 航向角 (heading) |
| ESP32 → Pi | 0x04 STATUS | 状态 (state, watchdog, battery) |
| Pi → ESP32 | 0x01 STOP | 停止电机 |
| Pi → ESP32 | 0x02 DRIVE | 直接 PWM (left, right) |
| Pi → ESP32 | 0x03 SET_SPEED | 差速 (linear, angular) |
| Pi → ESP32 | 0x04 BEEP | 蜂鸣器 |
| Pi → ESP32 | 0x06 RESET_ODOM | 重置里程计 |

## 项目结构

```
src/
├── esp32_firmware/                  # ESP32 下位机 (PlatformIO/Arduino)
│   ├── main.cpp                     # 主固件 (电机/编码器/超声波/串口协议)
│   └── platformio.ini               # PlatformIO 配置
├── ros2_trashbot_hardware/          # 硬件桥接 (Orange Pi 侧)
│   └── esp32_bridge.py              # 串口 ↔ ROS2 双向转换
├── ros2_trashbot_interfaces/        # 自定义接口
│   ├── msg/                         # TrashStatus, Waypoint, ...
│   ├── srv/                         # RecordWaypoint, SetTrashBin
│   └── action/                      # TrashCollection, Patrol
├── ros2_trashbot_nav/               # 导航
│   ├── waypoint_manager.py          # 航点管理 + Nav2 集成
│   ├── map_recorder.py              # 地图保存/加载
│   └── nav_to_goal.py               # 简单导航到目标
├── ros2_trashbot_vision/            # 视觉
│   └── trash_detector.py            # 摄像头垃圾检测 (OpenCV)
├── ros2_trashbot_behavior/          # 行为
│   ├── task_orchestrator.py         # 状态机 + Action Server
│   └── trash_collection_server.py   # 收集任务执行
└── ros2_trashbot_bringup/           # 启动
    ├── bringup.launch.py            # 完整启动
    ├── learn.launch.py              # 学习阶段 (SLAM)
    └── autonomous.launch.py         # 自主模式
```

## 快速开始

### 1. Orange Pi 端构建

```bash
sudo apt update && sudo apt install -y python3-serial
source /opt/ros/humble/setup.bash
cd ~/ros_rbs
colcon build --symlink-install
source install/setup.bash
```

### 2. ESP32 端烧录

```bash
cd src/esp32_firmware
pio run --target upload
```

### 3. 连接

将 ESP32 USB 连接到 Orange Pi，确认串口设备：
```bash
ls -l /dev/ttyUSB0   # 或 /dev/ttyACM0
```

### 4. 学习阶段（人工驾驶建图）

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py

# 手动驾驶，系统自动记录航点和地图
# 完成后:
ros2 service call /trashbot/save_map std_srvs/srv/Trigger
```

### 5. 自主模式

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  map_file:=~/.ros/trashbot_maps/trashbot_map.yaml

# 触发巡逻
ros2 action send_goal /trashbot/patrol \
  ros2_trashbot_interfaces/action/Patrol \
  "{use_saved_map: true, learn_mode: false}"
```

## 引脚分配 (ESP32 DevKit)

| 功能 | 引脚 | 备注 |
|------|------|------|
| 左电机 PWM | GPIO25 | TB6612 PWM |
| 左电机 DIR | GPIO26, 27 | TB6612 IN1/IN2 |
| 右电机 PWM | GPIO14 | TB6612 PWM |
| 右电机 DIR | GPIO12, 13 | TB6612 IN1/IN2 |
| 左编码器 A/B | GPIO32, 33 | 中断 |
| 右编码器 A/B | GPIO18, 19 | 中断 |
| 超声波-前 | GPIO4/16 | trig/echo |
| 超声波-左 | GPIO17/5 | trig/echo |
| 超声波-右 | GPIO21/22 | trig/echo |
| 蜂鸣器 | GPIO23 | PWM |
| 状态 LED | GPIO2 | 板载 |

## 安全特性

- **看门狗**: ESP32 500ms 无指令自动停电机
- **前向避障**: 超声波 < 15cm 紧急停止
- **心跳**: esp32_bridge 定期检查串口连通性
- **急停服务**: `ros2 service call /trashbot/stop std_srvs/srv/Trigger`

## 依赖

- **Orange Pi**: Ubuntu 22.04 + ROS2 Humble + Nav2 + SLAM Toolbox
- **ESP32**: PlatformIO + Arduino Framework
- **Python**: pyserial, opencv-python, cv_bridge

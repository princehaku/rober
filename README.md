# ros_rbs - ROS2 自主垃圾收集机器人

面向室内或小区固定路线场景的 ROS2 自主导航扔垃圾小车项目。系统采用 Orange Pi + WAVE ROVER ESP32 上下位机架构：Orange Pi 运行 ROS2 Humble、Nav2、SLAM、视觉检测和任务编排；WAVE ROVER ESP32 负责底盘电机控制和 UART JSON 通信。编码器、超声波、蜂鸣器等能力不得按项目默认硬件假设书写，除非有 `docs/vendor/VENDOR_INDEX.md` 指向的本地资料或上车 HIL 证据支撑。

## 架构

项目由 6 个主要模块组成：

- `ros2_trashbot_interfaces`：自定义 msg、srv、action。
- `ros2_trashbot_hardware`：ESP32 串口桥接，发布里程计和传感器状态，接收速度控制。
- `ros2_trashbot_nav`：Nav2 导航、航点管理、地图保存、固定路线记录与回放。
- `ros2_trashbot_vision`：基于摄像头的垃圾检测，当前为 OpenCV 阈值启发式方案。
- `ros2_trashbot_behavior`：任务编排状态机和垃圾收集 action server。
- `ros2_trashbot_bringup`：学习模式、自主模式和完整系统启动文件。

## 工作流程

1. 学习阶段：启动 SLAM，人工驾驶小车记录地图、路线点和关键帧。
2. 数据整理：将记录的 `route.csv` 转为固定路线 YAML，或直接使用 CSV。
3. 自主阶段：加载地图和路线，按航点巡逻，结合视觉检测和任务状态机执行垃圾收集。
4. 调试阶段：可用 dry-run 和 debug web 验证固定路线与关键帧匹配。

## 构建

```bash
source /opt/ros/humble/setup.bash
colcon build --symlink-install
source install/setup.bash
```

ESP32 固件使用 PlatformIO：

```bash
cd src/esp32_firmware
pio run --target upload
```

## 常用启动

学习建图：

```bash
ros2 launch ros2_trashbot_bringup learn.launch.py
```

自主运行：

```bash
ros2 launch ros2_trashbot_bringup autonomous.launch.py \
  map_file:=~/.ros/trashbot_maps/trashbot_map.yaml
```

发送巡逻任务：

```bash
ros2 action send_goal /trashbot/patrol \
  ros2_trashbot_interfaces/action/Patrol \
  "{use_saved_map: true, learn_mode: false}"
```

## 固定路线数据采集

人工驾驶时记录里程计航点和相机关键帧：

```bash
ros2 run ros2_trashbot_nav route_data_recorder \
  --ros-args \
  -p output_dir:=~/.ros/trashbot_runs/run_001 \
  -p min_distance_m:=0.8 \
  -p route_frame_id:=map
```

输出内容：

- `~/.ros/trashbot_runs/run_001/route.csv`：路线点。
- `~/.ros/trashbot_runs/run_001/keyframes/*.jpg`：关键帧图片。

将 CSV 转为固定路线 YAML：

```bash
ros2 run ros2_trashbot_nav route_csv_to_yaml \
  --ros-args \
  -p input_csv:=~/.ros/trashbot_runs/run_001/route.csv \
  -p output_yaml:=~/.ros/trashbot_maps/fixed_route.yaml
```

运行固定路线节点：

```bash
ros2 run ros2_trashbot_nav fixed_route_autonomy \
  --ros-args \
  -p route_file:=~/.ros/trashbot_runs/run_001/route.csv \
  -p keyframe_dir:=~/.ros/trashbot_runs/run_001/keyframes \
  -p enable_visual_gate:=true \
  -p visual_match_threshold:=25
```

## 本地联调

发布关键帧作为模拟相机输入：

```bash
ros2 run ros2_trashbot_nav keyframe_camera_sim \
  --ros-args -p keyframe_dir:=~/.ros/trashbot_runs/run_001/keyframes
```

dry-run 跑固定路线，不调用 Nav2：

```bash
ros2 run ros2_trashbot_nav fixed_route_autonomy \
  --ros-args \
  -p route_file:=~/.ros/trashbot_runs/run_001/route.csv \
  -p keyframe_dir:=~/.ros/trashbot_runs/run_001/keyframes \
  -p enable_visual_gate:=true \
  -p dry_run:=true
```

启动状态调试页面：

```bash
TRASHBOT_STATUS_FILE=/tmp/trashbot_fixed_route_status.json \
TRASHBOT_WEB_PORT=8765 \
ros2 run ros2_trashbot_nav route_debug_web
```

浏览器打开：

```text
http://<主机IP>:8765
```

## 串口协议

本项目底盘通信以 `docs/vendor/VENDOR_INDEX.md` 为硬件事实入口。当前 WAVE ROVER 官方 ESP32 固件使用 UART newline-delimited JSON：每条命令是一行 UTF-8 JSON，以 `\n` 结尾。vendor Raspberry Pi 示例为 `/dev/ttyAMA0`、`115200`，Orange Pi Zero 3 的实际串口设备名必须上车确认，launch 参数不得硬编码为 Raspberry Pi 路径。

常用命令：

- `{"T":1,"L":0.5,"R":0.5}`：左右轮速度命令，当前默认 `/cmd_vel` 映射路径。
- `{"T":13,"X":0.1,"Z":0.3}`：ROS 线速度/角速度命令，仅在硬件验证后通过参数启用。
- `{"T":131,"cmd":1}`：开启底盘反馈流。
- `{"T":142,"cmd":100}`：设置反馈间隔。
- `{"T":143,"cmd":0}`：关闭 UART echo。
- `T=1001` 反馈：用于 IMU、电池和底盘反馈解析；当前 `/odom` 来源需在代码和文档中明确。

## 安全边界

- 安全能力必须区分“已由 WAVE ROVER vendor 资料/实机验证支持”和“项目外接安全需求”。通信丢失停车、前向近障急停、蜂鸣提示等能力在没有对应 vendor 文件或 HIL 记录前，只能作为待验证/外接模块需求。
- 当前视觉检测是启发式演示方案，复杂光照和遮挡场景需要 YOLO、RT-DETR 或深度相机等更强感知方案。
- 当前系统适合封闭区域低速移动机器人，不适用于开放道路自动驾驶。

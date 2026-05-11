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

### Mac Docker Humble 环境

默认从 Mac 本地仓库路径启动 Docker Desktop/Engine，例如 `/Users/<user>/apps/rober`。不要在 Mac 目标流程里从 `/mnt/e/...` 或其他 WSL 挂载路径启动 Compose；这会把历史 WSL bind mount 路径带进 Docker 配置，容易出现 `/run/desktop/mnt/host/wsl/...` 这类不可用路径。

构建本项目的 ROS2 Humble 镜像并顺手跑一次 `colcon build`：

```bash
bash scripts/docker_humble_build.sh
```

脚本默认使用清华源加速 Ubuntu APT、ROS2 APT、rosdep、rosdistro index 和 pip。只想先构建镜像、不跑工作区编译：

```bash
SKIP_COLCON=1 bash scripts/docker_humble_build.sh
```

需要切换镜像源或 Humble base image 时可覆盖环境变量：

```bash
ROS_HUMBLE_BASE_IMAGE=osrf/ros:humble-desktop \
UBUNTU_APT_MIRROR=https://mirrors.aliyun.com/ubuntu \
ROS_APT_MIRROR=https://mirrors.aliyun.com/ros2/ubuntu \
PIP_INDEX_URL=https://mirrors.aliyun.com/pypi/simple \
bash scripts/docker_humble_build.sh
```

进入本地开发容器：

```bash
bash scripts/docker_humble_dev.sh
```

如需把串口设备透传给容器，可追加 Docker 参数。Mac 和 Linux 的设备路径不同，先用本机实际路径替换示例：

```bash
EXTRA_DOCKER_ARGS="--device=/dev/tty.usbserial-XXXX" bash scripts/docker_humble_dev.sh
```

也可以用 Docker Compose。默认 Compose 服务不挂载 Linux X11 socket，适合 Mac Docker Desktop/Engine：

```bash
docker compose -f docker-compose.humble.yml build
docker compose -f docker-compose.humble.yml run --rm humble
```

Linux/X11 图形显示是显式 opt-in 路径：

```bash
ROS_HUMBLE_ENABLE_X11=1 docker compose -f docker-compose.humble.yml --profile x11 run --rm humble-x11
ROS_HUMBLE_ENABLE_X11=1 bash scripts/docker_humble_dev.sh
```

Linux/WSL 仍可作为非默认辅助路径。需要在 WSL Ubuntu 中配置 Docker Hub 国内镜像时：

```bash
bash scripts/setup_wsl_docker_mirrors.sh
```

如果使用 Docker Desktop + WSL，需要在 Docker Desktop 里开启对应 WSL 发行版集成；如果使用 WSL 内部 Docker Engine，上面的脚本会写入 `/etc/docker/daemon.json` 并尝试重启 Docker。手动配置 Docker Hub 镜像时，也可在 Linux/WSL Docker Engine 写入 `/etc/docker/daemon.json` 后重启 Docker：

```json
{
  "registry-mirrors": [
    "https://docker.m.daocloud.io",
    "https://docker.1ms.run"
  ]
}
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

## 27. 技术选型决策记录（2026-05-10 21:00）

本次选型由 CEO 战略方向输入触发，产品北极星不变（面向普通手机用户的低成本送垃圾机器人），新增四个维度技术决策，写入 OKR 战略文件作为后续 sprint tech-plan 的参考基础。

### 27.1 渐进式建图（仅摄像头）

**决策**：主路线 ORB-SLAM3 单目混合架构，降级备选视觉里程计 + 固定路线记录。

- Orange Pi 本地跑特征提取与 tracking；关键帧异步上传常驻服务器做全局 BA/回环优化，结果推回设备。
- 普通用户可在手机端看到关键帧数量增长、地图覆盖状态，每次驾驶后可感知建图进度。
- 降级路线（断网/服务器不可用）：视觉里程计 + 固定路线记录，只做本地积分，无全局一致性。
- 淘汰选项：ElasticFusion（需深度相机）、Monodepth2 稠密建图（算力过高）、RTAB-Map 单目（Orange Pi 太重）。

### 27.2 4G 图传

**决策**：主路线 WebRTC P2P + coturn TURN 中继，MVP 降级 MJPEG over HTTP。

- 延迟目标 <500ms；WebRTC P2P 在 4G 下预期 <200ms，MJPEG over HTTP 在 4G 下约 200-500ms。
- 服务器侧只需部署 coturn（轻量，1 核 1G 内存足够），量产设备侧集成 GStreamer/aiortc。
- 商业视频云（声网/腾讯直播）因量产按分钟计费不作为默认方案，可作为应急备选。
- 摄像头用途：路线辅助、站点识别、障碍/异常记录、远程查看；不作为散落垃圾检测入口。

### 27.3 TTS/语音提示

**决策**：主路线预录真人普通话音频文件，补充路线 sherpa-onnx 本地神经 TTS（ARM 可跑）。

- 预录音频（约 10-20 条固定提示词）：aplay/mpg123 本地播放，完全离线，延迟 <50ms，零边际成本，普通话质量最高。
- sherpa-onnx：用于需要动态文本的场景，ARM 可本地运行，离线，100-300MB 模型可接受。
- 无需依赖 Edge-TTS、CosyVoice、ChatTTS 等在线或服务器 TTS API；核心提示全走预录，量产不引入网络依赖。

### 27.4 4090 + 常驻服务器利用

**决策**：4090 专注训练轻量视觉模型；服务器专注 ORB-SLAM3 全局优化 + WebRTC TURN 中继。

- **4090 最高价值训练任务**：站点识别轻量模型（YOLO-nano/RT-DETR-tiny 微调）、障碍检测模型。量产设备只跑推理（Orange Pi），不依赖 4090。
- **服务器最高价值用途**：ORB-SLAM3 异步全局优化（解放 Orange Pi）+ coturn TURN 中继（4G 穿透必须）。
- TTS 推理服务可选部署服务器，但主路线已用预录绕过，优先级低。
- 服务端能力由云持续服务支撑，量产设备本身只需 Orange Pi。

### 27.5 对 OKR 的影响

本次选型结论已写入：
- **战略定位第 2 条**（渐进式建图 ORB-SLAM3 方案、4G 图传 WebRTC + coturn + MJPEG 降级）
- **战略定位第 3 条**（4090 + 服务器研发期基础设施说明）
- **Objective 3 KR6**（渐进式建图能力 KR）
- **Objective 4 KR6**（4G 图传可行性验证 KR）
- **Objective 5 KR6**（4G 图传远程查看 KR）、**KR7**（语音提示 TTS/预录落地 KR）
- **风险表**（渐进式建图 tracking 丢失风险行、4G 图传穿透/延迟风险行）

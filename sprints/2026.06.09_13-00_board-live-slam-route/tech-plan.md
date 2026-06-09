# Board Live SLAM Route Sprint Tech Plan

## 责任 Engineer

派发给：`robot-algorithm-engineer`。

单 owner 闭环：本轮以 SLAM、Nav2、路线采集、固定路线回放为主。除非执行中发现真实 WAVE ROVER/UART 或 Orange Pi 硬件事实必须修改，否则不并行拆给硬件或平台同学。

## 允许改动文件范围

允许改动：

- `sprints/2026.06.09_13-00_board-live-slam-route/tech-done.md`
- `sprints/2026.06.09_13-00_board-live-slam-route/side2side_check.md`
- `sprints/2026.06.09_13-00_board-live-slam-route/final.md`
- 如必须记录现场操作补充，可更新 `docs/product/pc_tools_workstation.md` 中与真实路线回放材料消费相关的产品说明。

默认不改动：

- 产品代码、测试代码、launch、硬件配置、串口配置、WAVE ROVER 协议代码。

如执行中确认必须修代码才能产出 `map.yaml` / `route.csv` / replay evidence，先在 `tech-done.md` 写明失败根因和建议改动范围，再由主节点另派实现 sprint；不要在本 sprint 擅自扩大范围。

## 接口边界

- SSH 入口：`ssh root@192.168.1.11 -p 37878`。
- 目标 runtime：真实上位机 ROS2/Humble 环境，优先复用上位机已有 workspace。
- ROS topic：至少探测 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map`。
- 项目 launch：`ros2_trashbot_bringup learn.launch.py`。
- 项目工具：`ros2_trashbot_nav route_csv_to_yaml`、`ros2_trashbot_nav fixed_route_autonomy`。
- 产物边界：地图、路线、keyframe、rosbag、replay JSONL 是证据，不等于送达成功。

## Vendor 资料与硬件事实

执行前必须读取：

```bash
sed -n '1,180p' docs/vendor/VENDOR_INDEX.md
```

如果涉及以下任一事项，继续打开 `docs/vendor/VENDOR_INDEX.md` 指向的本地 vendor 文件并在 `tech-done.md` 引用来源：

- Orange Pi 串口设备名、GPIO、供电或引脚。
- WAVE ROVER UART、baudrate、JSON 指令、速度映射、反馈协议。
- 机械安装、传感器安装位置、底盘移动安全边界。

## 验收命令

在本机先确认工作区状态，避免覆盖他人改动：

```bash
git status --short
```

登录真实上位机：

```bash
ssh root@192.168.1.11 -p 37878
```

在上位机上执行最小环境探测：

```bash
set -e
hostname
date
command -v ros2
find / -maxdepth 4 -name setup.bash 2>/dev/null | head -20
```

按上位机实际路径 source ROS2 与工作区。优先尝试：

```bash
source /opt/ros/humble/setup.bash
if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
if [ -f ~/rober/onboard/install/setup.bash ]; then source ~/rober/onboard/install/setup.bash; fi
if [ -f ~/apps/rober/onboard/install/setup.bash ]; then source ~/apps/rober/onboard/install/setup.bash; fi
ros2 pkg list | egrep 'ros2_trashbot_(bringup|nav|hardware|behavior)'
```

探测传感器和 TF：

```bash
ros2 topic list | egrep '/scan|/camera/image_raw|/odom|/tf|/map' || true
timeout 12s ros2 topic hz /scan --window 5 || true
timeout 12s ros2 topic hz /odom --window 5 || true
timeout 12s ros2 topic hz /camera/image_raw --window 5 || true
timeout 12s ros2 topic echo /tf --once || true
```

启动建图与路线记录。输出目录必须带时间戳，避免覆盖旧材料：

```bash
RUN_ID="field_map_$(date +%Y%m%d_%H%M%S)"
OUT_DIR="$HOME/.ros/trashbot_runs/${RUN_ID}"
mkdir -p "$OUT_DIR"
ros2 launch ros2_trashbot_bringup learn.launch.py \
  route_recorder:=true \
  route_output_dir:="$OUT_DIR" \
  route_id:=trash_station_route \
  route_camera_topic:=/camera/image_raw \
  route_odom_topic:=/odom
```

在另一个 SSH session 中保存地图：

```bash
source /opt/ros/humble/setup.bash
if [ -f /ws/install/setup.bash ]; then source /ws/install/setup.bash; fi
ros2 service list | egrep '/trashbot/save_map|map'
ros2 service call /trashbot/save_map std_srvs/srv/Trigger {}
find "$HOME/.ros/trashbot_runs" -maxdepth 3 -type f | sort | tail -80
```

转换路线并 dry-run/replay：

```bash
ROUTE_CSV="$(find "$HOME/.ros/trashbot_runs" -name '*.csv' | sort | tail -1)"
ROUTE_YAML="${ROUTE_CSV%.csv}.yaml"
ros2 run ros2_trashbot_nav route_csv_to_yaml "$ROUTE_CSV" "$ROUTE_YAML"
ros2 run ros2_trashbot_nav fixed_route_autonomy \
  --ros-args \
  -p route_file:="$ROUTE_YAML" \
  -p dry_run:=true
```

可选 rosbag 证据：

```bash
timeout 30s ros2 bag record -o "$OUT_DIR/rosbag_minimal" /scan /odom /tf /camera/image_raw
```

## OKR 最低优先级核对

`OKR.md` 4.1 中最低 Objective 原为 O6。2026-06-09 已连续完成 O6 archive、tunnel、event/evidence、labeling、inference、consumer read 多个 local/mock software proof，O6 不应继续按 0% 判断。

本 sprint 不针对 O6；理由是 CEO 明确提供真实上位机 SSH，上一轮现场链路只因本机 runtime 不可用失败。按 Mission 执行偏置，本轮必须优先产出真实 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL，推动归档 O3 的现场验证，而不是继续做 O6/O7 surface。

## 成功标准

成功完成至少需要：

- `tech-done.md` 中记录 SSH 登录结果。
- `tech-done.md` 中记录 topic 探测输出。
- `tech-done.md` 中记录地图、路线、keyframe/replay 产物路径或失败根因。
- `tech-done.md` 中明确是否读取 vendor 资料，以及是否涉及 WAVE ROVER/UART/Orange Pi 硬件事实。
- `git status --short` 输出证明没有覆盖他人改动。

## 风险与降级

- SSH 不通：记录错误、网络和认证状态，回退为需要 CEO 网络/凭证决策。
- ROS2 不存在：记录 `command -v ros2` 和 setup 文件查找结果，不退回纯 review。
- topic 缺失：按缺失 topic 列出下一步 owner。雷达/相机/odom 缺失优先定位上位机 bringup。
- 地图保存失败：记录 service list、node list 和 launch 日志。
- 现场不能移动：至少产出 topic、静态 SLAM/recorder 启动、rosbag 或 keyframe 证据。

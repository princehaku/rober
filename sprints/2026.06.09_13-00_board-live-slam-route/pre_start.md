# Board Live SLAM Route Sprint Pre-start

## sprint_type: epic

## 触发背景

CEO 在 2026-06-09 13:00 前后明确给出真实上位机入口：

```text
ssh root@192.168.1.11 -p 37878
```

上一轮 `sprints/2026.06.09_12-05_slam-route-live-run/tech-done.md` 已证明本机阻塞不是建图/路线代码入口缺失，而是本机没有 ROS2 CLI、没有可用 Docker/Humble 镜像，导致无法产出 `map.yaml`、`route.csv`、keyframe 或 replay JSONL。现在真实上位机入口到位，本轮必须从 review/handoff/surface 切回现场执行链路。

## 用户价值和北极星

北极星仍是：普通用户把垃圾交给小车后，小车能沿固定路线把垃圾送到垃圾站点位，并留下可复盘证据。

本轮用户价值不是新增 UI 或云端面板，而是取得第一份真实上位机上的建图/路线证据包：确认传感器 topic 存在，跑 `learn.launch.py` 采集地图和路线，再把路线转换为可回放配置。该证据直接服务后续真实送达、手机一键发车和 PC 端路线回放。

## OKR 映射和方向判断

- 方向判断：调整。暂缓继续推进 O6/O7 只读 surface，转向 O3 真实路线采集和回放证据。
- 主要映射：归档 Objective 3「可验证导航与固定路线」临时激活为现场验证 lane。
- 次级映射：O2 真实送达、电梯 assisted delivery 和 O7 路线回放后续都依赖本轮产出的真实路线/关键帧材料。
- 不直接选择 O6 最低 Objective 的理由：O6 已在 2026-06-09 多轮 sprint 形成 archive、tunnel、event/evidence、labeling、inference、consumer read 的 local/mock 软件证据；CEO 当前提供的是上位机真实入口，按 Mission 执行偏置应优先产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。

## 核心抓手

通过真实上位机 SSH 执行一条最短现场证据链：

1. 登录上位机并确认 ROS2/Humble 工作区可 source。
2. 采集 `/scan`、`/camera/image_raw`、`/odom`、`/tf`、`/map` 等 topic 存在性。
3. 启动 `learn.launch.py` 进行 SLAM 建图和人工驾驶路线记录。
4. 调用保存地图服务并检查输出 `map.yaml` / map image。
5. 生成 `route.csv`、keyframe/evidence 文件和 route manifest。
6. 转换为 fixed-route YAML 并执行 dry-run/replay 验证。
7. 把材料落到 sprint `tech-done.md`，明确成功、失败或硬件阻塞原因。

## Owner

主责 Engineer：`robot-algorithm-engineer`。

原因：本轮核心是 SLAM、Nav2、地图、固定路线、路线回放和关键帧证据。若发现 WAVE ROVER/UART、底盘控制、串口或电气事实不清，再让 `rober-hardware-engineer` 只读补事实；不要先并行拆分。

## Vendor 资料要求

需要读 `docs/vendor/VENDOR_INDEX.md`。本轮不预设引脚、电压、串口设备名、WAVE ROVER 指令或底盘速度映射；如执行中涉及真实 WAVE ROVER、UART、serial port、baudrate、速度命令、反馈协议或 Orange Pi 设备路径，必须按 `docs/vendor/VENDOR_INDEX.md` 继续打开对应本地 vendor 文件后再下结论。

## 风险边界

- SSH 可达不等于 ROS2 环境、传感器、底盘、相机或雷达都可用。
- `topic list` 可见不等于可建图；必须检查频率、时间戳和 frame。
- 采集到地图和路线不等于真实送达完成；本轮验收止于建图/路线/回放证据包。
- 如果真实底盘移动不可安全执行，可先进行传感器 topic、SLAM 静态启动、路线 recorder dry-run 或 rosbag 录制，不因硬件移动受限而退回纯文档。


# rober 项目设计与前瞻 OKR

## 1. 北极星

把 `rober` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车沿固定路线出发，把垃圾送到垃圾站/垃圾桶点位，必要时跨楼层进出电梯，再安全返回或等待下一次任务。不是一次性 demo，不依赖机械臂捡垃圾。

当前项目核心包：

- `ros2_trashbot_interfaces`：msg/srv/action 契约层。
- `ros2_trashbot_hardware`：Orange Pi 到 WAVE ROVER ESP32 下位机的串口桥。
- `ros2_trashbot_nav`：Nav2、航点、地图、固定路线、关键帧调试。
- `ros2_trashbot_behavior`：任务编排、送达/投放 action。

项目的核心是把"能跑"升级为"可验证地可靠交付垃圾"：协议可信、固定路线可靠、任务可恢复、用户交互足够简单、数据可复盘、云端可运营。

---

## 2. 战略定位

1. **目标用户是不会电脑和硬件的普通人**
   - 用户默认只有手机，不要求会 SSH、ROS2、串口、地图文件或硬件调试。
   - 产品体验围绕手机端一键发车、状态查看、异常提示、人工接管和售后诊断设计。
   - 语音、喇叭和简单灯光/提示音降低使用门槛。

2. **核心任务是"送垃圾"，不是"捡垃圾"**
   - MVP 闭环：用户放入垃圾 → 手机/语音确认 → 小车出发 → 到达垃圾站点位 → 完成投放/提醒人工取走 → 返回或待命。
   - 当前预算和条件下不承诺机械臂抓取、地面散落垃圾拾取、复杂分类分拣。
   - 摄像头优先用于路线辅助、站点识别、障碍/异常记录和远程查看。

3. **预算有限，必须按量产约束做取舍**
   - 默认硬件边界：小车底盘、Orange Pi 上位板、随身 WiFi、摄像头、麦克风、喇叭。
   - 新增能力必须回答：是否降低用户使用难度、是否提高送达成功率、是否适合低成本量产。
   - 硬件事实来源：`docs/vendor/VENDOR_INDEX.md`。本文仅写产品战略，不新增引脚/电压/波特率假设。

---

## 3. 设计原则

1. **硬件事实必须本地可追溯**
   - WAVE ROVER、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件和机械尺寸，以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准。
   - 底盘通信按 WAVE ROVER 官方 UART newline-delimited JSON 处理，下位机不改动。

2. **ROS2 接口稳定，内部实现可替换**
   - 上层面向 `/cmd_vel`、`/odom`、`/imu/data`、`/battery`、`/trashbot/patrol`、`/trashbot/collect_trash` 等接口。
   - 底层硬件桥、视觉模型、导航实现可以迭代，不随意破坏接口契约。

3. **先送达闭环，再智能**
   - 第一优先级是完整送达闭环。复杂模型、动态规划、多机协同建立在稳定送达和可观测数据之上。

4. **每个关键行为要可观测、可回放、可解释**
   - 任务状态、导航目标、检测结果、失败原因、硬件反馈都落日志或状态文件。
   - 路线、关键帧、检测样本和失败案例形成持续改进数据集，上传云端存档。

5. **默认安全、低速、可停**
   - 任何自主行为必须有停止路径、超时策略、失败恢复策略。
   - 未经硬件验证的能力只能以参数关闭或 dry-run 形式存在。

6. **量产优先，少硬件、少配置、少售后**
   - 功能默认考虑批量装机、远程诊断、参数模板、用户误操作和售后成本。

7. **电梯识别是必须实现的 assisted delivery**
   - 跨楼层送垃圾是 MVP 必须能力：小车看门、进门、语音求助按键、判断目标楼层、开门后驶出，进入主 `task_orchestrator` 状态机。
   - 按"文档/合同 → 软件 dry-run → 受控实景"三层验收推进，写明必须不等于已完成实机。
   - 小车不按电梯按钮，不改造电梯，人工协助按目标楼层是产品边界。

8. **数据通路：Orange Pi → 隧道 → 云中转（核心后端）**
   - 上位机 Orange Pi 通过安全隧道（如 frp/ngrok/WireGuard）接入公网云中转，不依赖手机直连 WiFi。
   - 云中转是核心后端：命令/状态/ACK 控制面中转、任务记录与事件存档、模型推理与数据打标、OSS 大对象存储。
   - 控制面不暴露 `/cmd_vel`、不接受 inbound 直连小车。凭证只走 `.env`/环境变量，不进入仓库。

9. **手机端是普通用户唯一操作入口**
   - 美观、能直接使用、不依赖命令行/SSH/ROS2 知识。4G 场景走云端中转。
   - 实时可见机器人位置、任务状态、电梯状态，支持一键发车和人工接管。

10. **PC 端是运营调试与数据训练平台**
    - 实时可见 ROS2 路径、地图、机器人位置、电梯状态、楼层信息。
    - 历史路线回放、数据标注/打标、模型训练数据管理。
    - 实时 ASR 监听、TTS 发言操作、手动转向控制、自动寻路下发。
    - 与云端后端数据层对接，不绕过云端直连小车。

11. **允许各接口与硬件分阶段 Mock**
    - 软件逻辑开发与测试不应被物理硬件、公网/云端和真实电梯/路线环境的到位情况所阻塞。
    - 允许且鼓励在串口驱动、云端 API、ASR/TTS、雷达/ToF 传感器等接口设计并使用 `mock` 模式或本地/内存仿真。
    - 在推进 OKR 过程中，若在 Docker/本地环境中使用 Mock 运行且测试通过，可判定为『软件侧完成』，不必等到真实硬件实测后再合并推进，直到最终集成测试阶段再用真实数据和硬件实跑验证。

---

## 4. 2026 H1 OKR（当前推进中）

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**当前进度：约 93% software_reference + upper-computer serial-open observed; feedback not_proven** | Task A 已用 mock serial / virtual HIL packet 证明 JSON newline 编码、`T=1` wheel command、`T=1001` 反馈解析、IMU/Battery 发布、坏帧容错和参数边界。`2026.06.01_09-10_lidar-reference-ingest` 已把 `lidar_ros` 参考入库并标记 `150000` baud、`0xAA 0x55`、`LSN`、`/lidar/raw_packet`、`laser_frame`、LaserScan output 为 `source=software_reference`；`2026.06.01_10-11_lidar-ros2-driver-skeleton` 已建立 `ros2_trashbot_hardware` LiDAR skeleton 和 `bringup.launch.py` 默认关闭的 gated node。`2026.06.01_15-16_o1-upper-computer-readiness-probe` 已通过远端 SSH 对 `root@192.168.1.11:37878` 执行只读 upper-computer readiness probe，观察到 Linux aarch64、Python 3.10.12、若干串口候选、`pyserial.available=false`、`/opt/ros/humble/setup.bash` 不存在，且固定 fail-closed 控制字段。`2026.06.01_16-17_o1-wave-rover-serial-feedback-probe` 进一步观察到 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0`，远端 read-only probe 返回 `pyserial.available=true`、`serial_opened=true`、`read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`、`error=null`，且固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。真实 WAVE ROVER 上车实测、真实 LiDAR、真实 UART/HIL、真实 `T=1001` feedback、真实底盘控制、真实 LiDAR `/scan`、ROS Humble runtime、真实 IMU/battery 标定、TF、Nav2/SLAM、150000 上车稳定性和 PR #5 2D LiDAR / ToF 硬件材料仍为 `not_proven`，不能按 HIL pass 或真实硬件完成解读。（开发阶段支持通过 Mock/虚拟串口模式完成软件控制链路并进行验证，真机实测留待后期集成）

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` 只通过参数启用。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，明确 `/odom` 是命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码设备名。
- KR6：LiDAR 侧先以 `source=software_reference` + mock skeleton 推进 ROS2 `/scan` 接口、`/lidar/raw_packet` 可选 raw packet 和 `bringup.launch.py` 默认关闭接入；真实串口、TF、Nav2/SLAM 和 150000 波特率稳定性必须另行实机验收。

---

### Objective 5：云中转控制面产品化（原 O5/O6）

**当前进度：约 92% software + PC aggregated live-health probe；real material not_proven** | Task B 已用本地/mock control plane smoke 覆盖 `trashbot.remote.v1` commands/status/ack、bearer/env credential、mock 4G interruption、mock DB/queue artifact、mock OSS/CDN manifest 和 graceful degradation。`2026.06.01_14-15_o5-readiness-live-health` 新增 bearer-gated `GET /api/o5/readiness/health`，schema 固定为 `trashbot.o5.readiness_health.v1`，capability 固定为 `o5_readiness_live_health`，复用 `production_preflight_payload()` 但只输出脱敏 readiness 缺口摘要，并固定 `production_ready=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。`2026.06.01_17-18_o5-o6-cloud-relay-health` 进一步在 PC workstation 后端实现只读 `GET /api/o5-o6/cloud-relay-health`，聚合 O5 readiness health 与 O6 archive health；该 probe 只允许 loopback/private LAN `baseUrl`，bearer 只从 env 读取，固定 fail-closed false fields，不发控制、不 POST、不碰 `/robots/*`。验证证据为 PC workstation `npm run build` 通过、`npm run test` 2 files / 49 tests 通过、`npm run lint` 通过、scoped diff-check 通过。真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实 phone/browser 证据仍为 `not_proven`。（开发与测试阶段支持基于本地/Docker 的 Mock Cloud 进行控制面业务逻辑联调验证）

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`（4C 8G 无 GPU、SSH 端口、防火墙策略、容量边界）。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作公开只读视图入口；私有数据走 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，服务端/CI/上车均通过环境变量注入；密钥泄露有 rotate 流程。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须 graceful degradation，任务不丢，远程诊断能区分"网络问题"与"机器人问题"。

---

### Objective 6：云端核心后端——数据存档、模型推理与打标平台

**当前进度：约 92% software + PC aggregated live-health probe；real material not_proven** | Task C 已把 O6 archive task/event/annotation/inference/query、机器人侧 event publisher、algorithm feed 和 `trashbot.archive.v1` schema 兼容做成可复验 mock evidence，并证明 `o6_cloud_archive_state.json` 不落仓库根目录。`2026.06.01_13-14_o6-archive-live-health` 新增 bearer-gated `GET /api/o6/archive/health`，schema 固定为 `trashbot.o6.archive_health.v1`，capability 固定为 `o6_archive_live_health`，可返回 `empty` / `ready` / `store_unavailable`，并保持 `storage_backend=json_file_proof`、`production_ready=false`、`production_db_connected=false`、`real_oss_upload=false`、`real_inference_model_runtime=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。`2026.06.01_17-18_o5-o6-cloud-relay-health` 进一步通过 PC workstation 只读 `GET /api/o5-o6/cloud-relay-health` 将 O6 archive health 与 O5 readiness health 合并成运营侧单点 live-health 视图；该 probe 只读、不 POST、不访问 `/robots/*`，并固定 fail-closed false fields。验证证据为 PC workstation `npm run build` 通过、`npm run test` 2 files / 49 tests 通过、`npm run lint` 通过、scoped diff-check 通过。真实安全隧道、production DB/queue、真实 OSS upload、真实模型或外部推理 runtime、external live probe、真实云、真实 4G/SIM、真实 phone/browser 和上车数据仍为 `not_proven`。

**目标说明**：把云中转从轻量控制面升级为核心后端：持久化存档任务记录和感知事件，提供模型推理和数据打标能力，作为 PC 端/手机端的统一数据源。

**Key Results**

- KR1：Orange Pi 上位机通过安全隧道（frp/WireGuard/ngrok 任选，参数可配）接入公网，隧道断线后自动重连，云端能感知在线/离线状态。
- KR2：任务记录和感知事件（路线帧、关键帧、检测结果、电梯门状态、楼层证据、失败原因）持久化存档到云端数据库，支持按 `robot_id / task_id / date` 查询。
- KR3：摄像头帧/快照等大对象通过 OSS 存档，云端数据库只保留对象引用（`evidence_ref`），不直接存大文件。
- KR4：云端提供数据打标/标注 API：接受标注任务（路线帧标注、电梯楼层标注、障碍物标注），支持 PC 端提交和查询标注结果。
- KR5：模型推理接口（电梯门开/关、楼层识别）可在云端调用，推理结果写入事件存档，不要求 GPU 上线即可用（优先 CPU 轻量模型或调用外部推理 API）。
- KR6：REST API（或 WebSocket）供 PC 端和手机端消费：历史任务列表、任务详情、轨迹数据、事件流、标注状态。

---

### Objective 7：PC 端运营调试与数据训练平台

**当前进度：约 95% software + same-LAN Chromium browser 30s short-stability observed；product real material not_complete** | Task D 已让 PC workstation 消费 O6/O7 mock archive bundle，覆盖实时地图/位置、电梯状态、历史路线回放、数据标注、推理摘要、ASR/TTS stub、手控/寻路 stub，并固定 `safe_to_control=false`、`robot_control_executed=false`。`2026.06.01_00-01_local-webrtc-camera` 进一步在远端 Orange Pi `op-z3-b6.home` 上证明 LAN-only WebRTC camera smoke：`/offer` 返回 answer、`connection_state=connected`、`first_frame_received=true`、首帧 640x480；连续两轮 self-test 均 `status=ok`，并通过 answer `peer_id` + `POST /peers/{peer_id}/close` 证明 `server_peer_close.closed=true`、`active_peer_connections_after=0`。`2026.06.01_05-06_o7-browser-playback-real-proof` 修复了板端 peer close 后摄像头 FD 残留问题，远端 self-test 恢复到 `first_frame_received=true`、640x480、`server_peer_close.stopped_tracks=["video"]`、`active_peer_connections=0`；服务端日志证明 self-test 路径可连续编码 640x480 帧且 `camera_read_failures=0`。`2026.06.01_07-08_o7-browser-ice-gathering-stats` 关闭上一轮 PC Chromium/browser `first_frame_timeout` 缺口：`pc-tools/workstation/.workstation-runtime/o7-browser-playback-smoke.json` 显示 `status=ok`、`first_frame_received=true`、`video_width=640`、`video_height=480`、`first_frame_ms=2281`、ICE connected/complete、`ontrack_count=1`、`framesDecoded=1`、`post_smoke_remote_health.activePeerConnections=0`。`2026.06.01_08-09_o7-browser-stability-metrics` 进一步完成真实 30s smoke against `http://192.168.1.11:8088/`：`status=ok`、`first_frame_received=true`、`first_frame_ms=2044`、`stability_summary.status=observed`、`sample_count=6`、`estimated_fps=13.9`、`remote_system_metrics.process_uptime_s=370.036`、`load_1m=1.35009765625`、`process_rss_bytes=141357056`、`temperature_celsius=46.394`、`remote_stability_metrics.active_peer_count=1`、`active_frames_read=352`、`active_camera_read_failures=0`、`remote_active_peer_cleaned=cleaned`、`post_close_active_peer_connections=0`；补充 `post_smoke_remote_health.activePeerConnections=0`、`stabilityMetrics.last_closed_fps_estimate=13.301`、`last_closed_camera_read_failures=0`。PC workstation 的 API/UI 仍只消费板端 `/health` + `/devices` 与显式 browser-smoke JSON，不自动 POST `/offer`、不创建 WebRTC session、不发送控制，且 `/health` 保持 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`。这只关闭 O7 的“同 LAN Chromium 30s 短稳态 + 远端 CPU/温度/帧读数 + peer cleanup 可观测”缺口；不证明 3-5 分钟、弱网、TURN、公网云 relay、鉴权、真实用户浏览器/手机、ASR/TTS、手控/Nav2、真实 robot ACK 或完整上车任务闭环。

**目标说明**：PC 端面向开发者和运营人员，提供实时监控、历史回放、数据标注、手动控制和语音调试能力，与云端数据层对接，不绕过云端直连小车。

**Key Results**

- KR1：**实时地图与机器人位置**——PC 端展示当前地图、机器人实时位置（基于 ROS2 `/tf` 或云端转发位置），可见是否在路线上、是否进入电梯区域，刷新延迟 < 2 秒。
- KR2：**电梯状态展示**——实时展示电梯状态（等待/进入/运行中/到达楼层/驶出），当前楼层证据，人工接管原因；历史任务可回放电梯完整状态链。
- KR3：**历史路线回放**——从云端拉取历史任务的轨迹数据，在地图上逐帧回放，可查看每一帧的位置、速度、关键帧截图和状态转移。
- KR4：**数据标注/打标界面**——展示待标注的路线帧、关键帧、检测截图，支持标注电梯门状态、楼层信息、障碍物类型；标注结果提交云端，可导出训练数据集。
- KR5：**实时 ASR 监听 + TTS 发言控制**——PC 端可实时查看小车当前 ASR 输入流；可手动下发 TTS 文本，小车喇叭播报；支持测试电梯语音场景。
- KR6：**手动转向控制 + 自动寻路下发**——PC 端通过云端 API 发送方向键/速度控制命令（走云端，不直连），支持键盘/界面操作；可选择地图上的目标点下发自动寻路任务。

---

## 4.1 当前 OKR 进度快照

更新时间：2026-06-01。

| Objective | 进度 | 主要缺口 |
| --- | --- | --- |
| O1：硬件协议可信底盘 | 约 93% software_reference + upper-computer serial-open observed; feedback not_proven | Task A mock serial / virtual HIL packet 软件证据已覆盖主路径和坏帧容错；LiDAR reference ingest + ROS2 skeleton 已覆盖 `150000` baud、`0xAA 0x55`、`LSN`、`/lidar/raw_packet`、`laser_frame`、LaserScan output 的 `source=software_reference` 和默认关闭 gated launch；O1 upper-computer readiness probe 已通过远端 SSH 只读观察上位机 Linux/Python/串口候选状态；O1 WAVE ROVER serial feedback probe 已观察到 `/dev/serial/by-id/usb-STC_STC_USB_Serial-if00 -> /dev/ttyACM0` 且 read-only open 成功，`pyserial.available=true`、`serial_opened=true`，但 `read_line_count=0`、`parsed_json_count=0`、`observed_feedback_types=[]`；真实 WAVE ROVER feedback/T=1001、真实底盘控制、真实 LiDAR、真实 UART/HIL、真实 LiDAR `/scan`、ROS Humble runtime、真实 IMU/battery 标定、TF、Nav2/SLAM、150000 上车稳定性、PR #5 硬件材料仍 `not_proven`，不是 HIL pass |
| O5：云中转控制面 | 约 92% software + PC aggregated live-health probe | Task B mock control plane 已覆盖 commands/status/ack、bearer/env、mock 4G/DB/queue/OSS/CDN graceful degradation；O5 readiness live health endpoint 已提供 bearer-gated `GET /api/o5/readiness/health`、`trashbot.o5.readiness_health.v1` schema、`o5_readiness_live_health` capability、脱敏 readiness 缺口摘要和 fail-closed 字段；PC workstation `GET /api/o5-o6/cloud-relay-health` 已把 O5 readiness 与 O6 archive health 聚合为只读 live-health probe，限制 loopback/private LAN baseUrl、env bearer、fail-closed false fields、不 POST、不碰 `/robots/*`；真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 仍 `not_proven` |
| O6：云端核心后端 | 约 92% software + PC aggregated live-health probe | Task C mock archive/query/annotation/inference、board event publisher、algorithm feed、state path fence 已可复验；O6 archive live health endpoint 已提供 bearer-gated `GET /api/o6/archive/health`、`trashbot.o6.archive_health.v1` schema、`o6_archive_live_health` capability、`empty` / `ready` / `store_unavailable` 状态和脱敏/fail-closed 字段；PC workstation `GET /api/o5-o6/cloud-relay-health` 已把 O6 archive health 纳入 O5/O6 运营侧聚合只读探针；真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、external live probe、真实云、真实 4G/SIM、真实 phone/browser 和上车数据仍 `not_proven` |
| O7：PC 端运营调试平台 | 约 95% software + same-LAN Chromium browser 30s short-stability observed | PC console 六区 mock/live-like evidence 已覆盖回放、标注、推理、ASR/TTS stub、手控/寻路 stub 和 fail-closed；LAN-only WebRTC camera smoke 已证明 `/offer` answer、connected、`first_frame_received=true`、640x480 first frame 和 peer cleanup；PC Chromium/browser smoke 已从 `first_frame_timeout` 推进为首帧 OK，再进一步完成 30s smoke against `http://192.168.1.11:8088/`：`first_frame_ms=2044`、`stability_summary.status=observed`、`sample_count=6`、`estimated_fps=13.9`、`temperature_celsius=46.394`、`active_frames_read=352`、`active_camera_read_failures=0`、`post_close_active_peer_connections=0`；PC endpoint 只读展示 `/health` + `/devices` 和显式 smoke JSON，不自动发 `/offer` 或控制；3-5 分钟、弱网、TURN、公网云 relay、鉴权、真实用户浏览器/手机、ASR/TTS、手控/Nav2、真实 robot ACK 和完整上车任务闭环仍 `not_proven` |

**已归档 Objective（软件侧完成，等待真实现场验证）：**

| Objective | 软件侧进度 | 归档原因 |
| --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 软件完成 ~99% | 状态机、行为链、电梯状态链、任务记录软件侧全部完成；等待真实路线/电梯/现场跑通后升回当前 |
| O3：可验证导航与固定路线 | 软件完成 ~99% | learn.launch/fixed_route/Nav2 dry-run 全部完成；等待真实路线采集、Nav2 实跑、关键帧实景证据 |
| O4：手机用户体验与量产边界 | 软件完成 ~99% | 手机 UI、地图首屏、任务下发、状态展示软件侧全部完成；等待真实 iPhone/Android 设备验收和真实送达 |

> 归档 KR 详情见 `docs/process/okr_progress_log.md`。真实现场材料到位后重新激活对应 Objective。

---

## 5. 当前最高优先级

按完成度从低到高排序：

1. **O5（约 92% software + PC aggregated live-health probe；real material not_proven）**：与 O6 并列最低约 92%。本轮只关闭 PC workstation 运营侧 O5/O6 聚合 live-health 只读探针缺口，不证明生产控制面；下一步仍按 `docs/interfaces/o1_o5_90_evidence_boundary.md` 采集真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 材料。
2. **O6（约 92% software + PC aggregated live-health probe；real material not_proven）**：与 O5 并列最低约 92%。本轮只把 O6 archive live health 接入 PC workstation 聚合健康视图；下一步优先把 archive core 推进到真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、external live probe、真实云、真实 4G/SIM、真实 phone/browser 和上车数据。
3. **O1（约 93% software_reference + upper-computer serial-open observed; feedback not_proven）**：下一步不要把 upper-computer serial-open、read-only probe 或 LiDAR skeleton 当成 HIL pass；先按 `docs/hardware/lidar_ros_reference.md`、`docs/hardware/o1_upper_computer_readiness_probe.md`、`docs/hardware/o1_wave_rover_serial_feedback_probe.md` 和 `docs/interfaces/o1_o5_90_evidence_boundary.md` 补真实 WAVE ROVER UART/HIL packet、真实 `T=1001` feedback、真实底盘控制、真实 LiDAR 串口 `/scan`、ROS Humble runtime、TF、Nav2/SLAM 订阅、150000 波特率稳定性和 PR #5 硬件材料。
4. **O7（约 95% software + same-LAN Chromium browser 30s short-stability observed；product real material not_complete）**：下一步不要继续消费已关闭的 `first_frame_timeout` blocker，也不要把 30s same-LAN smoke 误读成真实产品视频能力；应把 30s 短稳态扩展到 3-5 分钟帧率/延迟/CPU/温度曲线、浏览器控制台、断开重连、camera release 与失败分类；随后再设计真实产品播放入口的安全确认、鉴权和会话生命周期。云 relay/公网 RTC/TURN/鉴权、真实用户浏览器/手机体验和长期性能仍未证明。

> 当前 90%+ 只代表 mock/software completion。真实材料未完成时，任何 Objective 都不得表述为真实硬件、真实生产云、真实 4G、真实 OSS/CDN、真实 PC/手机或真实上车完成。

---

## 6. OKR 完成路线

### 近期（O6 MVP）

- 确定隧道方案（frp/WireGuard/ngrok），Orange Pi → 云端稳定连通，断线自动重连。
- 云端建任务/事件存档表，小车侧完成后 POST 到云端，PC/手机可查询。
- 大对象走 OSS，云端只存引用。
- 提供最小 REST API：任务列表、任务详情、轨迹数据。

### 近期（O7 MVP）

- PC 端接入云端 API，展示历史任务列表和轨迹回放。
- 实时地图接入 ROS2 位置数据（通过云端转发或本地直连调试）。
- LAN-only WebRTC camera smoke 已完成机器级 `/offer` answer、connected、`first_frame_received=true`、640x480 first_frame 和连续自检 peer cleanup；PC Chromium browser smoke 已证明同 LAN 首帧 640x480、首帧 2281ms、ICE connected/complete、ontrack=1、inbound packets=2、framesDecoded=1，并进一步完成 30s smoke：`estimated_fps=13.9`、`temperature_celsius=46.394`、`post_close_active_peer_connections=0`。下一步补 3-5 分钟稳定性、产品入口安全边界和公网/云 relay 证据。
- 基本标注界面：拉取待标注帧，提交标注结果。

### 中期

- 模型推理上云（电梯门开/关、楼层识别）；推理结果写入存档。
- PC 端电梯状态实时展示，ASR/TTS 调试界面。
- PC 端手控和自动寻路下发（走云端 API）。
- O5 接入真实部署（production DB/queue/OSS/CDN）。
- LiDAR 从 `source=software_reference` + mock skeleton 推进到真实串口 `/scan`、TF、Nav2/SLAM 消费链路，但未完成前不得作为 O1 真实硬件闭环。

### 后期（真实现场验证，激活归档 Objective）

- 真实 WAVE ROVER 与真实 LiDAR 上车实测，O1 闭环。
- 真实路线采集 + Nav2/固定路线实跑，激活 O3。
- 真实电梯场景验证，激活 O2。
- 真实手机/browser 验收，激活 O4。

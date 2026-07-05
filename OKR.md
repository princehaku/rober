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

**当前进度：约 85%** | 主要缺口：真实 WAVE ROVER 上车实测的轮速非零原始反馈、轮速方向、IMU/battery 标定、HIL 准入和 PR #5 2D LiDAR / ToF 硬件材料。（开发阶段支持通过 Mock/虚拟串口模式完成软件控制链路并进行验证，真机实测留待后期集成）

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` 只通过参数启用。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，明确 `/odom` 是命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码设备名。

---

### Objective 5：云中转控制面产品化（原 O5/O6）

**当前进度：约 80%** | 主要缺口：真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 证据。（开发与测试阶段支持基于本地/Docker 的 Mock Cloud 进行控制面业务逻辑联调验证）

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`（4C 8G 无 GPU、SSH 端口、防火墙策略、容量边界）。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作公开只读视图入口；私有数据走 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，服务端/CI/上车均通过环境变量注入；密钥泄露有 rotate 流程。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须 graceful degradation，任务不丢，远程诊断能区分"网络问题"与"机器人问题"。

---

### Objective 6：云端核心后端——数据存档、模型推理与打标平台

**当前进度：0%** | 这是新 Objective，基于新架构需求。

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

**当前进度：约 28%** | 主要缺口：真实 RTC/视频、真实 ASR/TTS、真实 wheel raw 非零反馈、真实电梯/回放/标注数据流、云端生产链路和完整路线长期上车验证。（允许使用 Mock 视频数据流、ASR/TTS 本地模拟和轨迹 Mock 优先进行 PC 端功能开发，最终再利用真实数据跑通）

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

更新时间：2026-07-06。

| Objective | 进度 | 主要缺口 |
| --- | --- | --- |
| O1：硬件协议可信底盘 | ~85% | 已有真实上位机 first-jog 转发、T1001 L/R 反馈采样字段和 LiDAR delta 过阈值；当前真实 L/R 仍为 0，仍缺轮速非零原始反馈、轮速方向、HIL 准入、PR #5 2D LiDAR/ToF 硬件材料 |
| O5：云中转控制面 | ~80% | 真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实手机/browser 验收 |
| O6：云端核心后端 | ~30% | archive、tunnel online、event/evidence、labeling、model inference、consumer read API 已有 local/mock software proof；仍缺真实隧道、生产 DB/queue、OSS、TLS/4G、真实机器人数据 |
| O7：PC 端运营调试平台 | ~28% | PC 普通首屏已能连接真实上位机并开放 `0.0.0.0:7001`；PC 首页和 `/map` 当前默认 `300%` 可读大图，`完整态势` 回 `100%`、`细节放大` 到 `1200%`，已能显示地图 PNG、Nav2 路线、目标点、小车位置和雷达贴图，ROS2 配套固定为 RViz2/Foxglove 工程观察且不替代 PC 简易控制台；`trashbot-esp32-bridge.service` 与 `trashbot-lidar-lifecycle.service` 已固化开机自恢复，复验 `/cmd_vel` 仅一个 bridge 订阅者且 `/scan` 可读 LaserScan；2026-07-06 已修复 `/api/free-roam/autonomy/start` 在 `/free_roam_autonomy` runtime 缺失时失败的问题，上车 API 会托管启动 locked runtime 后再写参数，真实 7001 代理复验 start=`autonomy_forwarded`、latest=`decision_state=avoiding/cmd_vel_publish_enabled=true`，stop 后回到 `stopping/false`，证明自由移动不被相机首帧或雷达 proof 阻塞；相机 CMA 已恢复为 `cma_available_no_recent_failure`，PC status 会保留最近 first-frame probe 的 `probe_total_timeout / uvc_no_frame_not_exclusive` 结论，且代理层 `fetch_timeout_45000ms` 不再覆盖该事实；同日已执行 UVC 控制项复位、USB `3-1` reauthorize、mmap/userptr/ffmpeg/GStreamer 矩阵和 `camera_usb_recovery_smoke.py`，DV20 当前精确分类为 `streamon_success_zero_byte_no_frame / high_speed_zero_byte_no_frame`，PC recovery 已暴露 `software_capture_exhausted=true` 与 `known_good_uvc_required=true`；WASD/自由移动可读到 command raw，且 live-summary 已平铺 `command_raw_lr_nonzero_proven`、`command_raw_latest_left/right`、`keyboard_command_raw_lr_nonzero`，真实 7001 复验 forward PWM/ROS 短脉冲返回 raw L/R 非零、manual executed 和 auto stop true；wheel raw `T=1001 L/R=0/0` 仍是反馈风险；仍缺真实 RTC/视频、真实 ASR/TTS、云端回放/标注数据流、wheel raw 非零和完整路线长期验收 |

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

1. **现场 O3 验证 lane（归档 Objective 临时激活）**：CEO 已提供真实上位机 SSH，当前优先级是把 managed localization 继续推进到 no-motion planner readiness / path generation proof；随后再消费 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL，避免继续停留在只读 handoff/review/surface。
2. **O6（~30%）**：把 local/mock archive/tunnel/event/evidence/labeling/inference/consumer read proof 接到真实隧道、生产 DB/queue、OSS 与真实机器人数据。
3. **O7（~26%）**：基于真实上位机继续推进 PC 实时图传、历史回放、标注、ASR/TTS、手控/寻路和完整路线验收；当前大地图/WASD/自由移动/雷达贴图已有现场证据，并已补开机自恢复服务；相机 root cause 从 CMA 下沉为 UVC 无首帧/输入链路问题，但不能把 wheel raw 0/0 或相机无帧包装成闭环。
4. **O5（~80%）**：把已有命令/状态/ACK 控制面接到真实部署链路：公网 HTTPS、production DB/queue、OSS/CDN live traffic、真实手机/browser 验收。
5. **O1（~85%）**：真实 WAVE ROVER 上车，补轮速非零原始反馈、轮速方向和 HIL 证据，PR #5 硬件材料到位后继续提升。

> 2026-06-09 方向调整：O6 最小 local/mock 数据底座已形成，CEO 又提供真实上位机 SSH。因此下一轮优先跑 `sprints/2026.06.09_13-00_board-live-slam-route/`，用真实上位机补 O3 路线证据；O6/O7 后续必须消费这份真实路线材料，而不是继续堆叠只读 surface。
>
> 2026-06-10 方向微调：在 managed localization proof 之后，O3 现场验证 lane 先推进 no-motion planner readiness / path generation proof，再进入 route execution 材料收集。

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
- 基本标注界面：拉取待标注帧，提交标注结果。

### 中期

- 模型推理上云（电梯门开/关、楼层识别）；推理结果写入存档。
- PC 端电梯状态实时展示，ASR/TTS 调试界面。
- PC 端手控和自动寻路下发（走云端 API）。
- O5 接入真实部署（production DB/queue/OSS/CDN）。

### 后期（真实现场验证，激活归档 Objective）

- 真实 WAVE ROVER 上车实测，O1 闭环。
- 真实路线采集 + Nav2/固定路线实跑，激活 O3。
- 真实电梯场景验证，激活 O2。
- 真实手机/browser 验收，激活 O4。

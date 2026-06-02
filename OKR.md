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

**当前进度：约 93% software_reference + ttyS5 control write observed + low-speed T=1 field response observed + safe pulse acceptance runner ready / watched execution pending; T=1001/ACK/HIL not_proven** | Task A 已用 mock serial / virtual HIL packet 证明 JSON newline 编码、`T=1` wheel command、`T=1001` 反馈解析、IMU/Battery 发布、坏帧容错和参数边界。LiDAR 当前实现依据已收敛为 `docs/vendor/lidar_pkg_ros2-main/`，历史 `docs/vendor/lidar_ros/` 仍保留为 ROS1/protocol comparison；当前已确认 `150000` baud、`A5 60` 启动命令、`A5 00 A5 65 A5 65` 停止序列、`0xAA 0x55`、`LSN`、`/scan`、`/lidar/raw_packet` 为 `source=software_reference + user_manual_serial_observed_start`。2026-06-03 现场事实确认当前 WAVE ROVER 底盘可写控制口是 Orange Pi `/dev/ttyS5 @115200`，不是 USB STC `/dev/ttyACM0`；CEO 观察到 `T=1,L=0.08,R=0.08` 低速命令让底盘响应，随后现场发送 `T=1,L=0,R=0` 停车。`2026.06.03_03-04_o7-upper-robot-api-safety` 让 8787 统一上位机 Robot API 在软件侧具备 camera/radar/base 状态和 base manual 安全护栏：低速、限时、自动 stop、非法 direction 拒绝、fake pyserial 单测通过。`2026.06.03_05-06_o1-ttyS5-safe-pulse-acceptance` 进一步新增 O1 safe pulse acceptance runner：默认 dry-run/read-only，只读取 8787 `/api/status` 或 `--status-json`，schema 为 `trashbot.o1.ttyS5_safe_pulse_acceptance.v1`；只有同时传入 `--execute-motion --confirm-physical-clearance` 才会经 8787 `/api/base/manual` 执行低速短 pulse，runner 不直接打开串口。本轮没有发送任何运动命令，没有 POST `/api/base/manual` 或 stop，没有打开 `/dev/ttyS5`，没有发送 `T=1/T=13/T=130/T=131` 或 `/cmd_vel`。`/dev/ttyACM0` 仍保留为 STC/LiDAR 风险口：`2026.06.02_17-18_o1-usb-serial-inventory` 和 `2026.06.02_15-16_o1-port-identity-remote-evidence` 均显示 by-id/by-path/`ttyACM0` 同指 `/dev/ttyACM0`，sysfs 为 `34bf:ff0a`、`STC USB Serial`、`cdc_acm`，与 LiDAR vendor `99-lidar.rules` 线索一致。`2026.06.02_13-14_o1-t1001-live-recovery` 在该 STC 口显式 `{"T":130}\n` 后 12 秒无反馈；2026-06-03 现场在 `/dev/ttyS5 @115200` 上 `T=130` 仍未读到 `T=1001`，因此反馈/ACK、真实 `/imu/data`、`/battery`、`/odom` 和 HIL packet 仍未闭环。下一步最高优先级是 watched field pulse execution + ACK/`T=1001` capture：现场看护、物理净空、自动停车、速度限幅、操作日志、人工急停、8787 状态与 manual/stop 证据同源采集；不能把本轮写成 HIL pass、闭环安全控制、真实 ROS `/cmd_vel` 接入或 delivery success。（开发阶段支持通过 Mock/虚拟串口模式完成软件控制链路并进行验证，真机实测留待后期集成）

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` 只通过参数启用。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，明确 `/odom` 是命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码设备名。
- KR6：LiDAR 侧先以 `source=software_reference` + mock skeleton 推进 ROS2 `/scan` 接口、`/lidar/raw_packet` 可选 raw packet 和 `bringup.launch.py` 默认关闭接入；真实串口、TF、Nav2/SLAM 和 150000 波特率稳定性必须另行实机验收。

---

### Objective 5：云中转控制面产品化（原 O5/O6）

**当前进度：约 96% software + material acceptance queue visible in PC workstation；real material not_proven** | Task B 已用本地/mock control plane smoke 覆盖 `trashbot.remote.v1` commands/status/ack、bearer/env credential、mock 4G interruption、mock DB/queue artifact、mock OSS/CDN manifest 和 graceful degradation。`2026.06.01_14-15_o5-readiness-live-health` 新增 bearer-gated `GET /api/o5/readiness/health`，schema 固定为 `trashbot.o5.readiness_health.v1`，capability 固定为 `o5_readiness_live_health`，复用 `production_preflight_payload()` 但只输出脱敏 readiness 缺口摘要，并固定 `production_ready=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。`2026.06.01_17-18_o5-o6-cloud-relay-health` 进一步在 PC workstation 后端实现只读 `GET /api/o5-o6/cloud-relay-health`，聚合 O5 readiness health 与 O6 archive health；该 probe 只允许 loopback/private LAN `baseUrl`，bearer 只从 env 读取，固定 fail-closed false fields，不发控制、不 POST、不碰 `/robots/*`。`2026.06.01_18-19_o5-o6-external-live-probe` 新增 Node 版 external probe；`2026.06.01_21-22_o5-o6-python-external-probe` 补充同 schema 的 Python stdlib runner，标记 `runner=python_stdlib`，兼容 `python3 -s - --once-json` stdin 运行。`2026.06.01_23-24_o5-o6-external-probe-artifact-ui` 已给 Python runner 增加 `--output` 落盘能力，并让 PC workstation 暴露只读 `GET /api/o5-o6/external-probe-artifact` 与 O7 Console 摘要，展示 `probe_status`、runner、endpoint reachability、blocked reasons、fail-closed safety fields 和更新时间；该入口不执行 probe、不联网、不访问 `/robots/*`、不读取硬件、不回显 bearer/token/raw URL/artifact path/traceback。`2026.06.02_05-06_o5-o6-tls-evidence-summary` 进一步让 Python stdlib runner 在 HTTPS cloud base URL 时采集脱敏 TLS evidence summary，并由 PC workstation artifact API/contract 消费展示；边界仍是只读、GET-only、no POST、no `/robots/*`、no hardware read、no raw host/base URL/token/cert DN/traceback/artifact path。`2026.06.02_08-09_real-material-acceptance-queue` 新增只读 `GET /api/real-material/acceptance` 和 `RealMaterialAcceptancePanel.vue`，聚合 O5/O6 external probe artifact 与 O7 browser smoke JSON，形成真实材料验收队列、缺口和 next actions；`2026.06.02_09-10_real-material-runbook` 进一步让每条 item 包含 `artifact_freshness` 和 `collection_runbook`，operator 可见 artifact mtime/age/fresh/stale/missing 与手动采集 recipe，但 API 仍只返回 recipe 与只读 `stat` 摘要，不执行采集。该入口不执行 probe、不联网、不 SSH、不 POST、不访问 `/robots/*`、不读取硬件、不创建 WebRTC session、不发送控制，并固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。验证证据为 PC `npm run test` 57 tests passed、`npm run build` 通过、`npm run lint` 通过、scoped diff-check 通过。真实生产云 TLS 验收、真实公网 HTTPS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实 phone/browser 证据仍为 `not_proven`。（开发与测试阶段支持基于本地/Docker 的 Mock Cloud 进行控制面业务逻辑联调验证）

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`（4C 8G 无 GPU、SSH 端口、防火墙策略、容量边界）。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作公开只读视图入口；私有数据走 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，服务端/CI/上车均通过环境变量注入；密钥泄露有 rotate 流程。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须 graceful degradation，任务不丢，远程诊断能区分"网络问题"与"机器人问题"。

---

### Objective 6：云端核心后端——数据存档、模型推理与打标平台

**当前进度：约 96% software + material acceptance queue visible in PC workstation；real material not_proven** | Task C 已把 O6 archive task/event/annotation/inference/query、机器人侧 event publisher、algorithm feed 和 `trashbot.archive.v1` schema 兼容做成可复验 mock evidence，并证明 `o6_cloud_archive_state.json` 不落仓库根目录。`2026.06.01_13-14_o6-archive-live-health` 新增 bearer-gated `GET /api/o6/archive/health`，schema 固定为 `trashbot.o6.archive_health.v1`，capability 固定为 `o6_archive_live_health`，可返回 `empty` / `ready` / `store_unavailable`，并保持 `storage_backend=json_file_proof`、`production_ready=false`、`production_db_connected=false`、`real_oss_upload=false`、`real_inference_model_runtime=false`、`safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。`2026.06.01_17-18_o5-o6-cloud-relay-health` 进一步通过 PC workstation 只读 `GET /api/o5-o6/cloud-relay-health` 将 O6 archive health 与 O5 readiness health 合并成运营侧单点 live-health 视图；该 probe 只读、不 POST、不访问 `/robots/*`，并固定 fail-closed false fields。`2026.06.01_18-19_o5-o6-external-live-probe` 新增 Node 版 external probe；`2026.06.01_21-22_o5-o6-python-external-probe` 新增 Python stdlib runner，让上位机缺 Node.js 时仍可通过 SSH stdin 采集同一 O5/O6 external live probe schema。`2026.06.01_23-24_o5-o6-external-probe-artifact-ui` 已把该 runner 的 `--output` artifact 接入 PC workstation 只读摘要和 O7 Console，运维能看到 O6 archive endpoint 的 reachability/schema/fail-closed 结果，而浏览器不接触 raw base URL、token、artifact path 或 traceback。`2026.06.02_05-06_o5-o6-tls-evidence-summary` 已把 HTTPS cloud base URL 下的脱敏 TLS evidence summary 纳入同一 Python runner 与 PC workstation artifact contract，让 O6 archive endpoint 相关 TLS 摘要可见；该能力仍不回显 raw host/base URL/token/cert DN/traceback/artifact path。`2026.06.02_08-09_real-material-acceptance-queue` 新增只读 `GET /api/real-material/acceptance` 和 `RealMaterialAcceptancePanel.vue`，把 O6 archive/external probe 相关真实材料缺口纳入 PC workstation 验收队列、缺口和 next actions；`2026.06.02_09-10_real-material-runbook` 进一步让每条 item 包含 `artifact_freshness` 和 `collection_runbook`，operator 可见 artifact mtime/age/fresh/stale/missing 与手动采集 recipe，但不执行 probe 或采集。该入口不联网、不 SSH、不 POST、不访问 `/robots/*`、不读取硬件、不创建 WebRTC session、不发送控制，并固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`。验证证据为 PC `npm run test` 57 tests passed、`npm run build` 通过、`npm run lint` 通过、scoped diff-check 通过。真实安全隧道、production DB/queue、真实 OSS upload、真实模型或外部推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收和上车数据仍为 `not_proven`。

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

**当前进度：约 98% same-LAN camera/systemd + PC Live Operator + unified upper API software safety ready；production path / real control / ACK / HIL not_proven** | Task D 已让 PC workstation 消费 O6/O7 mock archive bundle，覆盖实时地图/位置、电梯状态、历史路线回放、数据标注、推理摘要、ASR/TTS stub、手控/寻路 stub，并固定 `safe_to_control=false`、`robot_control_executed=false`。O7 已形成 LAN-only WebRTC camera smoke、PC Chromium/browser smoke、30s smoke、180s long-stability collector、真实材料验收队列和 recovery readiness 的证据链。`2026.06.02_20-21_o7-camera-offer-recovery` 已证明 same-LAN 180s real browser material accepted / camera source guardrail ready。`2026.06.03_01-02_o7-camera-systemd-persistence` 已确认 8088 camera smoke 由 fixed systemd unit 接管，`enabled/active/loaded/running`，`MainPID` 与 listener pid 一致，`/health` 返回 ready 和 fail-closed 字段。`2026.06.03_03-04_o7-upper-robot-api-safety` 新增 8787 统一上位机 Robot API 的软件安全边界：状态面支持 camera/radar/base，base manual 只能低速、限时、自动停车，非法 direction 结构化拒绝，fake pyserial 单测通过。`2026.06.03_03-04_o7-pc-live-operator-upper-api` 把 PC 首屏 Live Operator 接入 8787 API 状态展示：显示 8787 `not_listening_observed`、8088 camera ready、radar `/scan` 缺口、base `/dev/ttyS5`、`T=1001 not observed` 和 manual control fail-closed。PC 没有 POST `/api/base/manual`，唯一 POST 是 camera WebRTC media preview 的 `/api/o7/local-webrtc-camera/offer`；该 `/offer` 只用于媒体预览，不是底盘控制链路。边界不变：真实 8787 远端监听、真实串口、真实 WAVE ROVER JSON、真实 `/cmd_vel`、真实 radar `/scan`、robot ACK、`T=1001`、真实 `/odom`、`/imu/data`、`/battery`、reboot 后自恢复、browser 180s long-stability 复跑、首屏 video 首帧、云 relay/TURN/auth/phone/browser production path、弱网、ASR/TTS、手控/Nav2 和完整上车任务闭环仍 `not_proven`。

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

更新时间：2026-06-03。

| Objective | 进度 | 主要缺口 |
| --- | --- | --- |
| O1：硬件协议可信底盘 | 约 93% software_reference + ttyS5 control write observed + low-speed T=1 field response observed + safe pulse acceptance runner ready / watched execution pending; T=1001/ACK/HIL not_proven | Task A mock serial / virtual HIL packet 软件证据已覆盖主路径和坏帧容错；LiDAR 当前实现依据收敛为 `docs/vendor/lidar_pkg_ros2-main/`，历史 `docs/vendor/lidar_ros/` 保留为 ROS1/protocol comparison；ROS2 driver 已接入 `A5 60` start command、best-effort stop sequence、fake serial/split packet/失败关闭测试和 mock no-serial safety。`2026.06.03` 现场确认底盘可写控制口是 Orange Pi `/dev/ttyS5 @115200`，CEO 观察到 `T=1,L=0.08,R=0.08` 低速响应，随后现场执行 `T=1,L=0,R=0` 停车；8787 upper Robot API 已有低速/限时/自动停车的软件 guardrail 和 fake pyserial 单测。`2026.06.03_05-06_o1-ttyS5-safe-pulse-acceptance` 已新增默认 dry-run/read-only 的 safe pulse acceptance runner，只读取 8787 `/api/status` 或 `--status-json`，只有 `--execute-motion --confirm-physical-clearance` 双确认才经 8787 `/api/base/manual` 执行低速短 pulse，且 runner 不直接打开串口；本轮没有打开真实串口、没有 POST `/api/base/manual` 或 stop、没有发送真实 WAVE ROVER JSON、没有发送 `/cmd_vel` 或运动命令。`/dev/ttyACM0` 保持 STC/LiDAR 风险口结论，不能再当底盘口；`/dev/ttyS5` 上 `T=130` 仍未读到 `T=1001`，robot ACK、真实 `/imu/data`、`/battery`、`/odom`、自动停车/急停真实演练和 HIL packet 仍 `not_proven`，不是 HIL pass |
| O5：云中转控制面 | 约 96% software + material acceptance queue visible in PC workstation | Task B mock control plane 已覆盖 commands/status/ack、bearer/env、mock 4G/DB/queue/OSS/CDN graceful degradation；O5 readiness live health endpoint、PC aggregate health、Node/Python external probe 均已存在；Python runner 已支持 `--output` 和 HTTPS cloud base URL 下的脱敏 TLS evidence summary，PC workstation artifact API/contract 能展示 probe status、endpoint reachability、TLS summary、blocked reasons、fail-closed safety fields；只读 `GET /api/real-material/acceptance` 与 UI `RealMaterialAcceptancePanel.vue` 已把 O5/O6 external probe artifact 与 O7 browser smoke JSON 聚合成真实材料验收队列，本轮 `2026.06.02_09-10_real-material-runbook` 增加 `artifact_freshness` 和 `collection_runbook`，operator 可见 artifact mtime/age/fresh/stale/missing 与手动采集 recipe；该入口不执行 probe、不联网、不 SSH、不 POST、不访问 `/robots/*`、不读取硬件、不创建 WebRTC session、不发送控制，固定 `safe_to_control=false`、`sends_commands=false`、`robot_control_executed=false`、`delivery_success=false`；真实生产 TLS 验收、真实公网 HTTPS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 仍 `not_proven` |
| O6：云端核心后端 | 约 96% software + material acceptance queue visible in PC workstation | Task C mock archive/query/annotation/inference、board event publisher、algorithm feed、state path fence 已可复验；O6 archive live health、PC aggregate health、Node/Python external probe 均已存在；PC workstation 现在能读取最近一次 external probe artifact 的脱敏摘要，显示 O6 archive endpoint 的 reachability/schema/fail-closed/TLS evidence summary 状态；只读 `GET /api/real-material/acceptance` 已把 O6 archive/external probe 相关真实材料缺口纳入验收队列和 next actions，本轮新增 `artifact_freshness` 和 `collection_runbook`，把 artifact 新鲜度与手动采集 recipe 暴露给 operator；真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收和上车数据仍 `not_proven` |
| O7：PC 端运营调试平台 | 约 98% same-LAN camera/systemd + PC Live Operator + unified upper API software safety ready | PC console 六区 mock/live-like evidence 已覆盖回放、标注、推理、ASR/TTS stub、手控/寻路 stub 和 fail-closed；LAN-only WebRTC camera smoke、PC Chromium/browser smoke、30s smoke 与 180s long-stability collector 已有真实材料链路。`2026.06.02_20-21` 已证明 same-LAN 180s real browser material accepted 和 camera source guardrail ready；`2026.06.03_01-02` 已让远端 8088 camera smoke 由 fixed systemd unit 接管，`/health` ready。`2026.06.03_03-04_o7-upper-robot-api-safety` 已形成 8787 统一上位机 Robot API 软件安全边界，支持 camera/radar/base 状态，base manual 低速/限时/自动 stop，fake pyserial 单测通过。`2026.06.03_03-04_o7-pc-live-operator-upper-api` 已让 PC 首屏展示 8787 API 状态、8088 camera、radar `/scan` 缺口、base `/dev/ttyS5`、`T=1001 not observed` 和 manual control fail-closed；PC 没有 POST `/api/base/manual`，唯一 POST 是 camera WebRTC media preview 的 `/api/o7/local-webrtc-camera/offer`，该 `/offer` 不是底盘控制。真实 8787 远端监听、真实串口、真实 WAVE ROVER JSON、真实 `/cmd_vel`、真实 radar `/scan`、`T=1001`、robot ACK、真实 `/odom`、`/imu/data`、`/battery`、production path、手控/Nav2 和完整上车任务闭环仍 `not_proven` |

补充：`2026.06.02_20-21_o7-camera-offer-recovery` 已关闭上一轮 `camera_service_ready_but_first_frame_timeout_offer_http_500`，真实 same-LAN 180s browser material accepted。`2026.06.03_01-02_o7-camera-systemd-persistence` 已把远端 8088 camera smoke 从 operator-run/nohup 风险推进到 fixed systemd unit active。`2026.06.03_03-04_o7-upper-robot-api-safety` 和 `2026.06.03_03-04_o7-pc-live-operator-upper-api` 让 O7 从 PC 本地 fail-closed 面板推进到 unified upper API + PC Live Operator software safety ready，因此 O7 从约 97.5% 上调到约 98%。`2026.06.03_05-06_o1-ttyS5-safe-pulse-acceptance` 让 O1 从 upper API guardrail ready 推进到 safe pulse acceptance runner ready / watched execution pending：runner 默认 dry-run/read-only，双确认才经 8787 API 做低速短 pulse，且本轮没有发送任何运动命令。O1 仍约 93%，是最低 Objective：`/dev/ttyS5 @115200` 和低速 `T=1` 现场响应是控制口事实，safe pulse runner 是受控现场执行前置，但 `T=1001`、ACK、HIL、真实 `/odom`、`/imu/data`、`/battery` 和真实控制闭环仍未证明，不能因本轮 runner ready 上调 O1 HIL 进度；下一轮 O1 必须围绕 watched field pulse execution + ACK/`T=1001` capture 做现场看护短时点动、自动停车、急停路径和同源证据采集。O5/O6 仍约 96%。

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

1. **O1（约 93% software_reference + ttyS5 control write observed + low-speed T=1 field response observed + safe pulse acceptance runner ready / watched execution pending; T=1001/ACK/HIL not_proven）**：当前最低。2026-06-03 现场已经把底盘控制口从 USB STC `/dev/ttyACM0` 风险口修正为 Orange Pi `/dev/ttyS5 @115200`；CEO 观察到 `T=1,L=0.08,R=0.08` 可让底盘响应，随后现场停车 `T=1,L=0,R=0`。8787 upper Robot API 已具备低速/限时/自动停车的软件 guardrail；O1 safe pulse acceptance runner 已具备默认 dry-run/read-only、双确认执行、速度/时长限幅和 stop evidence 合同，但本轮没有真实串口/SSH/WAVE ROVER JSON/`cmd_vel`/运动命令，不能提升为 HIL pass：`T=130` 仍未读到 `T=1001`，ACK、自动停车真实演练、急停、ROS `/cmd_vel` 接入、`/imu/data`、`/battery`、`/odom` 和同源 HIL packet 仍未完成。下一步最高优先级是 watched field pulse execution + ACK/`T=1001` capture：在现场看护、物理净空、人工急停可用的条件下，经 8787 `/api/base/manual` 做低速短 pulse，并采集 status/manual/stop、ACK 或 `T=1001`、日志与安全复位证据；`/dev/ttyACM0` 继续只作为 STC/LiDAR 风险材料保留，不再作为底盘控制候选。
2. **O5（约 96% software + material acceptance queue visible in PC workstation；real material not_proven）**：本轮 `2026.06.02_09-10_real-material-runbook` 让 `GET /api/real-material/acceptance` 每条 item 增加 `artifact_freshness` 与 `collection_runbook`，operator 能看到 artifact mtime/age/fresh/stale/missing 和手动采集 recipe；下一步仍按 `docs/interfaces/o1_o5_90_evidence_boundary.md` 实际采集真实生产 TLS 验收、真实公网 HTTPS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 材料。
3. **O6（约 96% software + material acceptance queue visible in PC workstation；real material not_proven）**：本轮把 O6 archive/external probe 的 artifact 新鲜度和采集 runbook 纳入 PC workstation 验收队列，便于 operator 手动补材料；下一步优先把 archive core 推进到真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收和上车数据。
4. **O7（约 98% same-LAN camera/systemd + PC Live Operator + unified upper API software safety ready；production path / real control / ACK / HIL not_proven）**：`2026.06.02_20-21_o7-camera-offer-recovery` 已证明 same-LAN 180s browser material accepted 和 camera source guardrail ready。`2026.06.03_01-02_o7-camera-systemd-persistence` 已确认远端 8088 camera smoke 由 fixed systemd unit 接管，`enabled/active` 且 `MainPID` 与 listener pid 一致。`2026.06.03_03-04_o7-upper-robot-api-safety` 已形成 8787 统一上位机 Robot API 软件安全边界，`2026.06.03_03-04_o7-pc-live-operator-upper-api` 已让 PC 首屏展示 8787 API 状态、8088 camera、radar `/scan` 缺口、base `/dev/ttyS5`、`T=1001 not observed` 和 manual control fail-closed。PC 没有 POST `/api/base/manual`，唯一 POST 是 camera WebRTC media preview `/api/o7/local-webrtc-camera/offer`，不是底盘控制。下一步优先补真实 8787 远端监听、真实 `/api/base/manual` 受控灰度验收、真实串口/ACK/HIL 证据、reboot 后自恢复、browser 180s long-stability 复跑、camera peer cleanup/独占首帧复验、云 relay/TURN/auth/phone/browser production path、弱网、ASR/TTS、手控/Nav2 和完整上车任务闭环；不要把 8787 软件 API、PC 状态展示或 camera `/offer` 解读为生产控制或真实手控完成。

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
- LAN-only WebRTC camera smoke 已完成机器级 `/offer` answer、connected、`first_frame_received=true`、640x480 first_frame 和连续自检 peer cleanup；PC Chromium browser smoke 已证明同 LAN首帧、30s smoke 和 180s long-stability。`2026.06.02_20-21` 修复 camera source guardrail 后，same-LAN 180s browser material 已 `accepted`：首帧 1928ms、估算 13.92 fps、`framesDecoded=2507`、console/page errors 为 0、peer close 后 active connections 为 0。`2026.06.03_01-02` 已补远端 8088 camera smoke systemd persistence active 证据。下一步补产品入口安全边界、公网/云 relay、TURN、鉴权、phone/browser production path、reboot 后自恢复和 browser 180s 复跑证据。
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

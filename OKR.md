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

**当前进度：约 92%** | 主要缺口：当前 live WAVE ROVER 上车同 run HIL pass、轮速方向、IMU/battery 标定、HIL 准入、current same-run path generation success、Nav2 route execution success 和 PR #5 2D LiDAR / ToF 硬件材料。2026-07-10 10-30 新增 `wave_rover_nonzero_feedback_gate`；2026-07-10 16-24 新增 `trashbot.wave_rover_same_session_wheel_feedback_material.v1`，消费历史真实上位机 same-session wheel feedback artifact，验证 `Ran 18 tests ... OK`；2026-07-10 18-24 新增 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，成包消费历史 motion / feedback / LiDAR delta / operator / map artifact，验证 `Ran 10 tests in 0.017s OK`；2026-07-10 19-25 接入 `free_cell_map_material_bundle`，消费同 run artifacts `33-38`，输出 `free_cell_pixel_count=394`、`free_cell_has_free_cells=true`、`map_navigation_material_ready=true`，验证 `Ran 16 tests in 0.051s OK`。2026-07-10 20-26 在同一合同中接入 `localization_path_material_bridge`，消费 `38_pc_summary_after_map_fix.json` 的 same-run localization/path readback，输出 `localization_path_material_bridge_present=true`、`same_run_path_generation_requested=true`、`same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`，并仅把 June 11 clean-baseline `cross_run_clean_baseline_path_summary.path_point_count=31` 作为 cross-run comparator；验证 `py_compile` 通过、`Ran 24 tests in 0.104s OK`、CLI exit `0`、anchor rg 和 scoped `git diff --check` 通过。2026-07-10 22-29 继续在同一合同中接入 `bounded_motion_feedback_material`，消费 2026-06-10 历史真实上位机 bounded motion / T1001 / IMU-battery / odom readback 材料，CLI 输出 `bounded_motion_feedback_material_present=true`、`base_feedback_samples_latest_present=true`、`t1001_observed_count=2`、`bounded_motion_lr_nonzero_proven=false`、`wheel_direction_proven=false`、`imu_battery_calibration_proven=false`、`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`，验证 `py_compile` 通过、`Ran 29 tests in 0.173s OK`、CLI exit `0`、anchor rg 和 scoped `git diff --check` 通过。2026-07-10 23-31 在同一合同中新增 `manual_hil_gate_current_evidence_material`，消费 2026-06-11 历史真实 PC proxy / real-board manual gate 材料，CLI 输出 `manual_hil_gate_current_evidence_material_present=true`、`manual_hil_gate_status=blocked`、`manual_hil_gate_missing_fields=[external_video_recorded, visible_content_proven, wheel_feedback_lr_nonzero_proven, physical_motion_lidar_delta_proven]`、`stop_safety_smoke_forwarded=true`、`manual_nonstop_local_reject_present=true`、`manual_nonstop_remote_base_manual_called=false`、`proxy_remote_base_manual_not_called_by_local_reject=true`、`manual_gate_t1001_observed_count=2`、`operator_structured_delivery_claim_material_only=true`，并继续固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`nav2_route_execution_success=false`；验证 `py_compile` 通过、`Ran 33 tests in 0.246s OK`、CLI exit `0`、anchor rg 和 scoped `git diff --check` 通过。证据边界仍为 `software_proof_o1_motion_map_hil_material_bundle_only` / historical upper-computer software proof only，不等于 current live HIL pass、真实 safe-to-control、真实 delivery success、manual gate 已通过、bounded-run L/R 非零、wheel direction、IMU/battery calibration、same-run path generation success、Nav2 route execution success、current live map navigation readiness 或 production cloud。（开发阶段支持通过 Mock/虚拟串口模式完成软件控制链路并进行验证，真机实测留待后期集成）

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` 只通过参数启用。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，明确 `/odom` 是命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码设备名。

---

### Objective 5：云中转控制面产品化（原 O5/O6）

**当前进度：约 85%** | 主要缺口：真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 证据。2026-07-10 07-13 在 `o5_sqlite_shadow_same_task_gate` 基础上，新增 `o5_o6_live_endpoint_probe_readback`：same-task smoke 复用既有 `cloud_external_probe` / `cloud_db_queue_external_probe` summary 逻辑，对本地 relay `/healthz`、`/readyz`、`/preflightz` 做 software proof live endpoint probe，并把两类 probe 摘要以 `cloud_external_probe` / `cloud_db_queue_external_probe` additive section 写入同一 `task_id` 的 O6 archive/readback，再通过 consumer 回读 `cloud_external_probe_ready_not_production_proof` 与 `cloud_db_queue_external_probe_ready_not_production_proof`；hostile probe payload 只把对应 section 降级为 `blocked_not_proven`，不回显 URL、token、连接串、response body、本地路径或 traceback。2026-07-10 17-22 新增 `trashbot.cloud_production_cutover_readiness_packet.v1` 和 CLI `--write-cloud-production-cutover-readiness-packet-artifact` / preflight `--cloud-production-cutover-readiness-packet-artifact`，把 cloud deployment readiness、public ingress/TLS、DB/queue external probe、worker migration/cutover drain、OSS/CDN live probe 和 external evidence intake 等既有 summary 聚合成 cutover readiness packet；Robot Software 验证 `python3 -m py_compile` 通过、relay `Ran 179 tests in 74.465s OK`、scoped `git diff --check` 通过。该 packet 固定 `okr_credit_allowed=false`、`support_only_reason=no_real_production_external_evidence`、`next_live_command`、`production_ready=false`，proof boundary 为 `software_proof_cloud_production_cutover_readiness_packet_only`；本轮不归档 KR、不上调 O5，仍不证明真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 或真实 delivery success。（开发与测试阶段支持基于本地/Docker 的 Mock Cloud 进行控制面业务逻辑联调验证）

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`（4C 8G 无 GPU、SSH 端口、防火墙策略、容量边界）。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作公开只读视图入口；私有数据走 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，服务端/CI/上车均通过环境变量注入；密钥泄露有 rotate 流程。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须 graceful degradation，任务不丢，远程诊断能区分"网络问题"与"机器人问题"。

---

### Objective 6：云端核心后端——数据存档、模型推理与打标平台

**当前进度：约 92%** | 主要缺口：真实隧道、生产 DB/queue、OSS、TLS/4G、真实机器人数据、生产级查询容量、真实 live Nav2 route execution、delivery record/operator confirmation 和现场长期数据回灌。archive、event/evidence、labeling、model inference、consumer read API 已有 local/mock software proof；2026-07-10 13-20 新增 `current_field_evidence_material` additive section，O6 archive/readback 能保留并 fail-closed 真实上位机 current evidence material 的 camera/radar/map/Nav2/manual gate 摘要。2026-07-10 14-22 新增 `trashbot.o6.clean_baseline_nav2_path_material.v1`，把 2026-06-11 真实上位机 clean-baseline Nav2 no-motion path proof 接入同一 `task_id` 的 field evidence、artifact bundle、archive detail、consumer detail 与 `include=clean_baseline_nav2_path_material`。2026-07-10 15-22 新增 `trashbot.o6.field_operator_confirmation_material.v1`，把 operator report / operator confirmation material 作为 additive section 接入 archive/readback/include。2026-07-10 21-27 进一步新增 `trashbot.o6.localization_path_material_readback.v1`，把 O1 `localization_path_material_bridge` 产出的 same-run localization/path readback 以 additive section 接入 archive detail、field evidence、artifact bundle、consumer detail 与 `include=localization_path_material_readback`，并在返工中对齐 Algorithm 当前实际 payload：同时接受 `same_run_localization_tf_map_to_odom` / `same_run_localization_tf_map_to_base_link` 与旧别名 `same_run_tf_map_to_odom_observed` / `same_run_tf_map_to_base_link_observed`，兼容 `localization_path_material_readback_ready_not_route_execution_proof`，向 O7 回读 `localization_path_material_bridge_present`、`same_run_localization_material_present` 与 O7-facing aliases。验证为 Algorithm `Ran 75 tests in 0.570s OK`、O6 `Ran 181 tests in 77.619s OK`；一次瞬时 HTTP connection reset 复跑后通过。证据边界为 `software_proof_localization_path_material_readback_only`，不证明真实 production cloud、production DB/queue、多实例一致性、TLS/4G、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator acceptance、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或 hardware safety/HIL。

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

**当前进度：约 92%** | 主要缺口：真实 RTC/视频、真实 ASR/TTS、真实 wheel raw 非零反馈、真实电梯/回放/标注数据流、云端生产链路、真实 live Nav2 route execution、delivery/operator 材料和完整路线长期上车验证。PC/O7 consumer detail 已可围绕同一 `task_id` 消费 route replay、labeling、artifact readiness、field motion packet、Nav2 goal、delivery result、route bag evidence、route bag payload replay、route bag semantic replay、route bag pose progress replay、route execution result delivery readiness、route bag full semantic decode matrix、route delivery closure packet、cloud terminal result source、`same_task_mission_evidence_gate`、`same_task_mission_material_checklist`、`same_task_field_material_packet`、`current_field_evidence_material`、`same_task_route_execution_material_packet`、`clean_baseline_nav2_path_material`、`field_operator_confirmation_material` 和 `localization_path_material_readback` 等软件证据；2026-07-10 21-27 O7 consumer/UI 新增 localization/path material 展示与返工兼容，区分 same-run map/localization present、`same_run_path_generation_requested=true`、`same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`、cross-run clean-baseline comparator、blocked reasons、next required evidence 和 fixed false fields；同时兼容 O6 初版/返工版 status 与 TF alias。验证为 `Tests 489 passed (489)`、build 通过、lint 通过；固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`hil_pass=false`。证据边界为 `software_proof_localization_path_material_readback_only`，不证明真实 production cloud、production DB/queue、真实 live Nav2 route execution、真实 delivery record、真实 operator acceptance、真实 annotation API/export、真实 dataset export、真实关键帧媒体可访问、真实机器人运动、hardware safety、真实 delivery success 或长期路线验收。（允许使用 Mock 视频数据流、ASR/TTS 本地模拟和轨迹 Mock 优先进行 PC 端功能开发，最终再利用真实数据跑通）

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

更新时间：2026-07-10。

| Objective | 进度 | 主要缺口 |
| --- | --- | --- |
| O1：硬件协议可信底盘 | ~92% | 已有真实上位机 first-jog 转发、T1001 L/R 反馈采样字段和 LiDAR delta 过阈值；`2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate` 新增 fail-closed gate；`2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake` 消费历史真实上位机 same-session wheel feedback，验证 `Ran 18 tests ... OK`；`2026.07.10_18-24_o1_motion_map_hil_material_bundle` 消费 historical same-run motion/map material，验证 `Ran 10 tests in 0.017s OK`；`2026.07.10_19-25_o1_free_cell_map_material_bundle` 接入 same-run free-cell materials 33-38，验证 `Ran 16 tests in 0.051s OK`；`2026.07.10_20-26_o1_localization_path_material_bridge` 接入 `localization_path_material_bridge`，消费 `38_pc_summary_after_map_fix.json` 的 same-run localization/path readback，输出 `same_run_path_generation_requested=true`、`same_run_path_generation_succeeded=false`、`same_run_path_generated=false`、`same_run_path_point_count=0`、`same_run_path_proven=false`；`2026.07.10_22-29_o1_bounded_motion_feedback_material` 接入 `bounded_motion_feedback_material`，消费 2026-06-10 历史真实上位机 bounded motion / T1001 / IMU-battery / odom readback 材料，输出 `bounded_motion_feedback_material_present=true`、`base_feedback_samples_latest_present=true`、`t1001_observed_count=2`、`bounded_motion_lr_nonzero_proven=false`、`wheel_direction_proven=false`、`imu_battery_calibration_proven=false`、`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`；`2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake` 接入 `manual_hil_gate_current_evidence_material`，消费 2026-06-11 历史真实 PC proxy / real-board manual gate 材料，输出 `manual_hil_gate_current_evidence_material_present=true`、`manual_hil_gate_status=blocked`、`manual_hil_gate_missing_fields=[external_video_recorded, visible_content_proven, wheel_feedback_lr_nonzero_proven, physical_motion_lidar_delta_proven]`、`stop_safety_smoke_forwarded=true`、`manual_nonstop_local_reject_present=true`、`manual_nonstop_remote_base_manual_called=false`、`proxy_remote_base_manual_not_called_by_local_reject=true`、`manual_gate_t1001_observed_count=2`、`operator_structured_delivery_claim_material_only=true`，验证 `Ran 33 tests in 0.246s OK`、CLI exit `0`、anchor rg 和 scoped diff check 通过；证据边界为 `software_proof_o1_motion_map_hil_material_bundle_only` / historical upper-computer software proof only，仍不是 current live HIL、safe-to-control、delivery success、manual gate 已通过、wheel direction、IMU/battery calibration、same-run path generation success、Nav2 route execution success、current live map navigation readiness 或 production cloud，仍缺当前同 run HIL 准入和现场 acceptance |
| O5：云中转控制面 | ~85% | `2026.07.10_07-13_o5_o6_live_endpoint_probe_readback` 已把 same-task smoke 推进到 `cloud_external_probe` / `cloud_db_queue_external_probe` additive readback；`2026.07.10_08-14_same_task_mission_artifact_credit_gate` 进一步把 same-task mission credit 误判固化为软件 hard gate，新增 `same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`，明确 local/mock probe、readback-only、checklist-only 不能再计主 OKR 增量；`2026.07.10_17-22_o5_production_cutover_readiness_packet` 新增 `trashbot.cloud_production_cutover_readiness_packet.v1`、CLI 写出和 preflight 消费，验证 `Ran 179 tests in 74.465s OK`，但因没有真实 external production evidence，固定 `okr_credit_allowed=false`、`next_live_command`、`proof_scope_class=software_proof_support_only`，proof boundary 为 `software_proof_cloud_production_cutover_readiness_packet_only`；本轮 O5 保持约 85%，不归档 KR，仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 验收 |
| O6：云端核心后端 | ~92% | local/mock archive/read model 已覆盖 field evidence、annotation、artifact bundle/access、offline seed、route-root seed、field motion packet、Nav2 goal evidence、delivery result evidence、route bag evidence、route bag payload replay、route bag semantic replay、route bag pose progress replay、route execution result delivery readiness、route bag full semantic decode matrix、route delivery closure packet、cloud terminal result delivery bridge、same task mission evidence gate、`same_task_field_material_packet`、`same_task_route_execution_material_packet`、`current_field_evidence_material`、`clean_baseline_nav2_path_material`、`field_operator_confirmation_material`、`cloud_external_probe` / `cloud_db_queue_external_probe` 与 `localization_path_material_readback` additive readback；本 sprint `2026.07.10_21-27_o6_o7_localization_path_material_readback` 消费 O1 `localization_path_material_bridge` 的新材料增量，并在 O6 返工中修复 Algorithm/O6/O7 真实 payload shape drift：兼容 `_readback` ready status、新旧 TF 字段别名和 O7-facing bridge/localization aliases，验证 Algorithm `Ran 75 tests`、O6 `Ran 181 tests`、O7 `489 passed`；仍缺真实 production cloud、真实隧道、生产 DB/queue、OSS、TLS/4G、真实机器人数据、真实 live Nav2 route execution、真实 delivery record、真实 operator acceptance、真实 annotation API/export、真实 delivery success 和生产级查询容量 |
| O7：PC 端运营调试平台 | ~92% | PC/O7 consumer detail 已可围绕同一 `task_id` 展示 route replay、labeling、artifact readiness、field motion packet、Nav2 goal evidence、delivery result evidence、route bag evidence、route bag payload replay、route bag semantic replay、route bag pose progress replay、route execution result delivery readiness、route bag full semantic decode matrix、route delivery closure packet、same task mission evidence gate、`same_task_mission_material_checklist`、`same_task_field_material_packet`、`same_task_route_execution_material_packet`、`current_field_evidence_material`、`clean_baseline_nav2_path_material`、`field_operator_confirmation_material` 与 `localization_path_material_readback`；本 sprint 新增 localization/path material 展示和 fail-closed 回归，区分 same-run localization/path false 结论、cross-run comparator、blocked reasons 和 required evidence，并兼容 O6 初版/返工版 status 与 TF/bridge alias，验证 `Tests 489 passed (489)`、build、lint 通过；仍缺真实 production cloud、production DB/queue、真实 RTC/视频、真实 ASR/TTS、真实回放/标注数据流、真实关键帧媒体可访问、真实 annotation API/export、真实 live Nav2 route execution、wheel raw 非零、真实 delivery record、真实 operator acceptance、真实 delivery success 和完整路线长期验收 |

**已归档 Objective（软件侧完成，等待真实现场验证）：**

| Objective | 软件侧进度 | 归档原因 |
| --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 软件完成 ~99% | 状态机、行为链、电梯状态链、任务记录软件侧全部完成；等待真实路线/电梯/现场跑通后升回当前 |
| O3：可验证导航与固定路线 | 软件完成 ~99% | learn.launch/fixed_route/Nav2 dry-run 全部完成；等待真实路线采集、Nav2 实跑、关键帧实景证据 |
| O4：手机用户体验与量产边界 | 软件完成 ~99% | 手机 UI、地图首屏、任务下发、状态展示软件侧全部完成；等待真实 iPhone/Android 设备验收和真实送达 |

> 归档 KR 详情见 `docs/process/okr_progress_log.md`。真实现场材料到位后重新激活对应 Objective。

---

## 5. 当前最高优先级

按当前可推进价值与完成度排序：

1. **O5（~85%）**：当前最低进度项。`cloud_production_cutover_readiness_packet` 已把 production cutover readiness 缺口聚合成 support-only packet，但 `okr_credit_allowed=false`，不归档 KR。下一轮只有接入真实 external production evidence（HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser）才可考虑 OKR 增量；否则转 O1 current same-run HIL 或 O6/O7 live route/delivery/operator/production readback。
2. **O1（~92%）**：本轮在 `bounded_motion_feedback_material` 之上，进一步接入 `manual_hil_gate_current_evidence_material`，消费 2026-06-11 历史真实 PC proxy / real-board manual gate 材料；`manual_hil_gate_current_evidence_material_present=true`、`manual_hil_gate_status=blocked`、`stop_safety_smoke_forwarded=true`、`manual_nonstop_local_reject_present=true`、`manual_nonstop_remote_base_manual_called=false`、`proxy_remote_base_manual_not_called_by_local_reject=true`、`manual_gate_t1001_observed_count=2` 已可复验，但 `manual_hil_gate_missing_fields` 仍包含 `external_video_recorded`、`visible_content_proven`、`wheel_feedback_lr_nonzero_proven`、`physical_motion_lidar_delta_proven`，且 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false` 仍说明这不是 current live HIL 或安全控制证明。下一步必须切到当前同 run `feedback_T1001.log`、motion command、operator observation、external video、LiDAR motion delta 和 HIL acceptance record，并把 localization/path bridge 接 current live path generation 或 route execution proof。
3. **O6（~92%）**：已能把 current field evidence material、clean-baseline Nav2 no-motion path material、field operator confirmation material 和 `localization_path_material_readback` 接入同一 `task_id` archive/readback，并兼容 Algorithm 当前实际 localization/path payload shape。下一步必须接真实 production cloud、真实隧道、生产 DB/queue、OSS、真实机器人数据，或接 live route execution / delivery record / operator acceptance，产出真正的 `mission_artifact_delta`；否则 O6 只能保持回归守护。
4. **O7（~92%）**：当前已能消费 current field evidence material、clean-baseline Nav2 path material、same-task route execution material packet、field operator confirmation material 和 `localization_path_material_readback`，并独立展示 O6 顶层状态、材料摘要、blocked reasons、next evidence 与 same-run/cross-run 边界。下一步必须继续消费更强的真实或准现场 materials，如 live route execution、delivery record、operator acceptance、真实关键帧可访问或生产云 readback；只读 checklist/surface 默认视为 support-only，不再提升 OKR。
5. **现场 O3 验证 lane（归档 Objective 临时激活）**：CEO 已提供真实上位机 SSH，当前优先级是把 managed localization 继续推进到 no-motion planner readiness / path generation proof；随后再消费 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL，避免继续停留在只读 handoff/review/surface。

> 2026-06-09 方向调整：O6 最小 local/mock 数据底座已形成，CEO 又提供真实上位机 SSH。因此下一轮优先跑 `sprints/2026.06.09_13-00_board-live-slam-route/`，用真实上位机补 O3 路线证据；O6/O7 后续必须消费这份真实路线材料，而不是继续堆叠只读 surface。
>
> 2026-06-10 方向微调：在 managed localization proof 之后，O3 现场验证 lane 先推进 no-motion planner readiness / path generation proof，再进入 route execution 材料收集。
>
> 2026-07-09 收口：`sprints/2026.07.09_02-31_o6_field_evidence_archive_ingest/` 已把 field evidence manifest 接入 O6 local/mock archive 并由 O7 consumer read 主路径兼容显示；该证据提升 O6/O7 软件侧数据链路，但不改变真实生产云、真实路线回放、真实视频、wheel raw 非零或 delivery success 缺口。
>
> 2026-07-09 收口：`sprints/2026.07.09_05-51_o7_route_replay_labeling_mvp/` 已把 O7 consumer detail 主路径推进到同一 `task_id` 下的 `route_replay_mvp` 与 `labeling_mvp`，并保留 `submit_blocked_fail_closed` 和所有危险字段 false；O7 保守上调到约 34%，但 KR3/KR4 不归档完成。
>
> 2026-07-09 收口：`sprints/2026.07.09_06-53_o6_o7_annotation_submit_export/` 已完成 local/mock annotation submit receipt 与 task-level JSONL export 主路径，O6 `test_remote_cloud_relay` 149 tests OK，O7 `catalog.test.ts` 204 passed、`App.test.ts` 247 passed、build、lint 通过；证据边界为 `software_proof_local_mock_annotation_only`，O6/O7 保守上调到约 36%/37%，不归档 KR。
>
> 2026-07-09 收口：`sprints/2026.07.09_07-55_o6_artifact_seed_media_preflight/` 已把 O6 `artifact_media_preflight` 接到同一 `task_id` 的 route/replay/keyframe/evidence 摘要回读，并让 O7 优先消费该合同；缺字段时保守派生 `derived_blocked_not_proven`，继续展示 media refs、blocked reasons 和 next required evidence。证据边界为 `software_proof_local_mock_media_preflight_only`，O6/O7 仅保守上调到约 37%/38%，不归档 KR。
>
> 2026-07-09 收口：`sprints/2026.07.09_08-56_o6_artifact_bundle_ingest/` 已新增 `POST /api/o6/archive/artifact-bundle`，接受 `trashbot.o6.artifact_bundle.v1` 结构化摘要并复用 file-backed archive store 写入 task、trajectory、events、evidence refs 和 `artifact_media_preflight`，archive task detail / consumer detail 同步增加 `artifact_bundle` / `artifact_bundle_consumer_ingest` additive alias，`field-evidence` 也兼容 wrapper/直传 bundle；`dangerous true`、empty refs、unsafe refs 继续 fail-closed，`test_remote_cloud_relay` 提升到 151 tests OK。证据边界为 `software_proof_local_mock_artifact_bundle_ingest_only`，O6 保守上调到约 39%，O7 不上调且不归档 KR。
>
> 2026-07-09 收口：`sprints/2026.07.09_09-57_o7_artifact_bundle_consumer_readiness/` 已把 O7 consumer detail 主路径继续推进到 `artifact_bundle_readiness`，让同一 `task_id` 的 bundle / ingest / wrapper 信息显式归一为计数、样本 refs、blocked reasons 和 next required evidence；worker 记录 `npm run test -- --runInBand` 因 Vitest 不支持该参数而失败，回退 `npm run test` 通过，结果 `3 passed` / `470 passed`，同时 `npm run build`、`npm run lint`、`git diff --check` 均通过。证据边界为 `software_proof_local_mock_artifact_bundle_consumer_readiness`，O7 保守上调到约 40%，O6 维持约 39%，本轮不归档 KR。
>
> 2026-07-09 收口：`sprints/2026.07.09_10-58_o6_artifact_access_probe/` 已把 O6 推进到 `trashbot.o6.artifact_access_probe.v1`，支持 `artifact_access_root` / `TRASHBOT_O6_ARTIFACT_ACCESS_ROOT`、64KB 小文件上限、allowlist root 内只读 exists/size/sha256/detected_type/blocked_reason/proof_scope 摘要，并暴露到 archive detail、field_evidence、artifact_bundle、consumer detail 和 `include=artifact_access_probe`；O7 secondary consumer 已读取 `artifact_access_probe` 并在 `artifact_bundle_readiness` / UI 展示 counts、basename refs、detected_type、size、sha256 prefix、blocked reasons 和 next evidence。验证为 O6 `Ran 153 tests in 52.427s OK`，O7 `npm run test` 通过 `3 passed` / `472 passed`，build、lint、`git diff --check` 通过。证据边界为 `software_proof_local_mock_artifact_access_probe_only`，O6/O7 保守上调到约 42%/42%，本轮不归档 KR；不证明真实 OSS/CDN、production cloud、真实机器人数据、真实媒体访问、真实 annotation API、真实 dataset export、ROS2 runtime、机器人运动或 delivery success。
>
> 2026-07-09 收口：`sprints/2026.07.09_12-58_o6_o7_route_root_seed_gate/` 已解除 route-root seed 对 `route_bag` gate 的硬依赖；Algorithm route-root fixture 输出 `gate_pass=true`，O6 新增 `trashbot.o6.route_root_seed_gate.v1` 并在缺 `route_bag` 时输出 `route_bag_required=false`、`route_bag_present=false`、`route_bag_missing_optional`、`route_bag_optional_evidence` 和 `route_root_seed_status=local_mock_route_root_seed_ready`，O7 展示 route-root seed readiness、blocked reasons、next evidence 和 false safety fields。验证为 O6 `Ran 154 tests in 53.491s OK`，O7 `npm run test` 通过 `3 passed` / `475 passed`，build、lint、`git diff --check` 通过。证据边界为 `software_proof_local_mock_route_root_seed_gate_only`，O6/O7 保守上调到约 47%/47%，本轮不归档 KR；不证明真实生产云、真实 route_bag、真实媒体、真实 annotation API、真实 dataset export、真实机器人运动或 delivery success。
>
> 2026-07-09 收口：`sprints/2026.07.09_14-00_o6_o7_field_motion_evidence_packet/` 已把 6 月现场 `map.yaml/.pgm`、`route.csv`、keyframes、remote_capture motion logs 与 `derived_replay.jsonl` 归一成 `field_motion_evidence_packet`，Algorithm 输出 `schema=trashbot.field_motion_evidence_packet.v1`、`proof_scope=software_proof_field_motion_evidence_packet_only`、`frame_count=17`、`distance_m=0.167998`、`nonzero_displacement_observed=true`、`live_motion_evidence_present=true`、`route_bag_or_live_nav2_log.present=true/source=live_motion_log/route_bag_present=false` 和 false safety fields；O6 支持 packet additive ingest/readback，验证 `Ran 155 tests in 53.281s OK`；O7 消费 packet 到 consumer detail、artifact bundle readiness、route replay、labeling workspace，前端验证 `3 passed` / `476 passed`、build、lint、`git diff --check` 通过。证据边界为 `software_proof_field_motion_evidence_packet_only`，O6/O7 保守上调到约 50%/50%，本轮不归档 KR；不证明真实 production cloud、真实 `route_bag`、真实 Nav2 live run、真实 delivery success、真实 OSS/CDN、真实 annotation API/export。
>
> 2026-07-09 收口：`sprints/2026.07.09_15-00_o6_o7_nav2_goal_evidence_packet/` 已把 O11 Nav2 goal execution proof 转成 `trashbot.nav2_goal_execution_evidence.v1`，证据边界为 `software_proof_nav2_goal_execution_evidence_only`；Algorithm 新增 `--nav2-goal-proof-json` 并把摘要写入 manifest 顶层和 field packet，验证 `Ran 29 tests in 0.059s OK`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 include 回读，验证 `Ran 156 tests in 53.382s OK`；O7 UI 展示 Nav2 goal evidence 只读摘要，验证 `npm run test` 3 files / `477 passed`，build、lint 通过。O6/O7 保守上调到约 53%/53%，本轮不归档 KR；不证明真实 production cloud、真实 `route_bag`、真实 live Nav2 run、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或完整路线长期验收。
>
> 2026-07-09 收口：`sprints/2026.07.09_16-00_o6_o7_delivery_result_evidence/` 已把 delivery result / operator confirmation readiness 推进成 `trashbot.delivery_result_evidence.v1`，证据边界为 `software_proof_delivery_result_evidence_only`；Algorithm 新增 `--delivery-result-json` 并把摘要写入 manifest 顶层和 field packet，验证 `Ran 20 tests in 0.069s OK`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=delivery_result_evidence` 回读，验证 `Ran 157 tests in 55.196s OK`；O7 UI 与 artifact bundle readiness 展示 delivery result evidence 只读摘要，验证 `npm run test` 3 files / `478 passed`，build、lint 通过。O6/O7 保守上调到约 56%/56%，本轮不归档 KR；不证明真实 production cloud、真实 `route_bag`、真实 live Nav2 run、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或完整路线长期验收。
>
> 2026-07-09 收口：`sprints/2026.07.09_18-01_o6_o7_route_bag_payload_replay/` 已把准现场 DB3 route bag 从 metadata 摘要推进到 `route_bag_payload_replay`，证据边界为 `software_proof_route_bag_payload_replay_only`；Algorithm 只读解析 DB3 `messages.data` BLOB 并把 `payload_sha256_prefix_samples` 收敛为短 hex `string[]`，验证 `Ran 26 tests ... OK`、worker report `32 tests passed`，payload replay smoke 输出 `payload_sample_count=8`、`payload_size_min_bytes=72`、`payload_size_max_bytes=921652`；O6 `test_remote_cloud_relay` 159 tests OK，O7 `npm run test` 3 files / `479 passed`、build、lint 通过。O6/O7 保守上调到约 62%/62%，本轮不归档 KR；不证明真实 production cloud、真实 live Nav2 route execution、raw ROS message payload 语义解析、robot motion、真实 delivery record、operator confirmation、delivery success、真实 OSS/CDN 或真实 annotation API/export。
>
> 2026-07-09 收口：`sprints/2026.07.09_19-00_o6_o7_route_bag_semantic_replay/` 已把准现场 DB3 route bag 从 payload 摘要推进到 `route_bag_semantic_replay`，证据边界为 `software_proof_route_bag_semantic_replay_only`；Algorithm 只读对白名单 ROS topic 做有限语义摘要，验证 `Ran 37 tests ... OK`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_semantic_replay` 回读，验证 `Ran 160 tests in 56.976s OK`；O7 UI 与 artifact bundle readiness 展示 semantic topic types、LaserScan/Image/TF summary、blocked reasons、next required evidence 和 false safety fields，验证 `npm run test` 3 files / `479 passed`、build `built in 1.74s`、lint 通过。O6/O7 保守上调到约 65%/65%，本轮不归档 KR；不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export，且不证明 raw ROS message payload 全量语义解析或真实生产云/现场回放链路。
>
> 2026-07-09 收口：`sprints/2026.07.09_20-03_o6_o7_route_bag_pose_progress_replay/` 已把准现场 DB3 route bag 从 semantic replay 推进到 `route_bag_pose_progress_replay`，证据边界为 `software_proof_route_bag_pose_progress_replay_only`；Algorithm 只读解析 TF/Odometry 白名单位姿进度摘要，验证 `Ran 41 tests in 0.192s OK`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_pose_progress_replay` 回读，验证 `Ran 161 tests in 57.594s OK`；O7 UI 与 artifact bundle readiness 展示 pose topic types、frame pairs、start/end pose、displacement、nonzero observed、blocked reasons、next required evidence 和 false safety fields，验证 `npm run test` 3 files / `479 passed`、build、lint 通过。O6/O7 保守上调到约 68%/68%，本轮不归档 KR；不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或 raw ROS message payload 全量语义解析。
>
> 2026-07-09 收口：`sprints/2026.07.09_21-04_o6_o7_route_execution_result_delivery_readiness/` 已把 O6/O7 从 `route_bag_pose_progress_replay` 进一步推进到 `route_execution_result_delivery_readiness`，证据边界为 `software_proof_route_execution_result_delivery_readiness_only`；Algorithm 新增 `trashbot.route_execution_result_delivery_readiness.v1`，把 route execution result、delivery readiness、operator confirmation readiness 写入 manifest 顶层和 `field_motion_evidence_packet.route_execution_result_delivery_readiness`，验证 `Ran 44 tests in 0.204s OK`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_execution_result_delivery_readiness` 回读，验证 `Ran 162 tests in 58.732s OK`；O7 UI 与 artifact bundle readiness 展示 route execution result、delivery readiness、operator confirmation readiness、blocked reasons、next required evidence 和 false safety fields，并在返工后收紧为顶层 ready 只信任 O6 顶层 `status==="route_execution_result_delivery_readiness_ready_not_delivery_proof"`，子 readiness 不得把整体 blocked 推成 ready，验证 `npm run test` `482 passed`、build、lint 通过。O6/O7 保守上调到约 71%/71%，本轮不归档 KR；不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或 raw ROS message payload 全量语义解析。
>
> 2026-07-09 收口：`sprints/2026.07.09_22-05_o6_o7_route_bag_full_semantic_decode_matrix/` 已把 O6/O7 从结果链 readiness 进一步推进到 `route_bag_full_semantic_decode_matrix`，证据边界为 `software_proof_route_bag_full_semantic_decode_matrix_only`；Algorithm 新增 `trashbot.route_bag_full_semantic_decode_matrix.v1`，只读 DB3 `topics` / `messages.data` 生成 per topic/type decoded、unsupported、failed coverage matrix，并写入 manifest 顶层和 `field_motion_evidence_packet.route_bag_full_semantic_decode_matrix`，验证 `Ran 48 tests in 0.251s OK`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_full_semantic_decode_matrix` 回读，验证 `Ran 163 tests in 61.181s OK`；O7 UI 与 artifact bundle readiness 展示 matrix status、coverage ratio、decoded/unsupported/failed counts、sample topic/type、blocked reasons、next required evidence 和 false safety fields，验证 `npm run test` `482 passed`、build、lint 通过。O6/O7 保守上调到约 74%/74%，本轮不归档 KR；不证明真实 production cloud、raw ROS message payload 已全量语义回放、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。
>
> 2026-07-09 收口：`sprints/2026.07.09_23-07_o6_o7_route_bag_odometry_semantic_decoder/` 已把 O6/O7 从 full semantic decode matrix 继续推进到 Odometry semantic decoder 覆盖；Algorithm 将 `nav_msgs/msg/Odometry` 纳入 `route_bag_semantic_replay` 白名单和 full matrix decoder map，新增 `decode_odometry_payload` 与 `odometry_summary`，验证 `Ran 48 tests in 0.275s OK`；O6 fixture/readback 证明 `nav_msgs.msg.Odometry` 和 `decoder=decode_odometry_payload` 可在 field evidence、artifact bundle、archive detail、consumer detail 和 include 中保留，验证 `Ran 163 tests in 60.247s OK`；O7 fixture/UI 证明 `semantic_topic_types` 包含 Odometry，`/odom` matrix item 为 decoded，验证 `npm run test` `482 passed`、build、lint 通过。O6/O7 保守上调到约 76%/76%，本轮不归档 KR；不证明真实 production cloud、raw ROS message payload 已全量语义回放、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。
>
> 2026-07-10 收口：`sprints/2026.07.10_00-06_o6_o7_diagnostic_array_semantic_decoder/` 已把 O6/O7 从 Odometry decoder 覆盖继续推进到 DiagnosticArray semantic decoder 覆盖；Algorithm 将 `diagnostic_msgs/msg/DiagnosticArray` 纳入 `route_bag_semantic_replay` 白名单和 full matrix decoder map，新增 `decode_diagnostic_array_payload` 与 `diagnostic_array_summary`，验证 `Ran 48 tests in 0.236s OK`；O6 fixture/readback 证明 `diagnostic_msgs.msg.DiagnosticArray` 和 `decoder_name=decode_diagnostic_array_payload` 可在 field evidence、artifact bundle、archive detail、consumer detail 和 include 中保留，验证 `Ran 163 tests in 60.706s OK`，并保持 `safe_to_control=false`、`delivery_success=false`；O7 fixture/UI 证明 `/diagnostics` matrix item 为 decoded，验证 `npm run test` `482 passed`、build、lint 通过。O6/O7 保守上调到约 78%/78%，本轮不归档 KR；不证明真实 production cloud、raw ROS message payload 已全量语义回放、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN 或真实 annotation API/export。下一轮优先真实/准现场 live Nav2 result、delivery record/operator confirmation 或 production cloud；若继续 decoder，必须选择 matrix 仍有实际 gap 的安全 topic type。
>
> 2026-07-10 收口：`sprints/2026.07.10_01-07_o6_o7_route_delivery_closure_packet/` 已把 O6/O7 从分散的 Nav2 goal evidence、delivery result evidence、route execution result delivery readiness 和 route bag pose progress replay，进一步收束成同一 `task_id` 的 `route_delivery_closure_packet` 软件闭合包；Algorithm 新增 `trashbot.route_delivery_closure_packet.v1` 并在 manifest 顶层与 `field_motion_evidence_packet.route_delivery_closure_packet` 输出 `route_delivery_closure_ready_not_success_proof`、linked evidence flags、blocked reasons、next required evidence 和固定 false safety fields，验证 `Ran 50 tests in 0.252s OK`；O6 新增 `trashbot.o6.route_delivery_closure_packet.v1`，让 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_delivery_closure_packet` 可安全回读，验证 `Ran 164 tests in 61.973s OK`；O7 workstation 新增 closure packet 摘要面板和多来源折叠，验证 `npm run test` `483 passed`、build、lint 通过。O6/O7 保守上调到约 80%/80%，本轮不归档 KR；不证明真实 delivery success、真实 production cloud、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 robot motion、真实 OSS/CDN 或真实 annotation API/export。下一轮优先 production cloud、真实或准现场 live route execution、delivery record/operator confirmation，而不是继续做 summary wrapper。
>
> 2026-07-10 收口：`sprints/2026.07.10_02-06_o5_o6_cloud_terminal_result_delivery_bridge/` 已把 O5 `trashbot.cloud_command_terminal_result.v1` robot-facing terminal result 桥接为 O6/O7 既有 `trashbot.delivery_result_evidence.v1` 安全来源；Algorithm 新增 `--cloud-terminal-result-json`，输出 `source=cloud_command_terminal_result`、`source_schema=trashbot.cloud_command_terminal_result.v1`、`status=ready_not_delivery_proof`，验证 `Ran 53 tests in 0.272s OK`；O6 返工接受 Algorithm 的短 status，并对外规范化为 `delivery_result_evidence_ready_not_delivery_proof`，archive detail、field evidence、artifact bundle、consumer detail 与 `include=delivery_result_evidence` 均保留来源，验证 `Ran 165 tests in 62.817s OK`。O5/O6/O7 保守调整到约 81%/82%/81%，本轮不归档 KR；证据边界为 `software_proof_cloud_terminal_result_delivery_bridge_only`，不证明真实 production cloud、真实 4G/TLS、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 robot motion 或真实 delivery success。下一轮必须优先用该桥接合同接真实或准现场 same-task terminal result + live route execution / production cloud evidence。
>
> 2026-07-10 收口：`sprints/2026.07.10_03-09_o5_o6_o7_same_task_mission_gate/` 已把上一轮 O5 terminal result bridge 推进为同一 `task_id` 的 `same_task_mission_evidence_gate`；Algorithm 新增 `trashbot.same_task_mission_evidence_gate.v1`，验证 `Ran 55 tests in 0.291s OK`；O6 新增 `trashbot.o6.same_task_mission_evidence_gate.v1` archive/readback/include，验证 `Ran 166 tests in 63.477s OK`；O7 workstation consumer/display 支持 gate 状态、terminal/cloud source、linked flags、blocked reasons 与 next evidence，验证 `Tests 484 passed (484)`、build、lint 通过。O5/O6/O7 保守调整到约 82%/84%/83%，本轮不归档 KR；证据边界为 `software_proof_same_task_mission_evidence_gate_only`，not production cloud，not delivery success，不证明真实 4G/TLS、production DB/queue、真实 live Nav2、真实 robot motion、真实 delivery record 或真实 operator confirmation。下一轮必须消费真实或准现场 same-task mission materials，而不是继续 wrapper/decoder。
>
> 2026-07-10 收口：`sprints/2026.07.10_04-10_o5_reconciliation_same_task_archive_smoke/` 已把 O5 relay `trashbot.cloud_command_result_reconciliation.v2` recorded wrapper 接入 Algorithm manifest 与 O6 archive/readback same-task gate；Algorithm 只在 `result_state=terminal_result_recorded` 且 nested `terminal_result.schema=trashbot.cloud_command_terminal_result.v1` 时下钻，输出合同仍为 `trashbot.delivery_result_evidence.v1` / `source_schema=trashbot.cloud_command_terminal_result.v1`，验证 `Ran 58 tests in 0.304s OK`；Robot Software 新增本地 smoke 串起 `POST /api/commands/confirm-dropoff`、terminal result、`GET /api/commands/<command_id>/result`、manifest、`POST /api/o6/archive/field-evidence` 和 `include=same_task_mission_evidence_gate` consumer readback，读回 `same_task_mission_gate_ready_not_success_proof`，验证 `Ran 2 tests in 1.180s OK` 与 relay `Ran 166 tests in 64.457s OK`。O5 保守上调到约 83%，O6/O7 维持约 84%/83%，本轮不归档 KR；证据边界为 `software_proof_o5_reconciliation_same_task_archive_smoke_only`，不证明真实 production cloud、真实 4G/TLS、production DB/queue、OSS/CDN live traffic、真实 live Nav2 route execution、真实 delivery record、真实 operator confirmation、真实 robot motion、真实手机/browser 或真实 delivery success。下一轮必须接真实或准现场 same-task production cloud / live route execution / delivery record 材料。
>
> 2026-07-10 收口：`sprints/2026.07.10_05-10_o5_sqlite_shadow_same_task_gate/` 已把上一轮 O5 in-process/file smoke 推进到 SQLite shadow restart/readback same-task gate；Robot Software 将 `o5_same_task_mission_archive_smoke.py` 增加 `--state-backend file|sqlite`，默认 file 兼容，SQLite 模式使用 `build_server(..., state_backend="sqlite")` 写入 terminal result 后关闭 relay，再用同一 SQLite state path 重启并读取 `GET /api/commands/<command_id>/result?robot_id=...`。readback reconciliation 继续进入 Algorithm manifest、O6 field evidence archive 和 `include=same_task_mission_evidence_gate` consumer readback，summary 输出 `relay_state_backend=sqlite`、`relay_restart_readback=true`、`sqlite_state_store_reopened=true`、`reconciliation.result_state=terminal_result_recorded`、`consumer.same_task_mission_gate_status=same_task_mission_gate_ready_not_success_proof`，并固定 `connects_cloud_production=false`、`delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。验证为 `py_compile` 通过、`Ran 3 tests in 2.282s OK`、relay `Ran 166 tests in 64.559s OK`、scoped `git diff --check` 通过。O5 保守上调到约 84%，O6/O7 维持约 84%/83%，本轮不归档 KR；证据边界为 `software_proof_o5_sqlite_shadow_same_task_gate_only`，不证明真实 production cloud、production DB、queue、多实例一致性、HTTPS/TLS、4G/SIM、OSS/CDN、live Nav2、delivery record、operator confirmation、真实手机/browser 或 delivery success。下一轮继续 O5 只能接真实 production cloud、production DB/queue external probe 或 live endpoint evidence；否则应转向 O7 的 same-task mission material checklist，不再用 local shadow/smoke 提升百分比。
>
> 2026-07-10 收口：`sprints/2026.07.10_06-10_o7_same_task_mission_material_checklist/` 已把 O7 从 `same_task_mission_evidence_gate` 只读摘要推进到 operator 可执行 `same_task_mission_material_checklist`；Full-stack/O7 新增 additive schema `trashbot.pc_tools_workstation.o7_same_task_mission_material_checklist.v1`，覆盖 same task identity、terminal/cloud result、route execution material、delivery record、operator confirmation、route pose progress、production cloud readback 和 safety invariants 8 个材料项，并在 UI 中邻近 gate 展示。验证 `cd pc-tools/workstation && npm run test && npm run build && npm run lint` 通过，关键结果 `Tests 484 passed (484)`，build 仅有 Vite chunk-size warning，lint 通过；首轮 TypeScript 失败已定位并修复；`git diff --check` 通过；固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。O7 从约 83% 保守上调到约 85%，O5/O6 维持约 84%，本轮不归档 KR；证据边界为 `software_proof_o7_same_task_mission_material_checklist_only`，不证明真实 production cloud、production DB/queue、live Nav2 route execution、真实 delivery record、operator confirmation、robot motion、hardware safety 或 delivery success。下一轮由于 O5/O6 约 84% 成为最低/并列低项，优先真实 production cloud / production DB/queue external probe / live endpoint evidence；若外部材料仍不可得，O7 下一步要消费真实或准现场 same-task materials，而不是再做只读 checklist/surface。
>
> 2026-07-10 收口：`sprints/2026.07.10_07-13_o5_o6_live_endpoint_probe_readback/` 已把 O5/O6 从 SQLite shadow same-task gate 推进到 `cloud_external_probe` / `cloud_db_queue_external_probe` additive readback。Robot Software 在 same-task smoke 中复用既有 probe summary 逻辑，对本地 relay `/healthz`、`/readyz`、`/preflightz` 做 software proof live endpoint probe，并把两类 probe 摘要写入同一 `task_id` 的 O6 archive/readback，再通过 consumer 回读 `cloud_external_probe_ready_not_production_proof` 与 `cloud_db_queue_external_probe_ready_not_production_proof`；O6 新增 `trashbot.o6.cloud_external_probe_readback.v1` 与 `trashbot.o6.cloud_db_queue_external_probe_readback.v1`，支持 archive detail、field evidence、artifact bundle、consumer detail 和 `include=cloud_external_probe,cloud_db_queue_external_probe` 回读；hostile probe payload fail-closed，只把对应 section 降级为 `blocked_not_proven`。验证为 `py_compile` 通过、`Ran 3 tests in 2.338s OK`、relay `Ran 167 tests in 64.655s OK`、`git diff --check` 通过。O5/O6 从约 84% 保守上调到约 85%，本轮不归档 KR；证据边界为 `software_proof_o5_o6_live_endpoint_probe_readback_only`，不证明真实 production cloud、production DB/queue、多实例一致性、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、真实 live Nav2、真实 robot motion、真实 delivery record、真实 operator confirmation 或真实 delivery success。下一轮必须消费真实 production cloud / production DB/queue external probe / 真实 live endpoint evidence，否则 O5/O6 不应继续靠 local/mock probe wrapper 提升百分比。
>
> 2026-07-10 收口：`sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/` 已把“same-task mission material 是否允许计主 OKR 进度”从流程口径固化成 hard gate 软件合同。Algorithm 在 `same_task_mission_evidence_gate` 中新增结构化 `mission_artifact_delta` 和 `same_task_id_consumed`、`live_or_field_command_executed`、`support_only_reason`、`okr_credit_allowed`；O6 archive/readback 回读并对 support-only、缺字段、legacy unstructured delta、unsafe text、dangerous true、task mismatch fail-closed；O7 consumer/UI 展示 credit fields，并把 `okr_credit_allowed=false` 收紧为 support-only/blocked。验证为 Algorithm `Ran 60 tests in 0.313s OK`、O6 relay `Ran 168 tests in 64.612s OK`、O7 `Tests 484 passed (484)`、build、lint、`git diff --check` 通过。由于本轮没有新增真实 production cloud、真实 live route execution、真实 delivery record、真实 operator confirmation 或真实 delivery success，O5/O6/O7 维持约 85%/85%/85% 不变，本轮不归档 KR；证据边界为 `software_proof_same_task_mission_artifact_credit_gate_only`。从这一轮起，`okr_credit_allowed=false` 的 probe/checklist/readback-only/support-only 工作只能算回归守护，不再计主 OKR 增量。
>
> 2026-07-10 收口：`sprints/2026.07.10_09-15_o6_o7_same_task_field_material_packet/` 已把上轮 hard gate 要求的“消费真实或准现场 same-task materials”推进为可回读软件合同。Algorithm 新增 `trashbot.same_task_field_material_packet.v1`，把同一 `task_id` 的 `map_yaml`（optional）、`route_csv`、keyframes、route bag / rosbag、replay JSONL 归一为 safe material packet，验证 `Ran 62 tests in 0.347s OK`；O6 新增 `trashbot.o6.same_task_field_material_packet.v1` archive/readback/include，返工后对齐 Algorithm 实际 `material_summaries` 与 list-shaped `sample_refs`，验证 `Ran 170 tests in 67.261s OK`；O7 consumer/UI 新增 packet 默认 include、展示和 checklist 第 9 项，返工后兼容 `material_summaries`、`material_sample_refs`、`sample_ref_summaries` 和 legacy dict-shaped sample refs，验证 `Tests 485 passed (485)`、build、lint 通过。O6/O7 保守上调到约 86%/86%，O5/O1 维持约 85%，本轮不归档 KR；证据边界为 `software_proof_same_task_field_material_packet_only`，不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success、真实 OSS/CDN、真实 annotation API/export 或 hardware safety。下一轮最低项回到 O5/O1；若继续 O6/O7，必须接 live route execution、delivery record 或 operator confirmation。
>
> 2026-07-10 收口：`sprints/2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate/` 已把 O1 当前“真实 nonzero L/R 与 HIL 准入仍缺证据”的缺口，先收敛成可执行的 fail-closed 软件 gate。Hardware owner 新增 `wave_rover_nonzero_feedback_gate.py`，复用 `wave_rover_feedback.py` 的 vendor `T=1001` parser，支持 `feedback_T1001.log` 或 `--feedback-sample-json` 输入，固定输出 `source=software_proof`、`evidence_boundary=software_proof_o1_wave_rover_nonzero_feedback_hil_gate_only`、`hil_pass=false`、`safe_to_control=false`。主会话首轮验收发现 mixed bad JSON + nonzero `T=1001` 仍可能误报成功；返工后任意 invalid feedback line 都会顶层锁成 `status=blocked_invalid_feedback`，CLI `exit 4`，非 `T=1001` 行仍 ignored。验证为 `python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*wave*rover*.py'` 输出 `Ran 9 tests in 0.005s OK`，相关硬件文档已同步。O1 由约 85% 保守上调到约 86%，因为新增了可复验的 nonzero feedback / HIL gate 软件证据链；O5/O6/O7 不变，本轮不归档 KR。该证据不证明真实 WAVE ROVER nonzero L/R、真实轮向确认、真实 safe-to-control 或真实 HIL pass；下一轮 O1 必须切到真实上车 run 的 `feedback_T1001.log`、motion command、operator report 与 HIL acceptance record。
>
> 2026-07-10 收口：`sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/` 已把 `same_task_field_material_packet` 深化为同一 `task_id` 的 `same_task_route_execution_material_packet`。Algorithm 新增 `trashbot.same_task_route_execution_material_packet.v1`，把 field materials、route execution readiness/closure、Nav2、delivery result、pose progress、route bag replay 和 replay JSONL 归一为安全摘要，验证 `Ran 65 tests in 0.453s OK`；O6 新增 `trashbot.o6.same_task_route_execution_material_packet.v1` archive/readback/include，验证 `Ran 171 tests in 68.334s OK`；O7 默认 include 并独立展示 packet，验证 `Tests 486 passed (486)`、build、lint 通过。O6/O7 保守上调到约 87%/87%，O5 维持约 85%，O1 维持约 86%，本轮不归档 KR；证据边界为 `software_proof_same_task_route_execution_material_packet_only`，不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success 或 hardware safety/HIL。下一轮若继续 O6/O7，必须接 live route execution、delivery record、operator confirmation 或 production cloud readback。
>
> 2026-07-10 收口：`sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/` 已把 `same_task_route_execution_material_packet` 从安全摘要推进为 credit-aware 同 task 材料合同。Algorithm 新增 `live_or_field_command_evidence_present`、`delivery_or_operator_material_consumed`、`route_execution_credit_candidate`、`credit_support_only_reason`、`credit_required_evidence`，验证 `Ran 67 tests in 0.499s OK`；O6 archive/readback 保留这些字段并对缺字段、字段类型错误、credit candidate 条件不一致与 unsafe payload fail-closed，验证 `Ran 171 tests in 68.289s OK`；O7 consumer/UI 展示 credit material 字段，修复 candidate-true 空 support reason 误判，并补充缺字段路径 selected task id 回归，验证 `Tests 486 passed (486)`、build、lint 通过。O6/O7 保守上调到约 88%/88%，O5 维持约 85%，O1 维持约 86%，本轮不归档 KR；证据边界为 `software_proof_o6_o7_route_execution_credit_material_only`，不证明真实 production cloud、真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success 或 hardware safety/HIL。下一轮若继续 O6/O7，必须输入真实或准现场 live route execution、delivery record、operator confirmation 或 production cloud readback，避免再做只读 wrapper。
>
> 2026-07-10 收口：`sprints/2026.07.10_15-22_o6_o7_field_operator_confirmation_material/` 已把 O6/O7 从 clean-baseline Nav2 path material 继续推进到 operator report / operator confirmation material 消费链。Algorithm 新增 `trashbot.field_operator_confirmation_material.v1` 和 `--field-operator-confirmation-json`，验证 `Ran 73 tests in 0.543s OK`；O6 新增 `trashbot.o6.field_operator_confirmation_material.v1` archive/readback/include，验证 `Ran 177 tests in 75.477s OK`；O7 新增 `trashbot.pc_tools_workstation.o7_field_operator_confirmation_material.v1` default include/UI summary，验证 `Tests 487 passed (487)`、build、lint 通过。O6/O7 从约 90% 保守上调到约 91%，O5 维持约 85%，O1 维持约 86%，本轮不归档 KR；证据边界为 `software_proof_field_operator_confirmation_material_only`，不证明 production cloud、production DB/queue、TLS/4G、live Nav2 route execution、robot motion、delivery success、operator acceptance、HIL 或 hardware safety。下一轮若继续 O6/O7，必须输入 live route execution、delivery record、operator acceptance 或 production cloud readback；否则应优先回到 O5/O1 的真实外部材料。
>
> 2026-07-10 收口：`sprints/2026.07.10_16-24_o1_same_session_wheel_feedback_material_intake/` 已把 O1 从 fail-closed nonzero feedback gate 推进到历史真实上位机 same-session wheel feedback material intake。Hardware owner 新增 `trashbot.wave_rover_same_session_wheel_feedback_material.v1`，消费 `sprints/2026.06.22_11-00_wheel_lr_samesession_first_jog/artifacts/01_upper_manual_samesession_012.json`，输出 `same_session_wheel_feedback_material_ready_not_delivery_proof`，摘要 `latest_nonzero_pair.left_speed=61.0/right_speed=61.0`、`phase=motion_window`，并固定 `hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。验证为 `py_compile` 通过、`Ran 18 tests ... OK`、positive CLI exit 0、dangerous temp artifact exit 4、scoped `git diff --check` 通过；主节点只读验收看到 positive CLI 输出没有 `/dev/tty`、baudrate、endpoint 或 raw frames。O1 从约 86% 保守上调到约 87%，O5 保持约 85%，O6/O7 保持约 91%，本轮不归档 KR；证据边界为 `software_proof_o1_same_session_wheel_feedback_material_intake_only`，不证明 current live HIL pass、safe-to-control、delivery success、轮速方向、IMU/battery 标定、Nav2 route execution、operator acceptance 或 hardware safety。下一轮 O1 必须采当前同 run `feedback_T1001.log`、motion command、operator observation 和 HIL acceptance record。
>
> 2026-07-10 收口：`sprints/2026.07.10_17-22_o5_production_cutover_readiness_packet/` 已把 O5 从分散 software-proof gate 推进到 `trashbot.cloud_production_cutover_readiness_packet.v1` support-only readiness packet。Robot Software 新增 CLI `--write-cloud-production-cutover-readiness-packet-artifact` 和 preflight consumption `--cloud-production-cutover-readiness-packet-artifact`，聚合 cloud deployment readiness、cloud external probe、public ingress/TLS、DB/queue external probe、worker migration rehearsal、worker cutover drain、OSS/CDN live probe 与 external evidence intake 的安全摘要，只输出短状态、counts、safe basename、sha256 短前缀、blocked reasons、`next_live_command` 和 gate 字段。验证为 `python3 -m py_compile` 通过、`python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py` 输出 `Ran 179 tests in 74.465s OK`、scoped `git diff --check` 通过。O5 保持约 85%，`okr_credit_allowed=false`，本轮不归档 KR；proof boundary 为 `software_proof_cloud_production_cutover_readiness_packet_only`，不证明真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser、真实 production cutover 或真实 delivery success。下一轮 O5 只有接入真实 external production evidence 才可考虑 OKR 增量；否则转 O1 current same-run HIL 或 O6/O7 live route/delivery/operator/production readback。
>
> 2026-07-10 收口：`sprints/2026.07.10_19-25_o1_free_cell_map_material_bundle/` 已把 O1 从 historical motion/map bundle 推进到同 run free-cell map material intake。Hardware owner 扩展 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，消费 `2026.06.22_01-35_motion_map_runtime_probe` artifacts `33-38`，positive output 包含 `free_cell_map_material_present=true`、`free_cell_pixel_count=394`、`free_cell_has_free_cells=true`、`free_cell_usable_map_count=1`、`map_navigation_material_ready=true`，并继续固定 `status=motion_map_hil_material_bundle_ready_not_hil_pass`、`proof_scope=software_proof_o1_motion_map_hil_material_bundle_only`、`hil_pass=false`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`map_navigation_ready=false`。验证为 `py_compile` 通过、`Ran 16 tests in 0.051s OK`、positive CLI exit 0、negative free-cell pixel review smoke exit 4 且命中 `free_cell_pixel_count_not_394`、scoped `git diff --check` 通过。O1 从约 88% 保守上调到约 89%，O5 保持约 85%，O6/O7 保持约 91%，本轮不归档 KR；证据边界仍为 `software_proof_o1_motion_map_hil_material_bundle_only`，不证明 current live HIL、safe-to-control、delivery success、wheel direction、IMU/battery calibration、Nav2 route execution success、current live map navigation readiness 或 production cloud。下一轮 O1 必须采 current same-run HIL acceptance，并把 free-cell material 接到 current live localization/path proof。
>
> 2026-07-09 收口：`sprints/2026.07.09_17-00_o6_o7_route_bag_evidence_intake/` 已把准现场 DB3 route bag 摘要推进成 `trashbot.route_bag_evidence.v1` / `trashbot.o6.route_bag_evidence.v1`，证据边界为 `software_proof_route_bag_evidence_intake_only`；Algorithm 新增 route bag evidence generator，验证 `Ran 26 tests ... OK`，DB3 smoke 输出 `topic_count=3`、`message_count=1473`、sample topics `/tf_static`、`/scan`、`/camera/image_raw`、`contains_abs_path=false`、`safe_to_control=false`、`delivery_success=false`；O6 archive/readback 支持 field evidence、artifact bundle、archive detail、consumer detail 和 `include=route_bag_evidence` 回读，验证 `Ran 158 tests in 56.274s OK`；O7 UI 与 artifact bundle readiness 展示 route bag evidence 只读摘要，验证 `npm run test` 3 files / `479 passed`，build `built in 1.72s`、lint 通过，并修复 `ProofFlags.source` collision。O6/O7 保守上调到约 59%/59%，本轮不归档 KR；不证明真实 production cloud、真实 live Nav2 route execution、raw ROS message payload、robot motion、真实 delivery record、operator confirmation、delivery success、真实 OSS/CDN、真实 annotation API/export 或完整路线长期验收。

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

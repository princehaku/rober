# ros_rbs P9 项目设计与前瞻 OKR

## 1. 北极星

把 `ros_rbs` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车沿固定路线出发，把垃圾送到垃圾站/垃圾桶点位，必要时跨楼层进出电梯，再安全返回或等待下一次任务，而不是一次性 demo，也不是依赖机械臂到处捡垃圾的机器人。

**跨楼层送垃圾是 MVP 必须能力**：在受控楼宇内，小车识别电梯是否开门，进入电梯后通过语音请求好心人帮忙按目标楼层，持续识别是否到达目标楼层，并在目标楼层开门时尽快驶出。这个能力服务于"普通用户只用手机，小车完成跨楼层 trash delivery"的北极星，**纳入 MVP 必须实现范围，但实机能力需要在受控场景验证**；它不默认要求机械臂、昂贵传感器或新增下位机硬件，人工协助（请旁人帮忙按楼层按钮）仍是产品流程的一部分。

**手机端是普通用户唯一入口**：必须美观、能直接使用、不依赖命令行/SSH/ROS2 知识。4G 场景下走云端中转，手机和小车不要求处于同一 WiFi。本地 `operator_gateway` 仅作 fallback 调试入口，正式手机入口必须满足美观与可用性验收口径。

当前项目已经具备 6 个核心包的雏形：

- `ros2_trashbot_interfaces`：msg/srv/action 契约层。
- `ros2_trashbot_hardware`：Orange Pi 到 WAVE ROVER ESP32 下位机的串口桥。
- `ros2_trashbot_nav`：Nav2、航点、地图、固定路线、关键帧调试。
- `ros2_trashbot_vision`：摄像头垃圾检测。
- `ros2_trashbot_behavior`：任务编排、送达/投放 action。
- `ros2_trashbot_bringup`：学习、自主、完整系统启动。

P9 视角下，项目下一阶段的核心不是继续堆节点，而是把“能跑”升级为“可验证地可靠交付垃圾”：协议可信、固定路线可靠、任务可恢复、用户交互足够简单、数据可复盘、硬件假设可追溯。

## 2. 战略定位

1. **目标用户是不会电脑和硬件的普通人**
   - 用户默认只有手机，不要求会 SSH、ROS2、串口、地图文件或硬件调试。
   - 产品体验必须围绕手机端的一键发车、状态查看、异常提示、人工接管和售后诊断设计。
   - 语音、喇叭和简单灯光/提示音用于降低使用门槛：提示“请放入垃圾”“准备出发”“已到垃圾站”“需要人工处理”等关键状态。

2. **核心任务是“送垃圾”，不是“捡垃圾”**
   - MVP 任务闭环是：用户放入垃圾 -> 手机/语音确认 -> 小车出发 -> 到达垃圾站/垃圾桶点位 -> 完成投放/提醒人工取走 -> 返回或待命。
   - 当前预算和机构条件下不承诺机械臂抓取、地面散落垃圾拾取、复杂分类分拣。
   - 摄像头优先用于路线辅助、站点识别、障碍/异常记录和远程查看；垃圾检测能力作为后续增强，不作为核心价值前提。

3. **预算有限，必须按量产约束做取舍**
   - 默认硬件边界是：小车底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭，不把昂贵传感器、机械臂、深度相机、多板卡作为默认方案。
   - 所有新增能力必须回答三个问题：是否降低普通用户使用难度、是否提高送达成功率、是否适合低成本量产。
   - 硬件事实来源采用 `docs/vendor/VENDOR_INDEX.md`；本文仅写产品战略，不新增引脚、电压、串口设备名、波特率或机械尺寸假设。

4. **电梯能力是 MVP 必须实现的 assisted delivery，而不是无人全自动乘梯**
   - 跨楼层送垃圾是 MVP 必须能力：小车看门、进门、语音求助按键、判断目标楼层、开门后驶出，必须进入主 `task_orchestrator` 状态机，不再作为可选 H2 分支默认关闭。
   - 实机完成度需要在受控场景中按"文档/合同 → 软件 dry-run → 受控实景"三层验收逐步推进；OKR 写明必须并不等于已完成实机闭环。
   - 小车不按电梯按钮，不改造电梯，不新增机械臂或电梯控制硬件；人工协助（请旁人按目标楼层）仍是产品流程边界。
   - 能力归属在 Orange Pi/ROS2 上位机的行为、感知和语音编排，ESP32/WAVE ROVER 下位机只保持底盘执行与反馈职责。

5. **4G 数据通路走云端中转，不走手机直连 WiFi**
   - 正式 4G 链路：手机 web/app → 云端 API → 小车 `remote_bridge` outbound polling → ROS2 behavior。
   - 云端服务端基线：4C 8G 无 GPU，公网入口，仅作命令/状态/ACK 控制面中转；详见 `docs/product/cloud_4g_infrastructure.md`。
   - 图片大对象通过阿里云 OSS（bucket `bytegallop`）+ CDN（`https://cdn.bytegallop.com/rober/`）流转，云中转节点不承担大文件带宽。
   - 控制面任何时候都不暴露 `/cmd_vel`、不接受 inbound 直连小车。敏感凭证（OSS AK/SK、bearer token）只走 `.env`/环境变量，不进入仓库。

## 3. 设计原则

1. **硬件事实必须本地可追溯**
   - 涉及 WAVE ROVER、ESP32、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件和机械尺寸时，以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准。
   - 当前底盘通信应按 WAVE ROVER 官方 UART newline-delimited JSON 处理，不再继续扩展旧二进制协议假设。

2. **ROS2 接口稳定，内部实现可替换**
   - 上层继续面向 `/cmd_vel`、`/odom`、`/imu/data`、`/battery`、`/trashbot/patrol`、`/trashbot/collect_trash` 等 ROS2 接口。
   - 底层硬件桥、视觉模型、导航实现可以迭代，但不能随意破坏接口契约。

3. **先送达闭环，再智能**
   - 第一优先级是用户交付垃圾、装载确认、固定路线导航、到站投放/提醒、返回/待命的完整闭环。
   - 复杂模型、动态规划、自动识别散落垃圾、多机器人协同都必须建立在稳定送达闭环和可观测数据之上。

4. **每个关键行为都要可观测、可回放、可解释**
   - 任务状态、导航目标、检测结果、失败原因、硬件反馈都要能落日志或状态文件。
   - 路线、关键帧、检测样本和失败案例要形成持续改进数据集。

5. **文档同步更新与工程质量**
   - 任何功能开发、修复或架构调整，必须同步更新 `docs/` 目录下的相关文档。文档必须始终反映项目的最新状态。
   - 采用中文注释规范：代码中的所有技术注释必须使用**中文**，且注释比例必须**超过 20%**，以确保代码的可读性和可维护性。

6. **默认安全、低速、可停**
   - 任何自主行为必须有停止路径、超时策略、失败恢复策略。
   - 未经硬件验证的能力只能以参数关闭或 dry-run 形式存在。

6. **量产优先，少硬件、少配置、少售后**
   - 任何功能默认要考虑批量装机、远程诊断、参数模板、用户误操作和售后成本。
   - 能用软件流程、固定路线、手机交互和语音提示解决的问题，不优先增加昂贵硬件。

## 4. 2026 H1 OKR

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**目标说明**：让 Orange Pi 通过 ROS2 以官方 WAVE ROVER UART JSON 协议稳定控制底盘，并发布最小可用状态反馈。

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，启动时配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` ROS 控制模式只通过参数启用，并标注需要硬件验证。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，并明确 `/odom` 是临时命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码 Orange Pi 实际设备名。

### Objective 2：把“巡逻 demo”升级成可恢复送垃圾任务闭环

**目标说明**：让行为层不再只是 sleep 和占位逻辑，而是能完成“用户已把垃圾交给小车”之后的送达任务：确认装载、导航到垃圾站、投放或提醒人工取走、失败后恢复。

**Key Results**

- KR1：`task_orchestrator` 状态机覆盖 `IDLE -> LOADED -> DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 的真实转换。
- KR2：送达 action 使用 garbage station waypoint/fixed route 输入，不再使用固定 `waypoints_total = 5` 占位逻辑。
- KR3：装载确认支持手机按钮、语音/麦克风触发或本地参数模拟；在没有可靠传感器前，不把“自动判断是否装了垃圾”写成强依赖。
- KR4：投放失败、导航失败、未找到垃圾站/垃圾桶点位、超时取消都返回明确 action result 和 error message。
- KR5：每次任务产出可复盘记录：起止时间、目标、状态转移、失败原因、导航结果、检测快照引用。
- KR6：行为状态机必须覆盖 elevator assisted delivery 完整状态链：等待电梯开门 → 进入电梯 → 语音请求"你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯," → 等待目标楼层 → 目标楼层开门后驶出 → 继续送达；失败、超时、未确认目标楼层、未开门必须返回明确 action result + error code，并触发人工接管。MVP 写明必须并不等于已完成受控实景验证，仍需按三层验收推进。

### Objective 3：建立可验证导航与固定路线能力

**目标说明**：让学习路线、固定路线、自主往返垃圾站和关键帧调试形成一条清晰可重复的工程流程。

**Key Results**

- KR1：`learn.launch.py` 能稳定完成 SLAM/人工驾驶/航点或 route 数据采集流程。
- KR2：`route_data_recorder`、`route_csv_to_yaml`、`fixed_route_autonomy` 的输入输出格式在文档中固化，并有静态/单元测试覆盖。
- KR3：fixed route dry-run 能在无 Nav2/无硬件环境下验证路线读取、关键帧匹配和状态输出。
- KR4：自主模式能选择 Nav2 waypoint 送达或 fixed route 送达，两者参数边界清晰。
- KR5：关键帧调试页面能展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。

### Objective 4：把摄像头从“捡垃圾检测”收敛为送达任务的可选感知能力

**目标说明**：当前 MVP 不随包发布默认散落垃圾 detector。摄像头能力先作为固定路线、垃圾站识别、障碍/异常记录、远程查看和数据沉淀的未来可选模块；垃圾检测只作为增强能力，不作为没有机械臂阶段的核心闭环前提。

**Key Results**

- KR1：`TrashStatus` 字段语义作为未来可选感知 contract 保留：坐标系、置信度、垃圾类型、是否垃圾桶、时间戳。
- KR2：当前 launch 不默认启动散落垃圾 detector；未来恢复视觉节点必须有显式 launch flag、参数边界和验证证据。
- KR3：未来视觉样本目录和 manifest contract 保留为可选诊断引用；当前 MVP 不声明默认生产原图、标注图或检测 JSON。
- KR4：行为层只依赖稳定感知契约，不直接耦合具体视觉算法；没有机械臂前，不把散落垃圾拾取作为任务成功标准。
- KR5：形成一份感知升级评估表：OpenCV、YOLO、RT-DETR、深度相机各自成本、算力、鲁棒性、量产成本和落地条件。
- KR6：感知 contract 必须覆盖电梯门开/关、是否已进入轿厢、目标楼层到达证据、目标楼层开门可驶出证据；P0 字段（door_open / inside_car / target_floor_reached / target_floor_door_open）作为 MVP 必交付，P1 字段（楼层显示屏识别、快照引用）作为后续增强。优先用现有摄像头识别/语音/日志证据验证，不把新硬件作为默认前提。

### Objective 5：建立手机用户体验与低成本量产边界

**目标说明**：让不会电脑和硬件的用户可以用手机完成核心任务，同时把硬件方案控制在低成本、可批量装配、可售后诊断的范围内。

**Key Results**

- KR1：定义手机端最小流程：连接设备 -> 选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车 -> 查看状态 -> 处理异常。
- KR2：定义语音/喇叭提示词和状态触发点，覆盖待装载、准备出发、行驶中、到达、失败、需要人工接管。
- KR3：形成量产硬件约束表，默认只包含小车底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭；新增硬件必须有成本、装配、维护和软件收益说明。
- KR4：建立远程诊断最小数据包：软件版本、地图/路线版本、最近任务状态、失败原因、关键日志、摄像头快照引用。
- KR5：形成用户验收标准：普通用户不接触命令行、不插线调试、不理解 ROS2，也能完成一次送垃圾任务并知道失败时该怎么做。
- KR6 ：跨楼层 trash delivery 的手机/语音体验必须落地：用户只选择目标楼层和垃圾站，小车在电梯内主动求助按键，失败时能在手机端解释"未开门、未确认目标楼层、需要人工接管"；手机端不暴露 raw JSON 或 ROS topic 名。
- KR7 ：手机端 UI **美观且能直接使用**：视觉系统统一（配色 token、字号、间距、卡片、按钮态）、主操作主路径 ≤ 3 步、文案中文优先、iPhone/Android 主流尺寸适配、最小可点击区域 ≥ 44pt、首屏可交互 < 3 秒。当前可用流程与 readiness gate 口径见 `docs/product/mobile_user_flow.md`；本地 phone-first HTML 仍是 fallback 调试入口，正式手机端必须另行完成真实手机浏览器/设备验收。

### Objective 6：4G 云中转 + OSS/CDN 数据通路产品化

**目标说明**：让小车通过 4G 走云端中转完成手机用户控制与数据回传，不依赖手机和小车处于同一 WiFi。图片/快照/任务记录类大对象通过阿里云 OSS + CDN 沉淀，云中转节点只承担轻量 JSON 控制面。

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连小车。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`，包含 4C 8G 无 GPU、SSH 端口、网络方向、防火墙策略、容量边界、运维与产品流量分离。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK，主 AK 不直放小车；超期对象可回收。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作为公开只读视图入口，diagnostics 引用以 URL 形式给出，不在小车本地暴露密钥；CDN 不承担私有任务数据，私有数据走云端 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，`.env.example` 仅占位；服务端、CI、上车机器人均通过环境变量注入；密钥泄露有 rotate 流程。任何 tracked 文件不得包含真实 `OSS_ACCESS_KEY_SECRET`、bearer token 或 root 密码。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须有 graceful degradation：本地 operator gateway fallback 可用，状态可恢复，任务不丢；远程诊断能区分"网络问题"与"机器人问题"。

## 4.1 当前 OKR 进度快照

更新时间：2026-05-13 00:33 Asia/Shanghai。最新 sprint：`2026.05.13_00-01_phone-offline-resume-gate`。

详细进度历史与 sprint 级证据见 [`docs/process/okr_progress_log.md`](docs/process/okr_progress_log.md)。本节只展示当前 6 个 Objective 的最新摘要，不再粘贴单 sprint 段落；本次结构精简未修改任何 Objective/KR 文字与完成度数字。

| Objective | 当前进度 | 最近一轮证据 | 剩余关键缺口 |
| --- | --- | --- | --- |
| Objective 1 硬件协议可信底盘 | 约 75% | 19-20 hardware proof 已接入 `/api/diagnostics.hardware_proof` 和 operator 页面；`operator_hardware_proof_ref` launch 参数链路完成；Docker preflight 强化但 registry mirror/proxy 仍 blocked（详见 21-22 sprint）。 | 仍缺真实 WAVE ROVER `hil_pass` evidence packet、`/odom`、`/imu/data`、`/battery` 实机样本与真实 UART/反馈频率/IMU/电池实测；software proof 不等于 HIL 通过。 |
| Objective 2 可恢复送垃圾任务闭环 | 约 74% | `TrashCollection` fixed-route 送达已写入结构化 `evidence`（`route_contract_version` / `route_progress` / `visual_gate_status`）；legacy `trash_collection_server.py` 已 quarantine 并返回 `legacy_server_quarantined`；patrol 学习阶段 proof-gated。 | 仍缺真实 fixed-route/Nav2 行驶、真实 SLAM/Nav2 学习到巡逻 E2E 实测。 |
| Objective 3 可验证导航与固定路线 | 约 76% | `route_proof_summary.missing_checkpoints` 归一化与 nav/operator 口径一致；fixed-route debug panel、`keyframe_preflight`、`route_data_recorder` runtime-style 文件写入证明均已落地；2026.05.10_23-24 sprint 收口（nav 44 tests / behavior 48 tests / smoke 128 tests OK）。 | 仍缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据，以及与 O1 HIL 同一 `evidence_ref` 的上车复账。 |
| Objective 4 感知模块产品化 | 约 75% | `trashbot.vision_samples.v1` manifest、review progress metrics、Vision evidence chain 诊断卡均已进入 operator/diagnostics；电梯感知 contract `door_open / inside_car / target_floor_reached / target_floor_door_open` 已纳入 KR6；按保守口径仅上调 +1pp（74% → 75%）。 | 仍未完成真实硬件/HIL、真实相机采集与上车验证；当前证据是软件/离线环境，不等于实机门识别/楼层识别。 |
| Objective 5 手机体验与量产边界 | 约 54%（software_proof_docker_phone_offline_resume_gate） | 00-01 sprint 完成 phone offline/resume readiness software proof（`trashbot.phone_offline_resume_readiness.v1`）；24-25 voice prompt readiness、22-23 support bundle、20-21 task-flow readiness、18-19 PWA/installability、15-16 local Chrome browser acceptance、13-14 command safety 软证据均已落地；电梯 assisted delivery 手机文案与 speaker prompt `你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,` 已写入 KR6/KR7。 | 仍无 production app、真实手机设备 Safari/Chrome、physical phone service worker runtime、真实喇叭/TTS 播放、普通用户实机验收、生产账号或真实远程手机流程；本轮是 local/Docker software proof，不等于真实云、真实 4G、OSS/CDN 实流量、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。 |
| Objective 6 4G 云中转 + OSS/CDN | 约 53%（software_proof_docker_production_recovery_gate） | 25-26 sprint 完成 production recovery gate；Docker relay/auth/readiness/degradation/ack/preflight、SQLite state、backup/restore drill、OSS/CDN manifest、phone/API manifest consumption、network recovery、credential rotation、provisioning audit、production store/queue、queue ordering、transaction isolation gate 全链软件证据已落地。 | 真实云部署、HTTPS/TLS、公网入口、真实 4G/SIM、生产鉴权/rotate、真实 STS issuance、真实 OSS upload、CDN origin fetch、生产 DB/queue、多实例一致性、真实生产备份策略/灾备、正式手机 app/真实手机设备验收和生产运维仍未实现或验证；上述 gate 只证明软件契约与降级语义，不等于真实云、真实 4G、真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL。 |

**最低 Objective 软提醒规则（2026-05-12 引入）**：每轮 Epic sprint 的 `tech-plan.md` 必须在 `## OKR 最低优先级核对` 段说明本轮是否针对当前 4.1 节里完成度最低的 Objective（按本节既有快照数字排序，含并列时一起列出）；如不针对，必须给出具体理由（如最低 Objective 当前无可推进的软件工作、依赖前置硬件 blocker、CEO 明确指定其他优先级、并行 sprint 已覆盖最低 Objective 等）。这是软提醒、不阻塞实现，但 `final.md` 收口时需复核理由是否仍然成立。Micro sprint 不强制此节。本规则不修改任何 Objective / KR / 完成度数字，也不修改本节既有快照表。详细判定矩阵、并行规则、blocker 红线和与既有规则的关系，见 `docs/process/iteration_velocity.md`。

## 5. 2026 H2 前瞻路线

### 阶段 A：工程闭环稳定化

- 完成官方 JSON 底盘桥硬件实测，确认 `T=1` 与 `T=13` 的实际运动表现。
- 明确 `/odom` 来源：短期命令积分，中期轮速/编码器融合，长期与 Nav2/SLAM/IMU 融合。
- 引入 launch 参数配置文件，减少命令行长参数和硬编码默认值。
- 为每个包建立最小 CI：导入检查、静态测试、核心单元测试。

### 阶段 B：任务自治能力

- 行为层引入任务队列：装载确认任务、送达任务、投放/提醒任务、返回任务。
- 增加恢复策略：导航失败重试、目标过期丢弃、连续失败降级、人工接管。
- 增加运行状态 topic 或 JSON 状态文件，供 debug web 和日志系统消费。
- 将 action feedback 从“进度数字”升级为可读状态机事件。

### 阶段 C：数据闭环与模型升级

- 把送达过程中的关键帧、站点识别结果、异常/失败案例沉淀为数据集。
- 使用固定路线场景先训练/验证轻量目标检测模型。
- 建立离线回放工具：输入 route/keyframes/detections，复现行为层决策。
- 引入指标面板：站点识别准确率、异常记录覆盖率、平均送达耗时、任务成功率。

### 阶段 D：产品化与安全边界

- 增加急停、限速、低电压处理、通信丢失停车、近障停车。
- 明确支持场景：封闭区域、低速、固定路线、可控光照；不承诺开放道路或复杂人群环境。
- 梳理安装文档：Orange Pi 系统、串口权限、ROS2 环境、WAVE ROVER 固件、摄像头、地图路径。
- 形成上车验收清单和回归测试清单。

### 阶段 E：电梯 assisted delivery 受控场景

- 在楼宇内定义可控测试路线：出发点 -> 电梯厅 -> 进入电梯 -> 人工协助按目标楼层 -> 目标楼层驶出 -> 垃圾站/垃圾桶点位。
- 行为层增加电梯子状态，但默认关闭；只有明确进入 H2 受控测试时启用。
- 感知层先验证电梯门开/关、目标楼层到达和可驶出证据，不把楼层识别写成无证据的全自动能力。
- 语音层由 Orange Pi/ROS2 编排，进入电梯后播放：“你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,”。
- 人工协助是产品边界：小车不按按钮，不改造电梯，不默认新增机械臂或电梯控制硬件。

## 6. 当前最高优先级

- 下一轮按 live `OKR.md` 4.1 节完成度重排：当前 O5 约 52%、O6 约 53%（含并列最低）。
- Docker-only 环境下，优先选 O5 真实设备前置 gate 或 O6 生产化前置 gate，不声明真实云/4G、真实手机、真实喇叭/TTS 或真实送达。
- 具备真实手机/音频/云/4G 条件时，优先补 O5 真实手机/喇叭/TTS 验收或 O6 真实云公网入口、生产 DB/queue、真实 4G/SIM 证据。
- O1/O2/O3/O4 仍受真实硬件、路线和感知证据约束，不能用 Docker/local software proof 冒充 HIL、真实云、4G 或真实送达。

1. **修正项目事实源**
   - README 中仍可能残留旧 ESP32 二进制协议描述，应统一到 WAVE ROVER 官方 UART JSON 协议。
   - 所有硬件相关说明必须指向 `docs/vendor/VENDOR_INDEX.md`。

2. **完成硬件桥上车验证**
   - 先验证串口设备名、波特率、`T=1` 左右轮速度方向、停止命令。
   - 再验证 `T=1001` 反馈字段、IMU yaw 单位、电池电压。
   - 最后验证 `T=13` 是否适合直接作为 `/cmd_vel` 映射。

3. **补齐行为层真实运行证据**
   - 主 `task_orchestrator` 的 patrol/collection/delivery 已进入 waypoint/fixed-route/action-result 路径；`use_saved_map=false` 学习阶段已要求真实 waypoint proof，不再模拟完成。
   - legacy `trash_collection_server.py` 已 quarantine，仅作为旧入口兼容保留；被调用时返回 `legacy_server_quarantined`，不能作为当前闭环完成证据。
   - Objective 2 剩余缺口集中在真实 fixed-route/Nav2 行驶，以及真实 SLAM/Nav2 学习到巡逻 E2E 实测。

4. **建立最小回归测试**
   - 硬件桥：协议函数测试。
   - 导航：route CSV/YAML 转换、fixed route dry-run。
   - 行为：action result、取消、失败路径、状态转移静态测试。

## 7. 风险与决策

| 风险 | 影响 | 决策 |
| --- | --- | --- |
| README/代码/厂商资料协议不一致 | 硬件无法通信或误判实现正确 | 以 `docs/vendor/` 为硬件事实源，README 后续修正 |
| Orange Pi 串口设备名不确定 | launch 默认值可能上车不可用 | 保持参数可覆盖，上车前确认实际设备 |
| `/odom` 不是实测里程计 | Nav2 定位和路线复现可能漂移 | 短期明确标注，中期接入轮速/编码器融合 |
| 把“捡垃圾”误当核心目标 | 在没有机械臂和高成本传感器时需求失焦 | 核心闭环固定为用户交付后的送达任务 |
| 普通用户不会电脑和硬件 | 上手失败、售后成本高 | 手机一键流程、语音提示、远程诊断优先 |
| 视觉检测启发式不足 | 站点识别或异常记录不稳定 | 先数据闭环，再模型升级，不作为送达 MVP 前提 |
| 行为层模拟逻辑过多 | 系统看似完整但无法真实运行 | 优先替换 sleep 和占位逻辑，建立真实状态机 |
| 缺少硬件在环测试 | 单元测试通过但上车失败 | 增加上车验收清单和硬件测试脚本 |
| 电梯场景被误读成全自动乘梯 | 用户以为小车能按按钮、控制电梯或已完成跨楼层实机闭环 | 定位为 H2/受控 assisted delivery；人工按键是流程边界，验证前不抬完成度 |
| 目标楼层识别不可靠 | 小车可能提前驶出或错过目标楼层 | 需要目标楼层到达证据、开门证据、超时/人工接管策略和任务记录 |
| 电梯门识别误判 | 可能撞门、挡门或错过驶出窗口 | 默认低速、可停、门开确认、驶出超时和手机端人工接管 |

## 8. P9 评审标准

一个阶段不能只以“代码写完”作为完成标准，必须同时满足：

- **功能闭环**：能从启动、用户装载确认、送达垃圾站、投放/提醒、返回形成完整路径。
- **接口稳定**：ROS2 topic/action/srv 契约清楚，内部替换不破坏上层。
- **硬件可信**：协议、参数、速度映射、反馈字段均有 vendor 资料或实测记录。
- **可验证**：有自动化测试、dry-run、上车验收三层证据。
- **可恢复**：失败不是卡死，而是进入明确错误状态、重试、降级或等待接管。
- **可复盘**：每次任务留下足够日志和数据，能回答“为什么这样决策”。
- **可使用**：普通用户只靠手机和语音提示即可完成核心任务，不需要理解电脑、ROS2 或硬件调试。
- **可量产**：默认方案不依赖机械臂、昂贵传感器或复杂装配，新增硬件必须有明确成本收益。

## 9. 下一步执行建议

1. 修正 README 的旧二进制协议描述，与当前 WAVE ROVER JSON 驱动保持一致。
2. 为硬件桥补一份 `docs/hardware/wave_rover_json_bridge.md`，记录命令、参数、实测结果和注意事项。
3. 把 `task_orchestrator` 的模拟巡逻/收集替换为真实“装载确认 -> 送达垃圾站 -> 投放/提醒 -> 返回”状态机和 waypoint/fixed route 驱动。
4. 增加 `run_smoke_tests.sh` 或等价脚本，在 WSL/Windows 混合开发环境上至少跑 Python 静态测试；在 Orange Pi 上跑 ROS2 build 和硬件 smoke test。
5. 建立 `docs/acceptance/robot_bringup_checklist.md`，作为每次上车前后的验收标准。
6. 补一份手机端最小流程和量产硬件约束表，明确用户只用手机、默认硬件只包含小车底盘、上位板、随身 WiFi、摄像头、麦克风和喇叭。
7. 为 H2 电梯 assisted delivery 建立受控场景产品文档和后续技术计划：先做流程、语音、状态机边界和验收口径，再由 Robot Platform、Autonomy、User Touchpoint 分别补行为、感知和语音/手机触点证据。

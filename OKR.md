# rober 项目设计与前瞻 OKR

## 1. 北极星

把 `rober` 做成一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人：用户把垃圾交给小车后，小车沿固定路线出发，把垃圾送到垃圾站/垃圾桶点位，必要时跨楼层进出电梯，再安全返回或等待下一次任务，而不是一次性 demo，也不是依赖机械臂到处捡垃圾的机器人。

当前项目已经具备 6 个核心包的雏形：

- `ros2_trashbot_interfaces`：msg/srv/action 契约层。
- `ros2_trashbot_hardware`：Orange Pi 到 WAVE ROVER ESP32 下位机的串口桥。
- `ros2_trashbot_nav`：Nav2、航点、地图、固定路线、关键帧调试。
- `ros2_trashbot_behavior`：任务编排、送达/投放 action。

项目的核心不是继续堆节点，而是把“能跑”升级为“可验证地可靠交付垃圾”：协议可信、固定路线可靠、任务可恢复、用户交互足够简单、数据可复盘、硬件假设可追溯。

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

## 3. 设计原则

1. **硬件事实必须本地可追溯**
   - 涉及 WAVE ROVER、Orange Pi、UART、波特率、JSON 指令、速度映射、反馈协议、引脚、电压、固件和机械尺寸时，以 `docs/vendor/VENDOR_INDEX.md` 及其指向资料为准。
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
   - 采用中文注释规范：代码中的所有技术注释必须使用**中文**，且注释比例必须**超过 20%**，以确保代码的可读性和可维护性；新增模块默认要求接口参数化与可扩展配置，禁止把硬件型号、阈值和状态分支写死在单一路径。

6. **默认安全、低速、可停**
   - 任何自主行为必须有停止路径、超时策略、失败恢复策略。
   - 未经硬件验证的能力只能以参数关闭或 dry-run 形式存在。

6. **量产优先，少硬件、少配置、少售后**
   - 任何功能默认要考虑批量装机、远程诊断、参数模板、用户误操作和售后成本。
   - 能用软件流程、固定路线、手机交互和语音提示解决的问题，不优先增加昂贵硬件。

7. **电梯识别是必须实现的 assisted delivery**
   - 跨楼层送垃圾是 MVP 必须能力：小车看门、进门、语音求助按键、判断目标楼层、开门后驶出，必须进入主 `task_orchestrator` 状态机，不再作为可选 H2 分支默认关闭。
   - 实机完成度需要在受控场景中按"文档/合同 → 软件 dry-run → 受控实景"三层验收逐步推进；OKR 写明必须并不等于已完成实机闭环。
   - 小车不按电梯按钮，不改造电梯，不新增机械臂或电梯控制硬件；人工协助（请旁人按目标楼层）仍是产品流程边界。
   - 能力归属在 Orange Pi/ROS2 上位机的行为、感知和语音编排，ESP32/WAVE ROVER 下位机只保持底盘执行与反馈职责。

5. **数据通路走云端中转，不走手机直连 WiFi**
   - 正式 4G 链路：手机 web/app → 云端 API → 小车 `remote_bridge` outbound polling → ROS2 behavior。
   - 云端服务端基线：4C 8G 无 GPU，公网入口，仅作命令/状态/ACK 控制面中转；详见 `docs/product/cloud_4g_infrastructure.md`。
   - 图片大对象通过阿里云 OSS（bucket `bytegallop`）+ CDN（`https://cdn.bytegallop.com/rober/`）流转，云中转节点不承担大文件带宽。
   - 控制面任何时候都不暴露 `/cmd_vel`、不接受 inbound 直连小车。敏感凭证（OSS AK/SK、bearer token）只走 `.env`/环境变量，不进入仓库。

6. **手机端是普通用户唯一入口**
   - 必须美观、能直接使用、不依赖命令行/SSH/ROS2 知识。4G 场景下走云端中转，手机和小车不要求处于同一 WiFi。本地 `operator_gateway` 仅作 fallback 调试入口，正式手机入口必须满足美观与可用性验收口径。
   - 能实时看到ros2的路径更佳

6. **PC端是ros2 打标 路径学习 展示 训练 用的**
   - 能看到每一轮的进展，debug，数据
   - 清晰美观
   - 能实时看到ros2的路径更佳

## 4. 2026 H1 OKR

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**目标说明**：让 Orange Pi 通过 ROS2 以官方 WAVE ROVER UART JSON 协议稳定控制底盘，并发布最小可用状态反馈。

**Key Results**

- KR1：`ros2_trashbot_hardware` 默认使用 UTF-8 JSON + `\n` 与 ESP32 通信，启动时配置 echo、反馈间隔和反馈流。
- KR2：`/cmd_vel` 默认映射到 `T=1` 左右轮速度命令，`T=13` ROS 控制模式只通过参数启用，并标注需要硬件验证。
- KR3：解析 `T=1001` 底盘反馈，发布 `/imu/data` 和 `/battery`，并明确 `/odom` 是临时命令积分还是实测里程计。
- KR4：硬件桥协议单元测试覆盖 JSON 编码、速度映射、反馈解析、坏数据容错。
- KR5：launch 参数暴露 `serial_port`、`serial_baudrate`、`command_mode`、`track_width_m`、`max_wheel_speed_mps`，不硬编码 Orange Pi 实际设备名。

### Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环

**目标说明**：能完成“用户已把垃圾交给小车”之后的送达任务，并把电梯 assisted delivery 作为必须实现能力进入主链：确认装载、自动识别电梯和电梯的进出、自动导航到垃圾站、投放或提醒人工取走、失败后恢复。

**Key Results**

- KR1：`task_orchestrator` 状态机覆盖 `IDLE -> LOADED -> DELIVERING -> DROPOFF -> RETURNING -> IDLE/ERROR` 的真实转换。
- KR2：送达 action 使用 garbage station waypoint/fixed route 输入，不再使用固定 `waypoints_total = 5` 占位逻辑。
- KR3：装载确认支持手机按钮、语音/麦克风触发或本地参数模拟；在没有可靠传感器前，不把“自动判断是否装了垃圾”写成强依赖。
- KR4：投放失败、导航失败、未找到垃圾站/垃圾桶点位、超时取消都返回明确 action result 和 error message。
- KR5：每次任务产出可复盘记录：起止时间、目标、状态转移、失败原因、导航结果、检测快照引用。
- KR6：行为状态机必须覆盖 elevator assisted delivery 完整状态链：等待电梯开门 → 进入电梯 → 语音请求"你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯," → 等待目标楼层 → 目标楼层开门后驶出 → 继续送达；失败、超时、未确认目标楼层、未开门必须返回明确 action result + error code，并触发人工接管。MVP 写明必须并不等于已完成受控实景验证，仍需按三层验收推进。
- KR7：跨楼层任务默认启用电梯状态链（非 feature flag 默认关闭），并在 task record/diagnostics 中落盘门状态、楼层证据、人工接管原因和可回放 evidence_ref；若降级关闭必须给出明确告警与恢复建议。

### Objective 3：建立可验证导航与固定路线能力

**目标说明**：让学习路线、固定路线、自主往返垃圾站和关键帧调试形成一条清晰可重复的工程流程。

**Key Results**

- KR1：`learn.launch.py` 能稳定完成 SLAM/人工驾驶/航点或 route 数据采集流程。
- KR2：`route_data_recorder`、`route_csv_to_yaml`、`fixed_route_autonomy` 的输入输出格式在文档中固化，并有静态/单元测试覆盖。
- KR3：fixed route dry-run 能在无 Nav2/无硬件环境下验证路线读取、关键帧匹配和状态输出。
- KR4：自主模式能选择 Nav2 waypoint 送达或 fixed route 送达，两者参数边界清晰。
- KR5：PC的关键帧调试页面能展示当前位置、目标点、匹配状态、失败原因和最近一次任务状态。

### Objective 4：建立手机用户体验与低成本量产边界

**目标说明**：让不会电脑和硬件的用户可以用手机完成核心任务，同时把硬件方案控制在低成本、可批量装配、可售后诊断的范围内。

**Key Results**

- KR1：定义手机端最小流程：连接设备 -> 选择/确认垃圾站 -> 确认已放入垃圾 -> 一键发车 -> 查看状态 -> 处理异常。
- KR2：定义语音/喇叭提示词和状态触发点，覆盖待装载、准备出发、行驶中、到达、失败、需要人工接管。
- KR3：形成量产硬件约束表，默认只包含小车底盘、上位板、随身 WiFi、摄像头、麦克风、喇叭；新增硬件必须有成本、装配、维护和软件收益说明。
- KR4：建立远程诊断最小数据包：软件版本、地图/路线版本、最近任务状态、失败原因、关键日志、摄像头快照引用。
- KR5：形成用户验收标准：普通用户不接触命令行、不插线调试、不理解 ROS2，也能完成一次送垃圾任务并知道失败时该怎么做。
- KR6 ：跨楼层 trash delivery 的手机/语音体验必须落地：用户只选择目标楼层和垃圾站，小车在电梯内主动求助按键，失败时能在手机端解释"未开门、未确认目标楼层、需要人工接管"；手机端不暴露 raw JSON 或 ROS topic 名。
- KR7 ：手机端 UI **美观且能直接使用**：视觉系统统一（配色 token、字号、间距、卡片、按钮态）、主操作主路径 ≤ 3 步、文案中文优先、iPhone/Android 主流尺寸适配、最小可点击区域 ≥ 44pt、首屏可交互 < 3 秒。当前可用流程与 readiness gate 口径见 `docs/product/mobile_user_flow.md`；本地 phone-first HTML 仍是 fallback 调试入口，正式手机端必须另行完成真实手机浏览器/设备验收。
- KR8：默认导航/感知硬件约束固化为“单目摄像头 + 2D LiDAR + ToF 安全环（可先 2 路后扩 4 路）”：2D LiDAR 负责 SLAM/Nav2 主链，单目负责电梯门/楼层语义证据，ToF 负责近场防撞；不把 ToF 当主建图输入。
- KR9：电梯 assisted delivery 作为必须实现能力写入工程扩展约束：状态机、感知 contract、手机状态展示均需预留参数化扩展点（传感器数量、阈值、状态枚举可配置），避免写死单机型/单传感器实现。

### Objective 5 云中转 + OSS/CDN 数据通路产品化

**目标说明**：让小车通过 云端中转完成手机用户控制与数据回传，不依赖手机和小车处于同一 WiFi。图片/快照/任务记录类大对象通过阿里云 OSS + CDN 沉淀，云中转节点只承担轻量 JSON 控制

**Key Results**

- KR1：云中转服务端最小契约（commands/status/ack）按 `trashbot.remote.v1` 实现：HTTPS、outbound polling 优先，幂等键 + bearer token 鉴权，不暴露 `/cmd_vel`、不接受 inbound 直连小车。
- KR2：服务端基线规格写入 `docs/product/cloud_4g_infrastructure.md`，包含 4C 8G 无 GPU、SSH 端口、网络方向、防火墙策略、容量边界、运维与产品流量分离。
- KR3：OSS 写入策略明确：bucket `bytegallop`，region `oss-cn-hangzhou`，对象前缀 `rober/<robot_id>/<date>/<task_id>/`；小车侧写入使用 STS 临时凭证或受限 AK，主 AK 不直放小车；超期对象可回收。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 只作为公开只读视图入口，diagnostics 引用以 URL 形式给出，不在小车本地暴露密钥；CDN 不承担私有任务数据，私有数据走云端 API 网关 + bearer。
- KR5：凭证管理 contract：`.env` 不入仓库，`.env.example` 仅占位；服务端、CI、上车机器人均通过环境变量注入；密钥泄露有 rotate 流程。任何 tracked 文件不得包含真实 `OSS_ACCESS_KEY_SECRET`、bearer token 或 root 密码。
- KR6：4G 中断、OSS 写失败、CDN 不可达三类失败必须有 graceful degradation：本地 operator gateway fallback 可用，状态可恢复，任务不丢；远程诊断能区分"网络问题"与"机器人问题"。

## 4.1 当前 OKR 进度快照

更新时间：2026-05-17 03:44 Asia/Shanghai。最新 sprint：`2026.05.17_03-04_hardware-sensor-hil-entry-execution-pack`。详细历史见 `docs/process/okr_progress_log.md`。

| Objective | 当前进度 | 本轮证据与边界 | 主要缺口 |
| --- | --- | --- | --- |

| Objective 1：硬件协议可信底盘 | 约 77% | 本轮完成 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`：Hardware PC gate 将 `hardware_sensor_hil_entry_readiness_review` 转成 fail-closed HIL-entry execution pack，包含 controlled HIL-entry manifest、material templates、first-run / rerun command summary、owner handoff 和 next required evidence；并引用 `docs/vendor/VENDOR_INDEX.md`、`ugv_rpi/base_ctrl.py`、`ugv_rpi/config.yaml`、`WAVE_ROVER_V0.9/json_cmd.h`、`WAVE_ROVER_V0.9/uart_ctrl.h` 作为 WAVE ROVER / Orange Pi / UART JSON source boundary。该证据只把 PR #5 暴露的 2D LiDAR / ToF 材料缺口从 readiness review 推进到 HIL-entry 执行材料模板和 owner handoff，因此 Objective 1 从约 76% 保守上调到约 77%；仍固定 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。 | 仍缺真实 WAVE ROVER `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本；2D LiDAR / ToF 仍缺真实 SKU/source、receipt、采购、安装、接线、电源、标定、真实 HIL-entry 和 field evidence。 |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 约 86% | 本轮不提升 Objective 2。`hardware_sensor_hil_entry_readiness_review` 只评审传感器 HIL-entry 材料完整性，Robot diagnostics 只做 metadata-only 消费，不触发 collect、dropoff、cancel、ACK、cursor、Nav2、HIL 或 delivery success。 | 仍缺真实电梯、真实喇叭/TTS、真实 Nav2/fixed-route 运行、真实 route completion signal、真实 task record、真实路线采集、真实 WAVE ROVER/UART/HIL、同一 `evidence_ref` 的上车实机复账、真实门状态、真实楼层确认、人工协助现场记录、真实送达、失败恢复实测、真实 dropoff completion、真实 cancel completion 和 delivery success。 |
| Objective 3：可验证导航与固定路线 | 约 86% | 本轮不提升 Objective 3。传感器 readiness review 只说明 2D LiDAR / ToF 材料、配置和下一步 HIL-entry 证据链可被 fail-closed 汇总；不包含真实 SLAM/Nav2、fixed-route runtime log、route completion signal、task record 或关键帧实景证据。 | 仍缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据、WAVE ROVER/HIL、真实串口、真实 route completion signal、真实 task record、真实电梯材料、真实 dropoff/cancel completion、delivery result 和同一 `evidence_ref` 上车实机复账。 |
| Objective 4：手机用户体验与低成本量产边界 | 约 97% | 本轮 mobile/web 新增只读“传感器 HIL 执行包” panel，兼容 status、phone_readiness、diagnostics 与 nested summary，只展示 execution-pack status、safe `evidence_ref`、manifest summary、material templates、safe command summary、owner handoff、next required evidence、boundary、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`；过滤 raw vendor docs、raw JSON、serial/UART、绝对路径、凭证、DB/queue URL、OSS AK/SK、checksums、complete artifacts 与 raw robot responses；Start Delivery / Confirm Dropoff / Cancel gating 未改变。该 phone-safe 解释能力把 HIL-entry execution pack 可读化给现场支持，因此 Objective 4 从约 96% 保守上调到约 97%，且仅为 software proof。 | `not_proven` 仍包括真实手机 / 真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 现场验收、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、delivery success、真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、WAVE ROVER、HIL 和量产实物验收。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化（历史 O6） | 约 66% | Objective 5 仍是数值最低，但本机只有 Docker。本轮没有新增真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部 O5 材料；`hardware_sensor_hil_entry_execution_pack` 只证明当前 repo 的本地 software proof / metadata-only fail-closed HIL-entry execution pack 链路，不替代外部云/4G/OSS/CDN/DB/queue proof。因此 Objective 5 保持约 66%；not real Objective 5 external proof。 | 仍没有真实公网 HTTPS/TLS、真实 4G/SIM、真实手机设备/browser、production app、真实 PWA prompt/user choice、OSS/CDN live traffic、真实 production DB/queue connectivity、migration、worker、多实例一致性、queue ordering、transaction isolation、backup/recovery、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。 |


## 5. OKR完成路线

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

### 阶段 E：电梯 assisted delivery 必须能力落地

- 在楼宇内定义可控测试路线：出发点 -> 电梯厅 -> 进入电梯 -> 人工协助按目标楼层 -> 目标楼层驶出 -> 垃圾站/垃圾桶点位。
- 行为层增加电梯子状态，并进入默认主链路；跨楼层任务默认启用电梯流程，受控场景持续验证与收敛。
- 感知层先验证电梯门开/关、目标楼层到达和可驶出证据，不把楼层识别写成无证据的全自动能力。
- 语音层由 Orange Pi/ROS2 编排，进入电梯后播放：“你好,好心人,.我要去1楼扔垃圾,请帮我按一下电梯,”。
- 人工协助是产品边界：小车不按按钮，不改造电梯，不默认新增机械臂或电梯控制硬件。

## 6. 当前最高优先级

- 下一轮按 `OKR.md` 4.1 重新排序。当前数值最低完成度为 Objective 5（约 66%），但只有拿到至少一种真实外部材料时才应继续推进 O5 completion：OSS/CDN live traffic、HTTPS/TLS 公网入口、4G/SIM、production DB/queue connectivity 或 production worker/migration 证据；若外部材料仍不可用，不要重复本地 O5 metadata depth。当前最高可行动作是补真实设备/现场材料：Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、真实 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料，或 Objective 2/O3 的受控现场材料回填（真实电梯门状态、真实楼层确认、人工协助记录、Nav2/fixed-route runtime log、同一 `evidence_ref` 的 task record/completion signal、dropoff/cancel completion 或 delivery result 材料）。不得把 `hardware_baseline_review` summary、`hardware_sensor_procurement_intake` summary、`hardware_sensor_procurement_review_decision` summary、`hardware_sensor_procurement_execution_pack` summary、`hardware_sensor_procurement_receipt_intake` summary、`hardware_sensor_hil_entry_config_precheck` summary、`hardware_sensor_hil_entry_readiness_review` summary、`hardware_sensor_hil_entry_execution_pack` summary、`route_task_terminal_completion_rehearsal` summary、`route_task_terminal_review_decision` summary、`route_task_field_retest_execution_pack` summary、`route_task_field_retest_session_handoff` summary、`route_task_field_retest_result_intake` summary、`route_task_field_retest_result_reconciliation` summary、`route_task_field_retest_material_pack` summary、`route_task_field_retest_operator_drill` summary、retest-request summary、review-decision summary、intake summary、precheck summary、browser proof、handoff artifact/summary、diagnostics/mobile summary、ACK、completion signal 或 route/elevator same-evidence-ref 对齐写成真实手机通过、真实 route/elevator field pass、HIL、真实投放或 delivery success。

## 7. 整体风险与待办

- 当前仍缺真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 现场验收、真实云/4G、production DB/queue、OSS/CDN live traffic、真实 2D LiDAR / ToF SKU/vendor/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料、Nav2/fixed-route、真实 route completion signal、真实 task record、真实路线采集、真实电梯门状态、真实楼层确认、真实人工协助记录、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 的上车实机复账、真实 cancel completed、真实 dropoff completion 和真实 delivery 证据；`hardware_baseline_review`、`hardware_sensor_procurement_intake`、`hardware_sensor_procurement_review_decision`、`hardware_sensor_procurement_execution_pack`、`hardware_sensor_procurement_receipt_intake`、`hardware_sensor_hil_entry_config_precheck`、`hardware_sensor_hil_entry_readiness_review`、`hardware_sensor_hil_entry_execution_pack`、`route_task_terminal_review_decision`、`route_task_field_retest_execution_pack`、`route_task_field_retest_session_handoff`、`route_task_field_retest_result_intake`、`route_task_field_retest_result_reconciliation`、`route_task_field_retest_material_pack` 与 `route_task_field_retest_operator_drill` 只证明当前 repo 的本地 software proof / metadata-only fail-closed 硬件基线、材料入口、采购评审决策、采购执行包、收货回填入口、HIL-entry config precheck、HIL-entry readiness review、HIL-entry execution pack、任务终态复核决策、现场复测执行包、现场复测交接、现场复测结果入口、现场复测结果复账、现场复测材料包和现场操作演练链路，不证明真实手机、真实 2D LiDAR、真实 ToF、真实电梯、真实 Nav2/fixed-route、HIL、真实投放或真实交付。

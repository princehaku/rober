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
   - MVP 闭环：用户放入垃圾 -> 手机/语音确认 -> 小车出发 -> 到达垃圾站点位 -> 完成投放/提醒人工取走 -> 返回或待命。
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
   - 按"文档/合同 -> 软件 dry-run -> 受控实景"三层验收推进，写明必须不等于已完成实机。
   - 小车不按电梯按钮，不改造电梯，人工协助按目标楼层是产品边界。

8. **数据通路：Orange Pi -> 隧道 -> 云中转（核心后端）**
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
    - 在推进 OKR 过程中，若在 Docker/本地环境中使用 Mock 运行且测试通过，可判定为"软件侧完成"，不必等到真实硬件实测后再合并推进，直到最终集成测试阶段再用真实数据和硬件实跑验证。

---

## 4. 2026 H1 OKR（当前推进中）

更新时间：2026-06-04，对应 `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/final.md`。

本轮按 CEO 反馈和四个 L2 owner 的只读复盘重置当前 OKR。判断原则从“软件入口是否存在”改成“普通用户价值是否可现场验证”：PC WASD 必须真的能让小车前进/后退/左右转和停止；右侧雷达必须有一键开启/关闭；建图、重置、保存、加载、定位必须和 ROS2/SLAM/Nav2 联动；电梯进出必须进入 OpenCV 视觉识别和 ROS2 状态链，而不是停留在合同、dry-run 或本地 fixture。

本轮不新增 Objective。现有 O1/O2/O3/O7 足以覆盖 CEO 指出的真实缺口；需要新增的是 KR 和验收口径，而不是继续堆新的抽象 O。O2/O3 已从“历史归档软件完成 ~99%”撤回当前推进区，O1/O2/O3/O7 的虚高比例被打回。

### 当前百分比与涨分规则

| Objective | 当前比例 | 方向判断 | 比例怎么涨 |
| --- | --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 约 72% | 调整，已从历史归档撤回当前推进区 | 只靠 OpenCV 电梯语义识别、ROS2 状态机接入、受控电梯材料、跨楼层任务记录和安全接管材料涨分；合同、dry-run、fixture、文案和本地校验不再涨。 |
| O3：可验证导航、建图、定位与固定路线 | 约 73% | 调整，已从历史归档撤回当前推进区 | 只靠 SLAM Toolbox `/map`、地图 artifact、reset/save/load、AMCL `/initialpose`、Nav2 消费 `/scan`+map、路线实跑和地图质量材料涨分；`learn.launch.py` 入口或 fixed-route dry-run 不再涨。 |
| O7：PC 端运营调试平台 | 约 88% | 打回后继续，PC 入口必须变成真实 operator workflow | 只靠真实 PC WASD 控车、雷达一键开关、建图/定位控制、真实 8787/browser 复跑、stop/急停/operator report 和任务记录涨分；UI/API mock、同源代理、rendered smoke 不再单独涨。 |
| O1：硬件协议可信底盘 | 约 95% | 打回后继续，底盘 HIL 和 ROS feedback 仍是硬门槛 | 只靠底盘低速短 pulse、stop/post-status、ACK 或 `T=1001` 同场证据、真实 `/odom`/`/imu/data`/`/battery`、LiDAR 长稳、production udev、SLAM/Nav2 消费和 HIL 复核涨分。 |
| O5：云中转控制面产品化 | 约 96% | 继续，但下一轮不再抢占真实操控/建图/电梯 Epic | 只靠真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 和 robot command/status/ACK 生产材料涨分。 |
| O6：云端核心后端 | 约 96% | 继续，但下一轮不再抢占真实操控/建图/电梯 Epic | 只靠真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据和 PC/手机查询回放涨分。 |

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**当前比例：约 95%（从约 97% 打回）**
**责任 Engineer：Hardware Infra Engineer 主责，Robot Software Engineer 配合 ROS2 topic/bringup。**
**方向判断：继续。LiDAR 首个 `/scan` smoke 可计入，但底盘 HIL、PC 手控真实运动、ACK/`T=1001` 同场闭环和 ROS feedback topic 未完成。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `mock serial`、fake serial、8787 status/stop/manual/feedback 软件入口、`/dev/ttyS5 @115200` 底盘可写入口材料、非运动 `T=130 -> T=1001` samples、`/dev/ttyACM0 @150000` LiDAR 口、`/scan` once/hz、`/lidar/raw_packet` once 和 `base_link -> laser_frame` static TF。 |
| KR-O1-Base-Manual-HIL | 在现场看护、物理净空、人工急停可用时，用 8787 `/api/base/manual` 完成 forward/back/left/right/stop 低速短 pulse；每次采集 manual response、stop response、post-status、operator report、视频或现场记录，并明确 `safe_to_control` 只在证据满足后才可转正。Owner：Hardware Infra Engineer。 |
| KR-O1/O7-ACK-T1001-Bridge | 把 PC 手控请求、8787 `/api/base/manual`、底盘 `T=1`、stop、`T=130 -> T=1001`、日志时间戳和 operator report 对齐到同一 evidence ref；`T=1001` 只能作为 vendor feedback material，不能单独写成 robot ACK。Owner：Hardware Infra Engineer + User Touchpoint Full-Stack Engineer。 |
| KR-O1-ROS-Feedback-Topics | 明确真实 `/odom`、`/imu/data`、`/battery` 与 vendor feedback 的边界，采集 ROS topic 一次性和长稳证据；没有 topic 证据时不得宣称 Nav2 可消费或底盘闭环。Owner：Robot Software Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明 PC WASD 已真实控车、底盘 HIL、闭环运动安全、左右转现场有效、急停演练、robot ACK、真实 `/odom`/`/imu/data`/`/battery`、SLAM/Nav2 消费、完整上车任务闭环或 `safe_to_control=true`。 |

### Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环

**当前比例：约 72%（从历史归档“软件完成 ~99%”打回）**
**责任 Engineer：Robot Algorithm Engineer 主责 OpenCV 识别，Robot Software Engineer 主责状态机接入，User Touchpoint Full-Stack Engineer 配合 PC/手机状态。**
**方向判断：调整。电梯 assisted delivery 是 MVP 必须能力，但当前证据停在合同、dry-run、fixture 和 visual gate；它不是 OpenCV 电梯门/轿厢/楼层语义识别，也不是实景进出电梯。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `docs/product/elevator_assisted_delivery.md` 定义用户流程、人工协助边界、dry-run evidence schema、材料校验 gate；行为层和 diagnostics 能消费 dry-run/fixture；visual gate 仅是 ORB keyframe 匹配，不等于电梯门、轿厢或楼层识别。 |
| KR-O2-OpenCV-Elevator-Taxonomy | 建立 OpenCV 电梯识别 taxonomy：门线/门缝、轿厢内外、楼层显示屏 ROI、目标楼层确认、可驶出/不可驶出、安全接管原因；每类样本需要定义正负例、最低数量、采集要求和失败边界。Owner：Robot Algorithm Engineer。 |
| KR-O2-OpenCV-ROI-Rule-Baseline | 基于真实或受控采集图片建立 OpenCV ROI + rule baseline，先做可解释的门开/关、进入轿厢、目标楼层候选、驶出安全条件判断；允许 mock/fixture 开发，但必须保留真实图片切换入口。Owner：Robot Algorithm Engineer。 |
| KR-O2-Offline-Eval | 对电梯识别 baseline 输出离线评估 artifact，至少包含样本清单、混淆项、false positive/false negative、置信度阈值、不可判定策略和 phone-safe operator summary。Owner：Robot Algorithm Engineer。 |
| KR-O2-ROS2-State-Integration | 将 OpenCV 识别结果接入 `task_orchestrator` 电梯状态链，覆盖等待开门、进入、请求按楼层、等待目标楼层、开门驶出、人工接管；task record 必须保留关键快照和失败原因。Owner：Robot Software Engineer。 |
| KR-O2-Controlled-Elevator-Field | 在受控电梯场景完成至少 3 次连续流程材料：等待开门、进入、语音求助、目标楼层确认、开门驶出、继续到垃圾站或安全中止。Owner：Robot Software Engineer + Robot Algorithm Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实相机电梯识别、楼层 OCR、目标楼层确认、OpenCV 规则有效、真实进出电梯、真实跨楼层送达、真实喇叭/TTS 播放、真实手机用户验收或 delivery success。 |

### Objective 3：可验证导航、建图、定位与固定路线

**当前比例：约 73%（从历史归档“软件完成 ~99%”打回）**
**责任 Engineer：Robot Software Engineer 主责 ROS2/SLAM/Map API，Robot Algorithm Engineer 主责 Nav2/路线质量，User Touchpoint Full-Stack Engineer 配合 PC 控制面。**
**方向判断：调整。`learn.launch.py` 有 SLAM Toolbox 入口，但没有 `/map` 建图、reset/save/load、AMCL 定位恢复、Nav2 消费 `/scan`+map 或路线实跑证据。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `learn.launch.py` 已有学习阶段入口；`map_recorder` 只有 `/trashbot/save_map` Trigger；`autonomous.launch.py` include Nav2；PC realtime map 当前为 waiting 状态；首个 LiDAR `/scan` smoke 已 observed。 |
| KR-O3-SLAM-Map-Lifecycle | 建立 ROS2 联动的建图生命周期：开启 SLAM、重置地图、保存地图、加载地图、列出 map artifact；至少形成 `/map` once、map file、metadata、日志和 PC/upper API 可回放证据。Owner：Robot Software Engineer。 |
| KR-O3-Localization-Reset | 建立定位恢复链路：PC/upper API 发布 `/initialpose`，AMCL lifecycle 正常，load map 后能恢复定位；证据包含 `/amcl_pose`、TF、pose freshness 和失败原因。Owner：Robot Software Engineer。 |
| KR-O3-Nav2-Consumption | 证明 Nav2 消费真实 `/scan` + map：map server、AMCL、planner/controller lifecycle 状态、路径生成、短距离目标或 fixed-route dry-run 到实跑的边界清晰。Owner：Robot Algorithm Engineer。 |
| KR-O3-Map-Quality-Metrics | 输出地图质量指标：覆盖区域、未知区比例、回环/漂移风险、关键 waypoint 可达性、保存/加载一致性、失败样例；低质量地图不得进入 O7 operator workflow 或 O2 电梯实景。Owner：Robot Algorithm Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实建图完成、地图 artifact 可用、重置/保存/加载链路、定位恢复、Nav2 真实路径执行、固定路线现场通过、关键帧实景匹配或任务闭环。 |

### Objective 5：云中转控制面产品化

**当前比例：约 96%**
**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Software Engineer 配合 robot command/ACK 合同。**
**方向判断：继续，但下一轮 Epic 不以 O5/O6 为主。真实操控、建图、定位、电梯识别缺口更直接阻塞北极星。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | 本地/mock control plane、readiness health、aggregate health、external probe、TLS evidence summary、real material acceptance queue、`pc_upper_ssh_collector` 和 runbook/preflight 分类。 |
| 当前下一步可涨分 KR | 真实公网 HTTPS/TLS、真实 4G/SIM 或等价蜂窝链路、production DB/queue/worker、OSS/CDN live traffic、真实 phone/browser 和 robot command/status/ACK 控制面记录。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产云、真实公网入口、真实蜂窝链路、production DB/queue、OSS/CDN 实流量、真实 phone/browser、真实 robot command 执行或上车任务闭环。 |

### Objective 6：云端核心后端 - 数据存档、模型推理与打标平台

**当前比例：约 96%**
**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Algorithm Engineer 配合数据/推理证据。**
**方向判断：继续，但下一轮 Epic 不以 O5/O6 为主。O6 需要等 O2/O3/O7 产生真实上车、电梯和地图材料后才有高质量数据可存档和推理。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `trashbot.archive.v1` task/event/annotation/inference/query、algorithm feed、archive health、external probe artifact、acceptance queue 与本地/Docker mock archive/query/annotation/inference 基线逻辑。 |
| 当前下一步可涨分 KR | 真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据查询回放；优先消费 O2/O3/O7 产生的电梯、地图、路线和 operator workflow 材料。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产数据链、真实 OSS、真实推理、真实上车数据、真实 4G/SIM、真实 phone/browser 或完整数据运营闭环。 |

### Objective 7：PC 端运营调试与数据训练平台

**当前比例：约 88%（从约 98.9% 打回）**
**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Software Engineer 配合 8787/ROS2 状态合同，Hardware Infra Engineer 配合底盘现场证据。**
**方向判断：继续并打回。PC 已有 WASD/按钮软件入口，但尚未证明 PC 能真实控制小车；雷达没有一键开启/关闭；建图/定位也没有 PC -> ROS2 操作链。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | PC 同源 API、WASD/按钮映射、camera 首屏 no auto-offer、realtime radar/map split、`GET /api/radar/status`、mock/fetch tests、build/lint/rendered smoke。 |
| KR-O7-PC-Manual-Field | PC 浏览器用 W/S/A/D 与 Space/X 完成受控 forward/back/left/right/stop 现场点动，证据与 O1 manual HIL 同源；UI 必须展示 ACK/T=1001 边界、stop 结果、失败原因和 operator report。Owner：User Touchpoint Full-Stack Engineer + Hardware Infra Engineer。 |
| KR-O7-Radar-OneClick | PC 右侧雷达提供一键开启/关闭，目标接口为 `POST /api/radar/start`、`POST /api/radar/stop` 和只读 status；开启只允许触发 LiDAR start/ROS2 driver，不得触碰 `/dev/ttyS5` 或底盘命令；关闭后状态、topic 和日志可回放。Owner：User Touchpoint Full-Stack Engineer + Robot Software Engineer。 |
| KR-O7-Map-SLAM-Controls | PC 提供建图开启、重置、保存、加载、定位入口，全部走 upper API/ROS2 服务，不让浏览器直连 ROS graph；每个按钮都要显示 ROS2 操作状态、artifact 路径、失败原因和 not_proven 边界。Owner：User Touchpoint Full-Stack Engineer + Robot Software Engineer。 |
| KR-O7-Stop-Estop-Report | PC operator workflow 必须包含停止/急停/恢复/人工报告入口；没有 stop/post-status 和 operator report 时，不得把 WASD 或 Nav2 下发写成可用。Owner：User Touchpoint Full-Stack Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实 PC WASD 控车、真实雷达一键开关、真实建图控制、真实定位恢复、真实 Nav2 下发、production path、弱网、ASR/TTS、robot ACK、HIL 或完整 operator workflow。 |

---

## 4.1 当前 OKR 进度快照

更新时间：2026-06-04，对应本轮 `sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic`。

**比例更新规则**：O2/O3/O7/O1 只有真实现场、ROS2 runtime、HIL、OpenCV eval、地图 artifact、operator workflow 或受控电梯材料才涨；O5/O6 仍只有真实生产云、4G/公网/DB/OSS/phone-browser/上车数据才涨。继续增加 micro sprint、mock、fixture、UI 文案、readback、状态面或只读 runbook 不再涨分。

| Objective | 当前比例 | 本轮变化 | 已验收/可计入 | 下一步可涨分 KR | 不得越界 |
| --- | --- | --- | --- | --- | --- |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 本轮完成 OpenCV taxonomy、ROI/rule baseline 和 offline fixture eval software guard；比例不涨 | 产品 contract、dry-run evidence schema、fixture/diagnostics、visual gate ORB 匹配、`trashbot.elevator_opencv_baseline.v1` software guard | 真实图片 manifest eval、ROS2 状态机接入、受控电梯 3 次材料 | 真实电梯识别、楼层 OCR、实景进出电梯、跨楼层送达 |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 本轮完成 8787 map/localize fail-closed API 合同；比例不涨 | `learn.launch.py` 入口、`/trashbot/save_map` 单一 Trigger、Nav2 include、首个 `/scan` smoke、`/api/map/*` 和 `/api/localize/reset` software guard | SLAM `/map`、reset/save/load、AMCL `/initialpose`、Nav2 消费 `/scan`+map、地图质量指标 | 真实地图可用、定位恢复、Nav2 实跑、路线通过 |
| O7：PC 运营调试平台 | 约 88% | 本轮 PC operator 接入 radar/map/localize/operator report 同源代理；比例不涨 | WASD/按钮软件入口、PC 同源代理、radar/map split、rendered smoke、direct-upper radar/map/localize/report UI/API 护栏 | PC WASD 现场控车、雷达一键 start/stop 真实运行、建图/定位控制、stop/急停/operator workflow | 真实控车、真实雷达开关、真实建图定位、production workflow |
| O1：硬件协议可信底盘 | 约 95% | 本轮补 HIL/串口隔离 vendor 边界文档；比例不涨 | `/dev/ttyS5` 可写材料、非运动 `T=130 -> T=1001`、LiDAR `/scan` once/hz、TF、PC manual/LiDAR 隔离准入 | 低速短 pulse、ACK/T=1001 同场证据、ROS feedback topics、LiDAR 长稳/udev、HIL | `safe_to_control=true`、HIL pass、robot ACK、真实 `/odom`/`/imu/data`/`/battery` |
| O5：云中转控制面 | 约 96% | 保持 | mock/control plane、readiness health、external probe、TLS summary、acceptance queue | 真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser | 真实生产云、真实蜂窝链路、真实 robot command 执行 |
| O6：云端核心后端 | 约 96% | 保持 | mock archive/query/annotation/inference、archive health、external probe artifact、acceptance queue | 真实隧道、production DB/queue、OSS upload、真实推理 runtime、真实上车数据回放 | 真实生产数据链、真实 OSS/推理/上车数据 |

**历史归档区调整：**

| Objective | 当前处理 | 历史记录位置 | 剩余风险 |
| --- | --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 撤出历史归档，回到当前推进区，比例打回约 72% | 旧 ~99% 软件归档仍保留在 `docs/process/okr_progress_log.md`，本轮追加打回原因 | 合同/dry-run 不等于 OpenCV 识别或真实电梯流程 |
| O3：可验证导航与固定路线 | 撤出历史归档，回到当前推进区，比例打回约 73% | 旧 ~99% 软件归档仍保留在 `docs/process/okr_progress_log.md`，本轮追加打回原因 | `learn.launch`/dry-run 不等于 SLAM map、定位恢复或 Nav2 实跑 |
| O4：手机用户体验与量产边界 | 暂留历史归档，不在本轮打回 | `docs/process/okr_progress_log.md` | 后续若 CEO 要求真实手机端发车/状态/接管，应单独拉回当前推进区 |

本轮没有已完成 KR 进入历史归档；本轮完成了 Epic 启动后的软件护栏推进，但没有真实 runtime/HIL/现场材料，因此百分比保持不变。下一步必须把 8787 雷达/建图/定位合同跑到真实 ROS2 runtime，并把电梯 baseline 接真实图片 manifest 和状态机消费，不能用 software proof 替代现场能力。

---

## 5. 当前最高优先级

按完成度和北极星阻塞程度排序，当前最高优先级为 **O2/O3 -> O7 -> O1 -> O5/O6**。原因是普通用户要的是“把垃圾交给小车后能跨楼层送达”，而当前最大缺口不是云端 runbook，而是 PC 真实控车、雷达开关、建图/定位和电梯 OpenCV 识别没有串成现场闭环。

当前 Epic：`sprints/2026.06.04_12-13_real-control-slam-elevator-field-epic/` 已完成本小时 software guard 交付：8787 新增 radar start/stop、map lifecycle、localize reset 的 fail-closed 合同；PC 工作站新增同源 operator controls 和 operator report 入口；Vision 新增 OpenCV 电梯 baseline/offline eval；Hardware 新增 PC manual 与 LiDAR 串口隔离准入。由于没有真实 runtime/HIL/现场材料，本轮不提升 Objective 完成度；涨分仍必须等待真实 PC 控车、雷达开关、SLAM/定位、真实图片 OpenCV eval、HIL 或受控现场材料。

本轮 Epic 建议拆成四个 L2 owner 并行/耦合集成：

1. **User Touchpoint Full-Stack Engineer**：O7 PC operator workflow。交付 WASD 现场控车入口复跑、一键雷达 start/stop、建图/定位控制按钮、stop/急停/operator report UI 和同源 API 证据。
2. **Robot Software Engineer**：O3 ROS2 map lifecycle。交付 `/api/map/start|reset|save|load|localize` 到 SLAM Toolbox、map server、AMCL `/initialpose`、Nav2 lifecycle 的 upper API/ROS2 glue。
3. **Robot Algorithm Engineer**：O2/O3 algorithm。交付 OpenCV 电梯 taxonomy、样本/ROI/rule baseline、offline eval、Nav2 消费 `/scan`+map 的质量指标和路线验证方案。
4. **Hardware Infra Engineer**：O1 field HIL。交付 WAVE ROVER 现场安全前提、底盘 low-speed pulse、stop/post-status、`T=1001` 同场材料、LiDAR start/stop/udev/长稳边界。

Epic 验收口径：

- PC WASD：W/S/A/D/Space/X 在现场对真实小车有效，forward/back/left/right/stop 全部有 manual response、stop response、post-status、operator report 和同一 evidence ref。
- 雷达：PC 一键开启/关闭 LiDAR/ROS2 driver，`/scan` once/hz、停止后状态和日志可回放，且不触碰底盘 UART。
- 建图/定位：PC 或 upper API 能开启、重置、保存、加载地图并发布定位；至少有 `/map` artifact、map metadata、AMCL pose、TF 和失败原因。
- 电梯 OpenCV：至少完成 taxonomy、样本/ROI/rule baseline 和 offline eval；进入 ROS2 状态机前必须输出 not_proven 边界和人工接管策略。
- 证据链：`pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md` 全套留档；不能再以 Micro sprint 替代战略推进。

> 当前 70%-90%+ 只代表软件入口、合同或首个 smoke。真实材料未完成时，任何 Objective 都不得表述为真实硬件闭环、真实 PC 控车、真实建图定位、真实 OpenCV 电梯识别、真实生产云、真实手机或真实送达完成。

---

## 6. OKR 完成路线

### 下一轮 Epic（必须启动）

- 打通 PC WASD -> PC 同源 API -> 8787 `/api/base/manual` -> WAVE ROVER low-speed pulse -> stop/post-status -> `T=1001` 同场材料 -> operator report。
- 增加雷达一键开启/关闭，明确 LiDAR start/stop 与底盘 UART 隔离。
- 增加建图、重置、保存、加载、定位 API，并让 PC 能看到 SLAM/map/AMCL/Nav2 的真实状态。
- 建立 OpenCV 电梯识别 taxonomy、样本集、ROI/rule baseline、offline eval 和 ROS2 状态机接入计划。
- 补完整 Epic 文档链和 side-to-side 验收，不再用连续 Micro sprint 刷 `software_proof`。

### 近期（现场闭环）

- O1：真实 WAVE ROVER 底盘低速短 pulse、stop/post-status、ACK/T=1001 同场证据、ROS feedback topics。
- O2：OpenCV 电梯识别 baseline 进入 ROS2 状态机，至少完成受控离线评估和人工接管策略。
- O3：SLAM Toolbox `/map`、map artifact、AMCL 定位恢复、Nav2 消费 `/scan`+map。
- O7：PC operator workflow 形成“查看状态 -> 开雷达 -> 建图/定位 -> WASD/stop -> 记录证据 -> 回放”的完整链路。

### 中期（真实生产和数据闭环）

- O5/O6 接入真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实推理 runtime。
- 电梯/路线/地图/手控材料进入 archive/query/annotation/inference，形成可训练和可复盘数据。
- PC 与手机共享真实任务状态、地图、路线、电梯和人工接管摘要。

### 后期（用户验收）

- 真实路线采集 + Nav2/固定路线实跑。
- 真实电梯受控流程 3 次连续通过。
- 真实手机/browser 一键发车、状态查看、人工接管和任务回放。
- 真实低成本量产边界复核：不新增机械臂、不改电梯、不让用户理解 ROS2/SSH/串口。

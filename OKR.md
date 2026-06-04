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

## 4. 2026 H1 OKR（当前推进区）

更新时间：2026-06-04 22:01 CST，对应 `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/final.md`；16:05 OKR rewrite 仍是本轮口径基础。

本轮复盘最近 6 个迭代后，方向判断是 **继续，但调整推进方式和完成度口径**。北极星没有变：普通手机用户把垃圾交给低成本小车，小车沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。最近 6 轮暴露的问题不是"缺更多入口"，而是入口、runbook、fixture 和 software guard 已经多于真实材料；下一步必须用 Epic 把 O2/O3/O7/O1 拉到 `robot_runtime_material` / `field_hil_material`。

### 最近 6 个迭代问题

| Sprint | 类型 | 结论 | OKR 影响 |
| --- | --- | --- | --- |
| `08-09_o5-o6-upper-ssh-preflight` | Micro | 只增强 SSH collector preflight/failure classification；没有 accepted live artifact。 | O5/O6 不涨分，继续缺真实公网/4G/DB/OSS/phone/browser。 |
| `09-10_o5-o6-upper-ssh-live-material` | Micro | SSH 可达但 artifact 为 `fail_closed`；主 blocker 是 PC base URL、cloud base URL、remote bearer token。 | 重复消费 O5/O6 配置 blocker，不支撑北极星主线。 |
| `10-11_agent-proactive-kr-reward-rule` | Micro | 主动 KR 奖励规则落地；这是流程资产，不是产品 KR 完成。 | 需要进入 O8 治理，不能把流程规则当业务结果。 |
| `10-11_o5-o6-upper-ssh-installed-probe` | Micro | installed probe 同步成功，但仍 `fail_closed`，同一生产配置缺口未解。 | O5/O6 96% 口径虚高，必须打回并降级为支线。 |
| `11-12_okr-strategy-reset-real-control-slam-elevator` | Epic | Product 主动打回 O1/O2/O3/O7，把主线拉回真实控车、SLAM/定位、OpenCV 电梯。 | 方向正确，但只重置口径，没有 runtime/HIL 证据。 |
| `12-13_real-control-slam-elevator-field-epic` | Epic | 四个 L2 owner 并行完成 software guard；没有真实 runtime/HIL/现场图片/地图/控车。 | 继续当前方向，不涨分；下一轮必须进入真实材料。 |

### 员工状态判断

| 角色 | 状态 | 调整要求 |
| --- | --- | --- |
| User Touchpoint Full-Stack Engineer | 产出高，但最近连续围绕 O5/O6 collector 做 Micro，开始偏离真实操控主线。 | 下一轮主责 O7 PC operator 真实 8787/browser runtime，不再优先做 O5/O6 runbook 或 fail-closed collector。 |
| Robot Software Engineer | 12-13 已补 upper API/map/localize/elevator readback guard，方向有效。 | 下一轮从 API 合同转到 ROS2 runtime：SLAM `/map`、AMCL、Nav2 lifecycle、真实 command hook。 |
| Robot Algorithm Engineer | OpenCV taxonomy、ROI/rule baseline、Nav2 map quality fixture 已可复跑。 | 下一轮必须接真实或受控图片 manifest 和真实 map artifact，不再只扩 fixture。 |
| Hardware Infra Engineer | 安全边界、vendor 引用和 HIL 准入清楚。 | 下一轮按现场条件做 stop-first 低速 pulse；若安全条件不满足，必须升级 blocker，不能继续写文档替代 HIL。 |
| Product Manager / OKR Owner | 已主动打回虚高 O1/O2/O3/O7，本轮继续打回 O5/O6 并新增 O8。 | 后续每轮收口必须查最近 2 轮 blocker 和 Micro/Epic 比例，防止 CEO 先发现节奏偏航。 |

### 当前百分比与涨分规则

| Objective | 当前比例 | 方向判断 | 比例怎么涨 |
| --- | --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 约 72% | 调整，主线第一优先级 | 只靠真实/受控图片 OpenCV eval、ROS2 电梯状态机接入、受控电梯流程、跨楼层任务记录和安全接管材料涨分。 |
| O3：可验证导航、建图、定位与固定路线 | 约 73% | 调整，主线第一优先级 | 只靠 SLAM Toolbox `/map`、地图 artifact、reset/save/load、AMCL `/initialpose`、Nav2 消费 `/scan`+map、路线实跑和地图质量材料涨分。 |
| O7：PC 端运营调试平台 | 约 90% | 继续，必须变成真实 operator workflow | 只靠真实 PC WASD 控车、雷达一键 start/stop 真实运行、建图/定位控制、真实 8787/browser 复跑、stop/急停/operator report 涨分。 |
| O1：硬件协议可信底盘 | 约 95% | 继续，HIL 和 ROS feedback 仍是硬门槛 | 只靠底盘低速短 pulse、stop/post-status、ACK 或 `T=1001` 同场证据、真实 `/odom`/`/imu/data`/`/battery`、LiDAR 长稳、HIL 复核涨分。 |
| O5：云中转控制面产品化 | 约 84%（从约 96% 打回） | 调整，降为支线 | 只靠真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 和 robot command/status/ACK 生产材料涨分。 |
| O6：云端核心后端 | 约 82%（从约 96% 打回） | 调整，等待真实上车材料 | 只靠真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据查询回放涨分。 |
| O8：Epic 交付节奏与证据治理 | 约 43%（从约 40% 上调） | 继续组织执行 Objective | 只靠连续 Epic 证据链、重复 blocker 升级、evidence type 标签、owner 健康检查和下一轮真实材料收口涨分；O8 是执行治理，不新增产品承诺。 |

### Objective 1：打通官方硬件协议，建立可信底盘控制层

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

**责任 Engineer：Robot Algorithm Engineer 主责 OpenCV 识别，Robot Software Engineer 主责状态机接入，User Touchpoint Full-Stack Engineer 配合 PC/手机状态。**
**方向判断：调整。电梯 assisted delivery 是 MVP 必须能力，但当前证据停在合同、dry-run、fixture 和 visual gate；它不是 OpenCV 电梯门/轿厢/楼层语义识别，也不是实景进出电梯。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `docs/product/elevator_assisted_delivery.md` 定义用户流程、人工协助边界、dry-run evidence schema、材料校验 gate；行为层和 diagnostics 能消费 dry-run/fixture；12-13 已有 OpenCV taxonomy、ROI/rule baseline 和 offline fixture eval。 |
| KR-O2-Real-Image-Manifest-Eval | 接入真实或受控采集的电梯图片 manifest，输出样本清单、门线/轿厢/楼层显示屏 ROI、false positive/false negative、阈值和不可判定策略。Owner：Robot Algorithm Engineer。 |
| KR-O2-ROS2-State-Integration | 将 OpenCV 识别结果接入 `task_orchestrator` 电梯状态链，覆盖等待开门、进入、请求按楼层、等待目标楼层、开门驶出、人工接管；task record 必须保留关键快照和失败原因。Owner：Robot Software Engineer。 |
| KR-O2-Controlled-Elevator-Field | 在受控电梯场景完成至少 3 次连续流程材料：等待开门、进入、语音求助、目标楼层确认、开门驶出、继续到垃圾站或安全中止。Owner：Robot Software Engineer + Robot Algorithm Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实相机电梯识别、楼层 OCR、目标楼层确认、OpenCV 规则有效、真实进出电梯、真实跨楼层送达、真实喇叭/TTS 播放、真实手机用户验收或 delivery success。 |

### Objective 3：可验证导航、建图、定位与固定路线

**责任 Engineer：Robot Software Engineer 主责 ROS2/SLAM/Map API，Robot Algorithm Engineer 主责 Nav2/路线质量，User Touchpoint Full-Stack Engineer 配合 PC 控制面。**
**方向判断：调整。`learn.launch.py` 有 SLAM Toolbox 入口，12-13 已有 map/localize fail-closed API 合同，但没有 `/map` 建图、reset/save/load、AMCL 定位恢复、Nav2 消费 `/scan`+map 或路线实跑证据。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `learn.launch.py` 学习阶段入口、`/trashbot/save_map` Trigger、Nav2 include、首个 LiDAR `/scan` smoke、8787 `/api/map/*` 和 `/api/localize/reset` software guard。 |
| KR-O3-SLAM-Map-Lifecycle | 建立 ROS2 联动的建图生命周期：开启 SLAM、重置地图、保存地图、加载地图、列出 map artifact；至少形成 `/map` once、map file、metadata、日志和 PC/upper API 可回放证据。Owner：Robot Software Engineer。 |
| KR-O3-Localization-Reset | 建立定位恢复链路：PC/upper API 发布 `/initialpose`，AMCL lifecycle 正常，load map 后能恢复定位；证据包含 `/amcl_pose`、TF、pose freshness 和失败原因。Owner：Robot Software Engineer。 |
| KR-O3-Nav2-Consumption | 证明 Nav2 消费真实 `/scan` + map：map server、AMCL、planner/controller lifecycle 状态、路径生成、短距离目标或 fixed-route dry-run 到实跑的边界清晰。Owner：Robot Algorithm Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实建图完成、地图 artifact 可用、重置/保存/加载链路、定位恢复、Nav2 真实路径执行、固定路线现场通过、关键帧实景匹配或任务闭环。 |

### Objective 5：云中转控制面产品化

**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Software Engineer 配合 robot command/ACK 合同。**
**方向判断：调整并打回。最近 6 个迭代里 O5/O6 连续 3 个 Micro 都没有 accepted live artifact，96% 会误导团队继续抢占主线。O5 继续存在，但下一轮不得优先于 O2/O3/O7/O1，除非生产 URL、token、4G/公网和 DB/queue 已经同时就绪。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | 本地/mock control plane、readiness health、aggregate health、external probe、TLS evidence summary、real material acceptance queue、`pc_upper_ssh_collector`、preflight 分类、installed probe 同步。 |
| KR-O5-Production-Live-Control | 真实公网 HTTPS/TLS、真实 4G/SIM 或等价蜂窝链路、production DB/queue/worker、真实 phone/browser 和 robot command/status/ACK 控制面记录进入 accepted live artifact。Owner：User Touchpoint Full-Stack Engineer。 |
| KR-O5-Blocker-Escalation | 若 `pc_base_url_not_configured_for_upper_ssh`、`cloud_base_url_not_configured`、`remote_bearer_token_absent` 再出现一次，必须在 Epic pre_start 升级 CEO 决策或暂停 O5 sprint，不得继续 Micro 消费。Owner：Product Manager / OKR Owner。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产云、真实公网入口、真实蜂窝链路、production DB/queue、OSS/CDN 实流量、真实 phone/browser、真实 robot command 执行或上车任务闭环。 |

### Objective 6：云端核心后端 - 数据存档、模型推理与打标平台

**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Algorithm Engineer 配合数据/推理证据。**
**方向判断：调整并打回。O6 的 archive/query/annotation/inference 软件合同很多，但缺真实 DB/queue、OSS、推理 runtime 和上车数据；在 O2/O3/O7 没有真实材料前，O6 无高质量数据可运营。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `trashbot.archive.v1` task/event/annotation/inference/query、algorithm feed、archive health、external probe artifact、acceptance queue 与本地/Docker mock archive/query/annotation/inference 基线逻辑。 |
| KR-O6-Production-Archive-Query | 真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据查询回放；优先消费 O2/O3/O7 产生的电梯、地图、路线和 operator workflow 材料。Owner：User Touchpoint Full-Stack Engineer + Robot Algorithm Engineer。 |
| KR-O6-Field-Material-Ingestion | 至少 ingest 一组来自 O2/O3/O7/O1 的真实 runtime/HIL/field material，并完成 phone/PC 安全摘要、查询回放和 not_proven 边界。Owner：User Touchpoint Full-Stack Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产数据链、真实 OSS、真实推理、真实上车数据、真实 4G/SIM、真实 phone/browser 或完整数据运营闭环。 |

### Objective 7：PC 端运营调试与数据训练平台

**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Software Engineer 配合 8787/ROS2 状态合同，Hardware Infra Engineer 配合底盘现场证据。**
**方向判断：继续。PC 已有 WASD/按钮软件入口和 12-13 direct-upper software guard，但尚未证明 PC 能真实控制小车、启动雷达、控制建图/定位或形成 operator workflow。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | PC 同源 API、WASD/按钮映射、camera 首屏 no auto-offer、realtime radar/map split、direct-upper radar/map/localize/report UI/API 护栏、真实 8787 operator report POST/GET route、PC 同源 operator report retest、mock/fetch tests、build/lint/rendered smoke。 |
| KR-O7-PC-Manual-Field | PC 浏览器用 W/S/A/D 与 Space/X 完成受控 forward/back/left/right/stop 现场点动，证据与 O1 manual HIL 同源；UI 必须展示 ACK/T=1001 边界、stop 结果、失败原因和 operator report。Owner：User Touchpoint Full-Stack Engineer + Hardware Infra Engineer。 |
| KR-O7-Radar-OneClick-Runtime | PC 右侧雷达一键 start/stop 真实运行，形成 `/scan` once/hz、停止后状态和日志；该链只允许触发 LiDAR/ROS2 driver，不得触碰 `/dev/ttyS5` 或底盘命令。Owner：User Touchpoint Full-Stack Engineer + Robot Software Engineer。 |
| KR-O7-Map-SLAM-Controls | PC 提供建图开启、重置、保存、加载、定位入口，全部走 upper API/ROS2 服务，不让浏览器直连 ROS graph；每个按钮都要显示 ROS2 操作状态、artifact 路径、失败原因和 not_proven 边界。Owner：User Touchpoint Full-Stack Engineer + Robot Software Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实 PC WASD 控车、真实雷达一键开关、真实建图控制、真实定位恢复、真实 Nav2 下发、production path、弱网、ASR/TTS、robot ACK、HIL 或完整 operator workflow。 |

### Objective 8：Epic 交付节奏与证据治理

**责任 Owner：Product Manager / OKR Owner 主责，四个 L2 Engineer 执行。**
**方向判断：新增。O8 是组织执行 Objective，不新增产品能力；它约束团队不要用连续 Micro、重复 blocker 和 software proof 制造虚假进度。**

| KR 类型 | 当前口径 |
| --- | --- |
| KR-O8-Epic-Cadence | 从 2026-06-04 16:05 起，下一轮实现类 sprint 必须是跨 owner Epic，目标至少覆盖 O2/O3/O7/O1 中两个 Objective，并产出 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md`。Owner：Product Manager / OKR Owner。 |
| KR-O8-Evidence-Type-Gate | 每个涨分 KR 必须标注 evidence type：`software_guard`、`robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material`；只有后四类中的真实材料可推动当前 Objective 完成度。Owner：Product Manager / OKR Owner。 |
| KR-O8-Repeated-Blocker-Stop | 最近 2 轮如果出现同一 blocker root cause，第 3 轮必须切 Objective 或升级 CEO 决策；O5/O6 的 URL/token/cloud 配置 blocker 已触发预警。Owner：Product Manager / OKR Owner。 |
| KR-O8-Owner-Health | 任一 L2 owner 连续两个 Micro 只产出入口、runbook、fixture 或 fail-closed artifact，下一轮必须转 Epic 真实材料或写明 blocker 升级。Owner：Product Manager / OKR Owner。 |
| 不可越界的 not_proven 风险 | O8 规则本身不证明产品能力完成；只有后续 sprint 按 O8 产出真实 runtime/HIL/production/user materials 才能涨产品 Objective。 |

---

## 4.1 当前 OKR 进度快照

更新时间：2026-06-04 22:01 CST，对应本轮 `sprints/2026.06.04_21-22_runtime-material-runtime-hooks`。

**比例更新规则**：O2/O3/O7/O1 只有真实现场、ROS2 runtime、HIL、OpenCV eval、地图 artifact、operator workflow 或受控电梯材料才涨；O5/O6 只有真实生产云、4G/公网/DB/OSS/phone-browser/上车数据才涨；O8 只有执行证据链、blocker 升级和 evidence type 复核生效才涨。继续增加 Micro sprint、mock、fixture、UI 文案、readback、状态面或只读 runbook 不再涨分。

| Objective | 当前比例 | 本轮变化 | 已验收/可计入 | 下一步可涨分 KR | 不得越界 |
| --- | --- | --- | --- | --- | --- |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 保持；20-21 复查本地和上位机仍无真实/受控 elevator image manifest | 产品 contract、dry-run evidence schema、fixture/diagnostics、OpenCV taxonomy/ROI/rule/offline fixture eval software guard、`--check-template` 采集模板护栏 | 真实图片 manifest eval、ROS2 状态机接入、受控电梯 3 次材料 | 真实电梯识别、楼层 OCR、实景进出电梯、跨楼层送达 |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 保持；21-22 本地新增只读 scan proof refresh 合同，但现场 8787 未部署，POST 返回 405 | `learn.launch.py` 入口、Nav2 include、首个 `/scan` smoke、`/api/map/*` 和 `/api/localize/reset` software guard、上位机 ROS2 package/launch parseability、LiDAR collector Humble CLI false-blocker 修复、本地 `/api/radar/scan-proof/refresh` 合同 | 部署 refresh route 后拿 fresh `/scan` once/hz、SLAM `/map`、reset/save/load、AMCL `/initialpose`、Nav2 消费 `/scan`+map | 真实地图可用、定位恢复、Nav2 实跑、路线通过 |
| O7：PC 运营调试平台 | 约 90% | 保持；PC refresh UI/API 已接入，但现场 upper refresh route 405，仍非 runtime workflow 完成 | WASD/按钮软件入口、PC 同源代理、radar/map split、direct-upper radar/map/localize/report UI/API 护栏、真实 8787 status/map/operator-report proxy runtime、operator-report readback、PC scan-proof refresh software guard | PC 触发 deployed refresh route、PC WASD 现场控车、雷达一键 start/stop 真实运行、建图/定位控制、stop/急停/operator workflow | 真实控车、真实雷达开关、真实建图定位、production workflow |
| O1：硬件协议可信底盘 | 约 95.5% | 保持；20-21 fresh `/api/base/feedback-request` 观察到非运动 `T=130 -> T=1001`，但 status samples 仍可能 stale，材料增强但不涨 HIL | `/dev/ttyS5` 可写材料、非运动 `T=130 -> T=1001`、LiDAR `/scan` once/hz、TF、PC manual/LiDAR 隔离准入 | 低速短 pulse、ACK/T=1001 同场证据、ROS feedback topics、LiDAR 长稳/udev、HIL | `safe_to_control=true`、HIL pass、robot ACK、真实 `/odom`/`/imu/data`/`/battery` |
| O5：云中转控制面 | 约 84% | 从约 96% 打回 | mock/control plane、readiness health、external probe、TLS summary、acceptance queue、SSH collector installed probe | 真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser | 真实生产云、真实蜂窝链路、真实 robot command 执行 |
| O6：云端核心后端 | 约 82% | 从约 96% 打回 | mock archive/query/annotation/inference、archive health、external probe artifact、acceptance queue | 真实隧道、production DB/queue、OSS upload、真实推理 runtime、真实上车数据回放 | 真实生产数据链、真实 OSS/推理/上车数据 |
| O8：Epic 交付节奏与证据治理 | 约 43% | 从约 42% 小幅上调；21-22 完成连续 Epic 留档、三条 owner notes、evidence type gate 和现场部署 blocker 收口 | AGENTS/iteration_velocity 规则、10-11 主动 KR 奖励流程、17-18/20-21/21-22 Runtime Material Epic 治理证据链 | 下一轮继续按 O8 产出真实材料收口、blocker 升级和 owner health 复核 | 不能把流程合规写成产品能力或 OKR 涨分 |

**历史归档区调整：**

| Objective | 当前处理 | 历史记录位置 | 剩余风险 |
| --- | --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 继续留在当前推进区，保持约 72% | 旧 ~99% 软件归档保留在 `docs/process/okr_progress_log.md`，11-12 已追加打回原因 | 合同/dry-run 不等于 OpenCV 识别或真实电梯流程 |
| O3：可验证导航与固定路线 | 继续留在当前推进区，保持约 73% | 旧 ~99% 软件归档保留在 `docs/process/okr_progress_log.md`，11-12 已追加打回原因 | `learn.launch`/dry-run 不等于 SLAM map、定位恢复或 Nav2 实跑 |
| O5：云中转控制面 | 从当前 96% 打回约 84%，旧 96% 仅作为软件证明历史 | 本轮追加到 `docs/process/okr_progress_log.md` | 连续 Micro 未产生 accepted live material，生产云/4G/DB/OSS/phone-browser 仍缺 |
| O6：云端核心后端 | 从当前 96% 打回约 82%，旧 96% 仅作为软件证明历史 | 本轮追加到 `docs/process/okr_progress_log.md` | 缺真实 DB/queue、OSS、推理 runtime、上车数据和查询回放 |
| O8：Epic 交付节奏与证据治理 | 从约 40% 上调到约 43%，继续留在当前推进区 | `sprints/2026.06.04_20-21_runtime-material-followup/`、`sprints/2026.06.04_21-22_runtime-material-runtime-hooks/` 与 `docs/process/okr_progress_log.md` | 治理进展不证明产品能力；下一轮仍需真实 runtime/HIL/field material |
| O4：手机用户体验与量产边界 | 暂留历史归档，不在本轮打回 | `docs/process/okr_progress_log.md` | 后续若 CEO 要求真实手机端发车、状态、接管，应单独拉回当前推进区 |

本轮没有 O2/O3/O7 产品 KR 进入历史完成归档；O8 的 Epic governance 和 evidence type gate 已进入 `docs/process/okr_progress_log.md` 历史进展。20-21 把 O3 root cause 收敛为 live 8787 hook 未配置和 ROS graph 空；21-22 进一步把下一步收敛为部署/重载本地已实现的 `POST /api/radar/scan-proof/refresh`。现场 8787 目前对该 route 返回 HTTP 405，因此本轮只计 `software_guard + blocked_with_root_cause`，不把 PC refresh 按钮或本地 upper API 合同写成 runtime material。下一步必须先部署 refresh route，再拿 fresh `/scan` proof；同时继续回填真实图片 manifest，并按 O8 全链路留档。

---

## 5. 当前最高优先级

当前优先级为 **O2/O3 真实材料 -> O7 operator 端到端 -> O1 stop-first HIL -> O8 持续治理 -> O5/O6**。O8 已完成首轮 Epic 治理小幅涨分，但不抢产品主线；产品侧最低缺口仍是 O2/O3，因为普通用户要的是“把垃圾交给小车后能跨楼层送达”，不是 collector、runbook 或 status 面。

下一轮必须继续跨 owner Epic，但 L2 派单要更窄，目标从“本地合同完成但现场未部署”转为 deployed refresh route、fresh ROS2 runtime、真实/受控图片和 stop-first HIL：

1. **Robot Software Engineer + User Touchpoint Full-Stack Engineer**：KR-O3/O7-Scan-Proof-Refresh-Deploy。确认 8787 安全 reload/service 路径，部署本地 `POST /api/radar/scan-proof/refresh` 和 PC 同源 refresh 代理；材料至少包含 live POST refresh 响应、`/api/radar/scan-proof/latest` fresh artifact、PC 同源触发结果、`safe_to_control=false` 和同一 `evidence_ref`。route 部署成功后再继续 map/localize/Nav2。
2. **Robot Algorithm Engineer**：KR-O2-Real-Image-Manifest-Eval。用 `pc-tools/evidence/templates/elevator_image_manifest_collection_template.json` 回填真实或受控电梯图片，再运行 `--check-template` 和 OpenCV offline eval，输出样本清单、混淆项、阈值、不可判定策略和 phone-safe operator summary。
3. **Hardware Infra Engineer + User Touchpoint Full-Stack Engineer**：KR-O1/O7-Stop-First-HIL。按 `docs/hardware/o1_pc_manual_lidar_hil_boundary.md` 做 stop-first 低速 pulse；材料至少包含现场安全前提、manual response、stop response、post-status、`T=1001` 同场边界、operator report 和视频/现场记录。
4. **Product Manager / OKR Owner**：KR-O8-Epic-Governance。下一轮 `tech-plan.md` 必须包含 OKR 最低优先级核对、最近 2 轮 blocker scan、evidence type gate、owner health 检查和不继续 O5/O6 Micro 的理由；`final.md` 必须复核这些理由是否成立。

Epic 验收口径：

- PC WASD：W/S/A/D/Space/X 在现场对真实小车有效，forward/back/left/right/stop 全部有 manual response、stop response、post-status、operator report 和同一 evidence ref。
- 雷达：PC 一键开启/关闭 LiDAR/ROS2 driver，`/scan` once/hz、停止后状态和日志可回放，且不触碰底盘 UART。
- 建图/定位：PC 或 upper API 能开启、重置、保存、加载地图并发布定位；至少有 `/map` artifact、map metadata、AMCL pose、TF 和失败原因。
- 电梯 OpenCV：必须从 fixture 扩展到真实或受控图片 manifest；进入 ROS2 状态机前必须输出 not_proven 边界和人工接管策略。
- O8：证据链必须完整，且所有涨分项标注 evidence type；没有 `robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material` 时不得上调产品 Objective。

> 当前 70%-90%+ 只代表软件入口、合同或首个 smoke。真实材料未完成时，任何 Objective 都不得表述为真实硬件闭环、真实 PC 控车、真实建图定位、真实 OpenCV 电梯识别、真实生产云、真实手机或真实送达完成。

---

## 6. OKR 完成路线

### 下一轮 Epic（必须启动）

- 打通 PC/8787 雷达 start/stop 到真实 LiDAR/ROS2 runtime，并采 `/scan` once/hz 和 stop 后状态。
- 打通 PC/8787 map/localize 到 SLAM Toolbox、map server、AMCL/Nav2 lifecycle，并采 map artifact、AMCL pose、TF 或明确 blocker。
- 把 OpenCV 电梯 baseline 接真实或受控图片 manifest，输出离线评估和人工接管策略。
- 做一次 stop-first 低速 HIL drill；安全条件不足时升级 CEO 决策，不继续写 Micro 文档。
- 补完整 Epic 文档链和 side-to-side 验收，不再用连续 Micro sprint 刷 `software_proof`。

### 近期（现场闭环）

- O1：真实 WAVE ROVER 底盘低速短 pulse、stop/post-status、ACK/T=1001 同场证据、ROS feedback topics。
- O2：OpenCV 电梯识别 baseline 进入 ROS2 状态机，至少完成真实/受控离线评估和人工接管策略。
- O3：SLAM Toolbox `/map`、map artifact、AMCL 定位恢复、Nav2 消费 `/scan`+map。
- O7：PC operator workflow 形成“查看状态 -> 开雷达 -> 建图/定位 -> WASD/stop -> 记录证据 -> 回放”的完整链路。
- O8：每轮收口检查 Micro/Epic 比例、重复 blocker 和 evidence type，防止流程产物替代真实交付。

### 中期（真实生产和数据闭环）

- O5/O6 接入真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实推理 runtime。
- 电梯/路线/地图/手控材料进入 archive/query/annotation/inference，形成可训练和可复盘数据。
- PC 与手机共享真实任务状态、地图、路线、电梯和人工接管摘要。

### 后期（用户验收）

- 真实路线采集 + Nav2/固定路线实跑。
- 真实电梯受控流程 3 次连续通过。
- 真实手机/browser 一键发车、状态查看、人工接管和任务回放。
- 真实低成本量产边界复核：不新增机械臂、不改电梯、不让用户理解 ROS2/SSH/串口。

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

更新时间：2026-06-04，对应 `sprints/2026.06.04_01-02_okr-current-state-rebalance/tech-done.md`。

本节只保留当前仍需推进或仍需验证的 Objective。详细历史、单 sprint 证据和旧百分比变更记录统一沉淀到 `docs/process/okr_progress_log.md`，避免当前 KR 被历史材料淹没。

### 当前百分比与涨分规则

| Objective | 当前比例 | 方向判断 | 比例怎么涨 |
| --- | --- | --- | --- |
| O5：云中转控制面产品化 | 约 96% | 继续，当前最低完成度，最高优先级排第一 | 只靠真实生产材料涨分：公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 每形成可回放证据再涨；继续扩 runbook/status 面不涨。 |
| O6：云端核心后端 | 约 96% | 继续，和 O5 并列最低，最高优先级排第二 | 只靠真实后端闭环材料涨分：真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据和 PC/手机查询回放每形成可回放证据再涨；mock archive 或只读摘要不再涨。 |
| O1：硬件协议可信底盘 | 约 97% | 继续，硬件主链路关键风险未关 | LiDAR `/scan` smoke 已计入；后续涨分来自 driver 优雅退出、production udev、长稳 smoke、SLAM/Nav2 消费、地图质量、底盘受控短 pulse、ACK/`T=1001` 同源证据、ROS feedback topics 和 HIL 复核。 |
| O7：PC 端运营调试平台 | 约 98.9% | 继续，但不再靠 UI 拆分大幅涨分 | realtime radar/map split 已计入；后续只靠真实 SLAM/map artifact、真实 8787/browser 复跑、production path、完整 operator workflow、弱网/reboot 自恢复和真实手控/Nav2 灰度材料小幅涨分。 |

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**当前比例：约 97%**
**责任 Engineer：Hardware Infra Engineer 主责，Robot Software Engineer 配合 ROS2 topic/bringup。**
**方向判断：继续。O1 已从 LiDAR runtime blocker 推进到首个 ROS2 `/scan` smoke observed，但底盘 HIL、ACK、安全准入和 SLAM/Nav2 消费仍未闭环。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `mock serial` / virtual HIL packet 已覆盖 WAVE ROVER JSON newline 编码、`T=1` wheel command、`T=1001` 解析、IMU/Battery 发布、坏帧容错和参数边界；8787 上位机 API 已有 status、stop、feedback-request、feedback-samples/latest、manual 软件入口；`/dev/ttyS5 @115200` 已作为底盘可写入口记录；非运动 `T=130 -> T=1001` samples 已有 3/3 observed 和 readback artifact；`/dev/ttyACM0 @150000` LiDAR 口已按 vendor ROS2 资料记录；`2026.06.04_00-01_o1-upper-ros2-bootstrap-continue` 首次观察到 `/scan` once、`/scan` hz 约 295-300 Hz、`/lidar/raw_packet` once、`tf2_echo base_link laser_frame` 和 `all_required_observations_observed=true`。 |
| 当前下一步可涨分 KR | 1. LiDAR 线：修 driver 优雅退出，补 `/dev/lidar` 或 by-id production udev，完成 10-30 分钟长稳 `/scan` smoke，并产出 SLAM/Nav2 消费与地图 artifact。2. 底盘线：在现场看护、物理净空、人工急停可用时，用 8787 `/api/base/manual` 做低速短 pulse，采集 status/manual/stop/post-status、operator report、ACK 或 `T=1001`、日志和安全复位证据。3. ROS feedback 线：把真实 `/odom`、`/imu/data`、`/battery` 与 vendor feedback 边界分清，形成可回放 topic 证据。 |
| 不可越界的 not_proven 风险 | 当前不证明 WAVE ROVER HIL、robot ACK 语义、闭环运动安全、左右转现场效果闭环、急停演练、真实 ROS `/cmd_vel` 接入、真实 `/odom`/`/imu/data`/`/battery`、SLAM/Nav2 消费、长稳运行、production udev、完整上车任务闭环或 `safe_to_control` 正向准入。 |

### Objective 5：云中转控制面产品化

**当前比例：约 96%**
**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Software Engineer 配合 robot command/ACK 合同。**
**方向判断：继续，最高优先级排第一。O5/O6 是当前最低完成度，下一轮必须优先补真实生产材料，不能继续只堆状态面。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | 本地/mock control plane 已覆盖 `trashbot.remote.v1` commands/status/ack、bearer/env credential、mock 4G interruption、mock DB/queue artifact、mock OSS/CDN manifest 和 graceful degradation；O5 readiness live health、O5/O6 aggregate health、Node/Python external probe、HTTPS cloud base URL 脱敏 TLS evidence summary、PC external probe artifact API、`GET /api/real-material/acceptance` 与 `RealMaterialAcceptancePanel.vue` 已形成真实材料验收队列和 collection runbook。 |
| 当前下一步可涨分 KR | 1. 真实公网 HTTPS/TLS endpoint 可由外部网络访问，TLS 摘要和 endpoint reachability 进入 external probe artifact。2. 真实 4G/SIM 或等价蜂窝链路下，Orange Pi outbound 连接云中转，采集断线/重连与 command polling 材料。3. production DB/queue/worker 真实运行，至少一条 robot command/status/ACK 控制面记录可查询、可回放。4. OSS/CDN live traffic 与真实 phone/browser 材料进入 real material acceptance queue。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产云、真实公网入口、真实 4G/SIM、production DB/queue、production worker/cutover、OSS/CDN 实流量、真实 phone/browser、真实 robot command 执行或上车任务闭环。ACK 仍只能按合同材料解释，不能外推为送达闭环。 |

### Objective 6：云端核心后端 - 数据存档、模型推理与打标平台

**当前比例：约 96%**
**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Algorithm Engineer 配合数据/推理证据。**
**方向判断：继续，最高优先级排第二。O6 与 O5 并列最低，必须从 mock archive/readiness 推进到真实生产数据链。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `trashbot.archive.v1` task/event/annotation/inference/query、机器人侧 event publisher、algorithm feed 和 state path fence 已可复验；O6 archive live health、O5/O6 aggregate health、Node/Python external probe、脱敏 TLS evidence summary、PC artifact 摘要、real material acceptance queue 与 collection runbook 已可见；本地/Docker mock 能证明 archive/query/annotation/inference 基线逻辑。 |
| 当前下一步可涨分 KR | 1. 真实隧道打通 Orange Pi -> 云端事件上报，至少一条上车状态/事件写入生产后端。2. production DB/queue 持久化任务、事件、轨迹与 ACK 材料，并能从 PC/手机查询回放。3. 真实 OSS upload 产出路线/截图/日志对象，云端只保存引用。4. 真实推理 runtime 或外部模型服务接入一次电梯/楼层/障碍材料，输出可追溯 inference artifact。 |
| 不可越界的 not_proven 风险 | 当前不证明真实安全隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实云、真实 4G/SIM、真实 phone/browser、真实生产 TLS 验收、真实上车数据或完整数据运营闭环。 |

### Objective 7：PC 端运营调试与数据训练平台

**当前比例：约 98.9%**
**责任 Engineer：User Touchpoint Full-Stack Engineer 主责，Robot Software Engineer 配合 8787/ROS2 状态合同。**
**方向判断：继续，但 UI split 不再大幅涨分。O7 已接近软件侧封顶，剩余分数必须来自真实 runtime 和 production operator workflow。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | LAN-only WebRTC camera smoke、30s/180s browser material、camera systemd persistence、PC Live Operator consuming unified upper API live status、direct manual buttons/WASD/direct API path、camera 首屏 no auto-offer 均已进入软件验收口径；`sprints/2026.06.04_00-01_o1-o7-realtime-scan-map-split/final.md` 证明 PC 首屏拆成 `实时雷达 (/scan)` 与 `实时图 (SLAM/map)`，`GET /api/o7/live-operator-panel` 新增 `realtime_radar` 与 `realtime_map`，8787 `/api/radar/status` 补齐 `/scan` hz、TF 和 required observations summary；Full-Stack 验证为 81 tests passed、build/lint passed、Playwright rendered smoke passed。 |
| 当前下一步可涨分 KR | 1. 接入真实 SLAM/map artifact，让 `realtime_map` 从 waiting 状态变为可检查地图证据。2. 用真实 8787 与 browser 复跑 O7 rendered smoke，记录 production path、auth/relay/TURN 或同 LAN 边界。3. 完整 operator workflow：查看状态 -> 预览 -> 受控手控或 Nav2 下发 -> 停止/恢复 -> 任务记录可回放。4. 验证 reboot 自恢复、弱网、ASR/TTS、真实 phone/browser 协同入口。 |
| 不可越界的 not_proven 风险 | 当前不证明真实 SLAM/map artifact、真实 `/api/base/manual` 受控灰度、robot ACK、真实 `/odom`/`/imu/data`/`/battery`、production path、真实 complete operator workflow、真实手控/Nav2、弱网、ASR/TTS 或完整上车任务闭环。raw packet proof 只能作为诊断材料，不能点亮 `/scan` ready。 |

---

## 4.1 当前 OKR 进度快照

更新时间：2026-06-04，对应本轮 `sprints/2026.06.04_01-02_okr-current-state-rebalance`。

**比例更新规则**：O5/O6 只有真实生产 TLS/公网/4G/DB/OSS/phone-browser 材料才涨；O1 只有长稳、SLAM/Nav2、production udev、HIL、ACK 或 `safe_to_control` 正向准入材料才涨；O7 只有真实 SLAM/map artifact、production operator workflow、真实手控/Nav2 或完整上车任务才涨。继续增加 runbook、状态面、只读 readback 或 UI 拆分，不再单独涨分。

| Objective | 当前比例 | 已验收/可计入 | 下一步可涨分 KR | 不得越界 |
| --- | --- | --- | --- | --- |
| O5：云中转控制面 | 约 96% | mock/control plane、readiness health、external probe、TLS summary、real material acceptance queue | 真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser | 真实生产云、真实蜂窝链路、真实 robot command 执行、完整上车任务闭环 |
| O6：云端核心后端 | 约 96% | mock archive/query/annotation/inference、archive health、external probe artifact、acceptance queue | 真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据查询回放 | 真实生产数据链、真实云、真实 4G/SIM、真实 OSS/推理/上车数据 |
| O1：硬件协议可信底盘 | 约 97% | ttyS5 可写材料、非运动 `T=130 -> T=1001` samples、LiDAR ROS2 `/scan` smoke、`/lidar/raw_packet` once、static TF | LiDAR 长稳/udev/SLAM/Nav2/map、底盘低速短 pulse、ACK/`T=1001` 同源材料、ROS feedback topics、HIL 复核 | 底盘 HIL、闭环安全控制、robot ACK 语义、ROS feedback topic、SLAM/Nav2、完整上车任务闭环、`safe_to_control` 正向准入 |
| O7：PC 端运营调试平台 | 约 98.9% | camera/systemd、PC direct manual UI/API、首屏 no auto-offer、realtime radar/map split 软件验收 | 真实 SLAM/map artifact、真实 8787/browser 复跑、production path、完整 operator workflow、弱网/reboot/ASR/TTS | 真实生产 operator workflow、真实手控/Nav2、真实任务闭环、真实 SLAM/map |

**已归档 Objective（软件侧完成，等待真实现场验证）：**

| Objective | 软件侧进度 | 归档原因 | 历史记录位置 |
| --- | --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 软件完成 ~99% | 状态机、行为链、电梯状态链、任务记录软件侧全部完成；等待真实路线/电梯/现场跑通后升回当前 | `docs/process/okr_progress_log.md` |
| O3：可验证导航与固定路线 | 软件完成 ~99% | `learn.launch`、fixed route、Nav2 dry-run 软件侧完成；等待真实路线采集、Nav2 实跑、关键帧实景证据 | `docs/process/okr_progress_log.md` |
| O4：手机用户体验与量产边界 | 软件完成 ~99% | 手机 UI、地图首屏、任务下发、状态展示软件侧完成；等待真实 iPhone/Android 设备验收和真实送达 | `docs/process/okr_progress_log.md` |

本轮 `2026.06.04_01-02_okr-current-state-rebalance` 没有新增完成 KR 归档；只是把当前推进区和历史区拆清楚。真实现场材料到位后，再按证据重新激活 O2/O3/O4 或提升 O1/O5/O6/O7。

---

## 5. 当前最高优先级

按完成度从低到高排序。O5/O6 约 96%，是当前最低完成度，因此最高优先级排序为 **O5/O6 -> O1 -> O7**；下一轮 Epic 的 `tech-plan.md` 应优先核对本节：

本轮 `sprints/2026.06.04_05-06_o5-o6-upper-ssh-pc-base-contract/tech-done.md` 只更新当前最高优先级抓手，不调整 O5/O6 百分比：`pc_upper_ssh_collector` 已修正上位机 SSH 视角的 PC base URL 合同，未显式传 `--pc-base-url http://<pc-workstation-host>:8787` 或 `ROBER_O5_O6_EXTERNAL_PROBE_PC_BASE_URL` 时，不再默认把远端 loopback `127.0.0.1:8787` 误当 PC workstation；artifact 仍为 `fail_closed` 时不得涨分。

1. **O5（约 96%，最高优先级第一）**：从真实材料验收队列进入实际采集。验收口径是公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 至少形成一条可回放 artifact；继续扩 runbook/status/readback 不涨分。
2. **O6（约 96%，最高优先级第二）**：把 archive core 从 mock/readiness 推到真实生产数据链。验收口径是真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据至少形成一条可查询回放链。
   - 当前抓手：`pc_upper_ssh_collector` 继续作为 O5/O6 真实材料采集入口；下一步必须配置有效 `cloud_base_url`、远端 bearer token、上位机可达的显式 PC workstation base URL（例如 `--pc-base-url http://<pc-workstation-host>:8787`），并修正 HTTP/schema 缺口，采到 accepted live artifact 后才能涨分。
3. **O1（约 97%）**：分 LiDAR 与底盘两条线推进。LiDAR 线补 driver 优雅退出、production udev、长稳 smoke、SLAM/Nav2 消费与地图质量；底盘线只在现场看护、物理净空、人工急停可用时做低速短 pulse，并采 status/manual/stop/post-status、operator report、ACK 或 `T=1001`、日志和安全复位证据。
4. **O7（约 98.9%）**：不再因 UI 文案或区块拆分大幅涨分。下一步补真实 SLAM/map artifact、真实 8787/browser 复跑、production path、完整 operator workflow、弱网/reboot、ASR/TTS、真实手控/Nav2 和完整任务闭环材料。

> 当前 90%+ 只代表 mock/software/material-entry completion。真实材料未完成时，任何 Objective 都不得表述为真实硬件闭环、真实生产云、真实 4G、真实 OSS/CDN、真实 PC/手机或真实上车完成。

---

## 6. OKR 完成路线

### 近期（O5/O6 MVP）

- 真实公网 HTTPS/TLS 云入口可由外部网络访问，external probe artifact 可回放。
- Orange Pi 通过真实 4G/SIM 或等价蜂窝链路 outbound 连接云中转，断线自动重连。
- 云端建任务/事件/轨迹/ACK 存档表，小车侧完成后 POST 到云端，PC/手机可查询。
- 大对象走 OSS，云端只存引用；至少产出一条真实 upload + query 材料。

### 近期（O1/O7 MVP）

- LiDAR 从首个 `/scan` smoke 推进到长稳、production udev、SLAM/Nav2 消费和地图质量 artifact。
- 底盘在现场安全条件满足后做低速短 pulse、stop/post-status、ACK 或 `T=1001`、日志和安全复位证据。
- PC 端接入真实 SLAM/map artifact，展示实时雷达和实时图的分离状态。
- 真实 8787/browser 复跑 operator workflow，保留 no auto-offer、安全锁、手控失败原因和任务记录。

### 中期

- 模型推理上云（电梯门开/关、楼层识别）；推理结果写入存档。
- PC 端电梯状态实时展示，ASR/TTS 调试界面。
- PC 端手控和自动寻路下发走云端 API 或受控 direct upper path，并保留 fail-closed 证据。
- O5/O6 接入 production DB/queue/OSS/CDN，并完成恢复/回放/审计材料。

### 后期（真实现场验证，激活归档 Objective）

- 真实 WAVE ROVER 与真实 LiDAR 上车实测，O1 闭环。
- 真实路线采集 + Nav2/固定路线实跑，激活 O3。
- 真实电梯场景验证，激活 O2。
- 真实手机/browser 验收，激活 O4。

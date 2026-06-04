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

更新时间：2026-06-05 04-05 CST，对应 `sprints/2026.06.05_04-05_okr-six-sprint-state-rewrite/tech-done.md`。本轮复盘最近 6 个迭代：`20-21_runtime-material-followup`、`21-22_runtime-material-runtime-hooks`、`22-23_runtime-material-deploy-refresh`、`00-01_o9-fresh-scan-proof-runtime`、`01-02_o9_scan_hz_tf_runtime`、`02-03_o9_radar_status_fresh_proof`；必要时引用 `17-18`/`19-20` 判断趋势。

本轮方向判断是 **继续：沿 O9 breakthrough 调整口径执行，不改变北极星**。北极星仍是普通手机用户把垃圾交给低成本小车，小车沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。

关键结论：16:05 之后团队从连续 Micro 转向 Epic，方向明显改善；`01-02` 进一步证明 O9 fresh scan proof 可以产出 live runtime material。`02-03_o9_radar_status_fresh_proof` 有价值，但只是 `/api/radar/status` 消费 latest proof 的状态契约/readback 改进：测试通过、远端文件已同步，但没有远端 restart/curl 验证，没有新 runtime material，PC 侧测试失败且半成品已清理。因此本轮不叠加 O9/O3/O7 产品涨分。下一步不能再开 Micro-only interface/readback sprint，必须拉一个窄 Epic，把 O3 拉向 continuous radar 或 SLAM `/map` lifecycle，把 O7 拉向 PC 同源触发复验，把 O2 拉向真实/受控电梯图片，把 O1 拉向 stop-first HIL 决策门。

真实材料边界：`22-23` 已解除 refresh route HTTP 405 和 ROS logging env blocker；`00-01` 把 blocker 收窄到 `scan_hz=false` / `tf=false`；`01-02` micro sprint 通过 live 8787 refresh/latest 形成 `proof_state=scan_once_hz_raw_packet_tf_observed`，`evidence_type=robot_runtime_material`，`scan_hz_average_rate_hz=257.987`，`runtime_summary_fallback_used=true`，`blockers_summary=[]`。安全字段保持 `safe_to_control=false`、`sends_base_motion_commands=false`、`robot_control_executed=false`、`hil_pass=false`。`02-03` 只让 `/api/radar/status` 能表达 `fresh_scan_proof_observed` 与 `continuous_scan_status=not_proven` 的差异，且未完成远端加载和 PC 消费。因此当前只证明 live fresh scan proof artifact，不证明 continuous radar ready、SLAM `/map`、AMCL、Nav2、PC WASD、HIL、WAVE ROVER ACK 或 `safe_to_control=true`。

### 最近迭代问题与新增证据

| Sprint | 类型 | 证据事实 | 战略判断 |
| --- | --- | --- | --- |
| `16-05_okr-six-sprint-strategy-rewrite` | Micro | 打回 O5/O6、重建 evidence type 和 O8 治理口径，强制下一轮 Epic。 | 方向正确，但只是 Product 口径，不产生产品材料。 |
| `16-17_o2-elevator-opencv-state-integration` | Micro | OpenCV baseline JSON artifact 已接入 `task_orchestrator`，测试和 smoke 通过。 | 支撑 O2 software guard，但仍缺真实/受控电梯图片 manifest，不涨 O2。 |
| `17-18_runtime-material-epic` | Epic | 真实 8787 operator report POST/GET 和 PC 同源 readback 通过；O8 首轮 Epic 治理闭环。 | O7/O8 小涨合理；O1/O2/O3 不涨，因为无 HIL、图片、map、AMCL、Nav2。 |
| `19-20_runtime-material-continue` | Epic | Algorithm 有 O2 模板/checker，Robot Software、Full-Stack、Hardware 三个 L2 超时无材料。 | 暴露派单粒度问题；O8 不涨，Product 必须检查员工状态。 |
| `20-21_runtime-material-followup` | Epic | 缩小 owner 任务后全员有 note；O7 operator-report readback 小涨，O8 小涨。 | 方法改善，但 O2 卡真实/受控图片，O3 卡 live hook/ROS graph 空，O1 只有非运动 `T=1001`。 |
| `21-22_runtime-material-runtime-hooks` | Epic | 本地 `scan-proof/refresh` 合同和 PC 按钮完成；live upper 8787 返回 HTTP 405，未部署新 route。 | O8 小涨；O3/O7 不涨。下一轮必须先部署 refresh route，拿 fresh scan proof。 |
| `22-23_runtime-material-deploy-refresh` | Epic | 上位机 route 已部署，HTTP 405 解除；PC fail-closed 展示 upper `not_proven` 与 blockers。 | O8 可计治理小涨；O3/O7 不涨，因为 fresh `/scan` runtime material 未成立。 |
| `00-01_o9-fresh-scan-proof-runtime` | Epic | API-managed LiDAR runtime hook 和远端 partial proof 成立，root cause 收窄到 `scan_hz=false` / `tf=false`。 | 方向正确，但未达到 `robot_runtime_material`，不涨 O9/O3/O7；两次 worker 超时暴露执行链路问题。 |
| `01-02_o9_scan_hz_tf_runtime` | Micro | live 8787 refresh/latest 返回 full fresh scan proof，`evidence_type=robot_runtime_material`，但 radar/status 仍 not_proven。 | O9/O3/O7 可按证据边界小幅涨分；不得写成 continuous radar、地图、导航、HIL 或控车成功。 |
| `02-03_o9_radar_status_fresh_proof` | Micro | `/api/radar/status` 增加 latest proof readback 字段，本地 40 tests/compileall/diff-check 通过；远端未 restart/curl，PC 侧 3 tests failed 后清理半成品。 | 只算状态契约改进，不新增 runtime material；不叠加 KR-O9/O3/O7 进度，并触发“下一轮不能再 Micro-only 接口/readback”的治理要求。 |

### 战略支撑判断

这些改进 **支撑 OKR 战略定位，但只支撑到治理和入口层**：

- O8 有价值：连续 Epic、evidence type、owner notes、blocker 收口和本轮 04-05 审计让团队不再只刷 Micro；因此 O8 只做治理性小幅上调，不证明产品能力。
- O7 有部分价值：真实 8787 operator report、PC 同源 readback 和 8787 refresh/latest 证明 operator workflow 的证据入口在变真；但 PC 按钮同源触发本轮未复验。
- O2 有结构价值：OpenCV baseline 进入行为状态机，说明电梯 assisted delivery 已从文档走向软件链路。
- O3 有一次真实 runtime 破局：fresh `/scan` once/hz、raw packet 和 TF 已成 artifact；但没有 continuous radar、`/map`、AMCL、Nav2、低速 pulse、stop/post-status 或 `safe_to_control=true`。`02-03` 的 radar/status readback 不改变这个边界。
- O1 仍未破局：没有 stop-first HIL、robot ACK、ROS feedback topics 或现场安全授权下的运动材料。
- O5/O6 不应抢主线：最近证据仍没有 production live material，它们只应等待 O2/O3/O7/O1 真实材料进入 archive/control plane。

### 员工状态

| 角色 | 当前状态 | 下一轮命令式要求 |
| --- | --- | --- |
| Full-stack Software Engineer | 能完成 PC 同源代理、operator report readback 和 refresh 按钮；但 01-02 未复验 PC 按钮，02-03 PC 侧消费 fresh proof 测试失败并清理半成品。 | 只接一个链路：复验 PC 同源触发 live 8787 `POST /api/radar/scan-proof/refresh`，正确展示 `runtime_summary_fallback_used`、hz、TF、fresh proof 和 continuous not_proven 边界；不扩 UI 面。 |
| Robot Software Engineer | 已把 live 8787 refresh/latest 推进到 fresh scan proof material；02-03 status contract 单测通过，但未 remote restart/curl，SLAM/map/AMCL/Nav2 未证明。 | P0 推进 continuous radar/status 或 SLAM/map lifecycle：保留 `safe_to_control=false`，不得把 fresh artifact 或 status readback 外推成导航可用。 |
| Robot Algorithm Engineer | O2 模板、checker、OpenCV baseline、fixture eval 可复跑；真实/受控图片 manifest 仍为空。 | P0 交付真实/受控电梯图片 manifest 和 offline eval，不再只扩 taxonomy、fixture 或 checker。 |
| Hardware Infra Engineer | 安全边界和 vendor/HIL 口径清楚；但 O1 仍只有非运动 `T=130 -> T=1001`。 | P1 做 stop-first HIL：只有现场看护、净空、急停、授权满足才低速 pulse；不满足必须升级 CEO 决策 blocker，不写成 HIL pass。 |
| Product Manager / OKR Owner | 已打回虚高产品 Objective，并在 04-05 明确 02-03 不叠加产品涨分。 | 每轮先查最近 2 轮 blocker、员工状态和 Micro/Epic 比例；O9 仍缺电梯图片、stop-first HIL 和 owner guard，不得让团队回到 runbook/接口扩写。 |

### 当前百分比与涨分规则

| Objective | 当前比例 | 方向判断 | 比例怎么涨 |
| --- | --- | --- | --- |
| O1：硬件协议可信底盘 | 约 95.5% | 继续，HIL 是硬门槛 | 只靠 stop-first 低速短 pulse、stop/post-status、`T=1001` 同场边界、ROS feedback topics、LiDAR 长稳和现场安全授权涨分。 |
| O2：可送垃圾任务 + 电梯 assisted delivery | 约 72% | 调整，主线第一优先级 | 只靠真实/受控电梯图片 manifest、OpenCV field eval、ROS2 电梯状态机 runtime、受控电梯流程和人工接管材料涨分。 |
| O3：可验证导航、建图、定位与固定路线 | 约 75% | 调整，主线第一优先级 | 已按 fresh `/scan` once/hz、raw packet、TF runtime artifact 小幅涨分；后续只靠 SLAM `/map`、map artifact、AMCL `/initialpose`、Nav2 消费 `/scan`+map、continuous radar 和路线材料继续涨。 |
| O5：云中转控制面产品化 | 约 84% | 调整，降为支线 | 只靠真实公网 HTTPS/TLS、真实 4G/SIM、production DB/queue、OSS/CDN live traffic、真实 phone/browser 和 robot command/status/ACK 生产材料涨分。 |
| O6：云端核心后端 | 约 82% | 调整，等待真实上车材料 | 只靠真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据查询回放涨分。 |
| O7：PC 端运营调试平台 | 约 91% | 继续，必须从 API runtime proof 走向 PC 同源 operator workflow | 已按 8787 refresh/latest runtime proof 小幅涨分；后续只靠 PC 触发 fresh runtime refresh 复验、真实雷达 start/stop、建图/定位控制、PC WASD 现场控车、stop/急停和 operator workflow 涨分。 |
| O8：Epic 交付节奏与证据治理 | 约 45% | 继续，组织治理小幅上调 | 04-05 完成最近 6 个迭代审计、员工状态检查、Micro/Epic 风险打回、02-03 不叠加涨分和下一轮窄 Epic 验收口径；O8 不证明产品能力。 |
| O9：短周期真实材料破局战役 | 约 18% | 继续，执行型 breakthrough Objective | 已完成 refresh route 部署和 01-02 fresh scan proof artifact；02-03 只是 status readback contract。后续只靠真实/受控电梯图片、stop-first HIL 授权、PC 同源复验、continuous radar/SLAM 推进和 Epic owner 超时防护涨分。 |

### Objective 1：打通官方硬件协议，建立可信底盘控制层

**责任 Engineer：Hardware Infra Engineer 主责，Robot Software Engineer 配合 ROS2 topic/bringup。**
**方向判断：继续。当前材料有 `/dev/ttyS5`、非运动 `T=130 -> T=1001` 和 LiDAR smoke，但没有 HIL、ACK 同场闭环或 ROS feedback topics。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | mock serial、fake serial、8787 status/stop/manual/feedback 软件入口、`/dev/ttyS5 @115200` 底盘可写入口材料、非运动 `T=130 -> T=1001` samples、LiDAR `/scan` once/hz、`/lidar/raw_packet` once 和 `base_link -> laser_frame` static TF。 |
| KR-O1-Stop-First-HIL | 现场看护、物理净空、人工急停和 CEO/现场授权同时满足后，用 8787 `/api/base/manual` 完成 forward/back/left/right/stop 低速短 pulse；材料必须包含 manual response、stop response、post-status、operator report、视频或现场记录。Owner：Hardware Infra Engineer。 |
| KR-O1/O7-ACK-T1001-Bridge | 把 PC 手控请求、8787 `/api/base/manual`、底盘 `T=1`、stop、`T=130 -> T=1001`、日志时间戳和 operator report 对齐到同一 evidence ref；`T=1001` 只能作为 vendor feedback material，不能单独写成 robot ACK。Owner：Hardware Infra Engineer + Full-stack Software Engineer。 |
| KR-O1-ROS-Feedback-Topics | 采集真实 `/odom`、`/imu/data`、`/battery` 与 vendor feedback 的边界证据；没有 topic 证据时不得宣称 Nav2 可消费或底盘闭环。Owner：Robot Software Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明 PC WASD 已真实控车、底盘 HIL、闭环运动安全、左右转现场有效、急停演练、robot ACK、真实 `/odom`/`/imu/data`/`/battery`、SLAM/Nav2 消费、完整上车任务闭环或 `safe_to_control=true`。 |

### Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环

**责任 Engineer：Robot Algorithm Engineer 主责 OpenCV 识别，Robot Software Engineer 主责状态机接入，Full-stack Software Engineer 配合 PC/手机状态。**
**方向判断：调整。16-17 已把 OpenCV baseline 接入状态机，这是有效 software guard；但没有真实/受控电梯图片 manifest，O2 不涨。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `docs/product/elevator_assisted_delivery.md`、dry-run evidence schema、OpenCV taxonomy、ROI/rule baseline、offline fixture eval、16-17 `opencv_baseline` 状态机接入和 fail-closed 回归。 |
| KR-O2-Real-Controlled-Image-Manifest | 回填真实/受控电梯图片 manifest，输出样本清单、拍摄位置、门线/轿厢/楼层显示屏 ROI、不可判定样本和安全边界。Owner：Robot Algorithm Engineer。 |
| KR-O2-OpenCV-Field-Eval | 基于真实/受控图片跑 OpenCV eval，输出 false positive、false negative、阈值、混淆项和人工接管策略；fixture eval 不再涨分。Owner：Robot Algorithm Engineer。 |
| KR-O2-ROS2-State-Runtime | 用真实/受控 eval artifact 驱动 `task_orchestrator` 电梯状态链，覆盖等待开门、进入、请求按楼层、等待目标楼层、开门驶出、人工接管；task record 必须保留关键快照和失败原因。Owner：Robot Software Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实相机电梯识别、楼层 OCR、目标楼层确认、OpenCV 规则有效、真实进出电梯、真实跨楼层送达、真实喇叭/TTS 播放、真实手机用户验收或 delivery success。 |

### Objective 3：可验证导航、建图、定位与固定路线

**责任 Engineer：Robot Software Engineer 主责 ROS2/SLAM/Map API，Robot Algorithm Engineer 主责 Nav2/路线质量，Full-stack Software Engineer 配合 PC 控制面。**
**方向判断：调整。22-23 已解除 live upper 8787 的 refresh route HTTP 405，00-01 把 blocker 收窄到 `scan_hz=false` / `tf=false`，01-02 已证明 live fresh `/scan` once/hz、raw packet 和 TF artifact；下一步必须从单次 proof 进入 continuous radar/status、SLAM `/map`、AMCL 和 Nav2 消费。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `learn.launch.py` 学习阶段入口、`/trashbot/save_map` Trigger、Nav2 include、首个 LiDAR `/scan` smoke、8787 `/api/map/*` 和 `/api/localize/reset` software guard、本地 `POST /api/radar/scan-proof/refresh` 合同、22-23 live route 部署后 HTTP 405 解除、01-02 live 8787 refresh/latest fresh `/scan` once/hz/raw/TF artifact。 |
| KR-O3/O7-Deploy-Refresh-Route | 当前状态：live route 已部署并解除 HTTP 405，`POST /api/radar/scan-proof/refresh` 返回 HTTP 200，01-02 latest 写入 full fresh proof；PC 按钮同源触发仍需复验。Owner：Robot Software Engineer + Full-stack Software Engineer。 |
| KR-O3-Fresh-Scan-Proof | 阶段完成：01-02 已采集 fresh `/scan` once/hz、`/lidar/raw_packet`、TF、latest artifact 和同一 evidence ref，证据边界为 `robot_runtime_material`；但采用同轮 runtime summary fallback，不是 continuous radar ready。Owner：Robot Software Engineer。 |
| KR-O3-SLAM-Map-Lifecycle | fresh scan proof 完成后，下一步推进开启 SLAM、重置地图、保存地图、加载地图、列出 map artifact；至少形成 `/map` once、map file、metadata、日志和 PC/upper API 可回放证据。Owner：Robot Software Engineer。 |
| KR-O3-Nav2-Consumption | 证明 Nav2 消费真实 `/scan` + map：map server、AMCL、planner/controller lifecycle 状态、路径生成、短距离目标或 fixed-route dry-run 到实跑的边界清晰。Owner：Robot Algorithm Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明 continuous radar ready、真实建图完成、地图 artifact 可用、重置/保存/加载链路、定位恢复、Nav2 真实路径执行、固定路线现场通过、关键帧实景匹配或任务闭环。 |

### Objective 5：云中转控制面产品化

**责任 Engineer：Full-stack Software Engineer 主责，Robot Software Engineer 配合 robot command/ACK 合同。**
**方向判断：调整并降为支线。O5 仍重要，但没有真实生产云、4G、DB/queue 和 phone/browser 材料前，不得抢 O2/O3/O7/O1 的破局战役。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | 本地/mock control plane、readiness health、aggregate health、external probe、TLS evidence summary、real material acceptance queue、`pc_upper_ssh_collector`、preflight 分类、installed probe 同步。 |
| KR-O5-Production-Live-Control | 真实公网 HTTPS/TLS、真实 4G/SIM 或等价蜂窝链路、production DB/queue/worker、真实 phone/browser 和 robot command/status/ACK 控制面记录进入 accepted live artifact。Owner：Full-stack Software Engineer。 |
| KR-O5-Blocker-Escalation | 若 `pc_base_url_not_configured_for_upper_ssh`、`cloud_base_url_not_configured`、`remote_bearer_token_absent` 再出现一次，必须在 Epic pre_start 升级 CEO 决策或暂停 O5 sprint。Owner：Product Manager / OKR Owner。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产云、真实公网入口、真实蜂窝链路、production DB/queue、OSS/CDN 实流量、真实 phone/browser、真实 robot command 执行或上车任务闭环。 |

### Objective 6：云端核心后端 - 数据存档、模型推理与打标平台

**责任 Engineer：Full-stack Software Engineer 主责，Robot Algorithm Engineer 配合数据/推理证据。**
**方向判断：调整并降为支线。O6 的 archive/query/annotation/inference 软件合同很多，但要等 O2/O3/O7/O1 产生真实上车材料后才有产品意义。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | `trashbot.archive.v1` task/event/annotation/inference/query、algorithm feed、archive health、external probe artifact、acceptance queue 与本地/Docker mock archive/query/annotation/inference 基线逻辑。 |
| KR-O6-Production-Archive-Query | 真实隧道、production DB/queue、真实 OSS upload、真实推理 runtime、真实上车数据查询回放；优先消费 O2/O3/O7/O1 产生的电梯、地图、路线和 operator workflow 材料。Owner：Full-stack Software Engineer + Robot Algorithm Engineer。 |
| KR-O6-Field-Material-Ingestion | 至少 ingest 一组来自 O2/O3/O7/O1 的真实 runtime/HIL/field material，并完成 phone/PC 安全摘要、查询回放和 not_proven 边界。Owner：Full-stack Software Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实生产数据链、真实 OSS、真实推理、真实上车数据、真实 4G/SIM、真实 phone/browser 或完整数据运营闭环。 |

### Objective 7：PC 端运营调试与数据训练平台

**责任 Engineer：Full-stack Software Engineer 主责，Robot Software Engineer 配合 8787/ROS2 状态合同，Hardware Infra Engineer 配合底盘现场证据。**
**方向判断：继续。O7 已从 UI/API 走到真实 8787 operator report readback 和 upper refresh/latest runtime proof；但还没完成 PC 按钮同源触发复验、控车或 HIL。**

| KR 类型 | 当前口径 |
| --- | --- |
| 已验收软件/材料入口 | PC 同源 API、WASD/按钮映射、camera 首屏 no auto-offer、realtime radar/map split、direct-upper radar/map/localize/report UI/API 护栏、真实 8787 operator report POST/GET route、PC 同源 operator report readback、PC scan-proof refresh software guard、01-02 8787 refresh/latest runtime proof。 |
| KR-O7-Refresh-Button-Live | PC refresh 按钮必须触发 live 8787 deployed refresh route，返回 fresh scan proof；01-02 已证明 8787 API refresh/latest full proof，但 PC 按钮同源触发未复验。Owner：Full-stack Software Engineer + Robot Software Engineer。 |
| KR-O7-PC-Manual-Field | PC 浏览器用 W/S/A/D 与 Space/X 完成受控 forward/back/left/right/stop 现场点动，证据与 O1 stop-first HIL 同源；UI 必须展示 ACK/T=1001 边界、stop 结果、失败原因和 operator report。Owner：Full-stack Software Engineer + Hardware Infra Engineer。 |
| KR-O7-Map-SLAM-Controls | PC 提供建图开启、重置、保存、加载、定位入口，全部走 upper API/ROS2 服务；每个按钮都要显示 ROS2 操作状态、artifact 路径、失败原因和 not_proven 边界。Owner：Full-stack Software Engineer + Robot Software Engineer。 |
| 不可越界的 not_proven 风险 | 当前不证明真实 PC WASD 控车、PC 按钮已同源触发 fresh proof、真实雷达一键长稳、真实建图控制、真实定位恢复、真实 Nav2 下发、production path、弱网、ASR/TTS、robot ACK、HIL 或完整 operator workflow。 |

### Objective 8：Epic 交付节奏与证据治理

**责任 Owner：Product Manager / OKR Owner 主责，四个 L2 Engineer 执行。**
**方向判断：继续。O8 是组织执行 Objective，不新增产品能力；04-05 可小涨，因为完成最近 6 个迭代审计、员工状态检查、Micro/Epic 风险打回、02-03 不实叠加进度拦截和下一轮窄 Epic 验收口径重写。**

| KR 类型 | 当前口径 |
| --- | --- |
| KR-O8-Epic-Cadence | 实现类工作继续默认 Epic；Micro 只允许单 owner 小修、单文档或单命令材料，且不能连续替代真实材料。Owner：Product Manager / OKR Owner。 |
| KR-O8-Owner-Timeout-Guard | Epic 任务必须拆成单 owner、单 artifact、单验收命令；19-20 的三 L2 超时进入反面样本，下一轮若再次发生，Product 必须改派单粒度而不是等待超时。Owner：Product Manager / OKR Owner。 |
| KR-O8-Evidence-Type-Gate | 每个涨分 KR 必须标注 evidence type：`software_guard`、`robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material`；只有后四类中的真实材料可推动产品 Objective 完成度。Owner：Product Manager / OKR Owner。 |
| KR-O8-Repeated-Blocker-Stop | 最近 2 轮如果出现同一 blocker root cause，第 3 轮必须切 Objective 或升级 CEO 决策；O3/O7 不能再消费 refresh route 405 或 `ros2_command_unavailable`，下一轮必须处理 LiDAR topics/TF runtime。Owner：Product Manager / OKR Owner。 |
| KR-O8-Micro-Loop-Stop | 下一轮实现工作不得再以 Micro-only 接口/readback sprint 消费 O9；若安全资源、电梯图片或现场权限缺失，必须在 Epic pre_start 写 CEO 决策 blocker，而不是拆成更多 status/readback Micro。Owner：Product Manager / OKR Owner。 |
| 不可越界的 not_proven 风险 | O8 规则和文档不证明产品能力完成；只有后续 sprint 按 O9 产出真实 runtime/HIL/field material 才能涨产品 Objective。 |

### Objective 9：短周期真实材料破局战役

**责任 Owner：Product Manager / OKR Owner 统筹，Robot Software Engineer、Full-stack Software Engineer、Robot Algorithm Engineer、Hardware Infra Engineer 分别交付。**
**方向判断：继续。O9 是 72 小时内解决真实材料断点的 breakthrough，不是长期流程愿景，也不是用 O8 继续写治理；当前已完成 01-02 fresh scan proof 子 KR，但 02-03 只完成 status readback contract，整体 O9 仍缺电梯图片、stop-first HIL、PC 同源复验和 continuous radar/SLAM 新材料。**

| KR 类型 | 当前口径 |
| --- | --- |
| KR-O9-Deploy-Refresh-Route | 阶段完成：live 8787 service/reload 已完成，`POST /api/radar/scan-proof/refresh` 不再 405，`/api/radar/scan-proof/latest` 可写入新 `evidence_ref`；PC 同源触发仍需 Full-stack 复验。Owner：Robot Software Engineer + Full-stack Software Engineer。证据边界：`robot_runtime_material`。 |
| KR-O9-Fresh-Scan-Proof | 完成归档：01-02 拿到 fresh scan proof，包含 `/scan` once/hz、`/lidar/raw_packet`、TF、artifact timestamp、`safe_to_control=false`、`hil_pass=false` 和 not_proven 边界；证据采用 runtime summary fallback，不能外推为 continuous radar ready。Owner：Robot Software Engineer。证据边界：`robot_runtime_material`。 |
| KR-O9-Radar-Status-Readback | 02-03 完成本地 status contract 和测试，但未 remote restart/curl，PC 侧消费失败后清理；作为 useful readback contract 记录，不作为 O9 完成度涨分 KR。Owner：Robot Software Engineer + Full-stack Software Engineer。证据边界：`software_guard`。 |
| KR-O9-Real-Controlled-Elevator-Images | 真实/受控电梯图片：采集并校验 `trashbot.elevator_image_manifest.v1`，完成 OpenCV eval、样本清单、混淆项、阈值和人工接管策略。Owner：Robot Algorithm Engineer。证据边界：`robot_runtime_material` 或受控 field 前置材料。 |
| KR-O9-Stop-First-HIL-Authorization | stop-first HIL：现场安全前提满足时完成一次低速 pulse + stop/post-status + operator report；不满足时形成 CEO 决策级 blocker，不得写成 HIL pass。Owner：Hardware Infra Engineer + Full-stack Software Engineer。证据边界：`field_hil_material` 或 `blocked_with_root_cause`。 |
| KR-O9-Narrow-Epic-Real-Material-Gate | 下一轮必须用窄 Epic 同时覆盖 PC 同源复验、continuous radar/status 或 SLAM map lifecycle、真实/受控电梯图片、stop-first HIL 决策门；任一资源缺失必须写 CEO blocker。Owner：Product Manager / OKR Owner。证据边界：组织治理，不涨产品 Objective。 |
| KR-O9-Epic-Owner-Timeout-Guard | Epic owner 超时防护：下一轮 `tech-plan.md` 将四个 owner 拆成单命令链和单 artifact；`final.md` 必须逐 owner 记录完成、超时、阻塞和重试策略。Owner：Product Manager / OKR Owner。证据边界：组织治理，不涨产品 Objective。 |
| CEO 决策点 | 若现场无法部署 8787 route、无法采电梯图片、无法满足 stop-first HIL 安全前提，CEO 需要在下一轮 pre_start 明确提供现场资源、允许远程部署、暂停对应 KR 或切换 Objective。 |

---

## 4.1 当前 OKR 进度快照

更新时间：2026-06-05 04-05 CST，对应本轮 `sprints/2026.06.05_04-05_okr-six-sprint-state-rewrite/tech-done.md`。

**比例更新规则**：O1/O2/O3/O7 只有真实现场、ROS2 runtime、HIL、OpenCV eval、地图 artifact、operator workflow 或受控电梯材料才涨；O5/O6 只有真实生产云、4G/公网/DB/OSS/phone-browser/上车数据才涨；O8 只有执行证据链、blocker 升级、员工状态和 evidence type 复核生效才涨；O9 只有短周期真实材料交付才涨。继续增加 Micro sprint、mock、fixture、UI 文案、readback、状态面或只读 runbook 不再涨产品 Objective。

| Objective | 当前比例 | 本轮变化 | 已验收/可计入 | 下一步可涨分 KR | 不得越界 |
| --- | --- | --- | --- | --- | --- |
| O1：硬件协议可信底盘 | 约 95.5% | 保持 | `/dev/ttyS5` 可写材料、非运动 `T=130 -> T=1001`、LiDAR `/scan` once/hz、TF、PC manual/LiDAR 隔离准入；01-02 安全字段继续 fail-closed | KR-O9-Stop-First-HIL-Authorization、KR-O1-ROS-Feedback-Topics | `safe_to_control=true`、HIL pass、robot ACK、真实 `/odom`/`/imu/data`/`/battery` |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 保持 | 产品 contract、dry-run evidence schema、OpenCV taxonomy/ROI/rule/offline fixture eval、16-17 状态机 software guard | KR-O9-Real-Controlled-Elevator-Images、KR-O2-OpenCV-Field-Eval、KR-O2-ROS2-State-Runtime | 真实电梯识别、楼层 OCR、实景进出电梯、跨楼层送达 |
| O3：建图、定位、Nav2 与固定路线 | 约 75% | +2pp；fresh scan proof artifact 成立 | `learn.launch.py`、Nav2 include、首个 `/scan` smoke、map/localize software guard、本地 scan-proof refresh 合同、deployed route HTTP 200/latest artifact loaded、01-02 live fresh `/scan` once/hz/raw/TF runtime material | KR-O3-SLAM-Map-Lifecycle、KR-O3-Nav2-Consumption、continuous radar/status | continuous radar ready、真实地图可用、定位恢复、Nav2 实跑、路线通过 |
| O5：云中转控制面 | 约 84% | 保持 | mock/control plane、readiness health、external probe、TLS summary、acceptance queue、SSH collector installed probe | KR-O5-Production-Live-Control | 真实生产云、真实蜂窝链路、真实 robot command 执行 |
| O6：云端核心后端 | 约 82% | 保持 | mock archive/query/annotation/inference、archive health、external probe artifact、acceptance queue | KR-O6-Production-Archive-Query、KR-O6-Field-Material-Ingestion | 真实生产数据链、真实 OSS/推理/上车数据 |
| O7：PC 运营调试平台 | 约 91% | 保持；02-03 PC 侧失败不叠加 | WASD/按钮软件入口、PC 同源代理、真实 8787 status/map/operator-report proxy runtime、operator-report readback、PC scan-proof refresh software guard、fail-closed blocker display、01-02 refresh/latest runtime proof；02-03 只验证后端 status contract，PC 消费未完成 | KR-O7-Refresh-Button-Live PC 同源复验、KR-O7-PC-Manual-Field | 真实控车、PC 按钮同源触发已验证、真实雷达长稳、真实建图定位、production workflow |
| O8：Epic 交付节奏与证据治理 | 约 45% | +1pp；04-05 OKR review materially improves governance | AGENTS/iteration_velocity 规则、16-05 口径重写、17-18/20-21/21-22 Epic 治理、22-23 解除部署 405、解除 ROS logging blocker、00-01 收窄到 LiDAR runtime、04-05 拦截 02-03 不实涨分并强制下一轮窄 Epic | KR-O8-Owner-Timeout-Guard、KR-O8-Repeated-Blocker-Stop、KR-O8-Micro-Loop-Stop、KR-O9-Epic-Owner-Timeout-Guard | 不能把流程合规写成产品能力或 OKR 产品涨分 |
| O9：短周期真实材料破局战役 | 约 18% | 保持；02-03 无新 runtime/HIL/field material | 22-23 完成 KR 定义、解除 405 和 blocker 收敛；00-01 修复 false negative；01-02 8787 refresh/latest 形成 `robot_runtime_material`，但 radar/status 仍 not_proven；02-03 是 status readback contract，不新增 runtime material | KR-O9-Real-Controlled-Elevator-Images、KR-O9-Stop-First-HIL-Authorization、KR-O9-Narrow-Epic-Real-Material-Gate、PC 同源复验、continuous radar/SLAM | 不能把 live fresh artifact 或 status readback 写成 continuous radar、SLAM/map、Nav2、PC 控车、HIL 或 `safe_to_control=true` |

**历史归档区调整：**

| Objective/KR | 当前处理 | 历史记录位置 | 剩余风险 |
| --- | --- | --- | --- |
| O7 operator report route/readback | 作为 O7 入口进展保留，仍留当前推进区等待 runtime workflow | `docs/process/okr_progress_log.md` 的 17-18、20-21、22-23 记录 | 不证明 PC WASD、refresh runtime、HIL 或 production archive |
| O8 Epic governance/evidence gate | 进入历史进展；22-23 治理进展保留到约 44%，04-05 审计后当前 O8 为约 45% | `docs/process/okr_progress_log.md` 的 16-05、17-18、20-21、21-22、22-23、04-05 记录 | 治理不证明产品能力，必须让 O9 交付真实材料 |
| O2 OpenCV 状态机 software guard | 继续作为 O2 软件入口保留，不进入完成归档 | `sprints/2026.06.04_16-17_o2-elevator-opencv-state-integration/tech-done.md` | 缺真实/受控图片 manifest 和 field eval |
| KR-O9-Fresh-Scan-Proof / O3 fresh `/scan` material | 完成归档：live 8787 refresh/latest 已返回 `proof_state=scan_once_hz_raw_packet_tf_observed` 和 `evidence_type=robot_runtime_material` | `sprints/2026.06.05_01-02_o9_scan_hz_tf_runtime/tech-done.md` | 采用 runtime summary fallback；`/api/radar/status` 仍 not_proven，不证明 continuous radar、SLAM/map、Nav2、HIL 或控车 |
| KR-O9-Radar-Status-Readback | 作为 useful readback contract 记录，不进入产品完成归档，也不叠加 O9/O3/O7 涨分 | `sprints/2026.06.05_02-03_o9_radar_status_fresh_proof/tech-done.md` | 本地测试通过但远端未 restart/curl；PC 侧 3 tests failed 后清理，仍缺 PC 同源消费与新 runtime material |
| O3/O7 scan-proof refresh deploy | route 部署、405 解除、ROS logging guard 和 fresh proof 进入历史进展；PC 同源按钮复验继续留当前推进区 | `sprints/2026.06.04_21-22_runtime-material-runtime-hooks/final.md`、`sprints/2026.06.04_22-23_runtime-material-deploy-refresh/final.md`、`sprints/2026.06.05_01-02_o9_scan_hz_tf_runtime/tech-done.md` | 不证明 PC 按钮已触发、真实雷达长稳、地图、定位、Nav2 或完整 operator workflow |
| O5/O6 旧高完成度 | 继续按 16:05 打回后的支线口径处理 | `docs/process/okr_progress_log.md` 的 16-05 记录 | 缺 production live material，不应抢 O9 |

本轮新增归档判断是：`02-03_o9_radar_status_fresh_proof` 有助于 operator 判读，但不是新的 KR-O9 runtime breakthrough。O1/O2/O3/O5/O6/O7/O9 不涨；O8 仅因 04-05 审计打回不实进度、检查员工状态和重写下一轮窄 Epic 验收口径小涨。下一轮如果只重复 refresh/latest 或 status/readback，而不推进 continuous radar、SLAM/map、PC 同源触发、真实/受控电梯图片或 stop-first HIL，不允许继续上调 O9。

---

## 5. 当前最高优先级

当前优先级为 **O9 窄 Epic 真实材料突破 -> O3 continuous radar/SLAM -> O7 PC 同源复验 -> O2 真实/受控电梯图片 -> O1 stop-first HIL 决策门 -> O8 防 Micro 回流治理 -> O5/O6 支线等待**。

下一轮不再接受“继续写接口”“重复 refresh/latest”“只补 status/readback”作为主任务。必须按 O9 拉一个短周期窄 Epic，四个 owner 任务必须窄到单命令链、单 artifact、单验收口径；如果安全、人、图像、远端权限或现场资源缺失，必须在 pre_start 写 CEO 决策 blocker，不能继续拆 Micro 消费同一缺口：

1. **Robot Software Engineer：推进 continuous radar/status 或 SLAM/map lifecycle。** 基于已成立的 fresh proof，修 `/api/radar/status` 仍 not_proven 的连续性问题，或进入 `/map` once、map artifact、AMCL/Nav2 前置验证；保持 `safe_to_control=false`。
2. **Robot Software Engineer + Full-stack Software Engineer：PC 同源 refresh 复验。** PC 按钮触发已部署 route，展示 `proof_state=scan_once_hz_raw_packet_tf_observed`、`scan_hz_average_rate_hz`、`runtime_summary_fallback_used`、fresh proof 和 continuous not_proven 边界。
3. **Robot Algorithm Engineer：真实/受控电梯图片。** 采集并校验 manifest，跑 OpenCV eval，输出样本清单、混淆项、阈值和人工接管策略。
4. **Hardware Infra Engineer + Full-stack Software Engineer：stop-first HIL。** 有现场看护、净空、急停、授权才做低速 pulse；否则直接升级 CEO 决策，不得产出 HIL pass 文案。
5. **Product Manager / OKR Owner：Epic owner 超时防护。** `pre_start.md` 必须写最近 2 轮 blocker scan、员工状态、Micro/Epic 风险、CEO 决策 blocker；`tech-plan.md` 必须写单 owner 验收命令和 evidence type；`final.md` 必须逐 owner 复盘超时、阻塞和重试。

验收口径：

- Continuous radar/status 或 SLAM/map：不能只复读 latest full proof；必须让 `/api/radar/status` blocker 有明确收敛，或形成 `/map` once/map artifact/metadata 的新 evidence ref。
- PC 同源 refresh：浏览器按钮必须触发 live 8787 route，UI/API 显示 `runtime_summary_fallback_used`、hz、TF 和 fail-closed 安全字段。
- 真实/受控电梯图片：manifest 必须能被 checker 接受，OpenCV eval 必须输出 false positive/false negative 和人工接管策略。
- Stop-first HIL：材料必须包含 safety preflight、manual response、stop response、post-status、`T=1001` 同场边界和 operator report；不满足安全前提时只允许写 blocker。
- O8/O9：所有涨分项必须标注 evidence type；重复 `01-02` 已归档的 fresh proof 或 `02-03` status readback 不再涨分，必须产生新的 `robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material`。

> 当前 70%-90%+ 只代表软件入口、合同、首个 smoke、operator readback 或单次 fresh runtime artifact。真实材料未完成时，任何 Objective 都不得表述为 continuous radar ready、真实硬件闭环、真实 PC 控车、真实建图定位、真实 OpenCV 电梯识别、真实生产云、真实手机或真实送达完成。

---

## 6. OKR 完成路线

### 下一轮窄 Epic（O9 必须继续）

- 基于 fresh scan proof，推进 `/api/radar/status` continuous radar blocker 收敛，或进入 SLAM `/map` artifact。
- 通过 PC 同源触发 fresh scan proof，证明按钮和 8787 latest 同源；如果 PC parser/UI 继续失败，必须定位并重开，不得写成 O7 完成。
- 回填真实/受控电梯图片 manifest，完成 OpenCV eval；如果没有图片资源，必须升级 CEO 决策 blocker。
- 按 stop-first HIL 做安全授权判断，满足则低速 pulse，不满足则升级 CEO 决策。
- 用 O8 owner 超时防护控制派单粒度，不再让多个 L2 同时超时，也不让 Micro 接口/readback 代替真实材料。

### 近期（现场闭环）

- O1：真实 WAVE ROVER 底盘低速短 pulse、stop/post-status、ACK/T=1001 同场证据、ROS feedback topics。
- O2：OpenCV 电梯识别 baseline 基于真实/受控图片进入 ROS2 状态机，至少完成受控流程材料和人工接管策略。
- O3：SLAM Toolbox `/map`、map artifact、AMCL 定位恢复、Nav2 消费 `/scan`+map。
- O7：PC operator workflow 形成“查看状态 -> refresh scan proof -> 开雷达 -> 建图/定位 -> WASD/stop -> 记录证据 -> 回放”的完整链路。
- O8/O9：每轮收口检查 Micro/Epic 比例、重复 blocker、员工状态、evidence type 和 breakthrough 材料。

### 中期（真实生产和数据闭环）

- O5/O6 接入真实公网 HTTPS/TLS、4G/SIM、production DB/queue、OSS/CDN、真实推理 runtime。
- 电梯/路线/地图/手控材料进入 archive/query/annotation/inference，形成可训练和可复盘数据。
- PC 与手机共享真实任务状态、地图、路线、电梯和人工接管摘要。

### 后期（用户验收）

- 真实路线采集 + Nav2/固定路线实跑。
- 真实电梯受控流程 3 次连续通过。
- 真实手机/browser 一键发车、状态查看、人工接管和任务回放。
- 真实低成本量产边界复核：不新增机械臂、不改电梯、不让用户理解 ROS2/SSH/串口。

# Pre Start: Real Control, SLAM, Elevator Field Epic

## sprint_type

sprint_type: epic

## 用户价值和产品北极星

北极星保持不变：普通手机用户把垃圾交给低成本小车后，小车沿固定路线送到垃圾站，必要时跨楼层进出电梯，并在异常时安全停止、请求人工协助和留下可复盘证据。

本小时 Epic 的用户价值不是继续补文案或软件入口，而是把现场 operator 的真实能力往前推：PC 能真实控车，右侧雷达能一键开关，建图/定位能和 ROS2/SLAM/Nav2 联动，电梯进出开始进入 OpenCV 语义识别与 ROS2 状态链。测试只做护栏；mock、stub、fixture 可以推进开发，但不得把 mock 写成真实完成。

## 上轮结论输入

证据来源：`sprints/2026.06.04_11-12_okr-strategy-reset-real-control-slam-elevator/final.md`。

| Objective | 当前比例 | 上轮方向判断 | 本轮必须推进的真实抓手 |
| --- | --- | --- | --- |
| O2：送垃圾任务 + 电梯 assisted delivery | 约 72% | 调整，撤回当前推进区 | OpenCV 电梯 taxonomy、ROI/rule baseline、offline eval、ROS2 电梯状态链 |
| O3：建图、定位、Nav2 与固定路线 | 约 73% | 调整，撤回当前推进区 | SLAM `/map`、reset/save/load、AMCL `/initialpose`、Nav2 消费 `/scan`+map |
| O7：PC 运营调试平台 | 约 88% | 继续并打回 | PC WASD 真实控车、雷达 start/stop、建图/定位控制、stop/急停/operator report |
| O1：硬件协议可信底盘 | 约 95% | 继续并打回 | WAVE ROVER 低速短 pulse、stop/post-status、`T=1001` 同场材料、ROS feedback topics |
| O5/O6：云与数据 | 约 96% | 继续但不抢占 | 等待 O2/O3/O7 产生真实上车材料后再涨分 |

## 本轮方向判断

继续，但从 OKR 打回转入真实能力 Epic。当前最低完成度是 O2 和 O3，本轮直接覆盖两者，同时联动 O7 和 O1，因为 PC 控车、雷达、建图定位、电梯识别是同一现场闭环的四个必要面。

不调整 Objective，不上调完成度，不把 SSH 可达性或无法上车作为 blocker 主线。`ssh root@192.168.1.11 -p 37878` 可作为上位机运行通道；若上车环境临时不可用，L2 仍应先用 mock/stub/fixture 把接口、状态、artifact 和 fail-closed 护栏跑通，并保留真实切换入口。

## KR 拆解和本轮核心抓手

| KR | Objective | Owner | 本轮抓手 | 验收口径 |
| --- | --- | --- | --- | --- |
| KR-O7-PC-Manual-Field | O7/O1 | full-stack-software-engineer + robot-hardware-engineer | PC WASD/按钮到 8787 manual/stop 的现场 operator workflow | W/S/A/D/Space/X 对真实小车形成 forward/back/left/right/stop 材料；缺现场时必须输出 not_proven 的 operator rehearsal artifact |
| KR-O7-Radar-OneClick | O7/O1 | full-stack-software-engineer + robot-software-engineer | PC 右侧雷达 start/stop 和 status | `POST /api/radar/start|stop` 只触发 LiDAR/ROS2 driver，不触碰底盘 UART；状态和日志可回放 |
| KR-O3-SLAM-Map-Lifecycle | O3/O7 | robot-software-engineer + full-stack-software-engineer | upper API/PC 控制建图、重置、保存、加载、列出 artifact | 至少形成 `/map` once、map file、metadata、API response、失败原因；无真实 ROS runtime 时用 fixture 明确 not_proven |
| KR-O3-Localization-Reset | O3/O7 | robot-software-engineer | `/initialpose`、AMCL lifecycle、load map 后定位恢复 | 输出 `/amcl_pose`、TF、pose freshness、失败原因；未实跑不得写成定位成功 |
| KR-O3-Nav2-Consumption | O3 | robot-algorithm-engineer + robot-software-engineer | 证明 Nav2 消费 `/scan` + map 的质量和路线边界 | lifecycle、path、短目标或 fixed-route 材料；mock 只能算 software guard |
| KR-O2-OpenCV-Elevator-Taxonomy | O2 | robot-algorithm-engineer | 定义门线/门缝、轿厢内外、楼层 ROI、可驶出/不可驶出的 taxonomy | 样本要求、正负例、失败边界、人工接管口径完整 |
| KR-O2-OpenCV-ROI-Rule-Baseline | O2 | robot-algorithm-engineer | OpenCV ROI + rule baseline | 对真实或受控图片 fixture 输出可解释识别结果、阈值和不可判定策略 |
| KR-O2-ROS2-State-Integration | O2 | robot-software-engineer + robot-algorithm-engineer | OpenCV 结果进入 `task_orchestrator` 电梯状态链 | task record 保留关键快照、失败原因、人工接管和 phone-safe summary |
| KR-O1-Base-Manual-HIL | O1/O7 | robot-hardware-engineer | 现场安全前提、低速短 pulse、stop/post-status、`T=1001` 同场材料 | 物理净空、人工急停、operator report、manual/stop/status 同一 evidence ref |

## 需要做什么

1. Product/OKR Owner 完成本轮 `pre_start.md`、`prd.md`、`tech-plan.md`，并在 `OKR.md` 只补当前 Epic 指向，不上调完成度。
2. Coordinator 后续按 `tech-plan.md` 四个 owner 并行派发 L2 Engineer；主节点不得直接写产品代码、测试代码或硬件配置。
3. L2 Engineer 在各自范围内实现、验证、修复并更新后续 `tech-done.md`；Product/OKR Owner 最后依据证据更新 `side2side_check.md` 和 `final.md`。

## 优先级和验收口径

1. P0：O2/O3。电梯 OpenCV 和 SLAM/定位是最低完成度，也是 trash delivery 北极星阻塞。
2. P0：O7。PC operator 必须提供真实控车、雷达、地图和人工报告入口，否则现场不能采证。
3. P1：O1。底盘 HIL 和 ROS feedback 是真实运动安全底座，必须和 O7 同场对齐。
4. P2：O5/O6。本轮只消费 O2/O3/O7 产生的材料，不作为主线。

验收必须区分三类：`software_guard`、`robot_runtime_material`、`field_hil_material`。只有 `robot_runtime_material` 或 `field_hil_material` 可以推动 O1/O2/O3/O7 百分比；mock/stub/fixture 只能证明接口和护栏。

## 风险、阻塞和证据链缺口

- 真实控车和底盘 HIL 依赖现场净空、观察员、急停和硬件状态；缺现场时不阻塞软件接口推进，但不得写成 HIL 完成。
- 上位机 SSH 是运行通道，命令为 `ssh root@192.168.1.11 -p 37878`；连接失败只能作为本轮执行风险，不能成为放弃 PC/SLAM/OpenCV 开发的 blocker 主线。
- 电梯真实识别依赖样本质量、光照、楼层屏和安全观察员；本轮允许先用受控图片 fixture，但必须保留真实图片切换入口。
- 硬件真实集成阶段必须二次查阅 `docs/vendor/VENDOR_INDEX.md` 及其指向 vendor 资料，本轮 Product 文档不新增引脚、电压、波特率或机械尺寸假设。

## 已完成 KR 历史记录位置

本轮启动阶段没有已完成 KR 进入历史归档。O2/O3 旧“软件完成约 99%”记录仍保留在 `docs/process/okr_progress_log.md` 作为历史纠偏材料，当前推进区以 `OKR.md` 4.1 节为准。剩余风险是旧软件证明容易被误读为真实闭环；本轮所有 L2 输出必须明确 evidence boundary。

## 需要创建或更新的 sprint 文档

- 已创建/更新：`pre_start.md`
- 已创建/更新：`prd.md`
- 已创建/更新：`tech-plan.md`
- 后续由 L2 执行后更新：`tech-done.md`
- 后续 Product/OKR Owner 收口更新：`side2side_check.md`
- 后续 Product/OKR Owner 收口更新：`final.md`

## 候选 KR 与 CEO 决策点

本轮不新增 Objective，但提出一个候选 KR 供 CEO 决策：

| Objective | KR 草案 | 用户价值 | owner | 最小实现路径 | 验收命令 | 证据边界 | 风险 | CEO 决策点 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| O7/O3 | KR-O7/O3-Operator-Map-Session-Replay | 现场 operator 能回放一次从开雷达到建图保存再定位的完整会话，降低调试和售后成本 | full-stack-software-engineer + robot-software-engineer | PC 记录 radar start、map start/reset/save/load、localize、ROS 状态和 artifact refs | `npm run build`、targeted API tests、ROS2/map lifecycle smoke | `software_guard` 到 `robot_runtime_material`，未上车不得涨为 field | 可能扩大 PC 数据模型范围 | 是否纳入本轮 P0，还是等 SLAM lifecycle 先完成后再做 |

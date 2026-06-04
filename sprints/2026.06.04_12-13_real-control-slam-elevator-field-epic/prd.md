# PRD: Real Control, SLAM, Elevator Field Epic

## 需求目标

sprint_type: epic

本轮 Epic 要把上一轮 OKR 打回后的真实能力缺口转成可执行任务，供四个 L2 IC 并行推进：

1. PC 端从 WASD 软件入口推进到真实 operator 控车 workflow。
2. 右侧雷达从状态展示推进到一键开启/关闭。
3. SLAM/定位从 launch 入口推进到建图、重置、保存、加载、定位和 Nav2 消费链。
4. 电梯 assisted delivery 从合同/dry-run 推进到 OpenCV taxonomy、ROI/rule baseline、offline eval 和 ROS2 状态机接入。

本轮目标是功能往前走，测试只做护栏。允许 mock/stub/fixture 先打通接口，但所有 PRD 和验收都必须写明 mock 不等于真实完成。

## 用户价值和产品北极星

普通用户只用手机，不理解 SSH、ROS2、串口或地图文件。为了让手机端最终能“一键发车、看状态、异常接管”，研发现场必须先有 PC operator 工具完成四件事：控制小车、开关雷达、建图定位、记录电梯识别证据。

产品北极星仍是低成本 trash delivery：用户把垃圾交给小车，小车送到垃圾站/垃圾桶点位，跨楼层时通过电梯 assisted delivery 完成等待、进入、请求按楼层、确认目标楼层、驶出和继续送达；不承诺机械臂捡垃圾，不改造电梯。

## OKR 映射和方向判断

| Objective | 当前比例 | 方向判断 | 本轮处理 |
| --- | --- | --- | --- |
| O2：可送垃圾任务 + 电梯 assisted delivery | 约 72% | 继续调整 | 用 OpenCV taxonomy、ROI/rule baseline、offline eval 和状态机接入推进；不因文档或 fixture 涨分 |
| O3：可验证导航、建图、定位与固定路线 | 约 73% | 继续调整 | 用 SLAM map lifecycle、AMCL reset、Nav2 consumption 和 map quality 推进 |
| O7：PC 运营调试平台 | 约 88% | 继续并打回后修复 | 用 PC WASD 现场 workflow、雷达 start/stop、建图/定位控制和 operator report 推进 |
| O1：硬件协议可信底盘 | 约 95% | 继续 | 配合 PC 手控 HIL、stop/post-status、`T=1001` 同场材料和 ROS feedback |
| O5/O6：云与数据 | 约 96% | 继续但暂停抢占 | 本轮只等待 O2/O3/O7 产出可存档材料 |

方向判断：继续，不替换 Objective。本轮 Epic 正面覆盖最低完成度 O2/O3，并把 O7/O1 作为现场能力底座。

## 角色和责任 Engineer

| 责任 Engineer | 主责用户价值 | 本轮可改范围建议 | 不可越界 |
| --- | --- | --- | --- |
| full-stack-software-engineer | PC operator 能控制、开关、建图、报告 | `pc-tools/workstation/**`、必要 PC docs | 不直接绕过后端访问 ROS graph；不把 mock UI 写成真实控车 |
| robot-software-engineer | ROS2/upper API 把 map、localize、Nav2、电梯状态接起来 | `onboard/scripts/upper_robot_api.py`、`onboard/src/ros2_trashbot_*`、bringup/launch 相关 docs | 不改硬件协议假设；无 ROS runtime 不得宣称定位成功 |
| robot-algorithm-engineer | 电梯识别和地图质量变成可评估能力 | `onboard/src/ros2_trashbot_vision/**`、`onboard/src/ros2_trashbot_nav/**`、`pc-tools/evidence/**`、算法 docs | 不把 ORB keyframe 或固定等待冒充电梯语义识别 |
| robot-hardware-engineer | 真实底盘与 LiDAR 现场安全材料 | hardware smoke/probe、vendor-readback、HIL evidence docs | 真实集成前必须读 `docs/vendor/VENDOR_INDEX.md`，不得猜引脚、电压、UART 或速度映射 |

## KR 拆解、更新或历史归档

| KR | Objective | 状态 | 验收口径 | 历史/当前处理 |
| --- | --- | --- | --- | --- |
| KR-O7-PC-Manual-Field | O7/O1 | 当前推进 | PC W/S/A/D/Space/X 现场点动，manual response、stop response、post-status、operator report 同一 evidence ref | 当前推进区 |
| KR-O7-Radar-OneClick | O7/O1 | 当前推进 | PC `POST /api/radar/start|stop`，只控制 LiDAR/ROS2 driver，状态和日志可回放 | 当前推进区 |
| KR-O7-Map-SLAM-Controls | O7/O3 | 当前推进 | PC 建图开启、重置、保存、加载、定位按钮走 upper API，显示 artifact/失败原因 | 当前推进区 |
| KR-O3-SLAM-Map-Lifecycle | O3 | 当前推进 | `/map` once、map file、metadata、reset/save/load、API evidence | 当前推进区 |
| KR-O3-Localization-Reset | O3 | 当前推进 | `/initialpose`、AMCL lifecycle、`/amcl_pose`、TF、pose freshness | 当前推进区 |
| KR-O3-Nav2-Consumption | O3 | 当前推进 | Nav2 lifecycle、path、短目标或 fixed-route 材料，清楚区分 dry-run 和实跑 | 当前推进区 |
| KR-O2-OpenCV-Elevator-Taxonomy | O2 | 当前推进 | 门线/门缝、轿厢、楼层 ROI、目标楼层、安全驶出 taxonomy 和样本要求 | 当前推进区 |
| KR-O2-OpenCV-ROI-Rule-Baseline | O2 | 当前推进 | OpenCV baseline 对 fixture/真实图片输出可解释结果和阈值 | 当前推进区 |
| KR-O2-Offline-Eval | O2 | 当前推进 | 样本清单、混淆项、FP/FN、置信度阈值、不可判定策略 | 当前推进区 |
| KR-O2-ROS2-State-Integration | O2 | 当前推进 | OpenCV evidence 接入电梯状态链，task record 有快照、失败原因和人工接管 | 当前推进区 |

本轮没有已完成 KR 可归档。旧 O2/O3 软件完成历史仍只作为 `docs/process/okr_progress_log.md` 中的历史记录，不作为当前完成度。

## 本轮核心抓手

1. **真实 operator workflow**：PC 不是展示面，而是现场低速控车、开雷达、建图定位、记录报告的入口。
2. **ROS2 map lifecycle**：建图、保存、加载、定位必须可被 PC/upper API 触发和回放。
3. **OpenCV first baseline**：电梯识别先走可解释的 ROI/rule baseline，不等模型训练完才开始接状态机。
4. **field-ready not_proven**：每条链路都允许 mock 先跑，但必须给真实切换入口、证据边界和人工接管。

## 需要做什么

| 优先级 | 工作 | Owner | 验收口径 |
| --- | --- | --- | --- |
| P0 | PC WASD + stop/operator report 复跑，并保留 HIL 证据入口 | full-stack-software-engineer + robot-hardware-engineer | browser/8787/manual/stop/status 同一 evidence ref；缺 HIL 时 not_proven |
| P0 | 雷达 start/stop API 与 PC 按钮 | full-stack-software-engineer + robot-software-engineer | start/stop 不触碰底盘 UART，`/scan` 状态和日志可回放 |
| P0 | SLAM map lifecycle 和 localization reset | robot-software-engineer | `/map`、map file、metadata、AMCL/TF/失败原因 |
| P0 | OpenCV 电梯 taxonomy + baseline + eval | robot-algorithm-engineer | 样本 manifest、ROI/rule 输出、混淆项、阈值、不确定策略 |
| P1 | Nav2 consumption 和 map quality metrics | robot-algorithm-engineer + robot-software-engineer | Nav2 lifecycle/path、地图覆盖/未知区/waypoint 可达性 |
| P1 | 底盘 HIL 和 LiDAR 长稳材料 | robot-hardware-engineer | safe preflight、low-speed pulse、stop/post-status、operator report |

## 风险、阻塞和需要补齐的证据链

- **风险：现场不可用**。处理：先推进 mock/stub/fixture 和 SSH/runbook 切换入口，最终结论标 `not_proven`，不把无法上车写成本轮 blocker 主线。
- **风险：接口耦合**。处理：Robot Software 主责 upper API/ROS2 glue，Full-stack 只走 HTTP API，不让 browser 直连 ROS graph。
- **风险：硬件事实漂移**。处理：Hardware 在真实集成前必须读 `docs/vendor/VENDOR_INDEX.md`，并在 tech-done/final 里写资料来源。
- **风险：电梯识别误判**。处理：Algorithm 必须输出不可判定策略和人工接管，不允许只给 happy path。
- **证据缺口：真实完成度**。处理：只有 HIL、ROS runtime、OpenCV eval、field material 能上调 O1/O2/O3/O7；mock 不涨分。

## 文档同步

- 本 PRD 同步 `OKR.md` 当前 Epic 指向。
- `docs/product/elevator_assisted_delivery.md` 补充本轮 OpenCV/field Epic 验收口径。
- L2 执行后必须更新本 sprint 的 `tech-done.md`，并按影响同步相关 `docs/` 文档。

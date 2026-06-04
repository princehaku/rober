# PRD: OKR Reset For Real Control, SLAM, Elevator

## 需求目标

把当前 OKR 重写为事实一致的产品推进口径：

1. PC WASD 必须从软件入口升级为真实控车 KR。
2. 雷达必须有一键开启/关闭 KR。
3. 建图、重置、保存、加载、定位必须进入 ROS2/SLAM/Nav2 KR。
4. 电梯进出必须进入 OpenCV 打标、识别、离线评估和 ROS2 状态机 KR。
5. 下一轮必须是跨 owner Epic，不再连续 Micro sprint 刷软件证明。

## 用户价值

普通用户不关心 `/cmd_vel`、SLAM Toolbox 或 `T=1001`。他们关心的是小车是否能真实移动、知道自己在哪、能跨楼层、异常时能停下并求助。PC operator 是研发和现场运营触点，必须支撑真实调试和证据采集，而不是只展示状态卡片。

## OKR 映射和方向判断

| Objective | 方向判断 | 本轮处理 |
| --- | --- | --- |
| O1：硬件协议可信底盘 | 继续并打回 | 从约 97% 打回约 95%，补 PC 手控 HIL、ACK/T=1001 同场、ROS feedback topic KR |
| O2：可送垃圾任务 + 电梯 assisted delivery | 调整 | 从历史归档 ~99% 打回约 72%，拉回当前推进区，新增 OpenCV 电梯识别 KR |
| O3：可验证导航、建图、定位与固定路线 | 调整 | 从历史归档 ~99% 打回约 73%，拉回当前推进区，新增 SLAM/map lifecycle、定位、Nav2 消费 KR |
| O5：云中转控制面产品化 | 继续 | 保持约 96%，但下一轮不作为最高优先级 |
| O6：云端核心后端 | 继续 | 保持约 96%，等待 O2/O3/O7 产生真实材料后再高质量推进 |
| O7：PC 端运营调试平台 | 继续并打回 | 从约 98.9% 打回约 88%，新增 WASD 现场控车、雷达一键开关、建图/定位控制 KR |

## KR 拆解

| KR | Objective | Owner | 验收口径 |
| --- | --- | --- | --- |
| KR-O7-PC-Manual-Field | O7/O1 | Full-stack + Hardware | PC W/S/A/D/Space/X 对真实小车完成低速前后左右/stop，采 manual/stop/post-status、operator report 和同一 evidence ref |
| KR-O1-Base-Manual-HIL | O1 | Hardware | 现场净空、人工急停和看护满足后完成底盘短 pulse、stop、日志和安全复位证据 |
| KR-O1/O7-ACK-T1001-Bridge | O1/O7 | Hardware + Full-stack | PC 请求、8787 manual、vendor `T=1`、stop、`T=130 -> T=1001`、日志和 operator report 同场对齐；不得把 `T=1001` 单独写成 robot ACK |
| KR-O7-Radar-OneClick | O7/O1 | Full-stack + Robot Software | PC 增加 `POST /api/radar/start|stop`，开启/关闭 LiDAR/ROS2 driver，状态和日志可回放，不触碰底盘 UART |
| KR-O3-SLAM-Map-Lifecycle | O3/O7 | Robot Software + Full-stack | 建图开启、重置、保存、加载、列出 artifact；至少有 `/map` once、map file、metadata 和 PC/upper API evidence |
| KR-O3-Localization-Reset | O3/O7 | Robot Software | PC/upper API 发布 `/initialpose`，AMCL lifecycle 正常，load map 后定位恢复并暴露失败原因 |
| KR-O3-Nav2-Consumption | O3 | Algorithm + Robot Software | Nav2 消费真实 `/scan` + map，形成 lifecycle、路径生成和短目标或 fixed-route 实跑证据 |
| KR-O2-OpenCV-Elevator-Taxonomy | O2 | Algorithm | 定义门线/轿厢/楼层 ROI、目标楼层确认、可驶出/不可驶出 taxonomy、样本要求和失败边界 |
| KR-O2-OpenCV-ROI-Rule-Baseline | O2 | Algorithm | 基于样本图片建立 OpenCV ROI + rule baseline，输出可解释识别结果 |
| KR-O2-Offline-Eval | O2 | Algorithm | 输出离线评估 artifact，包含样本清单、混淆项、阈值和不可判定策略 |
| KR-O2-ROS2-State-Integration | O2 | Robot Software + Algorithm | OpenCV 结果接入电梯状态链和 task record，保留关键快照、失败原因和人工接管 |

## 本轮核心抓手

本轮不是实现上述 KR，而是把 OKR 口径改正，避免后续继续围绕虚高百分比和 Micro sprint 做局部软件证明。下一轮 Epic 应直接围绕“PC 真实控车 + 雷达开关 + SLAM/定位 + 电梯 OpenCV”开工。

## 优先级

1. O2/O3：最低完成度，也是 trash delivery 北极星的真实阻塞。
2. O7：PC 是现场 operator 必须入口，缺真实控车、雷达开关和建图控制。
3. O1：所有真实移动和安全闭环的底座。
4. O5/O6：继续推进，但不应抢占下一轮真实能力 Epic。

## 风险

- 文档打回会降低 OKR 表观进度，但这是必要修正，避免 CEO 继续被虚高完成度误导。
- 下一轮 Epic 跨四个 owner，接口边界强耦合，必须先写完整 `tech-plan.md` 再派发。
- 真实现场/HIL 和电梯材料可能受硬件、场地、安全观察员限制；可用 mock/fixture 先开发，但不能涨完成度到真实闭环。

# Board Live Route Preflight and Capture Sprint Pre-start

## sprint_type: epic

## 触发背景

上一轮 `sprints/2026.06.09_13-00_board-live-slam-route` 在真实上位机接入环节失败于网络层：`ssh root@192.168.1.11 -p 37878` 因本机 LAN 网关与目标主机不可达而 `blocked`。本轮目标不是改功能，而是按 CEO 新一小时要求，完成现场链路验证的下一阶段准备与执行：优先重试真实上位机，优先产出 `map.yaml`、`route.csv`、keyframe、`rosbag` 或 replay 证据；若 SSH 不可达，则必须把同轮转为交付一个可复用的本地 preflight/capture 入口，避免再以“blocked”收口。

## 用户价值和北极星

本轮价值是让真实路径证据回到产线主链路。用户价值不变：从“软件侧宣称可送达”提升到“有可复盘的真实场地材料可驱动后续送达”。  
北极星仍保持不变：让普通用户把垃圾交付小车后，小车能按真实路线回程与投递闭环；本轮是该闭环的第一公里现场材料补齐。

## OKR 映射与方向判断

- 方向判断：**继续**。优先恢复 `O3` 的现场验证链路（`map.yaml/route.csv/fixed-route replay`），这是当前最低完成度能力在现场执行层面的“解锁项”。  
- 当前映射：本轮服务于 `OKR.md` 中的归档 Objective 3（可验证导航与固定路线）现场 lane，推动 `O2` 真实送达与 `O7` 路线回放的后续闭环。  
- 本轮不是 O6 O7 的面板/文档面收口任务，不符合“真实执行优先”的原则。

## 核心抓手

1. 在本机先执行预检：本机网络接口、网关路由、目标端口可达，确认是否具备真实上位机登录条件。
2. 成功可达时：执行 SSH 进入上位机并做最小 ROS2 环境与 topic 探测。
3. topic 符合条件时：执行 `learn.launch.py` 采集并生成本地 run 目录（避免覆盖），保存地图与路线文件。
4. 转换路线，执行 `fixed-route` dry-run/replay 验证工具链可消费。
5. 无法连线时：同一 sprint 内交付并可复用的本地 preflight/capture runbook（含 SSH、ROS2、topic、route 产物检查）作为下一次执行的标准入口。

## 本轮 Owner 与协作

- 主责 owner：`robot-algorithm-engineer`（SLAM/Nav2/路线采集/固定路线回放）。
- 硬件只读/执行配合：如需处理 `/scan`、`/odom`、`/tf`、`/map` 全缺失的硬件原因，`rober-hardware-engineer` 只读参与硬件事实核验（不修改硬件配置）；`robot-software-engineer` 与 `robot-algorithm-engineer` 仅在证据中记录并回发最小定位建议，不在本轮改代码。

## 风险边界与降级要求

- 真实上位机仍不可达时，不能把 sprint 直接 `blocked` 收口。必须产出本地可复用 runbook：
  - 一键预检 SSH/网关/端口
  - 一键探测 ROS2/关键 topic
  - 一键尝试 `learn.launch.py + route capture + replay` 模板
  - 明确记录失败原因和下一步网络修复动作
- topic 存在 ≠ 可建图；需检查 topic 频率/时间戳/数据输出稳定性。
- `map` 与 `route` 产物本轮是“现场可复盘”证据，不等于 delivery success。

## 与本轮允许改动范围

- 仅在本 sprint 的：
  - `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/pre_start.md`
  - `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/prd.md`
  - `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/tech-plan.md`

创建与更新其他文件。产品代码、测试代码、硬件配置、launch、`docs/product` 及其他 sprint 均不允许在本轮触达范围内变更。

# Pre Start - Board Live Evidence Capture

## sprint_type

`sprint_type: epic`

## 背景与启动原因

CEO 再次提供真实上位机入口：

```bash
ssh root@192.168.1.11 -p 37878
```

并明确要求：**设计好才能开始写功能点，功能点不完善不允许开始写代码**。本轮因此只完成 Epic sprint 的设计阶段，先把产品价值、功能点完整性门槛、SSH live 成功路径、SSH 不通降级产物、工程派工边界和验收命令写清楚，不写产品代码、不跑实现任务。

## 最近 blocker 扫描

已读取最近相关 sprint final：

- `sprints/2026.06.09_18-19_board-evidence-to-archive-consumer/final.md`：SSH 不可达不再阻断软件闭环，但仍未补齐真实 SSH / 真实 `map.yaml`、`route.csv`、keyframes、rosbag、replay JSONL。
- `sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md`：`field_route_evidence_preflight.py` 已能在 SSH 不可达时输出 `blocked_ssh_unreachable`，但未证明真实上位机 ROS2 topic、map、route、keyframe、rosbag 或 replay。
- `sprints/2026.06.09_14-15_board-live-route-preflight-and-capture/final.md`：`board_live_route_preflight.sh` 已交付，路线证据仍不可产出；风险明确为 `192.168.1.11:37878` 路由/ARP/端口层不可达。

判断：同一根因 `blocked_ssh_unreachable` 已连续被消费。CEO 本轮重新提供同一个真实上位机入口，等同于允许再次尝试 live lane，但本轮必须预设可执行 fallback 和 CEO 决策点，不能再以单纯 SSH blocker 收口。

## 用户价值和产品北极星

产品北极星：让普通用户把垃圾交给小车后，小车能沿固定路线完成投递，并且每次现场运行都有可复盘证据，而不是只留下开发机 mock 状态。

本轮用户价值不在“多一个工具页面”或“多一层 handoff”，而在把真实上位机入口转成以下任一可消费材料：

- `map.yaml`
- `route.csv`
- keyframe
- rosbag
- replay JSONL
- 或明确可执行的 fallback evidence packet，证明失败发生在 SSH/network/ROS2/topic/capture 的哪一层。

## OKR 映射和方向判断

方向判断：**继续，并临时优先 O3 现场验证 lane**。

- `OKR.md` 当前最高优先级写明：现场 O3 验证 lane 必须优先产出 `map.yaml`、`route.csv`、keyframe、rosbag 或 replay JSONL。
- O6/O7 已有多个 local/mock/software proof，但仍缺真实路线材料作为数据源。
- 若继续做 O6/O7 surface，会违反 CEO 的 Mission 执行偏置和 WIP 限制；本轮必须把工程注意力切回真实上位机/O3 lane。

## 本轮核心抓手

核心抓手是建立一个不可绕过的 live evidence capture gate：

1. SSH 成功时，直接进入上位机 preflight、ROS2 topic smoke、材料采集、manifest gate、replay/rosbag 最小验证。
2. SSH 不通时，仍必须产出标准 JSON fallback，并把失败根因分到 network、auth、host、port、ROS2 missing、topic missing 或 capture unsafe 之一。
3. 功能点不完整时禁止写新代码，只允许执行既有脚本、补充设计文档或升级 CEO 决策。

## 需要做什么

设计阶段完成后，下一阶段由对应 Engineer 执行：

- `robot-algorithm-engineer` 主责真实上位机 O3 live capture：SSH、ROS2、topic、learn.launch、map/route/keyframe、fixed-route replay、rosbag。
- `robot-software-engineer` 只在既有 CLI 无法生成 evidence packet 或 manifest gate 无法消费 live 产物时介入，且必须先确认功能点完整性门槛满足。
- `robot-hardware-engineer` 只在 live 阶段涉及 WAVE ROVER、Orange Pi、UART、串口、供电、传感器安装或硬件事实判断时介入，并必须引用 `docs/vendor/VENDOR_INDEX.md` 及其指向资料。
- `full-stack-software-engineer` 本轮不优先排，除非 live evidence 已产出且需要接入 O6/O7 consumer。

## 本轮不做

- 不写产品代码、测试代码、硬件配置、launch 参数或业务 docs。
- 不改 `OKR.md`。
- 不新增 O6/O7 surface、handoff、safe summary、owner response 或 review decision sprint。
- 不宣称 `delivery_success=true`、`safe_to_control=true` 或真实送达完成。

## 升级原因与 CEO 决策点

如果下一阶段仍出现 `blocked_ssh_unreachable`，必须把本轮视为第三次触碰同一根因。执行同学不能再只交付 blocker 文案，必须二选一：

1. 产出可执行 fallback：本机 preflight JSON、manifest gate local fixture、capture runbook、可复跑命令、失败层级和下一步 owner；
2. 升级 CEO 决策：确认上位机是否在线、是否在同一局域网、端口 `37878` 是否开放、是否需要更换 host/port/网络或改用现场人工导出材料。

## 需要创建或更新的 sprint 文档

本轮设计阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现阶段必须继续补齐：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

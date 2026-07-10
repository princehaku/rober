# O6/O7 Route Execution Credit Material Pre-Start

## Sprint 声明

- `sprint_type: epic`
- 启动时间：2026-07-10 12:20 CST
- Sprint 路径：`sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/`
- 主目标：O6 云端核心后端、O7 PC 端运营调试平台。
- 辅助目标：保持 O5/O1 blocker 不被连续消费。

## 上轮输入

- 最新 O5 约 `85%`，但最近 final 已要求下一轮必须拿到真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence。
- 最新 O1 约 `86%`，但真实 WAVE ROVER 材料仍显示 `T=1001` 的 `L=0,R=0`，缺同一 run 的 nonzero wheel feedback、motion command record、operator report 和 HIL acceptance。
- 最新 O6/O7 约 `87%`，上轮已完成 `same_task_route_execution_material_packet`，但 final 明确下一步必须接 live route execution、delivery record、operator confirmation 或 production cloud readback。

## 本轮选择

本轮不继续 O5 local/mock probe，也不继续 O1 software gate 包装。当前环境没有 production 云凭证、真实 4G/TLS、production DB/queue、真实手机/browser 验收，也没有新的 WAVE ROVER nonzero L/R 或 HIL 材料。

本轮转向 O6/O7 的原因：现有代码已经能把 same-task route execution materials 接入 Algorithm -> O6 -> O7，但 packet 本身还没有把“是否具备 live/field command evidence、delivery/operator record material、是否只是 support-only”作为一等字段暴露。补上这层 credit-aware material summary，可以让后续 Product/O7 直接区分可计主 OKR 的 mission artifact delta 与只读回归守护。

## Owner

- `robot-algorithm-engineer`：Algorithm producer，扩展 `same_task_route_execution_material_packet`。
- `robot-software-engineer`：O6 archive/readback，保留新 credit/material 字段并 fail-closed。
- `full-stack-software-engineer`：O7 consumer/UI，展示新字段但不解锁成功或控制。
- Product / main：拆解、派单、验收、收口文档和 OKR 判断。

## 风险边界

- 本轮仍是软件证据链，不证明真实 production cloud、真实 live Nav2、真实 robot motion、真实 delivery success、真实 HIL。
- 若没有 live/field command evidence 或 delivery/operator material，新字段必须输出 support-only/blocked，不允许虚增 OKR。
- `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` 必须继续固定。

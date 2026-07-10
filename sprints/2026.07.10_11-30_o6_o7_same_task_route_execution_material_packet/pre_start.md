# O6/O7 Same-Task Route Execution Material Packet Pre-Start

## Sprint 声明

- `sprint_type: epic`
- 计划时间：2026-07-10 11:30 CST
- Sprint 路径：`sprints/2026.07.10_11-30_o6_o7_same_task_route_execution_material_packet/`
- 当前阶段：planning only，本阶段只产出 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 目标 Objective：O6 云端核心后端、O7 PC 端运营调试平台。
- 方向判断：从当前最低或近最低但缺外部材料的 O5/O1，调整到当前环境可推进的 O6/O7 same-task route execution material packet。

## 最近两轮 blocker 与选择理由

### `2026.07.10_10-30_o1_wave_rover_nonzero_feedback_hil_gate`

- 收口结论：O1 已新增可复验的 `wave_rover_nonzero_feedback_gate` 软件 gate，O1 从约 85% 保守上调到约 86%。
- 主要 blocker：下一步必须使用同一真实 run 的 `feedback_T1001.log`、motion command、operator report 或外部运动观察材料、HIL acceptance record。
- 本轮不继续 O1 的原因：当前环境没有上述真实上车材料；继续做 mock/sample gate 会重复消费同一硬件证据 blocker，不能证明真实 WAVE ROVER nonzero L/R、轮向确认、safe-to-control 或 HIL pass。

### `2026.07.10_09-15_o6_o7_same_task_field_material_packet`

- 收口结论：O6/O7 已把同一 `task_id` 的 `map.yaml` optional、`route.csv`、keyframes、route bag / rosbag、replay JSONL 归一为 `same_task_field_material_packet` 并完成 Algorithm -> O6 -> O7 readback/UI 消费。
- 主要 blocker：该 packet 仍停留在 field material consumption；不证明真实 live Nav2 route execution、真实 robot motion、真实 delivery record、真实 operator confirmation、真实 delivery success 或 production cloud。
- 本轮继续 O6/O7 的理由：已有/准现场 same-task field materials 可以继续深化为 route execution material packet，把 route execution result、pose progress、replay timeline 与 field packet 绑定成可验证软件证据；这比再做 checklist/readback wrapper 更接近任务履约材料。

## 为什么 O5 本轮不继续

- 当前 OKR 快照中 O5 约 85%，是最低 Objective。
- 最近 O5 final 已明确：继续计 OKR 必须拿到真实 production cloud、production DB-queue external probe 或真实 live endpoint evidence。
- 当前环境没有真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic、真实手机/browser 验收或可核验凭证。
- `same_task_mission_artifact_credit_gate` 已固化规则：local/mock probe、readback-only、checklist-only、support-only 工作只能作为回归守护，不再计主 OKR 增量。
- 因此本轮不再用本地 O5 probe/readback 包装成进展。

## 为什么 O1 本轮不继续

- O1 当前约 86%，上一轮已把 software gate 补齐。
- 下一步有效增量必须是同一真实 run 的硬件材料：`feedback_T1001.log`、motion command、operator report、HIL acceptance record。
- 当前没有真实 WAVE ROVER nonzero L/R、轮向确认或 HIL 准入材料。
- 因此本轮不再增加 O1 software wrapper，避免第三次消费“缺真实硬件材料”这一 blocker。

## 本轮目标

把已有/准现场 same-task field materials 推进为 `same_task_route_execution_material_packet`：

1. Algorithm producer 从同一 `task_id` 的 field material packet、route execution result、route replay/pose progress、Nav2 goal/result、route bag / rosbag、replay JSONL 中生成安全摘要。
2. O6 archive/readback 能写入并通过 archive detail、field evidence、artifact bundle、consumer detail 与 `include=same_task_route_execution_material_packet` 读取。
3. O7 consumer/UI 消费同一个 O6 对象并展示 route execution material status、blocked reasons、next required evidence 与固定 false safety/control/delivery flags。

本轮计划必须坚持：这是 `software_proof_same_task_route_execution_material_packet_only`，不证明真实 delivery success、hardware safety、production cloud 或真实 robot motion。

## Owner 与下一阶段责任

- `robot-algorithm-engineer`：route execution material packet producer。
- `robot-software-engineer`：O6 archive/readback 合同与 fail-closed sanitization。
- `full-stack-software-engineer`：O7 consumer adapter/UI 展示与只读验收。
- `product-okr-owner`：本阶段 planning docs；实现完成后负责验收、OKR 判断和 closeout。

## 本阶段限制

- 允许改动：本 sprint 的 `pre_start.md`、`prd.md`、`tech-plan.md`。
- 禁止改动：代码、测试、`OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`。
- 本阶段不运行构建、单测或硬件命令，只运行计划文件存在性、关键词和 diff 空白检查。

# O6/O7 Same-Task Field Material Packet Pre-Start

## Sprint Type

sprint_type: epic

## 上轮未完成项与阻塞

- `sprints/2026.07.10_08-14_same_task_mission_artifact_credit_gate/final.md` 已把 `okr_credit_allowed=false` 的 support-only、probe-only、readback-only、checklist-only 工作固化为不再计主 OKR 增量。
- 上轮明确要求下一轮必须消费同一 `task_id` 下的真实或准现场 mission artifact delta，例如 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、delivery record 或 operator confirmation。
- O5/O6 真实 production cloud、production DB/queue、TLS/4G/OSS/CDN 凭证与环境当前不可用；O1 真实 WAVE ROVER 非零轮速反馈和 HIL 材料当前不可用。

## 本轮目标

本轮不继续包装本地 probe 或 checklist，而是把仓库已有的准现场 route material 消费成同一 `task_id` 的 `same_task_field_material_packet`：

- Algorithm 只读扫描 `route.csv`、keyframes、route bag / rosbag、replay JSONL 等材料，输出安全摘要和 artifact delta。
- O6 archive/readback 接收并回读该 packet，保留 artifact counts、短 hash、material flags 与 fail-closed 状态。
- O7 workstation 在同一 task detail 中展示该 packet，并把它接入 existing same-task material checklist，证明 operator 可直接看到真实/准现场材料是否已被消费。

## Owner

- Robot Algorithm Engineer：产出 `trashbot.same_task_field_material_packet.v1` manifest section 和单测。
- Robot Software Engineer：产出 O6 `trashbot.o6.same_task_field_material_packet.v1` archive/readback section 和单测。
- User Touchpoint Full-Stack Engineer：产出 O7 consumer/UI 展示和 test/build/lint 证据。
- Product / OKR Owner：最终收口 OKR 进度、证据边界和剩余风险。

## 验收口径

- 必须基于同一 `task_id` 消费准现场 route materials；不能只增加空 schema、fixture panel 或 wrapper。
- 所有输出必须继续固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`。
- 不回显绝对路径、raw payload、base64、credential、URL token 或大对象原文；只允许 basename、计数、短 hash、状态和安全 reason。
- 验证失败必须定位并修复后复验。

## 风险

- 本轮使用仓库内历史 field artifacts，证明准现场材料消费链路，不证明新的 live Nav2 execution、真实机器人运动、真实 delivery success 或 production cloud。
- 如果既有材料缺 `map.yaml`，本轮必须把缺口写成 blocked reason，同时仍消费可用的 `route.csv`、keyframes、rosbag/route bag、replay JSONL。

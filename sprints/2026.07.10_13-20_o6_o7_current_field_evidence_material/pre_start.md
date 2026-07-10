# O6/O7 Current Field Evidence Material Pre-start

## sprint_type

epic

## 背景

本轮自动化已读 `AGENTS.md`、`OKR.md`、最近 sprint final 和自动化记忆。当前活跃 Objective 进度为：O5 约 85%、O1 约 86%、O6/O7 约 88%。

最低 O5 的下一步必须是真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence；当前工作区没有可直接消费的真实外部材料。O1 下一步必须是真实同一 run 的 `feedback_T1001.log`、motion command、operator report 和 HIL acceptance；当前已知 wheel raw L/R 仍为 0/0，不能继续包装 software gate 作为主进度。

为避免连续消费 O5/O1 的同一外部 blocker，本轮切到可推进的 O6/O7：把 2026-06-11 真实上位机 current evidence smoke 中的 camera/radar/map/Nav2 no-motion path/manual gate 材料，接入同一 `task_id` 的 O6 archive/readback 与 O7 consumer/UI 材料链。

## 本轮目标

- 新增 `trashbot.current_field_evidence_material.v1` 安全摘要，消费真实上位机 current evidence bundle，但不暴露 URL、绝对路径、traceback、raw payload 或 token。
- O6 archive/readback 能把该摘要作为 additive section 保存、fail-closed、include 回读。
- O7 consumer/detail 能只读展示 current field evidence material，并保持所有控制、送达、安全 flag 为 false。

## owner

- Algorithm owner：`robot-algorithm-engineer`
- O6 backend owner：`robot-software-engineer`
- O7 consumer/UI owner：`full-stack-software-engineer`
- Product closeout owner：`product-okr-owner`

## 风险边界

- 本轮不证明 production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic。
- 本轮不证明真实 NavigateToPose、真实 robot motion、wheel raw L/R 非零、HIL pass、delivery record、operator confirmation 或 delivery success。
- 本轮只消费已有真实上位机 readback 材料，禁止执行新的运动命令。

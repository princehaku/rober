# Pre Start: Runtime Material Continue

## sprint_type

sprint_type: epic

## 背景

本轮接续 `sprints/2026.06.04_17-18_runtime-material-epic/`，目标不是继续写入口和 runbook，而是把 O2/O3/O7/O1 推向真实或受控材料。上一轮已经证明 SSH 到上位机、8787 operator report route、PC 同源代理和非运动 `T=130 -> T=1001` 有材料；同时也明确 O3 缺 application ROS2 nodes 和 fresh `/scan`/`/map`，O2 缺真实/受控电梯图片 manifest，O1 缺 HIL 安全前提。

本轮继续优先 O2/O3，兼顾 O7/O1/O8；不再转回 O5/O6 collector、URL/token 或云端 runbook blocker。

## 上轮未完成项

- O2：没有真实/受控电梯图片 manifest，OpenCV baseline 只能算 `software_guard`。
- O3：上位机有 ROS2 Humble 和 trashbot packages，但没有 fresh `/scan`、`/map`、`/amcl_pose`、TF 或 Nav2 lifecycle。
- O7：operator report route 已通，但还没有 PC operator UI/field-chain 对同一 evidence ref 的完整展示与现场 workflow。
- O1：只有非运动 feedback runtime material；没有现场看护、净空、急停、低速 pulse、stop/post-status 或 ROS feedback。

## Owner

- Robot Software Engineer：O3 non-motion ROS2 runtime 和上位机 command hook。
- Robot Algorithm Engineer：O2 真实/受控电梯图片 manifest 和 eval artifact。
- User Touchpoint Full-Stack Engineer：O7 PC operator workflow 展示与同源 evidence ref。
- Hardware Infra Engineer：O1 stop-first HIL 准入和非运动/安全证据。
- Product Manager / OKR Owner：O8 evidence type gate、blocker scan、OKR 收口。

## 验收边界

产品 Objective 只有 `robot_runtime_material`、`field_hil_material`、`production_live_material` 或 `user_acceptance_material` 才能涨分。`software_guard`、fixture、mock、入口、状态页、只读文档和 runbook 不作为 O1/O2/O3/O7 产品涨分依据。

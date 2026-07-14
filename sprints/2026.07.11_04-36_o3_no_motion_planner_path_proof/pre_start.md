# O3 No-Motion Planner Path Proof

## sprint_type

sprint_type: epic

## 背景

`OKR.md` 4.1 当前最低 Objective 仍是 O5，约 `~85%`。但上一轮 epic `sprints/2026.07.11_03-40_o5_external_evidence_or_field_execution_pivot/final.md` 已经 fail-closed：当前环境没有新的真实 external production evidence，也没有新的 same-task field execution material，继续做 O5 readiness、probe、checklist、readback 或 support packet 只会重复消费同一 blocker，并保持 `okr_credit_allowed=false`。

`sprints/2026.06.09_20-21_board-live-evidence-capture/tech-plan.md` 已经明确过现场 lane 的正确方向：当 O5/O6/O7 surface 无法带来新的 external artifact delta 时，要把优先级切回真实上位机/O3 lane，先争取 `map.yaml`、`route.csv`、keyframe、rosbag、replay JSONL、planner/path proof 这类上游材料。

当前 no-motion planner/path 链已有可复用入口和边界资料：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `docs/interfaces/real_material_readiness_board.md`
- `onboard/scripts/field_route_evidence_preflight.py`

这些资料共同指向一个保守结论：本轮可以尝试真实上位机 HTTP/SSH no-motion proof 或 fail-closed fallback，但不能承诺 delivery、HIL、真实路线执行成功，也不能把 planner proof 包装成 `safe_to_control`。

## 用户价值和北极星

用户真正需要的不是再多一个 readiness surface，而是回答一个更前置的问题：现场链路在完全不触发底盘运动的前提下，能否产出一份可复验的 planner/path 证据，证明后续 O6/O7 至少有新的真实材料可消费。北极星仍是“机器人可被验证地完成现场垃圾收集任务”，而这轮只负责补上其中最小、最安全的一段上游证据链。

## 本轮目标

创建一个可执行的 epic 计划，让 `robot-algorithm-engineer` 尝试以下二选一结果：

1. 通过真实上位机 `HTTP/SSH` 的 **no-motion** 路径，产出 planner readiness / path generation proof；
2. 若现场链路不可达或条件不足，则产出明确分层的 fail-closed fallback 证据，说明卡在 API、SSH、ROS2 setup、topic、map、planner 哪一层。

本轮目标只包括：

- no-motion planner/path proof
- `/api/nav2/proof/refresh` 或 SSH 分层失败证据
- 本地 mock fallback 模板/证据

本轮目标**不包括**：

- `delivery_success`
- `safe_to_control`
- `HIL pass`
- 真实固定路线执行成功
- Nav2 `NavigateToPose` 真正发车
- `/cmd_vel` 或 `/api/base/manual` 控制

## Owner

- 主责任 Engineer：`robot-algorithm-engineer`
- 条件咨询：`robot-software-engineer`（仅在 HTTP/SSH 入口、proof API、脚本接口事实需要澄清时）
- Product closeout：主节点汇总，不在本轮预先改 `OKR.md`

## 验收口径

- 必须形成 `pre_start.md`、`prd.md`、`tech-plan.md` 三份 epic 计划文档。
- `tech-plan.md` 必须包含 `OKR 最低优先级核对`，并明确说明 O5 虽最低但本轮不继续 support-only。
- 计划必须把真实上位机触达边界写清：**不会发送 `/cmd_vel`、不会调用 `/api/base/manual`、不会执行 Nav2 `NavigateToPose`、不会启动真实底盘运动**。
- 计划必须给出真实 SSH/HTTP 路径与 fail-closed fallback 路径，且两条路径都只允许产出 no-motion proof。

## 风险与阻塞

- `root@192.168.1.11` 的 SSH、ROS2 setup、topic、map server、planner proof API 任何一层都可能不可达，本轮很可能以 fail-closed fallback 收口。
- 真实上位机已有 runtime 若混入 managed Nav2 或底盘控制面，必须先在计划中约束“只读 proof / refresh，不执行运动控制”。
- 即使拿到 path generation proof，也只能证明 O3 上游材料新增，不能直接上调为 route execution success、delivery success 或 O5/O6/O7 当前生产完成。

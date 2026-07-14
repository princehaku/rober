# Pre-Start - O3 Daemon-Safe Graph Readback

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned start time: `2026-07-12 04:51 CST`
- Target lane: `O3/O1 no-motion runtime recovery`

## 用户价值和产品北极星

用户价值是把 true-board 现场调试从“知道 graph timeout 在哪里”推进到“拿到下一条可复验命令的结果”。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本轮仍处于进入 path generation、route execution 和 delivery 前的 no-motion runtime diagnostic，不是送达闭环。

## 上轮结果与本轮切入点

上一轮 `sprints/2026.07.12_03-52_o3_daemon_dds_graph_split/` 已把 blocker 从泛化 graph timeout 收窄到：

- `daemon_dds_split.primary_candidate=ros2_daemon_state_timeout`
- `daemon_dds_split.primary_candidate.reason=daemon_status_timed_out_and_daemon_reset_not_confirmed`
- `ros2_topic_list.boundary=ros2_topic_list_ok`
- `reset_skipped=true`
- `reset_skip_reason=ros2_node_list_help_not_ok`

上轮已经给出 `next_live_command` 等价动作。本轮切入点不是继续扩写 wrapper/readback，而是执行 daemon-safe stop/start + 8s graph readback，把结果固化为可复验 artifact，并在 graph/lifecycle/localization ready 前继续保持 no-motion。

## OKR 映射和方向判断

- O5：当前约 `85%`，本轮 `不直接针对`。原因是 O5 只剩真实 production/external evidence 缺口，support-only/readback/wrapper 不能继续计分。
- O1：当前约 `93%`，本轮 `继续 supporting lane`。目标是缩短 same-run path generation 前的 runtime blocker 链。
- O3：当前仍处于 no-motion supporting diagnostic，方向 `继续`。
- O6/O7：本轮 `暂停`，不新增 consumer/readback surface。
- 本轮 Product 判断：除非出现 same-run path generation、route execution、delivery/operator acceptance、HIL 或 production external evidence，否则 `不调整 OKR 百分比`、`不归档 KR`。

## 本轮核心抓手

1. 执行上一轮 artifact 的 `next_live_command` 等价 daemon-safe stop/start + 8s graph readback。
2. 把 daemon status、daemon stop/start、8s node/topic graph 结果写成可复验 artifact。
3. 明确 graph readback 后的下一跳是继续 lifecycle/localization gate，还是继续 daemon/DDS/runtime 根因分裂。

## Owner 与边界

- Product owner：`product-okr-owner`
- Implementation owner：`robot-software-engineer`
- 本轮为单 owner 闭环；Product 只负责计划、验收口径和后续收口判断。

## 文件范围

允许 Implementation owner 修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/tech-done.md`
- `sprints/2026.07.12_04-51_o3_daemon_safe_graph_readback/artifacts/`

本轮 Product 计划文档只更新当前 sprint 的：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

## No-Motion 红线

在 graph/lifecycle/localization ready 前，禁止：

- 发送 `/cmd_vel`
- 调用 `/api/base/manual`
- 尝试 NavigateToPose
- 打开 WAVE ROVER UART
- 把 `safe_to_control`、`robot_control_executed`、`route_execution_success`、`delivery_success`、`hil_pass` 写成 true

## Product Closeout 口径

本轮 closeout 只接受以下两类结果：

1. daemon-safe stop/start + 8s graph readback 产生新的 same-run blocked artifact，并把 blocker 进一步前移或排除；
2. graph/lifecycle/localization ready 出现新的可执行下一跳，但仍未跨越 no-motion。

如果没有 same-run path generation、route execution、delivery/operator acceptance、HIL 或 production external evidence，则：

- `OKR.md` 百分比不调整；
- 不归档任何 KR；
- 只记为 O3/O1 supporting diagnostic delta。

## 风险与阻塞

- true board 可能慢或不稳定，导致 8s graph readback 仍 timeout。
- daemon stop/start 可能成功但 graph 仍 blocked，说明 root cause 不止 daemon state。
- 即使 graph readback 成功，也不等于 localization ready，更不等于 path generation、route execution 或 HIL。

# PRD - O6/O7 Bounded Route Terminal Result Intake

## Product Goal

普通用户和运营同学需要在 PC/O7 侧看到同一个送达任务的 terminal-result material 是否已进入证据链。00:24 已经证明 O5 local/mock command/result/reconciliation 可以记录 `mock_route_execution_completed_not_live_delivery`，但该材料尚未进入 O6/O7 selected-task readback。

本 sprint 要把这个 terminal-result material 转成 O6/O7 可读的安全 receipt，帮助后续区分：

- 软件 mock terminal result 已记录；
- 真机 route execution / delivery / HIL 仍未发生；
- 下一步需要哪些 live evidence。

## User Value

- O6/O7 能围绕同一 `task_id` 呈现更完整的任务材料链。
- PC 触点可显示 terminal-result bridge 的状态、来源、proof boundary 和 next required evidence。
- Product 可避免把 mock route terminal result 误判成 delivery success。

## Scope

In scope:

- O6 `field_evidence` additive section / consumer detail readback。
- O7 local-loopback selected-task intake endpoint。
- O7 receipt、adapter fail-closed、PC 只读展示和 tests。
- 相关 `docs/interfaces/`、`docs/product/` 同步。

Out of scope:

- 真实公网云、生产 DB/queue、worker cutover、OSS/CDN、4G/SIM。
- `/cmd_vel`、`/api/base/manual`、NavigateToPose、WAVE ROVER UART。
- live route execution、delivery/operator acceptance、current live HIL 或 safe-to-control。
- 修改 00:24 source artifact 或历史 sprint artifact。

## Source Material

Primary source:

`sprints/2026.07.14_00-24_o5_bounded_route_terminal_result_bridge/artifacts/o5_bounded_route_terminal_result_bridge_summary.json`

Required accepted fields:

- `schema=trashbot.o5.bounded_route_terminal_result_bridge.v1`
- `proof_boundary=software_proof_o5_bounded_route_terminal_result_bridge_only`
- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `packet_id=packet_o3_28_pose_same_task_replay_7d57826142b0c79c`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `result_code=mock_route_execution_completed_not_live_delivery`
- `terminal_result_state=terminal_result_recorded`
- `reconciliation_state=terminal_result_recorded`
- `delivery_success=false`
- `route_execution_success=false`
- `safe_to_control=false`
- `hil_pass=false`
- `robot_control_executed=false`

## Acceptance

Accepted if:

- O6 readback contains `bounded_route_terminal_result_material`.
- O7 selected task can write/read the material through local loopback and return a safe receipt.
- O7 UI/API exposes the receipt or summary without raw paths, tokens, URLs, commands, serial/UART, ROS control strings or dangerous true fields.
- Unit/build/lint checks pass for touched owners.

Rejected if:

- Any receipt or readback implies real delivery, route execution, HIL, safe-to-control, production cloud or robot control.
- O7 can accept mismatched `task_id`, `packet_id`, `route_intent_id`, unsafe refs, raw local paths, URLs, credentials, `/cmd_vel`, `/api/base/manual`, NavigateToPose, UART/WAVE ROVER strings, or dangerous true fields.
- O6/O7 only write a receipt without selected-task readback.

## OKR Impact

This sprint targets O6/O7, not the lowest O5, because O5 currently requires external production evidence that is absent. The expected OKR result is likely support-only and flat unless the implementation uncovers a stronger same-task evidence class. Product closeout must not raise O5 or claim KR archival.

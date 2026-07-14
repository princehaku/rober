# Side-by-Side Check - O3 Same-Window Route Readiness Precheck

## Sprint Metadata

- sprint_type: epic
- sprint: `sprints/2026.07.14_13-38_o3_same_window_route_readiness_precheck/`
- Product acceptance time: 2026-07-14 13-38 Asia/Shanghai
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Product status: accepted with blocker boundary
- Acceptance status: `blocked_missing_same_window_live_evidence`
- Proof boundary: `software_proof_o3_o1_same_window_route_readiness_precheck_only`

## Product Acceptance 结论

本轮 Product acceptance 接受 `same_window_route_readiness_precheck`，但只接受为 O3/O1 same-window live route/HIL 前置 readiness precheck software proof。它证明既有 same-task route material 可以被机器验收并汇总为下一轮 live capture 缺口清单；它不证明 route execution、delivery、HIL、safe-to-control、O5 production/cloud evidence 或任何真实控制链路。

OKR 百分比不调整：O5 继续约 `85%`，O1 继续约 `94%`，O6/O7 继续约 `93%`。本轮 KR `不归档`。

## 对照验收

| 验收项 | Product 判断 | 证据 |
| --- | --- | --- |
| schema | 通过 | `trashbot.o3.same_window_route_readiness_precheck.v1` |
| status | 通过 | `blocked_missing_same_window_live_evidence` |
| proof boundary | 通过 | `software_proof_o3_o1_same_window_route_readiness_precheck_only` |
| same-task identity | 通过 | `packet_id`、`task_id`、`route_intent_id` 继承 28-pose route chain |
| counts | 通过 | `route_csv_row_count=28`、`segment_count=27` |
| missing live evidence | 通过 | operator approval、current live stop/HIL、same-window `/scan`、AMCL、dynamic `map_to_odom` TF、Nav2/controller result、delivery/operator acceptance 均列入 |
| control and success fields | 通过 | `route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`、`robot_control_executed=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`next_live_capture_allowed=false` |
| no-motion guard | 通过 | no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART |

## 拒绝声明

本轮明确拒绝把该 artifact 解释为 route execution、fixed-route movement、Nav2 controller/BT execution、delivery success、operator acceptance、current live HIL、safe-to-control、O5 production/cloud evidence、`/cmd_vel` publish、`/api/base/manual` call、NavigateToPose goal 或 WAVE ROVER UART command。

## Product 验证摘要

Product acceptance 复核了 implementation owner 的 `tech-done.md` 与生成 artifact：

- `py_compile` exit 0
- targeted unittest `Ran 5 tests ... OK`
- CLI artifact generation status ok
- `json.tool` exit 0
- implementation assertion `same_window_route_readiness_precheck_acceptance_ok`
- Product assertion `product_same_window_route_readiness_precheck_acceptance_ok`
- required rg anchors passed
- scoped `git diff --check` passed

## 剩余风险和下一轮建议

剩余风险仍是 live evidence 缺口，不是 software artifact 缺口。下一轮不要重复 readiness/precheck/wrapper/readback/export/offline smoke；只有 explicit operator approval 后，才由 `rober-hardware-engineer` 先采 current live stop/HIL，再由 `robot-algorithm-engineer` 在同一窗口采 `/scan`、`/amcl_pose`、dynamic `map_to_odom` TF、Nav2/controller result 和 delivery/operator acceptance。仍然保持 no /cmd_vel、no /api/base/manual、no NavigateToPose、no WAVE ROVER UART，直到安全准入和证据链同时满足。

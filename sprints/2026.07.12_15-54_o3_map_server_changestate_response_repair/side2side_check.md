# Side2Side Check - O3 Map Server ChangeState Response Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 16:24 CST`
- Product status: accepted as O3/O1 strict no-motion blocker narrowing only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_changestate_response_repair_only`

## 用户价值和北极星对照

产品北极星仍是普通手机用户一键发车送垃圾。这个 sprint 没有交付用户可见的新能力，但它继续解除 fixed-route/nav 的上游阻塞：`/map_server` 必须 lifecycle clean/active 后，才有资格恢复 `/map`、AMCL、dynamic TF、planner-only path，再进入 route execution 和 delivery evidence。

本轮工程没有修到 `/map_server active`，但 true-board artifact 把上一轮 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 继续收窄为 `map_server_changestate_response_false_before_map_io_completion`。因此产品验收只接受为 blocker narrowing，不接受为路线、导航、交付或生产能力。

## PRD / Tech Plan 对照

| 验收项 | 结果 | Product 判断 |
| --- | --- | --- |
| strict no-motion，不发布 `/cmd_vel`、不调用 `/api/base/manual`、不发 NavigateToPose、不打开 WAVE ROVER UART | true-board final artifact 固定 `safe_to_control=false`、`calls_base_manual=false`、`uses_base_uart=false`、`path_generation_attempted=false` | 通过 |
| 若成功，证明 `/map_server active` 或 lifecycle clean | `/map_server` 仍未 active / clean | 未通过，但不作为失败，因为有更窄 root cause |
| 若未成功，必须比上一轮 root cause 更窄 | 从 `map_server_changestate_response_failure_after_image_load_before_map_read_completed` 收窄到 `map_server_changestate_response_false_before_map_io_completion` / `lifecycle_manager_changestate_response_false_while_map_io_completed_later` | 通过 |
| true-board artifact 拉回并记录字段 | `artifacts/live_o10_map_server_changestate_response_repair.raw.json` 已拉回，`tech-done.md` 记录 return code 和关键字段 | 通过 |
| 不把支持性 proof 包装成 OKR 增量 | O5 继续约 `85%`，O1/O6/O7 继续约 `93%`，`不调整` 百分比，`不归档` KR | 通过 |

## Artifact 核对

主验收 artifact：

- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/artifacts/live_o10_map_server_changestate_response_repair.raw.json`
- `status=blocked_with_root_cause`
- `evidence_type=blocked_with_root_cause`
- `proof.root_causes[0].reason=map_server_changestate_response_false_before_map_io_completion`
- `proof.artifact_closeout.primary_root_cause.reason=map_server_changestate_response_false_before_map_io_completion`
- `proof.map_server_transition_callback_probe.canonical_classification=map_server_changestate_response_false_before_map_io_completion`
- `proof.map_server_transition_callback_probe.service_rpc_timing.changestate_response_false_before_map_io_completion=true`
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_or_rpc_error_observed_in_log=false`
- `proof.map_server_transition_callback_probe.service_rpc_timing.service_timeout_s=12.0`
- `map_io_timing.image_load_to_state_failure_ms=43.624`
- `map_io_timing.state_failure_to_map_read_completed_ms=93.266`
- `map_io_timing.configure_to_map_read_completed_ms=139.415`

configure ordering 已足够说明：lifecycle manager configure requested，map_server callback entered，YAML/image load started，state change failed，然后 map read completed。Product 采用 primary root cause 与 transition callback probe，不把 delay8 诊断 artifact 作为最终验收依据。

## Product Acceptance

Accepted as O3/O1 strict no-motion blocker narrowing only。

本轮不是：

- lifecycle clean
- path generation
- route execution
- delivery/operator acceptance
- current live HIL
- safe-to-control
- current live map navigation readiness
- production cloud evidence

## OKR 和 KR 判断

- O5：继续约 `85%`，没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1：继续约 `93%`，本轮是 O3 supporting no-motion map_server blocker narrowing，不是 current live HIL、safe-to-control、same-run path generation success 或 Nav2 route execution success。
- O6/O7：继续约 `93%`，没有新的 live route execution、delivery record、operator acceptance、真实关键帧可访问或 production readback。
- KR 处理：本轮 `不归档` KR；已归档 O3 仍只是临时现场验证 lane，不恢复为完成项。

## 下一轮建议

P0 继续由 `robot-software-engineer` 主责，检查 Nav2 map_server `on_configure` return false path、ChangeState response false while map IO still incomplete、executor/service future timing、map IO sync/async ordering。不要 hand off to Algorithm until `/map_server` lifecycle clean；Hardware only if LiDAR serial/runtime becomes primary and vendor docs are read。

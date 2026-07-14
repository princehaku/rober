# Side2Side Check - O3 Map Server Graph/Lifecycle Visibility

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Check time: `2026-07-12 10:29 CST`
- Product status: accepted as strict no-motion diagnostic delta
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`

## 用户价值和产品北极星

用户价值是把真实上位机 `/map_server` lifecycle retry 的 `Node not found` 从黑盒现象收敛成可执行的 graph/lifecycle failure 分类。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 只解除 same-run path generation 之前的诊断阻断，不交付路线执行、送达闭环、HIL 或生产云。

## OKR 映射和方向判断

- O5：`暂停`，继续约 `85%`。缺真实 production external evidence，继续 support-only/readback/wrapper 不计分。
- O3/O1：`继续`，本轮接受为 O3/O1 strict no-motion diagnostic delta。它把 `/map_server` blocker 收窄到 `map_server_node_absent` / `lifecycle_retry_node_not_found`，但没有 path 或 route proof。
- O6/O7：`不调整`，继续约 `93%`。没有新的 same-task route execution、delivery record、operator acceptance 或 production readback material。
- 方向判断：继续 O3/O1 no-motion；`不调整` 百分比；`不归档` KR。

## 验收对照

| 计划验收点 | 实际证据 | Product 判断 |
| --- | --- | --- |
| 新增 `/map_server` graph/lifecycle visibility schema | `proof.map_server_graph_lifecycle_visibility.schema=trashbot.o10.map_server_graph_lifecycle_visibility.v1` | Accepted |
| 保持 source/readiness 不回退 | live artifact readiness inputs: `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` | Accepted |
| 解释 `/map_server` retry `Node not found` | `canonical_classification=map_server_node_absent`、`failure_detail=lifecycle_retry_node_not_found`、retry `stderr="Node not found\n"` | Accepted |
| 保留 `/amcl active [3]` 事实 | `amcl_lifecycle_reference.current_active=true`，current retry stdout contains `active [3]`，previous accepted fact is `08-55 /amcl retry stdout contains active [3]` | Accepted, no evidence of AMCL regression based on actual fields |
| 保持 no-motion safety fields | `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false` | Accepted |
| Targeted validation | `py_compile` RC 0；targeted unittest `Ran 110 tests ... OK`；local dry-run RC 2 fail-closed；board SSH/SCP passed；live helper RC 2 wrote blocked artifact；scoped `git diff --check` passed | Accepted |

Product wording intentionally follows the live artifact fields. It does not treat a top-level AMCL regression flag as an accepted field; accepted `/amcl` evidence is `current_active=true`, retry stdout `active [3]`, and the previous accepted 08-55 fact.

## KR 拆解、更新或历史归档

本轮没有 KR 达到完成条件，不做历史归档。证据只新增到当前 O1/O3 supporting evidence chain：

- `map_server_graph_lifecycle_visibility` diagnostic delta accepted.
- `/map_server` next exact blocker is now node/process/lifecycle manager presence, not generic lifecycle timeout.
- No same-run path generation success.
- No route execution.
- No delivery/operator acceptance.
- No current live HIL.
- No safe-to-control proof.
- No production cloud evidence.

已完成 KR 历史记录位置：本轮无新增完成 KR，历史区不更新。证据来源为本 sprint `tech-done.md`、live artifact、this `side2side_check.md`、`final.md`、`OKR.md` Key Results note 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

核心抓手是让 Robot Software 把 `/map_server` lifecycle readback 从 retry `Node not found` 收敛成 `trashbot.o10.map_server_graph_lifecycle_visibility.v1` 的 canonical diagnostic field。结果有效，但只是 blocked-with-root-cause material。

## 需要做什么

下一轮 P0：恢复 `/map_server` node/process/lifecycle manager presence，让 lifecycle readback 能越过 `Node not found`。之后再由 Algorithm 消费 `/map`、TF 和 planner/path readiness。Hardware 当前不需要介入，除非后续证据证明 LiDAR serial/runtime/wiring facts。

## 优先级和验收口径

- P0：Robot Software 恢复 `/map_server` graph/lifecycle visibility，至少让 `ros2 lifecycle get /map_server` 不再是 `Node not found`。
- P1：lifecycle clean 后再进入 `/map` topic、dynamic `map->odom`、planner-only no-motion path readiness。
- 禁止项保持：NavigateToPose、`/cmd_vel`、`/api/base/manual`、WAVE ROVER UART、route execution、delivery success、HIL pass、safe-to-control 宣称。

## 对应责任 Engineer

- 下一轮主责：`robot-software-engineer`
- 后续 Algorithm 条件：`/map_server` lifecycle clean 后再处理 `/map`、TF、planner/path readiness。
- Hardware 条件：只有新证据证明 LiDAR serial/runtime/接线事实时才介入，并先读 `docs/vendor/VENDOR_INDEX.md`。
- Full-stack：不介入，禁止 O7 surface/handoff/intake 包装替代 mission material。

## 风险、阻塞和证据链缺口

- `/map_server` 仍 absent，当前 live map navigation readiness 不成立。
- `/amcl current_active=true` 只证明 lifecycle retry active，不证明 AMCL pose freshness、dynamic `map->odom` 或 localization ready。
- `RTPS_TRANSPORT_SHM` port lock warnings 仍只作为 stdout noise/risk 记录，未被证明为主因。
- O5 仍是最低约 `85%`，但没有 real production external evidence 前保持暂停。

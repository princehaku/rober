# O6/O7 Localization Path Material Readback Side-by-side Check

## 验收结论

本轮满足 PRD 和 tech-plan 的核心验收：`localization_path_material_readback` 已从 Algorithm producer 贯通到 O6 archive/readback/include，再到 O7 default include/UI summary。验收结论是通过，但仅限 `software_proof_localization_path_material_readback_only`。

## Side-by-side 对照

| 验收项 | 计划口径 | 实际结果 | 结论 |
| --- | --- | --- | --- |
| Algorithm producer | 新增 `trashbot.localization_path_material_readback.v1` 和安全输入入口 | 新增 `--localization-path-material-json`，输出 manifest 顶层与 `field_motion_evidence_packet.localization_path_material_readback` | 通过 |
| O6 archive/readback | 新增 `trashbot.o6.localization_path_material_readback.v1`、archive detail、field evidence、artifact bundle、consumer detail 和 include 回读 | O6 新增 sanitizer/summary/placeholder/include handler，返工后兼容 Algorithm 当前 status / TF alias / bridge alias，验证 `Ran 181 tests in 77.619s OK` | 通过 |
| O7 consumer/UI | 默认 include 并只读展示 localization/path material summary | O7 新增 `trashbot.pc_tools_workstation.o7_localization_path_material_readback.v1`，返工后兼容 O6 初版/返工版 status 与 TF/bridge alias，验证 `Tests 489 passed (489)`、build、lint 通过 | 通过 |
| Fail-closed | 缺字段、task mismatch、proof mismatch、危险 true、unsafe raw/path/token/url/base64/traceback 降级 | 三个 owner report 均记录 fail-closed 覆盖；O6/O7 集成返工已补上真实 payload 兼容缺口 | 通过 |
| Safety invariants | 不开启控制，不宣称路线执行或送达成功 | 全链路固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false`、`route_execution_success=false`、`nav2_route_execution_success=false`、`hil_pass=false` | 通过 |

## 用户价值核对

本轮让 latest same-run localization/path material 从 O1 单点 bridge，进入同一 `task_id` 的可查询、可展示、可 fail-closed 材料链。用户和运营能看到 localization 已出现但 path generation 仍失败，避免把 June 11 clean-baseline comparator 误读成当前 run 已经能出路径。

## OKR 核对

- O6：约 `91%` -> 约 `92%`，因为 archive/readback 新增 localization/path additive section，并修复了真实 producer/consumer 字段漂移。
- O7：约 `91%` -> 约 `92%`，因为 workstation 默认 include/UI summary 已消费该材料，并修复了 O6 实际 payload 兼容，且 `Tests 489 passed (489)`、build、lint 通过。
- O5：维持约 `85%`，本轮没有 production cloud / DB / queue / TLS / 4G / OSS / CDN / real browser evidence。
- O1：维持约 `90%`，本轮没有 current same-run HIL、motion command、operator/external observation、path generation success 或 route execution proof。

本轮不归档 KR。证据仍不足以把 O6/O7 的真实生产云、真实路线执行、delivery record、operator acceptance 或 delivery success 相关 KR 标为完成。

## Proof Boundary

`software_proof_localization_path_material_readback_only` 只证明 localization/path material 可被安全摘要化、归档、回读和展示。

明确不证明：

- production cloud、production DB/queue、TLS/4G、OSS/CDN live traffic 或 production worker/cutover。
- live Nav2 route execution、NavigateToPose/FollowPath/controller/BT 执行。
- robot motion、WAVE ROVER nonzero L/R、safe-to-control、HIL pass 或 hardware safety。
- delivery success、真实投放完成、operator acceptance、长期路线验收或用户现场验收。

## 下一步验收口径

下一轮如果继续 O6/O7，必须消费更强 same-task 材料：live route execution result、delivery record、真实/准现场 operator acceptance、production cloud readback 或 DB/queue readback。否则只能作为回归守护，不应继续提升主 OKR 百分比。

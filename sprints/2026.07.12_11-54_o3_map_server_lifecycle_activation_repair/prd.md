# PRD - O3 Map Server Lifecycle Activation Repair

## 背景

最新 accepted sprint `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/` 已把 `/map_server` failure 从 09-54 的 `map_server_node_absent` 推进为 lifecycle/configure 阶段失败：

- `managed_runtime_requested=true`
- `managed_runtime_started=true`
- `managed_runtime_boundary=explicit_opt_in_managed_localization_runtime_no_motion`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- runtime log 证明 lifecycle manager starts、map_server `Configuring`、`trashbot_map.yaml` 和 `trashbot_map.pgm` load，随后 `Failed to change state for node: map_server`
- `path_generation_attempted=false`、`path_generated=false`
- safety fields 全部 false

这说明上一轮已经越过 node absent，但还没有越过 lifecycle manager `Failed to change state for node: map_server`。本轮需求是修复或继续收窄 `/map_server` configure/activate failure。

## 用户价值和产品北极星

目标用户最终只需要手机一键发车、机器人沿固定路线送垃圾。当前阻塞在真实上位机 Nav2 map server lifecycle transition 不 clean，导致 `/map`、AMCL pose、TF、planner/path readiness 无法进入可验证状态。

本轮用户价值是补齐"地图服务能够 clean configure/activate，或明确失败原因"这个前置能力。它不是用户可见功能，但直接解锁下一步现场路径 proof。

## OKR 映射和方向判断

- O5：约 `85%`，仍是最低 Objective，但缺真实 external production evidence。方向为 `暂停` support-only；本轮不做 O5。
- O3/O1：方向为 `继续`。本轮聚焦 strict no-motion `/map_server` lifecycle activation repair，服务 O1 current same-run path generation 缺口前置条件。
- O6/O7：方向为 `暂停等待材料`。没有新的 route execution、delivery/operator 或 production readback。
- 本轮不调整 OKR 百分比，不归档 KR。

## Problem Statement

当前 true-board proof 能证明 managed runtime 已显式请求并启动，map server 进入 `Configuring` 并读取 `trashbot_map.yaml` / `trashbot_map.pgm`，但 lifecycle manager 仍报告 `Failed to change state for node: map_server`。如果继续调查 `/scan`、TF 或 planner，会重复消费下游 blocked evidence。

需要 Robot Software 在 strict no-motion 条件下定位并修复 `/map_server` configure/activate 失败原因，或输出比 `lifecycle_manager_failed_to_change_state_for_map_server` 更窄的 configure failure classification。

## 非目标

- 不执行 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不做 O5 support-only readiness/surface/review/handoff/intake。
- 不把 `/scan`、AMCL、TF 或 planner timeout 作为本轮 primary success。
- 不改硬件配置、不假设串口/波特率/接线事实。

## 范围

本轮范围：

- strict no-motion managed runtime map_server lifecycle activation repair/proof。
- map_server stderr/stdout、lifecycle_manager log、process exit、lifecycle readback 采集。
- map yaml/pgm 可读性、yaml 字段、image path、frame_id、map server 参数检查。
- launch 参数、lifecycle manager managed node list、node name/namespace、lifecycle 管辖关系检查。
- local fail-closed dry-run 和 true-board artifact。
- 实施文档同步到 navigation docs 和 sprint `tech-done.md`。

范围外：

- route execution、delivery/operator acceptance、HIL、safe-to-control。
- O7 UI/API、O6 archive、O5 production cloud。
- WAVE ROVER、ESP32、UART、LiDAR serial wiring 或硬件配置。

## KR 拆解、更新或历史归档

本轮不完成 KR。目标证据只用于 O3/O1 supporting chain：

- `/map_server` lifecycle transition clean，或更窄的 configure/activate blocker。
- `map_server_lifecycle_not_active_after_recovery` 不再只落到 `lifecycle_manager_failed_to_change_state_for_map_server` 这句泛化结果。
- artifact 记录 map_server stdout/stderr、lifecycle_manager log、map yaml/pgm proof、frame_id/parameter checks、process exit。
- strict no-motion 字段全部保持 false。

已完成 KR 历史记录位置：无新增。本轮完成后只在 sprint closeout 和必要的 OKR note 中记录 supporting evidence。

## 本轮核心抓手

核心抓手是把 10-54 artifact 的下一步 `inspect_map_server_configure_error_and_map_yaml_runtime_log` 做成可验收 implementation：

- 读取和收束 map_server configure/activate stderr/stdout。
- 明确 `trashbot_map.yaml` 与 `trashbot_map.pgm` 的可读性、字段、相对 image path 和 frame_id/参数。
- 明确 lifecycle manager 是否管辖正确 node name/namespace。
- 明确 map_server process 是否退出，或 lifecycle service 是否超时/返回错误。
- 在 artifact 中给出 canonical classification 和 next action。

Robot Software 可在实施中选择修复或只读诊断路径，但必须在 `tech-done.md` 记录选择理由、命令、返回码和 artifact 字段。

## 验收口径

P0：

- true-board strict no-motion artifact 证明 `/map_server` lifecycle transition clean，或 recovery/activation 失败点比 `lifecycle_manager_failed_to_change_state_for_map_server` 更窄且可执行下一步修复。
- artifact 明确包含 map_server stderr/stdout、lifecycle_manager log、map yaml/pgm readback、frame_id/parameter/launch lifecycle 管辖、process exit 或 timeout 信息。
- safety fields false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

P1：

- local strict no-motion dry-run fail-closed，不能产生 motion/control success。
- targeted unittest 覆盖 lifecycle clean、configure failure、yaml/pgm read failure、frame_id/parameter issue、lifecycle manager mismatch、process exit 和 safety invariants。
- navigation docs 同步说明本轮 proof boundary。

不接受：

- 只把 timeout 或 `Failed to change state for node: map_server` 文案换名。
- 仍输出完全相同 `lifecycle_manager_failed_to_change_state_for_map_server`，且没有更窄 stderr/stdout/process/map yaml classification。
- 把 `/scan`、AMCL、TF 或 planner timeout 当成本轮 primary result。
- 任何运动、底盘控制、WAVE ROVER UART 或 hardware config 改动。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- Product 验收：`product-okr-owner`
- Algorithm：等待 `/map_server` lifecycle clean 后接 `/map`、AMCL pose、dynamic `map->odom`、planner-only path gate。
- Hardware：仅在实施需要硬件事实时介入，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 同一 Blocker 红线判断

- 09-54：`map_server_node_absent`。
- 10-54：`map_server_lifecycle_not_active_after_recovery` / `lifecycle_manager_failed_to_change_state_for_map_server`。
- 本轮允许继续一次，因为 blocker 已从 node absent 进入 lifecycle/configure failure。
- 若本轮仍停在完全相同 `lifecycle_manager_failed_to_change_state_for_map_server` 且没有更窄错误，下一轮必须 CEO 升级或切 Objective。

## 风险和证据链缺口

- 即使 `/map_server` active，也仍未证明 `/map` topic sample、AMCL pose freshness、dynamic `map->odom`、path generation、route execution 或 delivery。
- true-board access 失败会阻断本轮主要验收；本地 proof 只能作为 fail-closed software check。
- 如果需要硬件事实，必须停止本 sprint 的软件假设并按 AGENTS.md 读取 vendor 资料；本轮默认不触碰硬件配置。

## Sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实施和验收阶段还需要：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

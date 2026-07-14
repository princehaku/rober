# Pre Start - O3 Map Server Lifecycle Activation Repair

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Start time: `2026-07-12 11:54 CST`
- Direction: continue O3/O1 strict no-motion现场链路
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_map_server_lifecycle_activation_repair_only`

## 用户价值和产品北极星

用户价值是让真实上位机在不运动、不控制底盘的前提下，把 `/map_server` 从"已启动但 lifecycle manager 无法完成 state change"推进到 clean lifecycle transition，或产出比 `lifecycle_manager_failed_to_change_state_for_map_server` 更窄的 configure/activate 错误。只有 `/map_server` lifecycle clean，后续 `/map` sample、AMCL pose、dynamic `map->odom` 和 planner-only path gate 才有继续验证的基础。

产品北极星仍是普通手机用户一键发车完成固定路线送垃圾。本 sprint 不做 NavigateToPose、不发布 `/cmd_vel`、不调用 `/api/base/manual`、不打开 WAVE ROVER UART、不改硬件配置；它只修复送达链路前置的 Nav2 map server lifecycle activation blocker。

## 上轮事实和进入条件

最新 accepted sprint 是 `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/`。其 `final.md` 和 `tech-done.md` 已确认：

- `status=blocked_with_root_cause`
- `managed_runtime_requested=true`
- `managed_runtime_started=true`
- `managed_runtime_boundary=explicit_opt_in_managed_localization_runtime_no_motion`
- `managed_runtime_cleanup_ok=true`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- runtime log 证明 lifecycle manager starts、map_server enters `Configuring`、`trashbot_map.yaml` 和 `trashbot_map.pgm` load，随后 `Failed to change state for node: map_server`
- `path_generation_attempted=false`、`path_generated=false`
- no-motion 字段继续为 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`

09-54 accepted sprint `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/` 的 blocker 是 `map_server_node_absent` / `lifecycle_retry_node_not_found`。10-54 已越过 node absent，进入 `map_server_lifecycle_not_active_after_recovery` / `lifecycle_manager_failed_to_change_state_for_map_server`。因此本轮允许继续一次，但必须以修复或收窄 configure/activate 失败为目标。

## OKR 映射和方向判断

- O5：约 `85%`，当前最低 Objective，但只能靠真实 production external evidence 计分。本轮 `暂停` O5 support-only；不得用 readiness packet、surface、review、handoff 或 intake 继续包装进度。
- O3/O1：`继续` strict no-motion 现场链路。目标是让 `/map_server` lifecycle transition clean，或输出更窄 configure failure classification，服务 O1 current same-run path generation 缺口的前置条件。
- O6/O7：约 `93%`，本轮不触碰。只有 route execution、delivery/operator、production readback 等新材料出现才恢复消费链。
- 方向判断：`继续` O3/O1，不调整 OKR 百分比，不归档 KR。

## KR 拆解、更新或历史归档

本轮目标只进入 O3/O1 supporting chain，不归档任何 KR。

预期新增证据：

- `/map_server` lifecycle transition clean，或更窄的 configure/activate failure classification。
- `map_server` stderr/stdout、lifecycle_manager log、process exit、map yaml/pgm 可读性、frame_id、yaml 字段、参数/launch lifecycle 管辖事实。
- lifecycle manager `Failed to change state for node: map_server` 被越过，或被拆成可执行的下一级原因。
- 所有 motion/control/delivery/HIL 字段保持 false。

已完成 KR 的历史记录位置：无新增完成 KR，本轮不移动当前 KR 到历史区。证据来源将是本 sprint 的 `tech-done.md`、live artifact、`side2side_check.md`、`final.md`，必要时后续再同步 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

Robot Software 需要单线闭环检查 `map_server` configure/activate 失败原因：

1. 采集 map_server stderr/stdout、lifecycle_manager log、managed runtime command log 和 process exit。
2. 验证 `trashbot_map.yaml` 与 `trashbot_map.pgm` 可读性、image path、resolution、origin、occupied/free thresholds、mode、frame_id 或等价 map server 参数。
3. 核对 launch 参数、lifecycle manager managed node list、node name/namespace、map yaml path policy 和 map server lifecycle 管辖关系。
4. 优先让 artifact 越过 lifecycle manager `Failed to change state for node: map_server`；若无法越过，必须输出更窄 configure failure classification，而不是重复 10-54 的同一句 `lifecycle_manager_failed_to_change_state_for_map_server`。

## 需要做什么

- 创建或更新 Robot Software 实施所需的 helper、test、navigation docs 和本 sprint artifact。
- 运行本地 py_compile、targeted unittest、local strict no-motion dry-run、true-board strict no-motion run/pull artifact、scoped `git diff --check`。
- 实施后补齐本 sprint `tech-done.md`；Product 验收后再创建 `side2side_check.md` 和 `final.md`。

## 优先级和验收口径

P0 验收：

- true-board artifact 显示 `/map_server` lifecycle transition clean，或不再停留在完全相同 `lifecycle_manager_failed_to_change_state_for_map_server`。
- 若仍 blocked，必须有更窄 classification，例如 map yaml image load/parse failure、frame_id/parameter issue、lifecycle manager managed-node mismatch、node namespace mismatch、process exit、map_server exception、resource/path permission 或 activate callback failure。
- strict no-motion 安全字段保持 false。
- 不执行 NavigateToPose，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。

P1 验收：

- local dry-run 在 macOS 无 ROS2 runtime 时 fail-closed。
- targeted unittest 覆盖 lifecycle clean、configure failure、map yaml/pgm unreadable、lifecycle manager mismatch、process exit、safety fields false。
- docs/navigation 说明 proof boundary 和下一步 Algorithm 可消费条件。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- Algorithm：本轮不主责，等 `/map_server` lifecycle transition clean 后再恢复 `/map`、AMCL pose、dynamic `map->odom`、planner-only path gate。
- Hardware：默认不介入。本轮不触碰 WAVE ROVER、UART、串口、接线、波特率或硬件配置。
- Full-stack：不介入。

## 同一 Blocker 红线判断

- 09-54 blocker：`map_server_node_absent` / `lifecycle_retry_node_not_found`。
- 10-54 blocker：`map_server_lifecycle_not_active_after_recovery` / `lifecycle_manager_failed_to_change_state_for_map_server`。
- 本轮允许继续一次，因为 10-54 已从 node absent 推进到 map_server 已配置并读取 map yaml/pgm 后的 lifecycle transition failure。
- 如果本轮仍停在完全相同 `lifecycle_manager_failed_to_change_state_for_map_server`，且没有更窄错误、stderr/stdout、process exit 或 map yaml/pgm/parameter classification，下一轮必须 CEO 升级或切 Objective，不得继续消费同一 blocker。

## 风险、阻塞和需要补齐的证据链

- `/map_server` lifecycle clean 不等于 localization ready、dynamic `map->odom`、path generation success、route execution、delivery success 或 HIL。
- ROS2 daemon/node-list timeout、FastDDS warning、LiDAR 串口读空可以保留为 secondary context，但不得替代本轮 primary map_server lifecycle root cause。
- 如实现过程中需要硬件串口、接线、波特率、JSON 指令、速度映射或 feedback 协议事实，Robot Software 必须停止相关假设并派 Hardware 读取 `docs/vendor/VENDOR_INDEX.md` 及其指向资料后再继续；本轮默认不触碰硬件配置。
- 真实板 SSH 可能不可达；不可达只能作为 blocked evidence，不能把本地 mock 当作 true-board proof。

## 需要创建或更新的 Sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实施阶段必须由 `robot-software-engineer` 创建或更新：

- `tech-done.md`

验收阶段由 Product 更新：

- `side2side_check.md`
- `final.md`

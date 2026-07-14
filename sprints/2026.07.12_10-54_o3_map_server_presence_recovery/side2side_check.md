# Side2Side Check - O3 Map Server Presence Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Closeout time: `2026-07-12 12:07 CST`
- Product status: accepted as O3/O1 strict no-motion presence recovery delta only
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_presence_recovery_only`

## 用户价值和产品北极星

用户价值是把真实上位机 `/map_server` 从 09-54 的 read-only `Node not found` blocker 推进到显式 managed runtime recovery proof。产品北极星仍是普通手机用户一键发车完成固定路线送垃圾；本 sprint 只是恢复后续 `/map`、TF 和 planner/path readiness 的前置链路，不是用户可见送达能力。

## OKR 映射和方向判断

- O5：继续约 `85%`，方向为 `暂停 support-only`。本轮没有真实 HTTPS/TLS、公网入口、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 或 external production evidence。
- O1/O3：`继续`。本轮接受为 O3/O1 strict no-motion presence recovery delta，说明 `/map_server` 已越过 read-only absent 诊断，进入 lifecycle/configure failure 的更窄 blocker。
- O6/O7：继续约 `93%`，方向为 `暂停等待材料`。本轮没有 route execution、delivery record、operator acceptance 或 production readback material。
- Product 结论：`不调整` OKR 百分比，`不归档` KR。

## KR 拆解、更新或历史归档

本轮不完成任何 KR，不移动任何 KR 到历史区。新增证据只进入 O3/O1 supporting chain：

- `managed_runtime_requested=true`
- `managed_runtime_started=true`
- `managed_runtime_boundary=explicit_opt_in_managed_localization_runtime_no_motion`
- `managed_runtime_cleanup_ok=true`
- `proof.map_server_presence_recovery.canonical_classification=map_server_lifecycle_not_active_after_recovery`
- `failure_detail=lifecycle_manager_failed_to_change_state_for_map_server`
- `root_cause_filtering.applied=true`

已完成 KR 的历史记录位置：无新增。证据来源是本 sprint `tech-done.md`、live artifact、本 `side2side_check.md`、`final.md`、`OKR.md` closeout note 和 `docs/process/okr_progress_log.md`。

## Side-by-side 验收对照

| 验收项 | 计划口径 | Product 验收 |
|---|---|---|
| `/map_server` recovery | 越过 `Node not found`，或给出更窄 blocker | 通过。live artifact 进入 `map_server_lifecycle_not_active_after_recovery`，detail 为 `lifecycle_manager_failed_to_change_state_for_map_server`。 |
| managed runtime | 必须显式记录 recovery path | 通过。`managed_runtime_requested=true`、`managed_runtime_started=true`，boundary 为 `explicit_opt_in_managed_localization_runtime_no_motion`。 |
| root cause 归因 | 不允许把 package missing 或 graph timeout 噪声当顶层 blocker | 通过。Robot Software 初版 root-cause 误导已返工，当前顶层 `proof.root_causes` 只保留 `Nav2 map_server presence recovery / map_server_lifecycle_not_active_after_recovery / lifecycle_manager_failed_to_change_state_for_map_server`。 |
| runtime log | 需要证明恢复路径确实启动并读 map | 通过。runtime log 显示 lifecycle manager 启动、`Configuring map_server`、加载 `trashbot_map.yaml` 与 `trashbot_map.pgm`，随后 `Failed to change state for node: map_server`。 |
| no-motion 安全 | 不发布命令、不控制底盘、不打开 UART | 通过。`path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。 |
| OKR credit | supporting evidence only | 通过。本轮不是 same-run path generation、route execution、delivery/operator acceptance、HIL、safe-to-control、current live map navigation readiness 或 production cloud evidence，因此 `不调整` 百分比，`不归档` KR。 |

## 本轮核心抓手

核心抓手已经从 09-54 的 read-only existing graph 诊断，推进为 explicit opt-in managed localization runtime no-motion proof。它证明 map yaml/map image 可读，map_server 进入 configure 流程，但 lifecycle manager 不能把 map_server 切到目标状态。

## 需要做什么

下一步由 `robot-software-engineer` 主责修复 `map_server` configure/lifecycle transition failure，先检查 map_server configure error、lifecycle manager 管辖节点、duplicate process / FastDDS port lock、map yaml/image runtime 兼容性和 launch 参数。`robot-algorithm-engineer` 等 lifecycle clean 后再接 `/map`、AMCL pose、dynamic `map->odom` 和 planner-only path gate。

## 优先级和验收口径

P0：修到 `/map_server` lifecycle transition clean 或输出比 `lifecycle_manager_failed_to_change_state_for_map_server` 更窄的 configure error，并继续保持 no-motion 字段 false。

P1：只有 `/map_server` active 且 `/map` sample、AMCL pose、dynamic `map->odom` 与 planner-only path gate 出现后，才恢复 Algorithm 消费链。任何 path/route/delivery/HIL 计分必须另开 sprint 并提供当前 run 证据。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- `robot-algorithm-engineer`：等待 lifecycle clean 后消费 `/map`、TF 和 planner/path readiness。
- `rober-hardware-engineer`：本轮不介入；只有后续证据把 LiDAR `/dev/ttyACM0` 读空或多进程占用确定为下一 blocker，才先读 `docs/vendor/VENDOR_INDEX.md` 后介入。
- `full-stack-software-engineer`：不介入；本轮没有 O5/O6/O7 API/UI/production cloud 变化。

## 风险、阻塞和需要补齐的证据链

- 当前 blocker：`map_server_lifecycle_not_active_after_recovery` / `lifecycle_manager_failed_to_change_state_for_map_server`。
- package missing、graph timeout、ROS2 daemon timeout 等噪声只在 `root_cause_filtering.suppressed_root_causes` 中保留，不作为本轮顶层 root cause。
- 仍缺 same-run path generation success、route execution、delivery/operator acceptance、current live HIL、safe-to-control、current live map navigation readiness、production cloud evidence。
- LiDAR `SerialException` 是后续可能风险，不是本轮 primary blocker；若下一轮要消费 `/scan`，需要单独拆分。

## 需要创建或更新的 Sprint 文档

本 Product acceptance closeout 创建或更新：

- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/side2side_check.md`
- `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

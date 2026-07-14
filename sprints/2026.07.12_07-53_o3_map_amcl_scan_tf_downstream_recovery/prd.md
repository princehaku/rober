# PRD - O3 Map/AMCL/Scan/TF Downstream Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Product status: plan ready
- Proof boundary: `software_proof_o3_o1_strict_no_motion_downstream_recovery_only`

## 用户价值和产品北极星

用户价值：让真实上位机在不运动、不控制底盘的前提下，恢复固定路线送垃圾所需的 map、AMCL、scan、TF 下游诊断链。用户最终关心的是手机一键发车后能稳定沿固定路线送垃圾；当前 sprint 的价值是把“为什么还不能生成路径”从泛化 runtime blocker 收敛到可修复的 ROS2/Nav2 事实。

产品北极星：普通手机用户交付垃圾后，机器人沿固定路线送达垃圾站点并可复盘。此 sprint 不交付手机体验、不交付送达、不交付运动能力；只为 current-run path generation 和后续 route execution 准备可验证前置条件。

## 背景和问题

上一轮 `06-54` 已证明：

- `board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`

因此本轮不得再停留在 source/path mismatch、`ros2 --help` 或 O5 support-only readiness。当前真实 blocker 是 downstream recovery：

- `map_lifecycle_preflight_map_server_and_amcl_inactive`
- `amcl_lifecycle_not_active`
- `/scan_no_publisher`
- `/map_once_not_observed`
- `/tf_topic_missing`

这些 blocker 仍导致 `path_generation_attempted=false`、`path_generated=false`，所以不能声明 route execution、delivery success、safe-to-control 或 HIL。

## OKR 映射和方向判断

- O5：当前约 `85%`，但本轮 `暂停`，因为缺真实 external production evidence。继续产出 O5 support-only readiness/readback 会重复消费同一 blocker。
- O3/O1：本轮 `继续` O3/O1 strict no-motion runtime lane。它直接服务 O1 缺口里的 current same-run path generation success 和 Nav2 route execution success，也服务 Mission Objective 0 的 current-run delivery evidence chain。
- O6/O7：本轮 `不调整`，除非后续 Robot Software 产出可被消费的新 same-task route/path/delivery material；否则不安排 Full-stack surface 或 readback 包装。
- KR 拆解：本轮只拆到 downstream proof gate，不把任何 KR 标为完成。
- 历史归档：本轮无已完成 KR，不更新历史区。

方向判断：`继续` O3/O1 no-motion downstream recovery；`暂停` O5 support-only；`不归档` KR；`不调整` OKR 百分比，除非后续 artifact 出现更强 current-run mission evidence。

## 需求

### P0 - Strict no-motion downstream recovery

Robot Software 必须让 helper 对 `map_server`、`amcl`、`/scan`、`/map`、`/tf`、`/tf_static` 形成可读、可回归的分层 artifact。artifact 至少要能回答：

- `map_lifecycle_preflight_map_server_and_amcl_inactive` 是否仍成立。
- `amcl_lifecycle_not_active` 是否仍成立，是否有 lifecycle stdout/stderr/timeout。
- `/scan_no_publisher` 是否是真无 publisher、graph 不可见、topic 不存在、QoS/sample window 问题，还是 helper 预算问题。
- `/map_once_not_observed` 是 topic 缺失、publisher 缺失、sample timeout，还是 map server lifecycle 未 active。
- `/tf_topic_missing` 是 `/tf` topic 缺失、publisher 缺失、sample timeout，还是 dynamic `map->odom` source 缺失。

### P0 - Safety invariants

所有验收必须保持 strict no-motion：

- 禁止 NavigateToPose。
- 禁止 `/cmd_vel`。
- 禁止 `/api/base/manual`。
- 禁止 WAVE ROVER UART。
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

若 planner-only no-motion path gate 被触发，artifact 必须清楚证明它只调用 ComputePathToPose 类路径计算，不发送 goal、不执行 route、不控制底盘；此时只允许 `path_generation_attempted=true`，不允许任何 motion 或 delivery 字段变为 true。

### P0 - Evidence artifact

若 true board 可达，必须产出新的 raw artifact 到本 sprint artifacts 目录，例如：

- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/artifacts/live_o10_map_amcl_scan_tf_downstream_recovery.raw.json`

若 true board 不可达，Robot Software 必须记录 SSH/SCP/timeout 失败定位，并保留 local fail-closed artifact。不可达不能被写成 mission progress。

### P1 - Regression coverage

单测必须覆盖：

- `board_source_preflight_ready` 不被回退成 source/path mismatch。
- `lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 后进入 downstream probes。
- `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing` 被结构化记录。
- 所有危险字段 fail-closed。

### P1 - 文档同步

Robot Software 必须同步更新：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

文档必须说明 `07-53` 的 proof boundary、最新 blocker、strict no-motion 禁止项，以及如何读取 live/local artifact。

## 非目标

- 不做 O5 support-only readiness/readback。
- 不修改 `OKR.md`。
- 不修改 `docs/process/okr_progress_log.md`。
- 不改硬件配置、串口参数、WAVE ROVER 协议或 launch 参数，除非后续另起硬件 owner sprint。
- 不做 NavigateToPose、route execution、delivery success、HIL pass 或 safe-to-control 宣称。
- 不做 Full-stack/O7 独立 surface 工作。

## 优先级和验收口径

P0 验收：

1. 新 artifact 明确包含 `07-53` / `map_amcl_scan_tf_downstream` 本轮标识或文件路径。
2. `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 不回退。
3. downstream blocker 至少覆盖 `map_lifecycle_preflight_map_server_and_amcl_inactive`、`amcl_lifecycle_not_active`、`/scan_no_publisher`、`/map_once_not_observed`、`/tf_topic_missing` 的保留或解除状态。
4. 所有危险字段保持 false；若 path planner-only gate 触发，artifact 必须证明没有运动和底盘控制。
5. `python3 -m py_compile`、targeted unittest、local dry-run、true-board strict no-motion run 或明确不可达定位、scoped `git diff --check` 均有记录。

P1 验收：

1. navigation docs 同步。
2. `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
3. Product closeout 能据此判断是否仍保持 OKR flat。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 咨询：无默认咨询。
- 硬件升级条件：如果 `/scan_no_publisher` 被证明依赖 LiDAR 进程、串口设备、波特率、WAVE ROVER 或上车接线事实，Product 再派 `rober-hardware-engineer`，且必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 风险、阻塞和证据链缺口

- true-board 可达性可能波动；若无法执行，最多算 blocked with root cause，不能算 progress。
- map/AMCL inactive 可能与 managed runtime 启动顺序、lifecycle manager、地图文件或 process graph 相关；需要 artifact 保留命令历史。
- `/scan_no_publisher` 可能从 Robot Software 问题升级为 LiDAR runtime/hardware 事实；升级前不能猜测串口、波特率或接线。
- 即使 `/scan`、`/map`、`/tf` 恢复，也仍不等于 route execution、delivery success、HIL pass 或 production evidence。

## 需要创建或更新的 Sprint 文档

- 已创建计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施后必须创建：`tech-done.md`。
- Product 验收后必须创建：`side2side_check.md`、`final.md`。

# PRD - O3 Lifecycle CLI Budget Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Product status: plan ready
- Proof boundary: `software_proof_o3_o1_strict_no_motion_lifecycle_cli_budget_recovery_only`

## 用户价值和产品北极星

用户价值：让真实上位机在不运动、不控制底盘的前提下，把 `/map_server` 与 `/amcl` lifecycle readback 从 timeout 黑盒变成可解释的命令预算、stdout、graph 和状态机事实。用户最终关心的是手机一键发车后机器人能稳定沿固定路线送垃圾；当前 sprint 的价值是消除路径生成前的 lifecycle 诊断黑盒，让后续 `/scan`、`/map`、TF 和 planner-only proof 不再被不透明 timeout 阻断。

产品北极星：普通手机用户交付垃圾后，机器人沿固定路线送达垃圾站点并可复盘。此 sprint 不交付手机体验、不交付送达、不交付运动能力；只为 current-run path generation 和后续 route execution 准备可验证前置条件。

## 背景和问题

上一轮 `07-53` 已证明：

- `board_source_preflight.classification=board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `/scan` publisher visible，canonical blocker 为 `/scan_reliable_and_best_effort_timeout`
- `/map` blocker 为 `/map_topic_missing`
- TF blocker 为 `/tf_topic_missing`

但 lifecycle 层仍不 clean：

- `ros2 lifecycle get /map_server` 暴露 `map_server_lifecycle_command_timeout`
- `ros2 lifecycle get /amcl` 暴露 `amcl_lifecycle_command_timeout`
- `downstream_recovery_summary.amcl.blocked_reason=amcl_lifecycle_not_active`
- `path_generation_attempted=false`
- `path_generated=false`

因此本轮不得回到 O5 support-only、source/path mismatch、`ros2 --help` readiness 或泛化 wrapper。当前问题是 lifecycle CLI budget/retry/command-summary 不足，导致 Product 只能看到 timeout，不能判断是预算、inactive stdout、graph ok but lifecycle timeout，还是 active 后的下游 blocker。

## OKR 映射和方向判断

- O5：当前约 `85%` 且是最低 Objective，但本轮 `暂停`。O5 缺真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence；继续 O5 support-only/readback/wrapper 不计分。
- O3/O1：本轮 `继续` O3/O1 strict no-motion lifecycle lane。它直接服务 O1 缺口里的 current same-run path generation success 和 Nav2 route execution success，也服务 Mission Objective 0 的 current-run delivery evidence chain。
- O6/O7：本轮 `不调整`，除非后续 Robot Software 产出可被消费的新 same-task path/route/delivery material；否则不安排 Full-stack surface 或 readback 包装。
- KR 拆解：本轮只拆到 lifecycle CLI budget recovery proof gate，不把任何 KR 标为完成。
- 历史归档：本轮无已完成 KR，不更新历史区。

方向判断：`继续` O3/O1 no-motion lifecycle CLI budget recovery；`暂停` O5 support-only；`不归档` KR；`不调整` OKR 百分比，除非后续 artifact 出现更强 current-run mission evidence。

## 需求

### P0 - Lifecycle CLI budget recovery

Robot Software 必须让 helper 对 `/map_server` 和 `/amcl` lifecycle readback 形成分层 artifact。artifact 至少要回答：

- 当前执行的 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` 的 command、timeout budget、elapsed、stdout、stderr、returncode。
- 是否执行 retry；retry 与 first attempt 的差异是什么。
- 结果分类是 `lifecycle_command_timeout`、`inactive stdout`、`graph ok but lifecycle timeout`、`active`，还是 source/runtime 前置失败。
- graph/node 可见时，lifecycle command timeout 是否被明确标记为 `graph ok but lifecycle timeout`。
- stdout 为 `inactive [2]`、`active [3]` 或其他状态时，artifact 是否能保留原始 stdout 和 canonical classification。

### P0 - Downstream gating

只有 lifecycle readback clean 后，才允许继续采集下游 blocker：

- `/scan_reliable_and_best_effort_timeout`
- `/map_topic_missing`
- `/tf_topic_missing`

本轮仍不做 path generation 或 motion。即使 lifecycle clean，也只允许把下游 blocker 写入 artifact；不得发送 NavigateToPose、不得发布 `/cmd_vel`、不得调用 `/api/base/manual`、不得打开 WAVE ROVER UART。

### P0 - Safety invariants

所有验收必须保持 strict no-motion：

- `path_generation_attempted=false`
- `path_generated=false`
- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`

### P0 - Evidence artifact

若 true board 可达，必须产出新的 raw artifact 到本 sprint artifacts 目录，例如：

- `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/artifacts/live_o10_lifecycle_cli_budget_recovery.raw.json`

若 true board 不可达，Robot Software 必须记录 SSH/SCP/timeout 失败定位，并保留 local fail-closed artifact。不可达不能被写成 mission progress。

### P1 - Regression coverage

单测必须覆盖：

- `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 不回退。
- `ros2 lifecycle get /map_server` timeout 被分类为 `lifecycle_command_timeout`。
- `ros2 lifecycle get /amcl` timeout 被分类为 `lifecycle_command_timeout`。
- stdout `inactive [2]` 与 `active [3]` 分别进入明确 classification。
- graph/node 可见但 lifecycle timeout 时，artifact 命中 `graph ok but lifecycle timeout`。
- lifecycle 未 clean 时，不执行 path generation，且保持 `path_generation_attempted=false`。
- 所有危险字段 fail-closed。

### P1 - 文档同步

Robot Software 必须同步更新：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

文档必须说明 `08-55` 的 proof boundary、lifecycle CLI budget/retry/command-summary 读法、最新 blocker 和 strict no-motion 禁止项。

## 非目标

- 不做 O5 support-only readiness/readback/wrapper。
- 不修改 `OKR.md`。
- 不修改 `docs/process/okr_progress_log.md`。
- 不改硬件配置、串口参数、WAVE ROVER 协议或 launch 参数。
- 不做 NavigateToPose、path generation、route execution、delivery success、HIL pass 或 safe-to-control 宣称。
- 不做 Full-stack/O7 独立 surface、handoff、review decision 或 intake 工作。

## 优先级和验收口径

P0 验收：

1. 新 artifact 明确包含 `08-55` / `lifecycle_cli_budget_recovery` 本轮标识或文件路径。
2. `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 不回退。
3. artifact 对 `ros2 lifecycle get /map_server` 与 `ros2 lifecycle get /amcl` 包含 command-summary、预算、stdout/stderr、elapsed、retry 和 classification。
4. classification 能区分 `lifecycle_command_timeout`、`inactive stdout`、`graph ok but lifecycle timeout`、`active`。
5. lifecycle readback clean 前不继续 path generation；本轮必须保持 `path_generation_attempted=false`、`safe_to_control=false`、`publishes_cmd_vel=false`。
6. `python3 -m py_compile`、targeted unittest、local dry-run、true-board strict no-motion run 或明确不可达定位、scoped `git diff --check` 均有记录。

P1 验收：

1. navigation docs 同步。
2. `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
3. Product closeout 能据此判断是否仍保持 OKR flat。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 咨询：无默认咨询。
- 硬件升级条件：如果 lifecycle readback clean 后，`/scan_reliable_and_best_effort_timeout` 被证明依赖 LiDAR 进程、串口设备、波特率、WAVE ROVER 或上车接线事实，Product 再派 `rober-hardware-engineer`，且必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 风险、阻塞和证据链缺口

- true-board 可达性可能波动；若无法执行，最多算 blocked with root cause，不能算 progress。
- lifecycle timeout 可能来自 ROS daemon、lifecycle manager、process startup budget、CLI plugin discovery 或 node graph 可见性；artifact 必须保留命令历史，避免猜测。
- `/scan_reliable_and_best_effort_timeout` 可能升级为 LiDAR runtime/hardware 事实；升级前不能猜测串口、波特率或接线。
- 即使 lifecycle clean 并继续暴露 `/map_topic_missing` 或 `/tf_topic_missing`，仍不等于 path generation、route execution、delivery success、HIL pass 或 production evidence。

## 需要创建或更新的 Sprint 文档

- 已创建计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施后必须创建：`tech-done.md`。
- Product 验收后必须创建：`side2side_check.md`、`final.md`。

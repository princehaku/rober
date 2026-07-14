# PRD - O3 Map Server Graph/Lifecycle Visibility

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Product status: plan ready
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`

## 用户价值和产品北极星

用户价值：让真实上位机在 strict no-motion 下恢复 `/map_server` graph/lifecycle visibility，把 retry `Node not found` 拆成可行动的工程事实。用户最终关心的是手机一键发车后机器人能稳定沿固定路线送垃圾；当前 sprint 的价值是解除 same-run path generation 前的 `/map_server` 可见性阻断。

产品北极星：普通手机用户交付垃圾后，机器人沿固定路线送达垃圾站点并可复盘。本 sprint 不交付手机体验、不交付送达、不交付运动能力；只为 current-run path generation 和后续 Nav2 route execution 准备可验证前置条件。

## 背景和问题

`07-53` 下游恢复已把 blocker 从 generic inactive 收窄为：

- `board_source_preflight.classification=board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `map_server_lifecycle_command_timeout`
- `amcl_lifecycle_command_timeout`
- `/scan` publisher visible 但 sample timeout
- `/map_topic_missing`
- `/tf_topic_missing`

`08-55` lifecycle CLI budget recovery 进一步证明：

- `board_source_preflight_ready`
- `lightweight_cli_ready=true`
- `cli_ready=true`
- `runtime_ready=true`
- `/amcl` first attempt timeout 后 retry stdout contains `active [3]`
- `/map_server` first attempt `lifecycle_command_timeout`
- `/map_server` retry `returncode=1` 且 `stderr="Node not found\n"`
- downstream scan/map/odom/TF probes 被正确 gating，未抢跑
- `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`

因此本轮主要问题不是 O5、不是 ROS2 source、不是 `ros2 --help`、不是 generic lifecycle timeout，也不是 `/scan`/TF 下游恢复。主要问题是 `/map_server` 在当前 live run 中为何不出现在 graph/lifecycle readback：节点确实缺席、lifecycle manager/process startup 没启动、DDS/daemon graph 不可见，还是 helper command budget/timing 造成观测窗口不足。

## OKR 映射和方向判断

- O5：当前约 `85%` 且是最低 Objective，但本轮 `暂停`。原因是 O5 缺真实 production cloud、HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser 和 external production evidence；继续 O5 support-only/readback/wrapper 不计分。
- O3/O1：本轮 `继续` O3/O1 strict no-motion map-server visibility lane。它直接服务 O1 缺口里的 current same-run path generation success 和 Nav2 route execution success，也服务 Mission Objective 0 的 current-run delivery evidence chain。
- O6/O7：本轮 `不调整`，除非后续 Robot Software 产出可消费的新 same-run path/route/delivery material；否则不安排 Full-stack surface、review、handoff 或 intake。
- KR 拆解：本轮只拆到 `/map_server` graph/lifecycle visibility proof gate，不把任何 KR 标为完成。
- 历史归档：本轮无已完成 KR，不更新历史区。

方向判断：`继续` O3/O1 no-motion `/map_server` graph/lifecycle visibility；`暂停` O5 support-only；`不归档` KR；`不调整` OKR 百分比，除非后续 artifact 出现更强 current-run mission evidence。

## 需求

### P0 - Map-server graph/lifecycle visibility

Robot Software 必须让 helper 对 `/map_server` 形成分层 artifact。artifact 至少要回答：

- `/map_server` 在 node graph 中是否可见。
- lifecycle command 使用的 exact command、timeout budget、elapsed、stdout、stderr、returncode。
- first attempt 与 retry attempt 的差异是什么。
- daemon/DDS graph 是否可读，是否存在 daemon stale、graph timeout、node absence 或 helper timeout。
- lifecycle manager 或 process startup 是否看起来未启动、启动太慢、或已启动但 graph 不可见。
- 结果分类是否能区分 `map_server_node_absent`、`lifecycle_manager_or_process_startup_missing`、`daemon_or_dds_graph_visibility_failed`、`helper_budget_or_timing_exhausted`、`map_server_lifecycle_active`。

### P0 - Keep AMCL fact stable

`/amcl` retry 已读到 `active [3]`。本轮必须保留或复验该事实，不能把 AMCL 回退成 generic inactive/timeout 叙述。若 `/amcl` 在新 run 中回退，artifact 必须清楚写出这是新 live state，而不是覆盖 08-55 事实。

### P0 - Downstream gating

本轮 downstream `/scan`、`/map`、TF 只作为 guarded context。只有 `/map_server` graph/lifecycle visibility 足够 clean 后，才允许记录下游状态；仍不得把 `/scan`/TF downstream 作为 primary target。

### P0 - Safety invariants

所有验收必须保持 strict no-motion：

- `safe_to_control=false`
- `publishes_cmd_vel=false`
- `calls_base_manual=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `delivery_success=false`
- `hil_pass=false`
- `uses_base_uart=false`
- `path_generation_attempted=false`
- `path_generated=false`

### P0 - Evidence artifact

若 true board 可达，必须产出新的 raw artifact 到本 sprint artifacts 目录，例如：

- `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/artifacts/live_o10_map_server_graph_lifecycle_visibility.raw.json`

若 true board 不可达，Robot Software 必须记录 SSH/SCP/timeout 失败定位，并保留 local fail-closed artifact。不可达不能被写成 mission progress。

### P1 - Regression coverage

单测必须覆盖：

- `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 不回退。
- `/map_server` retry `Node not found` 能进入 node absence 或 graph visibility 分类，而不是 generic timeout。
- node graph visible 但 lifecycle command timeout 时，命中 graph-visible lifecycle timeout 分类。
- daemon/DDS graph timeout 与 helper command budget timeout 能被区分。
- lifecycle manager/process startup missing 时，artifact 给出明确分类。
- `/amcl active [3]` 仍能被保留为 active fact。
- lifecycle 未 clean 时，不执行 path generation，且保持所有 dangerous booleans false。

### P1 - 文档同步

Robot Software 必须同步更新：

- `docs/navigation/field_route_evidence_preflight.md`
- `docs/navigation/fixed_route_workflow.md`

文档必须说明 `09-54` 的 proof boundary、`/map_server` graph/lifecycle visibility 读法、最新 blocker、strict no-motion 禁止项，以及 08-55 与 07-53 的关系。

## 非目标

- 不做 O5 support-only readiness/readback/wrapper。
- 不修改 `OKR.md`。
- 不修改 `docs/process/okr_progress_log.md`。
- 不改硬件配置、串口参数、WAVE ROVER 协议或 launch 参数。
- 不做 NavigateToPose、path generation、route execution、delivery success、HIL pass 或 safe-to-control 宣称。
- 不把 `/scan`/TF downstream 当 primary target。
- 不做 Full-stack/O7 独立 surface、handoff、review decision 或 intake 工作。

## 优先级和验收口径

P0 验收：

1. 新 artifact 明确包含 `09-54` 或 `map_server_graph_lifecycle_visibility` 本轮标识或文件路径。
2. `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true` 不回退。
3. artifact 对 `/map_server` 包含 graph inventory、daemon/DDS visibility、lifecycle command first/retry、预算、stdout/stderr、elapsed、returncode 和 classification。
4. classification 能区分 node absence、lifecycle manager/process startup、daemon/DDS graph visibility、helper budget/timing。
5. `/amcl active [3]` 事实被保留或以新 live state 解释。
6. 本轮必须保持 `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。
7. `python3 -m py_compile`、targeted unittest、local dry-run、true-board strict no-motion run 或明确不可达定位、scoped `git diff --check` 均有记录。

P1 验收：

1. navigation docs 同步。
2. `tech-done.md` 记录实际改动、验证结果、失败定位和剩余风险。
3. Product closeout 能据此判断是否仍保持 OKR flat。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- 咨询：无默认咨询。
- 硬件升级条件：如果 `/map_server` visibility clean 后，新证据证明 blocker 依赖 LiDAR serial/runtime/接线、WAVE ROVER、UART 或硬件事实，Product 再派 `rober-hardware-engineer`，且必须先读 `docs/vendor/VENDOR_INDEX.md`。
- Algorithm 介入条件：`/map_server` 和 AMCL lifecycle/readiness clean 后，再由 `robot-algorithm-engineer` 消费 `/scan`、`/map`、TF/path readiness。

## 风险、阻塞和证据链缺口

- true-board 可达性可能波动；若无法执行，最多算 blocked with root cause，不能算 progress。
- `Node not found` 可能来自节点缺席、launch/process startup、lifecycle manager、DDS/daemon graph、ROS_DOMAIN_ID/env、或 helper command timing；artifact 必须保留命令历史，避免猜测。
- `/amcl active [3]` 不证明 AMCL pose freshness、dynamic `map->odom` 或 localization ready。
- 即使 `/map_server` visibility 恢复，仍可能继续 blocked 于 `/map_topic_missing`、`/tf_topic_missing` 或 `/scan` sample timeout；这仍不是 path generation、route execution、delivery success、HIL pass 或 production evidence。

## 需要创建或更新的 Sprint 文档

- 已创建计划文档：`pre_start.md`、`prd.md`、`tech-plan.md`。
- 实施后必须创建：`tech-done.md`。
- Product 验收后必须创建：`side2side_check.md`、`final.md`。

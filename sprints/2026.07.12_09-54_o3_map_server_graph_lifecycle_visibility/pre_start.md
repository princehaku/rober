# Pre Start - O3 Map Server Graph/Lifecycle Visibility

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`
- Start time: `2026-07-12 09:54 CST`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Proof boundary: `software_proof_o3_o1_strict_no_motion_map_server_graph_lifecycle_visibility_only`
- Direction: continue O3/O1 strict no-motion runtime recovery; pause O5 support-only/readback/wrapper work.

## 用户价值和产品北极星

用户价值是让真实上位机在不运动、不控制底盘的前提下，把 `/map_server` 从 retry `Node not found` 的黑盒恢复为可解释的 graph/lifecycle 可见性事实。只有先知道 `/map_server` 是节点缺席、lifecycle manager 未拉起、process startup 未完成、DDS/daemon graph 不可见，还是 helper command budget/timing 不足，后续 same-run path generation 和 Nav2 route execution 才有可执行下一步。

产品北极星仍是普通手机用户一键发车完成固定路线送垃圾。本 sprint 只恢复路径生成前的诊断链，不交付路线执行、底盘控制、送达闭环、HIL 或云端生产证据。

## 已读证据和上轮结论

- `AGENTS.md`：Epic sprint 必须按 `pre_start.md -> prd.md -> tech-plan.md -> tech-done.md -> side2side_check.md -> final.md` 留档；实现、测试和修复由 owner 子 agent 执行；本阶段只创建规划文档。
- `OKR.md`：O5 约 `85%` 是当前最低 Objective，但缺真实 production external evidence；O1/O6/O7 约 `93%`，O1 主要缺 current same-run path generation success 与 Nav2 route execution success。
- `sprints/2026.07.12_08-55_o3_lifecycle_cli_budget_recovery/final.md`：最新 live artifact 证明 `board_source_preflight_ready`、`lightweight_cli_ready=true`、`cli_ready=true`、`runtime_ready=true`；`/amcl` retry 已读到 `active [3]`，但 `/map_server` retry `returncode=1` 且 `stderr="Node not found\n"`。下一轮建议恢复 `/map_server` graph/lifecycle visibility，并区分 node absence、lifecycle manager/process startup、daemon/DDS graph visibility、helper budget/timing。
- `sprints/2026.07.12_07-53_o3_map_amcl_scan_tf_downstream_recovery/final.md`：下游 blocker 曾从 generic inactive 收窄为 `map_server_lifecycle_command_timeout`、`amcl_lifecycle_command_timeout`、`/scan` publisher visible sample timeout、`/map_topic_missing`、`/tf_topic_missing`。本轮不能把这些 downstream blocker 当 primary。

## OKR 映射和方向判断

- O5：`暂停`。O5 仍是当前最低约 `85%`，但继续 production readiness/readback/support-only 工作缺真实 external production evidence，不计分，也会重复消费同一 blocker。
- O3/O1：`继续`。本轮处理 `/map_server` graph/lifecycle visibility，是 O1 current same-run path generation success 与 Nav2 route execution success 的前置诊断条件。严格 no-motion，不做路径执行。
- O6/O7：`不调整`。没有新的 same-task route execution、delivery record、operator acceptance 或 production readback material 前，不安排 Full-stack surface、handoff、review、intake。
- KR 历史归档：本轮规划阶段不归档任何 KR；已完成 KR 历史区不更新。

方向判断：`继续` O3/O1 no-motion `/map_server` graph/lifecycle visibility；`暂停` O5 support-only；默认 `不调整` OKR 百分比；`不归档` KR。

## 本轮核心抓手

本轮核心抓手是让 `robot-software-engineer` 单 owner 继续扩展 `onboard/scripts/o10_amcl_nav2_runtime_proof.py` 的 strict no-motion helper，使新 artifact 能解释 `/map_server` 为什么在 retry 中 `Node not found`：

1. 区分 node absence、lifecycle manager/process startup、daemon/DDS graph visibility、helper command budget/timing。
2. 保留 `/map_server` first/retry lifecycle command、node graph inventory、daemon status、process/runtime startup、stdout/stderr、returncode、elapsed 和 timeout budget。
3. 保持 `/amcl active [3]` 的既有事实，不把本轮回退成 generic lifecycle timeout。
4. 下游 `/scan`、`/map`、TF 只作为 guarded context，不作为 primary target。

## 范围和责任人

- Product owner：`product-okr-owner`，负责计划、验收口径、方向判断和收口边界。
- Implementation owner：`robot-software-engineer`，负责 helper、单测、navigation docs、raw artifact 和 `tech-done.md`。
- Algorithm owner：本轮默认不改代码；等 `/map_server` graph/lifecycle visibility clean 后再消费 `/scan`、`/map`、TF/path readiness。
- Hardware owner：本轮默认不介入。只有新证据证明 LiDAR serial/runtime/接线、WAVE ROVER、UART 或硬件事实相关时，才升级 `rober-hardware-engineer`，并必须先读 `docs/vendor/VENDOR_INDEX.md`。
- Full-stack owner：本轮不介入；禁止做 O7 surface/handoff/intake 包装。

## 安全红线

本轮验收严格保持 no-motion：

- 禁止 NavigateToPose。
- 禁止发布 `/cmd_vel`。
- 禁止调用 `/api/base/manual`。
- 禁止打开或使用 WAVE ROVER UART。
- 禁止 route execution、delivery success、HIL pass 或 safe-to-control 宣称。
- 默认所有危险字段必须保持 `false`：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。
- 路径相关字段必须保持未执行：`path_generation_attempted=false`、`path_generated=false`。

## 同一 Blocker 重复消费判断

本轮不应重复消费 O5 external production blocker，也不应回退到旧 O3 blocker：

- 不回到 O5 readiness/readback/support-only。
- 不回到 source/path mismatch。
- 不回到 `ros2 --help` single gate。
- 不把 generic lifecycle timeout 当本轮 primary 结论。
- 不把 `/scan`/TF downstream blocker 当本轮 primary。

本轮可验收为进展的最低条件是：artifact 明确解释 `/map_server` graph/lifecycle visibility 的失败层级，至少能区分 node absence、lifecycle manager/process startup、daemon/DDS graph visibility、helper budget/timing 中的一个或多个具体分支；如果仍 blocked，必须给出下一条 exact blocker。

## 需要创建或更新的 Sprint 文档

- 本阶段创建：`pre_start.md`、`prd.md`、`tech-plan.md`。
- Robot Software 实施后必须创建或更新：`tech-done.md`。
- Product 验收后必须创建或更新：`side2side_check.md`、`final.md`。

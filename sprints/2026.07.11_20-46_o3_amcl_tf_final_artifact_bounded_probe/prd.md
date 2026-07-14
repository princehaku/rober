# O3 AMCL TF Final Artifact Bounded Probe PRD

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.11_20-46_o3_amcl_tf_final_artifact_bounded_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-algorithm-engineer`
- Product direction: continue O3/O1 no-motion localization/path readiness; pause O5 support-only packaging

## 1. 用户价值和产品北极星

普通用户不关心 ROS2 CLI、AMCL lifecycle 或 TF edge 名称；用户关心的是小车是否能在当前环境里知道自己在哪里、算出一条固定路线，并最终完成送垃圾任务。当前 product north star 是 current-run delivery evidence chain：同轮地图/定位/path、route execution、delivery/operator acceptance 和可回放材料。

本 sprint 的产品价值是把真实板 no-motion 链路从“前置 runtime 已 ready”推进到“AMCL/TF/path readiness 是否真的 ready”。如果成功，本轮能为下一轮 route execution 或 O6/O7 material consumption 提供 current-run localization/path artifact；如果失败，也必须把最先失败的 AMCL/TF/root cause 写清，避免继续在 source/CLI 或 O5 support-only 层原地转圈。

## 2. 背景事实

当前最低 Objective 是 O5，约 `85%`。但 O5 缺的是真实 production/external evidence：公网 HTTPS/TLS、4G/SIM、production DB/queue、worker cutover、OSS/CDN live traffic、真实手机/browser。最近 O5 工作已把 readiness packet 和 credit gate 写清，且 `okr_credit_allowed=false`。继续做 O5 wrapper、readback、checklist 或 intake surface 不能产生主 OKR 增量。

O3/O1 no-motion 链路最近的事实变化更具体：

- 18-45：阻塞在 `board_source_preflight_ros2_cli_unavailable`。
- 19-46：已修到 `board_source_preflight_ready`，`ros2_cli_ok=true`，`rclpy_import_ok=true`。
- 19-46 下游仍 blocked：`sigterm_before_final_artifact`、`/amcl_pose_once_not_observed`、`map_to_odom_not_observed`、`map_to_base_link_blocked_by_missing_map_to_odom`。
- 19-46 path 状态：`path_generation_requested=true`，但 `path_generation_attempted=false`、`path_generated=false`。

因此本轮产品方向是继续 O3/O1 no-motion localization/path readiness，而不是回到 O5。

## 3. OKR 映射和方向判断

- O5：方向 `暂停 support-only 包装`。没有真实 external production evidence 前，不继续安排 O5 readiness/readback/checklist 小切片。
- O1：方向 `继续 supporting no-motion localization/path readiness`。本轮可能推动 current same-run path generation success 的前置条件，但不自动上调百分比。
- O3 现场验证 lane：方向 `继续`。虽然不单独计分，但它是当前可动的 mission execution 前置链路。
- O6/O7：方向 `等待可消费 current-run material`。只有本轮产出 same-run path artifact、route execution material、delivery/operator material 或 production readback，才进入 O6/O7 消费。

方向判断：`调整执行焦点`，从 O5 support-only 外部材料缺口转向 O3/O1 no-motion AMCL/TF/path readiness。不是替换产品北极星，也不是给 O5 重新计分。

## 4. KR 拆解、更新或历史归档

本轮不预先把任何 KR 标为完成，不移动 KR 到历史区。

当前 KR 仍需保留在推进区：

- O1 current same-run path generation success；
- O1 Nav2 route execution success；
- O1 current live HIL pass 和 safe-to-control；
- O5 production external evidence；
- O6/O7 current-run route/delivery/operator/production material consumption。

本轮可能产生的 KR 输入材料：

- AMCL lifecycle readback；
- `/amcl_pose` observed/not observed；
- dynamic `map->odom` observed/not observed；
- `map->base_link` 分层结果；
- planner-only path generation attempted/generated 结果；
- live final/partial artifact root cause。

历史记录位置规则：

- 若本轮只产出 fail-closed diagnosis，不移动 KR；
- 若本轮产出 `path_generated=true` 且 artifact 证明 same-run planner-only path point count 大于 0，只能作为 O1/O3 supporting material，是否计分由 `final.md` 再判断；
- 若本轮没有 route execution、delivery/operator 或 production external evidence，不允许把 O6/O7/O5 KR 归档完成。

## 5. 本轮核心抓手

核心抓手是让 `robot-algorithm-engineer` 单线闭环修复 final artifact 有界收口，并把 AMCL/TF/path readiness 拆成可判定字段：

- `managed_runtime_started`；
- `map_server_active`；
- `amcl_active`；
- `/amcl_pose` topic type、freshness、sample 结果；
- `map->odom` dynamic source 和 freshness；
- `map->base_link` blocked reason；
- path generation requested、attempted、generated、point count；
- false safety fields 和 no-motion proof boundary。

## 6. 需求范围

必须做：

- 保证 helper 在 live SIGTERM、timeout 或 partial runtime 时尽量写出 structured final/partial artifact；
- 明确 AMCL lifecycle 与 `/amcl_pose` sample 的边界；
- 明确 dynamic `map->odom` 与 downstream `map->base_link` 的边界；
- 在 localization ready 时只做 planner-only `ComputePathToPose` path probe；
- 更新 Algorithm 相关 tests 和导航文档；
- 更新本 sprint `tech-done.md`、artifact 与 closeout 文档。

不得做：

- 不发布 `/cmd_vel`；
- 不调用 `/api/base/manual`；
- 不发送 NavigateToPose goal；
- 不使用 WAVE ROVER UART；
- 不接 cloud/O6/O7 UI；
- 不把 historical latest path 或 clean-baseline comparator 当成 current-run success；
- 不把 runtime started 当成 HIL、route execution 或 delivery success。

## 7. 优先级和验收口径

P0 验收：

- helper/unit tests 通过；
- local helper 可 fail-closed 写 artifact；
- live helper 可写 final artifact，或至少写出结构化 partial artifact 并定位 `sigterm_before_final_artifact`；
- artifact 必须包含 AMCL lifecycle、`/amcl_pose`、`map->odom`、`map->base_link` 和 path generation requested/attempted/generated 结果；
- 顶层 `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`。

P1 验收：

- 如果 path readiness 成功，artifact 包含 same-run `path_generated=true` 与 point count；
- 如果 path readiness 失败，artifact 包含最先失败 root cause，并区分 lifecycle、topic、TF 和 planner layer；
- 导航文档同步说明新的 AMCL/TF/final artifact 字段。

## 8. 对应责任 Engineer

责任 owner：`robot-algorithm-engineer`。

不并行派发其他 owner。Robot Software、Hardware、Full-stack 本轮不改文件；如执行中发现接口或硬件事实需要确认，再由 Algorithm 在 `tech-done.md` 标注风险，Product closeout 决定下一轮是否切换 owner。

## 9. 风险、阻塞和需要补齐的证据链

主要风险：

- live runtime 继续被 SIGTERM 打断，无法拿到 final artifact；
- AMCL lifecycle active 但 `/amcl_pose` 不发布；
- `map->odom` 仍缺失，导致 `map->base_link` 与 path generation 无法继续；
- planner-only path 成功仍可能无法转化为 route execution；
- O5 仍因 production external evidence 缺失保持约 `85%`。

需要补齐的证据链：

1. same-run localization readiness；
2. same-run TF readiness；
3. same-run planner-only path artifact；
4. 后续 live route execution；
5. delivery record 或 operator acceptance；
6. production external evidence 或 O6/O7 可消费 material。

## 10. 需要创建或更新的 Sprint 文档

本计划阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

执行阶段更新：

- `tech-done.md`

验收收口阶段更新：

- `side2side_check.md`
- `final.md`

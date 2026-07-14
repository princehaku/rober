# Pre Start - O3 Map Server LoadMap Return Code Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_17-55_o3_map_server_loadmap_return_code_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Planned start time: `2026-07-12 17:55 CST`
- Target objective: O3/O1 strict no-motion field lane
- Product status: ready for Robot Software implementation
- Proof boundary: planned `software_proof_o3_o1_strict_no_motion_map_server_loadmap_return_code_probe_only`

## Read-First Evidence

本轮开工前已读取并采用以下证据：

- `AGENTS.md`
- `OKR.md`
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/final.md`
- `sprints/2026.07.12_16-55_o3_map_server_on_configure_return_source_repair/tech-done.md`
- `sprints/2026.07.12_15-54_o3_map_server_changestate_response_repair/final.md`
- Automation memory quick pass: O5 support-only blocked 时优先转 O3 strict no-motion，不重复包装 blocker。

## 用户价值和产品北极星

用户价值仍是让普通手机用户最终可以一键发车送垃圾。当前最短产品阻塞不是界面或云端，而是真实上位机 fixed-route/nav 链路里的 `/map_server` lifecycle：只有 `/map_server active` 后，Algorithm 才能继续验证 `/map`、AMCL、dynamic `map->odom`、planner-only path generation、route execution 和后续 delivery/operator acceptance。

本 sprint 不交付路线执行、底盘运动、HIL、送达、operator acceptance 或 production cloud。它只推进 O3/O1 strict no-motion field lane 中 `/map_server` configure failure 的最短解阻路径。

## OKR 映射和方向判断

- O5 当前约 `85%`，是数字最低 Objective，但当前只缺真实 external production evidence。继续做 O5 readiness、handoff、review、intake、surface 或 support-only packet 会重复消费 `no_real_production_external_evidence` blocker，因此本轮不排 O5。
- O1 当前约 `93%`，主要缺口包含 current same-run path generation success 与 Nav2 route execution success。本轮通过 O3 strict no-motion field lane 解除 `/map_server` lifecycle 前置 blocker，服务 O1 的 path/route evidence gate。
- O3 是已归档 Objective 的现场验证 lane，本轮只作为临时激活的 no-motion supporting evidence，不恢复为已完成 KR，不自动提升 OKR 百分比。
- O6/O7 当前约 `93%`，等待 live route execution、delivery/operator 或 production readback；本轮不做触点 surface。

方向判断：继续 O3/O1 strict no-motion field lane；暂停 O5 support-only；不调整 OKR 百分比；不归档 KR。

## 上轮 Blocker 摘要

16:55 最新 accepted root cause：

- `map_server_on_configure_return_false_after_valid_map_io_deferred_completion`
- `on_configure_returned_failure_after_valid_yaml_image_readback_with_map_io_completion_logged_later`
- `on_configure_return_source.source_family=on_configure_return_false_source`
- `on_configure_return_source.primary_source=on_configure_return_false_after_valid_map_inputs_while_map_io_log_completes_later`

已知事实：

- lifecycle manager 已请求 configure。
- `/map_server` configure callback 已进入。
- managed map YAML/PGM 可读，YAML 字段有效，runtime analysis OK。
- `map_input_validation.valid_for_map_server=true`。
- 没有 map_server-scoped exception。
- 没有 service/RPC timeout。
- map IO completion 在 ChangeState failure 后完成。
- `/map_server active=false`。
- `path_generation_attempted=false`、`path_generated=false`、`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`。

## 同一 Blocker 红线

本轮不能只重复 16:55 的 `map_server_on_configure_return_false_after_valid_map_io_deferred_completion` 标签。

Product 接受条件必须满足以下之一：

- 修到 `/map_server active=true`，并保持 strict no-motion；或
- 把 root cause 继续下钻到比 16:55 更具体的返回码、错误码、异常、参数、`loadMapResponseFromYaml` return path、`on_configure` return path、executor/log ordering 或 lifecycle manager ChangeState response handling。

如果工程输出仍只是同一 blocker 标签，且没有 active 证明或更具体 return code / call path，Product 验收失败并要求 `robot-software-engineer` 返工。若返工后仍重复，下一轮必须升级 CEO 或切换 Objective。

## Owner 边界

- 主责 owner：`robot-software-engineer`。
- Algorithm 只能在 `/map_server` lifecycle clean/active 后介入 `/map`、AMCL、TF、planner path 或 route execution。
- Hardware 只有在 LiDAR serial/runtime/wiring 成为 primary root cause 时介入；届时必须先读 `docs/vendor/VENDOR_INDEX.md`，并以本地 vendor 资料为准。
- Full-Stack 不介入，本轮没有手机/Web/API/UI 交付。

## 严格 No-Motion 边界

本轮 strict no-motion 禁止：

- 发布 `/cmd_vel`
- 调用 `/api/base/manual`
- 发送 NavigateToPose
- 打开 WAVE ROVER UART
- 声称 safe-to-control、route execution、delivery、HIL 或 production success

安全和 mission booleans 必须 fail-closed，包括但不限于 `safe_to_control=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

## 本轮核心抓手

Robot Software 需要直接 inspect/fix/narrow Nav2 map_server `loadMapResponseFromYaml` return code 与 `on_configure` return path。优先抓手包括：

- `loadMapResponseFromYaml` 的返回值、异常、error string 或 response status 是否能从 runtime/proof 中读出。
- `on_configure` 返回 `CallbackReturn::FAILURE` 的直接代码路径。
- map YAML/PGM 已 valid 时，是否仍有 mode、threshold、origin、frame、map response 或 occupancy grid 组装失败。
- executor/log ordering 是否让 map IO completion log 延后于 lifecycle failure，造成误判。
- lifecycle manager ChangeState response handling 是否把 callback 中间态或 future 状态当成 terminal failure。
- 如果可以小修，优先证明 `/map_server active=true`；如果不能小修，则输出比 16:55 更窄、下一轮可直接修复的 primary root cause。

## 需要创建或更新的 Sprint 文档

本阶段只创建产品计划三件套：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

后续实现阶段由对应 owner 更新 `tech-done.md` 和 artifacts。Product closeout 阶段再按证据更新 `side2side_check.md`、`final.md`、`OKR.md` 和进展日志；本阶段不修改这些范围外文件。

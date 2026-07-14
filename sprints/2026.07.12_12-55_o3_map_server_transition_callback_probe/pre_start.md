# Pre Start - O3 Map Server Transition Callback Probe

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_12-55_o3_map_server_transition_callback_probe/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Start time: `2026-07-12 12:55 CST`
- Direction: continue O3/O1 strict no-motion field chain
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_map_server_transition_callback_probe_only`

## 用户价值和产品北极星

用户价值是把真实上位机固定路线前置阻塞从 `/map_server` lifecycle activation callback failure 继续推进到可执行的下一层事实：要么 `/map_server` lifecycle clean/active，要么明确是 callback return、service call、bond wait、RPC timing 或 configure/activate return path 的哪一段失败。

产品北极星仍是普通手机用户一键发车完成固定路线送垃圾。本 sprint 不交付用户可见发车能力，不做 NavigateToPose，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART，不改硬件配置；它只处理送达链路前置的 Nav2 map_server lifecycle transition blocker。

## 上轮事实和进入条件

最新 accepted sprint 是 `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/`。其 `tech-done.md` / `final.md` 已确认：

- Primary live artifact `live_o10_map_server_lifecycle_activation_repair.raw.json` 为 `status=blocked_with_root_cause`。
- `proof.root_causes[0].layer=Nav2 map_server lifecycle activation`。
- `proof.root_causes[0].reason=map_server_activate_callback_failed`。
- `proof.root_causes[0].detail=lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback`。
- `proof.map_server_lifecycle_activation.canonical_classification=map_server_activate_callback_failed`。
- map yaml/PGM readback 已证明 `yaml.readable=true`、`pgm.readable=true`，fields valid for map_server。
- lifecycle manager managed node list matches `["map_server","amcl"]`，`frame_id=map`，`service_timeout_s=12.0`，`bond_timeout_s=8.0`，`RMW_FASTRTPS_USE_SHM=0`。
- `/map_server` 仍未 lifecycle clean/active。
- `path_generation_attempted=false`、`path_generated=false`。
- no-motion 字段继续为 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

近期链路已从 `/map_server Node not found` 推进到 `lifecycle_manager_failed_to_change_state_for_map_server`，再推进到 valid map readback 后的 `map_server_activate_callback_failed`。本轮允许继续，但验收必须越过这个分类，或输出比 `map_server_activate_callback_failed` 更窄的 callback/service/bond/RPC timing failure。

## OKR 映射和方向判断

- O5：约 `85%`，仍是最低 Objective，但没有真实 external production evidence。方向为 `暂停 support-only`；不得继续安排 readiness packet、surface、review、handoff、intake 或状态面板小切片。
- O3/O1：方向为 `继续` strict no-motion 现场链路。本轮把 `/map_server` lifecycle callback/timing blocker 做到可修复或可交给下一 owner 消费的粒度，服务 O1 current same-run path generation 缺口。
- O6/O7：约 `93%`，方向为 `暂停等待新材料`。没有新的 route execution、delivery/operator 或 production readback。
- OKR 结论：本 planning 阶段不调整百分比，不归档 KR。

## KR 拆解、更新或历史归档

本轮目标只进入 O3/O1 supporting chain，不归档任何 KR。

预期新增证据：

- `/map_server` lifecycle clean/active，或更窄的 transition callback/service/bond/RPC timing failure。
- transition path 证据包含 configure callback、activate callback、lifecycle `ChangeState` service response、lifecycle manager wait、bond creation/wait、process alive/exit 和 relevant log window。
- `map_server_activate_callback_failed` 不再作为终点；若保留，必须被下钻到具体 callback return / service / bond / RPC timing 子原因。
- 所有 motion/control/delivery/HIL 字段保持 false。

已完成 KR 的历史记录位置：无新增完成 KR，本轮不移动当前 KR 到历史区。证据来源将是本 sprint 的 `tech-done.md`、live artifact、`side2side_check.md`、`final.md`，必要时后续再同步 `OKR.md` 和 `docs/process/okr_progress_log.md`。剩余风险是即使 `/map_server` active，也仍未证明 `/map` sample、AMCL pose、dynamic `map->odom`、planner-only path generation、route execution、delivery 或 HIL。

## 本轮核心抓手

Robot Software 需要单线闭环检查/修复 Nav2 map_server lifecycle transition callback：

1. 采集 lifecycle manager 对 `/map_server` 的 configure/activate `ChangeState` service call、return value、timeout、exception 和 callback return path。
2. 采集 bond create/wait/result、service timeout、RPC timing、process status、map_server log window 和 lifecycle state readback。
3. 如果是参数、launch、namespace、service timeout、bond timeout 或 runtime env 可修复问题，优先修复到 `/map_server` lifecycle clean/active。
4. 如果无法修复，artifact 必须输出比 `map_server_activate_callback_failed` 更窄的 canonical classification，不能只重复上一轮文案。

## 需要做什么

- 由 `robot-software-engineer` 实施 helper / launch / test / navigation docs / artifact 更新，并负责本地与 true-board strict no-motion 验证。
- 实施后创建或更新本 sprint `tech-done.md`，记录实际改动、命令、返回码、关键 artifact 字段、失败定位和剩余风险。
- Product 验收后再创建 `side2side_check.md` 和 `final.md`，并按证据决定是否更新 `OKR.md` / `docs/process/okr_progress_log.md`。

## 优先级和验收口径

P0 验收：

- true-board artifact 显示 `/map_server` lifecycle clean/active；或输出比 `map_server_activate_callback_failed` 更窄的 callback/service/bond/RPC timing failure。
- artifact 明确包含 lifecycle transition request/response、configure/activate callback path、service timing、bond timing、process alive/exit、runtime log window 和 final lifecycle state。
- strict no-motion 安全字段保持 false。
- 不执行 NavigateToPose，不发布 `/cmd_vel`，不调用 `/api/base/manual`，不打开 WAVE ROVER UART，不改硬件配置。

P1 验收：

- local dry-run 在 macOS 无 ROS2 runtime 时 fail-closed。
- targeted unittest 覆盖 lifecycle clean、callback failure、service timeout、bond timeout、RPC timing failure、process exit 和 no-motion safety invariants。
- docs/navigation 说明 proof boundary 和 Algorithm 后续可消费条件。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- Algorithm：本轮不主责。等 `/map_server` lifecycle clean/active 后再恢复 `/map` sample、AMCL pose、dynamic `map->odom`、planner-only path gate。
- Hardware：本轮不介入。本轮不触碰 WAVE ROVER、UART、串口、接线、波特率、JSON 指令、速度映射或硬件配置。
- Full-stack：本轮不介入。

## 同一 Blocker 红线判断

- 09-54 blocker：`map_server_node_absent` / `/map_server Node not found`。
- 10-54 blocker：`lifecycle_manager_failed_to_change_state_for_map_server`。
- 11-54 blocker：`map_server_activate_callback_failed` after valid map readback。
- 本轮不是 generic lifecycle wrapper；它必须下钻 transition callback/service/bond/RPC timing 或修到 `/map_server` clean/active。
- 如果本轮仍停在完全相同 `map_server_activate_callback_failed`，且没有更窄 callback/service/bond/RPC timing evidence，下一轮必须 CEO 升级或切 Objective，不得继续消费同一 blocker。

## 风险、阻塞和需要补齐的证据链

- `/map_server` lifecycle clean/active 不等于 localization ready、dynamic `map->odom`、path generation success、route execution、delivery success、safe-to-control 或 HIL。
- true-board SSH 不可达会阻断主要验收；本地 proof 只能作为 fail-closed software check。
- ROS2 daemon/node-list transient 可以保留为 secondary context，但不得替代本轮 primary transition callback/timing root cause。
- 如实现过程中需要硬件串口、接线、波特率、JSON 指令、速度映射或 feedback 协议事实，必须停止相关假设并派 Hardware 读取 `docs/vendor/VENDOR_INDEX.md` 及其指向资料后再继续；本轮默认不触碰硬件配置。

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

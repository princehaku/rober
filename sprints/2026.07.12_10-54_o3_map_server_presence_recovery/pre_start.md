# Pre Start - O3 Map Server Presence Recovery

## Sprint Metadata

- sprint_type: epic
- Sprint: `sprints/2026.07.12_10-54_o3_map_server_presence_recovery/`
- Product owner: `product-okr-owner`
- Implementation owner: `robot-software-engineer`
- Start time: `2026-07-12 10:54 CST`
- Direction: continue O3/O1 strict no-motion现场链路
- Proof boundary target: `software_proof_o3_o1_strict_no_motion_map_server_presence_recovery_only`

## 用户价值和产品北极星

用户价值是把真实上位机当前卡住的 `/map_server` lifecycle retry `Node not found` 从"已诊断"推进到"strict no-motion presence recovery/proof"。只有 `/map_server` node/process/lifecycle manager presence 被恢复或证明进入新的更窄 root cause，后续 `/map`、TF、planner/path readiness 才有可执行入口。

产品北极星仍是普通手机用户一键发车完成固定路线送垃圾。本轮不做发车、不做路线执行、不做底盘控制；它只恢复送达链路前置的 Nav2 map server 可见性。

## 上轮事实和进入条件

最新 accepted sprint 是 `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/`。其 `final.md` 和 `tech-done.md` 已确认：

- `/map_server` retry `stderr="Node not found\n"`。
- canonical classification 为 `map_server_node_absent`。
- `/amcl` 事实保持 `amcl_lifecycle_reference.current_active=true`，retry stdout contains `active [3]`。
- `path_generation_attempted=false`、`path_generated=false`。
- no-motion 字段继续为 false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

主节点只读最新 artifact 后确认当前边界仍是：

- `managed_runtime_requested=false`
- `managed_runtime_started=false`
- `managed_runtime_boundary=default_read_only_existing_ros_graph_no_runtime_start`

因此本轮不能继续做 generic timeout、visibility review、handoff、O5 support-only packet、`/scan` 或 TF 下游诊断。必须升级为 strict no-motion `/map_server` presence recovery/proof。

## OKR 映射和方向判断

- O5：约 `85%`，当前最低，但缺真实 production external evidence。本轮 `暂停` O5 support-only 消费；不再用 readiness packet、surface、review 或 handoff 包装为进度。
- O3/O1：`继续` strict no-motion 现场链路。目标是越过 `/map_server` `Node not found`，为 current same-run path generation 前置条件扫清 map server presence blocker。
- O6/O7：约 `93%`，本轮不触碰。只有 route execution、delivery/operator、production readback 等新材料出现才恢复消费链。
- 方向判断：`继续` O3/O1，不调整 OKR 百分比，不归档 KR。

## KR 拆解、更新或历史归档

本轮目标只进入 O3/O1 supporting chain，不归档任何 KR。

预期新增证据：

- `/map_server` node/process/lifecycle manager presence recovery attempt。
- lifecycle readback 越过 `Node not found`，进入 active/inactive/configure error/map yaml missing/manager mismatch 等更窄结论。
- managed runtime recovery path 被显式记录，包括是否使用 `--managed-runtime-opt-in`、`--managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml`，或等价 `/api/nav2/start` + proof refresh 只读恢复路径。
- 所有 motion/control/delivery/HIL 字段保持 false。

已完成 KR 的历史记录位置：无新增完成 KR，本轮不移动当前 KR 到历史区。证据来源将是本 sprint 的 `tech-done.md`、live artifact、`side2side_check.md`、`final.md`，必要时后续再同步 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 本轮核心抓手

Robot Software 需要把 `/map_server` presence 从"只读诊断为 absent"推进到"strict no-motion 恢复或恢复失败的更窄 proof"：

1. 确认上一轮 `map_server_node_absent` 是否因为没有启动 managed runtime、map server process/lifecycle manager 未起、launch 参数未进入、map yaml path 未传入或 lifecycle manager 管辖节点名不一致。
2. 在不触发运动的前提下选择恢复路径：helper `--managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml`，或等价 `/api/nav2/start` + proof refresh 只读路径。
3. 重跑 true-board strict no-motion proof，拉回 artifact。
4. 如果 `/map_server` 不再 `Node not found`，记录新的 lifecycle/map/readiness blocker；如果仍是 `Node not found`，必须输出具体 recovery attempt、命令、stderr/stdout、process/lifecycle manager presence 事实，不得只写 timeout。

## 需要做什么

- 创建或更新 Robot Software 实施所需的 helper、test、navigation docs 和本 sprint artifact。
- 运行本地 py_compile、targeted unittest、local fail-closed dry-run、true-board strict no-motion run/pull artifact、scoped `git diff --check`。
- 实施后补齐本 sprint `tech-done.md`；Product 验收后再创建 `side2side_check.md` 和 `final.md`。

## 优先级和验收口径

P0 验收：

- true-board artifact 显示 `/map_server` lifecycle retry 不再是 `Node not found`，或明确证明 recovery path 已执行且失败点比 `map_server_node_absent` 更窄。
- strict no-motion 安全字段保持 false。
- artifact 明确记录 `managed_runtime_requested`、`managed_runtime_started`、managed map yaml basename/path policy、recovery command 和 lifecycle readback。
- 不发布 `/cmd_vel`，不执行 NavigateToPose，不调用 `/api/base/manual`，不打开 WAVE ROVER UART。

P1 验收：

- local dry-run 在 macOS 无 ROS2 runtime 时 fail-closed。
- targeted unittest 覆盖 presence recovered、still node absent、managed map yaml missing、lifecycle manager/process startup missing、safety fields false。
- docs/navigation 说明 proof boundary 和下一步 Algorithm 可消费条件。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- Algorithm：本轮不主责，等 `/map_server` lifecycle readback clean 后再恢复 `/map`、TF、planner/path readiness。
- Hardware：默认不介入。本轮不触碰 WAVE ROVER、UART、串口、接线、波特率或硬件配置。
- Full-stack：不介入。

## 风险、阻塞和需要补齐的证据链

- 同一 blocker 连续消费风险：08-55 已看到 `/map_server` retry `Node not found`，09-54 已分类为 `map_server_node_absent`。本轮只允许做 recovery/proof，不允许第三轮 diagnostic wrapper。若实施后仍无法越过 `Node not found`，必须在 `final.md` 中升级为 CEO 决策或切换 Objective。
- `/map_server` recovered 不等于 localization ready、dynamic `map->odom`、path generation success、route execution、delivery success 或 HIL。
- 如实现过程中需要硬件串口、接线、波特率、JSON 指令、速度映射或 feedback 协议事实，Robot Software 必须停止相关假设并派 Hardware 读取 `docs/vendor/VENDOR_INDEX.md` 及其指向资料；本轮默认不触碰硬件配置。
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

# PRD - O3 Map Server Presence Recovery

## 背景

最新 accepted sprint `sprints/2026.07.12_09-54_o3_map_server_graph_lifecycle_visibility/` 已把 `/map_server` failure 从模糊 lifecycle/graph 失败收敛为 `map_server_node_absent`：

- lifecycle retry `stderr="Node not found\n"`。
- canonical classification `map_server_node_absent`。
- `/amcl` 保持 active reference。
- `managed_runtime_requested=false`、`managed_runtime_started=false`、`managed_runtime_boundary=default_read_only_existing_ros_graph_no_runtime_start`。

这说明上一轮主要是只读 existing ROS graph diagnostic。本轮需求是恢复或启动 `/map_server` presence，让 lifecycle readback 越过 `Node not found`。

## 用户价值和产品北极星

目标用户最终只需要手机一键发车、机器人沿固定路线送垃圾。当前阻塞在真实上位机 Nav2 map server 不存在，导致 `/map`、TF、planner/path readiness 无法进入可验证状态。

本轮用户价值是补齐"可安全恢复地图服务 presence"这个前置能力。它不是用户可见功能，但直接解锁下一步现场路径 proof。

## OKR 映射和方向判断

- O5：约 `85%`，仍是最低 Objective，但缺真实 external production evidence。方向为 `暂停` support-only；本轮不做 O5。
- O3/O1：方向为 `继续`。本轮聚焦 strict no-motion `/map_server` presence recovery/proof，服务 O1 current same-run path generation 缺口前置条件。
- O6/O7：方向为 `暂停等待材料`。没有新的 route execution、delivery/operator 或 production readback。
- 本轮不调整 OKR 百分比，不归档 KR。

## Problem Statement

当前 true-board proof 能证明 ROS2 CLI/runtime readiness 和 `/amcl` active reference，但 `/map_server` lifecycle retry 返回 `Node not found`。如果继续调查 `/scan`、TF 或 planner，会重复消费下游 blocked evidence。

需要 Robot Software 在 strict no-motion 条件下恢复或证明 `/map_server` node/process/lifecycle manager presence。

## 非目标

- 不执行 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不做 O5 support-only readiness/surface/review/handoff。
- 不把 `/scan`、TF、planner/path 下游 timeout 作为本轮 primary success。
- 不改硬件配置、不假设串口/波特率/接线事实。

## 范围

本轮范围：

- strict no-motion managed runtime opt-in recovery/proof。
- `/map_server` node/process/lifecycle manager presence readback。
- managed map yaml 路径传入或等价 API start + proof refresh 只读恢复路径。
- local fail-closed dry-run 和 true-board artifact。
- 实施文档同步到 navigation docs 和 sprint `tech-done.md`。

范围外：

- route execution、delivery/operator acceptance、HIL、safe-to-control。
- O7 UI/API、O6 archive、O5 production cloud。
- WAVE ROVER、ESP32、UART、LiDAR serial wiring 或硬件配置。

## KR 拆解、更新或历史归档

本轮不完成 KR。目标证据只用于 O3/O1 supporting chain：

- `map_server_presence_recovery_attempted=true` 或等价字段。
- `managed_runtime_requested=true` 或等价 API start proof。
- `managed_runtime_started=true` 或明确的 managed runtime startup blocker。
- lifecycle retry 不再是 `Node not found`，或 blocker 比 `map_server_node_absent` 更窄。
- strict no-motion 字段全部保持 false。

已完成 KR 历史记录位置：无新增。本轮完成后只在 sprint closeout 和必要的 OKR note 中记录 supporting evidence。

## 本轮核心抓手

核心抓手是把 helper/board path 从默认只读 existing graph 提升到显式恢复路径：

- 首选：`--managed-runtime-opt-in --managed-map-yaml /root/rober/onboard/runtime/maps/trashbot_map.yaml`。
- 可接受等价：先通过 `/api/nav2/start` 启动 no-motion managed runtime，再执行 `/api/nav2/proof/refresh` 或 helper proof refresh，并记录 API 响应和 artifact。

Robot Software 可在实施中选择路径，但必须在 `tech-done.md` 记录选择理由、命令、返回码和 artifact 字段。

## 验收口径

P0：

- true-board strict no-motion artifact 证明 `/map_server` lifecycle retry 越过 `Node not found`，或 recovery attempt 的失败点比 node absent 更窄且可执行下一步修复。
- artifact 明确包含 managed runtime requested/started/readback 边界。
- safety fields false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

P1：

- local dry-run fail-closed，不能产生 motion/control success。
- targeted unittest 覆盖 success、blocked 和 safety invariants。
- navigation docs 同步说明本轮 proof boundary。

不接受：

- 只把 timeout 文案换名。
- 继续只读 existing graph 且仍输出 `managed_runtime_requested=false`、`managed_runtime_started=false`。
- 把 `/scan`、TF 或 planner timeout 当成本轮 primary result。
- 任何运动、底盘控制、WAVE ROVER UART 或 hardware config 改动。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- Product 验收：`product-okr-owner`
- Algorithm：等待 `/map_server` presence/lifecycle clean 后接 `/map`、TF、planner/path readiness。
- Hardware：仅在实施需要硬件事实时介入，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 风险和证据链缺口

- 如果 `/map_server` presence recovery 失败且仍是 `Node not found`，本轮不能算 mission progress；需要升级 CEO 决策或切换目标，避免同一 blocker 第三轮消费。
- 即使 `/map_server` active，也仍未证明 `/map` topic sample、dynamic `map->odom`、path generation、route execution 或 delivery。
- true-board access 失败会阻断本轮主要验收；本地 proof 只能作为 fail-closed software check。

## Sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实施和验收阶段还需要：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

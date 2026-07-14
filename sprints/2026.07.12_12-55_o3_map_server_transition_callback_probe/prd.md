# PRD - O3 Map Server Transition Callback Probe

## 背景

最新 accepted sprint `sprints/2026.07.12_11-54_o3_map_server_lifecycle_activation_repair/` 已把 `/map_server` failure 从 generic lifecycle manager state-change failure 继续收窄：

- `proof.root_causes[0].reason=map_server_activate_callback_failed`
- `proof.root_causes[0].detail=lifecycle_manager_failed_to_change_state_for_map_server_after_valid_map_readback`
- `proof.map_server_lifecycle_activation.canonical_classification=map_server_activate_callback_failed`
- map yaml/PGM 在 true-board 上 readable 且 valid for map_server
- lifecycle manager managed node list、`frame_id=map`、`service_timeout_s=12.0`、`bond_timeout_s=8.0`、`RMW_FASTRTPS_USE_SHM=0` 已记录
- `/map_server` 仍未 lifecycle clean/active
- `path_generation_attempted=false`、`path_generated=false`
- safety fields 全部 false

这说明本轮不能再做 generic lifecycle wrapper。需求是检查/修复 Nav2 map_server transition callback、service/bond/RPC timing 或 configure/activate return path，并在 strict no-motion 下产出可验收 artifact。

## 用户价值和产品北极星

目标用户最终只需要手机一键发车、机器人沿固定路线送垃圾。当前阻塞在真实上位机 Nav2 map server lifecycle transition 不 clean，导致 `/map`、AMCL pose、TF、planner/path readiness 无法进入可验证状态。

本轮用户价值是让地图服务从 "valid map readback 后 activation callback failed" 进入 `/map_server` lifecycle clean/active，或拿到足够窄的 callback/service/bond/RPC timing failure，让下一轮可以直接修复，而不是继续重复包装 lifecycle failure。

## OKR 映射和方向判断

- O5：约 `85%`，仍是最低 Objective，但缺真实 external production evidence。方向为 `暂停` support-only；本轮不做 O5。
- O3/O1：方向为 `继续`。本轮聚焦 strict no-motion `/map_server` transition callback probe，服务 O1 current same-run path generation 缺口前置条件。
- O6/O7：方向为 `暂停等待材料`。没有新的 route execution、delivery/operator 或 production readback。
- 本轮不调整 OKR 百分比，不归档 KR。

## Problem Statement

当前 true-board proof 已证明 map_server 能进入加载 map yaml/PGM 的路径，但 lifecycle manager 在 valid map readback 后仍无法让 `/map_server` 成为 active。上一轮 canonical classification 是 `map_server_activate_callback_failed`。

如果本轮只继续输出相同 `map_server_activate_callback_failed`，没有 callback return、service response、bond/RPC timing 或 process/log 子原因，就会连续消费同一 blocker。需要 `robot-software-engineer` 在 strict no-motion 条件下把失败点下钻到可执行层，或修复到 `/map_server` lifecycle clean/active。

## 非目标

- 不执行 NavigateToPose。
- 不发布 `/cmd_vel`。
- 不调用 `/api/base/manual`。
- 不打开 WAVE ROVER UART。
- 不改硬件配置。
- 不做 O5 support-only readiness/surface/review/handoff/intake。
- 不把 `/scan`、AMCL、TF 或 planner timeout 作为本轮 primary success。
- 不把 `map_server_activate_callback_failed` 原样重复当作 accepted result。

## 范围

本轮范围：

- strict no-motion map_server lifecycle transition callback/service/bond/RPC timing proof。
- configure/activate callback return path、lifecycle `ChangeState` request/response、service timeout、bond timeout、RPC timing、process exit/status、runtime log window 采集。
- 必要时修复 launch 参数、lifecycle manager timing、managed node list、namespace/name 或 map_server 参数。
- local fail-closed dry-run、targeted unittest、true-board artifact。
- 实施文档同步到 navigation docs 和 sprint `tech-done.md`。

范围外：

- route execution、delivery/operator acceptance、HIL、safe-to-control。
- O7 UI/API、O6 archive、O5 production cloud。
- WAVE ROVER、ESP32、UART、LiDAR serial wiring 或硬件配置。

## KR 拆解、更新或历史归档

本轮不完成 KR。目标证据只用于 O3/O1 supporting chain：

- `/map_server` lifecycle clean/active，或比 `map_server_activate_callback_failed` 更窄的 callback/service/bond/RPC timing failure。
- Artifact 记录 transition request/response、callback return path、service/bond timing、process status、log window、final lifecycle state。
- strict no-motion 字段全部保持 false。

已完成 KR 历史记录位置：无新增。本轮完成后只在 sprint closeout 和必要的 OKR note 中记录 supporting evidence。剩余风险是 active map_server 仍只是 path proof 的前置条件，不是路线执行或送达闭环。

## 本轮核心抓手

核心抓手是把 11-54 `Next run` 的 "inspect Nav2 map_server lifecycle transition callback/service/bond/RPC timing or map_server configure/activate return path" 做成可验收 implementation：

- 区分 configure callback failure、activate callback failure、lifecycle service response failure、lifecycle manager wait timeout、bond wait timeout、RPC timing failure 和 process exit。
- 能修则修到 `/map_server` lifecycle clean/active。
- 不能修则给出 canonical classification、证据字段和下一步 action。

## 验收口径

P0：

- true-board strict no-motion artifact 证明 `/map_server` lifecycle clean/active；或 recovery/activation 失败点比 `map_server_activate_callback_failed` 更窄且可执行下一步修复。
- artifact 明确包含 lifecycle transition request/response、configure/activate callback path、service/bond/RPC timing、process alive/exit、runtime log window 和 final lifecycle state。
- safety fields false：`safe_to_control=false`、`publishes_cmd_vel=false`、`calls_base_manual=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`uses_base_uart=false`。

P1：

- local strict no-motion dry-run fail-closed，不能产生 motion/control success。
- targeted unittest 覆盖 lifecycle clean、callback failure、service timeout、bond timeout、RPC timing failure、process exit 和 safety invariants。
- navigation docs 同步说明本轮 proof boundary。

不接受：

- 只把 `map_server_activate_callback_failed` 文案换名。
- 仍输出完全相同 `map_server_activate_callback_failed`，且没有更窄 callback/service/bond/RPC timing evidence。
- 把 `/scan`、AMCL、TF 或 planner timeout 当成本轮 primary result。
- 任何运动、底盘控制、WAVE ROVER UART 或 hardware config 改动。

## 对应责任 Engineer

- 主责：`robot-software-engineer`
- Product 验收：`product-okr-owner`
- Algorithm：等待 `/map_server` lifecycle clean/active 后接 `/map`、AMCL pose、dynamic `map->odom`、planner-only path gate。
- Hardware：仅在实施需要硬件事实时介入，并必须先读 `docs/vendor/VENDOR_INDEX.md`。

## 同一 Blocker 红线判断

- 09-54：`/map_server Node not found`。
- 10-54：`lifecycle_manager_failed_to_change_state_for_map_server`。
- 11-54：`map_server_activate_callback_failed after valid map readback`。
- 本轮允许继续，因为它不是泛化 lifecycle wrapper，而是专门下钻 callback/service/bond/RPC timing。
- 若本轮仍停在完全相同 `map_server_activate_callback_failed` 且没有更窄错误，下一轮必须 CEO 升级或切 Objective。

## 风险和证据链缺口

- 即使 `/map_server` active，也仍未证明 `/map` topic sample、AMCL pose freshness、dynamic `map->odom`、path generation、route execution 或 delivery。
- true-board access 失败会阻断本轮主要验收；本地 proof 只能作为 fail-closed software check。
- 如果需要硬件事实，必须停止本 sprint 的软件假设并按 AGENTS.md 读取 vendor 资料；本轮默认不触碰硬件配置。

## Sprint 文档

本 planning 阶段创建：

- `pre_start.md`
- `prd.md`
- `tech-plan.md`

实施和验收阶段还需要：

- `tech-done.md`
- `side2side_check.md`
- `final.md`

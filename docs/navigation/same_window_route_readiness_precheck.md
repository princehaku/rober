# Same-Window Route Readiness Precheck

本文定义 `sprints/2026.07.21_01-28_o3_o1_nav2_readiness_repair_bounded_mission/` 使用的 O10 严格 no-motion readiness 合同。历史 precheck 只证明软件侧 blocker 清单；本轮把门禁收紧为一个 current natural-final 内可复算的九门结果，但仍不执行导航或底盘控制。

## 运行所有权与安全边界

- O11 持有当前 LiDAR lifecycle。O10 使用 managed runtime 时必须显式传入 `--reuse-existing-lidar-lifecycle`，只复用当前 ROS graph，不启动第二个串口驱动，也不清理 O11 的进程组。
- `/initialpose` 只有同时传入 `--initialpose-opt-in` 与 `--initialpose-canonical-free-cell-opt-in` 时才允许发布，并且最多一次、零重试。坐标必须来自当前 canonical map 可复算 free cell。
- O10 只允许调用 `ComputePathToPose` 生成 planner-only path；可以读取 `FollowPath` action 是否存在来证明 controller readiness，但不得创建或发送 FollowPath/NavigateToPose goal。
- 全程保持 `publishes_cmd_vel=false`、`calls_base_manual=false`、`uses_base_uart=false`、`robot_control_executed=false`、`route_execution_success=false`、`delivery_success=false`、`hil_pass=false`、`safe_to_control=false`。

## Current natural-final 合同

`proof.current_natural_final_readiness` 使用 schema `trashbot.o10.current_natural_final_readiness.v1`。只有以下 natural-final 条件和九门全部为真时，`proof.READINESS_GO` 才能为 `true`：

- `artifact_kind=final`
- `last_phase=final`
- `current_command=null`
- `generated_at_ms >= started_at_ms`

九门固定为：

1. `map`：map_server active；canonical YAML/image 审计干净；current transient-local `/map` 已接收且处于本轮窗口；frame 为 `map`；宽高、分辨率、origin、数据长度和 OccupancyGrid 内容 hash 与 canonical map 一致。
2. `amcl`：AMCL active；current pose 门通过；AMCL 当前订阅 `/scan`。
3. `planner`：planner_server active；当前 interface inventory 中存在 lifecycle service 和 `ComputePathToPose` action。
4. `controller`：controller_server active；当前 interface inventory 中存在 lifecycle service 和 `FollowPath` action。这里只读接口，不调用 FollowPath。
5. `current_pose`：current `/amcl_pose` sample 已接收；header stamp 可解析，stamp 与 receipt 在 natural-final 时仍 fresh；frame 为 `map`；6x6 covariance 为有限、非负且位置/偏航对角项不全为零。
6. `persisted_pose`：来源是 current runtime persisted AMCL 参数，或 canonical free-cell 单次 `/initialpose`；来源时间、地图身份、pre/post 顺序均可审计；不存在 current/reference conflict；live 输出确实晚于来源并消费该状态。
7. `dynamic_tf`：`map->odom` 必须是 fresh dynamic TF 且唯一归因 AMCL；`odom->base_link` 必须是 fresh dynamic TF；两条 edge 的 callback receipt 同窗，且在 natural-final 时仍 fresh，并可组成 `map->base_link`。static、stale 或多 publisher 一律 NO-GO。
8. `planner_only_path`：固定 `task_id`、`route_intent_id` 与固定目标必须完全一致；`ComputePathToPose` 返回 map-frame 非空 path，result receipt 与 path header stamp 在 natural-final 时仍 fresh；不得调用 NavigateToPose/FollowPath。
9. `obstacle_clear`：复用本轮 `/scan` 门的同一个 `sample_id`；publisher 必须恰好一个，stamp 与 callback receipt 在 natural-final 时仍 fresh，存在有限正数距离；最小距离必须 `>= 0.45m`。

原始 `/scan` 证据是 `amcl` 和 `obstacle_clear` 的共同输入，不另算第十门。任一字段 missing、stale、conflict、static、ambiguous 或阈值不足都会产生稳定的 `blockers`，并保持 `READINESS_GO=false`。

## 固定 planner-only 请求

本轮请求身份不可由 helper 自适应：

- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- goal：`frame_id=map, x=0.8, y=0.25, yaw=0.0`

如果固定目标越出 current map bounds，helper 必须在 action 前失败并记录 `path_generation_blocked_by_fixed_goal_out_of_map_bounds`；禁止把目标夹到地图内制造 success-shaped path artifact。

## Current evidence 字段

- `/scan` current sample：`ranges_count`、`finite_positive_count`、`invalid_count`、`min_distance_m`、`ranges_sha256`、`sample_id`、header stamp、receipt 与 endpoint inventory。
- `/map` current sample：frame、receipt、width、height、resolution、origin、data_count、`occupancy_data_sha256`。
- `/amcl_pose` current sample：frame、pose、6x6 covariance、header stamp、receipt。
- ROS graph：actions 与 services 当前 inventory，用于 planner/controller lifecycle 和 action readiness 判定。
- TF：source class、freshness、publisher attribution 与 current chain。
- planner result：固定 request identity、action name、path frame、point count、result receipt。

这些字段都必须来自同一个 O10 natural-final，不允许把历史 readback、旧 artifact、partial closeout 或 reference snapshot 拼成 GO。

## Nav2 参数边界

local costmap 的 obstacle layer 必须消费 current `/scan`：

- `observation_persistence: 0.0`，不让历史障碍观测继续伪装 current clearance。
- `expected_update_rate: 10.0`（Hz），让 scan 断流可被诊断；该值不是 0.10Hz 的十秒容忍窗口。
- `use_collision_detection: true`，平滑器不得绕过碰撞检查。

参数只提高软件门禁，不证明真实环境已清障，也不授予发车权限。

## 结果解释

- `READINESS_GO=true` 只表示当前 no-motion readiness 九门 9/9；它不是 route execution、HIL、delivery 或 safe-to-control 证据。
- `READINESS_GO=false` 时应直接消费 `current_natural_final_readiness.blockers` 修复当前 blocker，不得引用旧 artifact 抵消红门。
- partial、exception 或超时 artifact 必须保持 fail-closed；没有 natural final 时不能沿用先前的 GO。

只有后续独立获得明确 bounded-motion 授权并进入受控执行阶段，才可把本合同作为发车前置输入；本合同本身不扩大任何运动权限。
# Current bounded mission Phase 0 NO-GO contract

`o11_nav2_goal_execution_proof.py` 提供 `build_phase0_no_go_manifest`，用于在严格只读准入未全绿时冻结
`trashbot.o6_o7.current_bounded_mission_attempt.v1`。该产物显式固定 pre-stop、NavigateToPose、post-stop、
UART、service mutation、manual、`/cmd_vel`、`/initialpose`、retry 与 second-goal 计数为 `0`，并保留
`authorization_state=unconsumed_phase0_no_go`。历史 goal、命令日志或 T=1001 反馈不得补成 current evidence；
失败后不得改用另一 wrapper 重跑 Phase 0。

## Corrected Phase 0 compatibility gate

`build_corrected_phase0_no_go_manifest` 使用
`trashbot.o6_o7.corrected_current_bounded_mission_attempt.v1`，补齐
`remote_write_count`、`deploy_count` 与全部动作/危险面计数。corrected 探针必须 source
ROS 2 Humble 与 onboard setup，并使用 current listener 证明的 Upper `8787`；systemd unit inactive
本身不是红门，只有唯一 PID/listener/health/routes/current-task ownership 的组合不兼容才红。

local/remote SHA 不一致时不得部署或覆盖远端文件。准入只能通过远端 current source route
registration 与 GET/OPTIONS capability 读回逐项证明；其中 `/api/base/stop` 必须仍是 stop-only
合同。`uart_open_count=0`、`uart_write_count=0` 只统计本轮 agent 或新进程直接抢占/打开/写
`/dev/ttyS5`，不把已授权 pre/post-stop 通过现有 Upper stop-only 合同的内部 ROS/serial 零命令
误算为 direct UART。Phase 0 只读证明 endpoint，不调用它；GO 后 pre/post-stop 各独立计 `1`。

corrected Phase 0 允许一次 `ComputePathToPose` planner-only 计算；它不计
`navigate_to_pose_invocation_count`。任一 current map/scan/pose/dynamic TF、planner/controller、
planner-only path、obstacle、NavigateToPose action、current task/goal、stop 或 feedback readback 门不绿，
必须保持授权 `unconsumed_phase0_no_go`，pre-stop/user receipt/goal/post-stop 全为 `0`，且不得重跑。

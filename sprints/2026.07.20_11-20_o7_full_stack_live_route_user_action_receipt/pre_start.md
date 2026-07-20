# O7 Full-stack live route 用户动作回执 - Pre-start

## Sprint metadata

- `sprint_type: epic`
- `ROUTE=O7_FULL_STACK_LIVE_ROUTE_USER_ACTION_RECEIPT`
- Sprint 路径：`sprints/2026.07.20_11-20_o7_full_stack_live_route_user_action_receipt/`
- Product owner：`product-okr-owner`
- 主责 owner：`full-stack-software-engineer`
- 主推 Objective：O7（约 `93%`），联动 O6（约 `93%`）与 O1（约 `94%`）
- 当前 Proof boundary：`planning_only_o7_full_stack_live_route_user_action_receipt`
- 目标 Proof boundary：`live_upper_computer_o7_route_user_action_receipt_attempt_only`

## 用户价值与产品北极星

用户需要的不是另一份 readiness、handoff、browser smoke 或 wrapper，而是一次由用户触点发起、能绑定既有
`task_id`/route lineage、能从真实上位机得到 terminal/readback、并且随时可 stop 的动作回执。产品北极星仍是
“用户下发任务 -> 小车执行 -> 用户看见结果”；本 sprint 先把“用户下发动作”从本地 fixture 提升为真实上位机
fixed proxy receipt，不把一次动作尝试自动外推为送达成功。

## Blocker-aware 路由与方向判断

1. O5 约 `85%` 是最低 Objective，但 production/provider runtime blocker 已消费 `2/2`；本轮暂停 O5，不再做
   CDN/TLS、provider preflight、review decision 或本地 cloud wrapper。
2. Algorithm bounded-route 与 Hardware pre-gate 已在业务文件/命令前多次 runtime stall；本轮禁止再派这两个
   owner 的 wrapper/fallback/canary，也不重开 localization-bag Phase A。
3. Full-stack 是不同、尚未在本轮 runtime blocker 中消费的业务 owner。仓库已有核心 live endpoint：
   `POST /api/robot-control/nav2/goal/execute?baseUrl=http://192.168.1.11:8787`，它固定转发真实上位机
   `POST /api/nav2/goal/execute`；现有测试和产品文档记录过 `execution_forwarded` 真实链路事实。
4. 因此 O7 方向为“继续，但调整执行入口”：不等待 Algorithm/Hardware 新 helper，直接由 Full-stack 在既有核心
   endpoint 增加 same-task 用户动作 receipt，并执行 exactly one live/fail-closed action。O6/O1 只接受同一回执的
   supporting evidence；Mission Objective 0 在真实动作发生前仍暂停。

## 本轮核心抓手

复用既有 28-pose route identity，不新造路线、不新增 endpoint：

- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `run_id=run_o7_full_stack_live_route_user_action_20260720_01`
- `action_id=action_o7_live_nav_20260720_01`
- `authorization_ref=ceo_20260720_bounded_motion_operator_watch_route_clear_v1`
- fixed goal：`map (0.8, 0.25, yaw=0)`；route preview `28/28`，first pose `(0.0761511531, 0.25)`。

Full-stack 先让既有 execute response 在 forwarded、rejected、failed 三条路径都保留上述 identity 与
`user_action_receipt`，随后只调用一次真实 workstation execute endpoint。Live 不可达、preflight fail、timeout、
schema drift 或危险 true field 都必须产生 fail-closed receipt，不得切换到 mock 后再宣称 live。

## CEO 授权、安全边界与 stop rule

本轮 CEO 已明确：小车运动授权、物理位置受限、operator 看护、路线清空。该授权只允许上述 fixed goal 的一次
workstation 用户动作；不允许第二个 goal、重试、manual/free-roam、直接 `/cmd_vel`、`/initialpose`、direct UART
或扩大坐标范围。

`stop rule`：execute 请求只准 invocation count=`1`；请求返回、超时、连接中断、响应不可解析或 operator 要求停止后，
必须通过既有 `POST /api/robot-control/base/stop` 最多调用一次并保存 stop receipt，然后清理本地 API 进程。任何失败均
`no retry`。若动作未 forwarded，仍可接受为 fail-closed 用户动作 receipt，但不得声明
`robot_control_executed=true`、`route_execution_success=true`、`hil_pass=true`、`safe_to_control=true` 或
`delivery_success=true`。

## Owner、优先级与预期验收

- P0 / `full-stack-software-engineer`：扩展既有 execute contract、测试 fail-closed matrix、运行 workstation 全量验收、
  发起 exactly one live action、保存 action/terminal/stop readback，并更新 `tech-done.md`。
- P1 / `product-okr-owner`：只在 Engineer 回传后验收 receipt lineage、live invocation count、stop、真实终态和 proof
  boundary；再决定是否更新 `side2side_check.md`、`final.md`、`OKR.md` 与 progress log。
- 不派 Algorithm/Hardware；不修改 ROS2、Nav2 helper、UART、硬件配置或旧 sprint。

最低可接受结果是一个真实 workstation 用户动作 receipt：即使 upper computer 拒绝或超时，也必须有明确失败原因、
`user_action_delta` 判定和 stop 结果。只有 upstream 明确返回 succeeded、同窗口 route/readback 与 stop clean 时，Product
才可评估 O7/O6/O1 credit；receipt 本身绝不等于 delivery 或 HIL。

## 后续留档条件

本文件只启动 Epic。Engineer 完成后必须创建/更新 `tech-done.md`，记录实际改动、完整命令、live invocation count、
action receipt、terminal/readback、stop receipt、失败定位与风险。Product 仅在真实验收后创建
`side2side_check.md` 与 `final.md`；只有出现可接受业务 delta 时才更新 `OKR.md` 和
`docs/process/okr_progress_log.md`。本阶段不得预写后三份完成文档，也不得归档 KR。

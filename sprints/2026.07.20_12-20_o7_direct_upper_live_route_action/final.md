# O7 Direct Upper Live Route Action - Final

## Sprint metadata

- `sprint_type: epic`
- Sprint：`sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/`
- Product owner：`product-okr-owner`
- Implementation owner：`full-stack-software-engineer`
- Final status：`accepted_read_only_pre_gate_no_go_no_okr_credit`
- Proof boundary：`direct_upper_current_read_only_pre_gate_blocked_nav2_lifecycle_not_running`
- `pre_gate_pass=false`
- execute invocation=`0`
- stop invocation=`0`
- `no.retry=true`

## Product acceptance decision

Product 接受 Full-stack 真实到达上位机本机 8787、固化 current status/latest、执行保守 pre-gate 和完整回归；拒绝把 health/SSH/readback 当 route action。Current gate 明确不安全且不 ready，因此 execute 与 stop 均保持 `0` 是正确产品行为。

本 sprint 的北极星原本是一次受控 fixed-route action；实际只到达 action 前的 guardrail，没有进入 mission attempt。用户得到的是可信 no-go 原因，不是发车、到点、停止或送达结果。

## 实际交付与证据

- 使用新 identity 绑定既有 28-pose task/route lineage，request 固定 `confirm_navigation_execution=true`，但 request 未发送。
- SSH 内 remote curl 对 `/health`、`/api/health`、`/api/status`、`/api/nav2/goal/execution/latest` 取得真实 JSON。
- `pre_gate_decision.json` 与 `live_sequence_invocation_manifest.json` 如实记录 current runtime、read invocation、no-go、零动作和 no retry。
- 未生成 execute/stop/post-readback raw，因为对应 invocation 为 `0`；没有 synthetic/mock 补件。
- 未修改 product code、test、ROS2、hardware/vendor 或 runtime configuration。

## Current blocker 与历史证据冲突

Current upper status 明确显示：

1. `nav2_lifecycle_not_running`，lifecycle stopped；
2. planner/controller inactive；
3. localization not ready，`map_to_odom=false`、`map_to_base_link=false`；
4. path generation 未尝试、未生成；
5. `lidar_min_distance_m=0.03500000014901161`，`obstacle_clear=false/not_proven`。

因此 `explicit_unsafe_blocker_present=true`、`pre_gate_pass=false`。Operator 的路线清空声明不能覆盖 current LiDAR 反证。

Nav2 latest 内嵌的旧 `goal_succeeded/robot_control_executed=true` 比 current response 老 `1414019199ms`，约 16.4 天，且明确 `current_for_this_action_window=false`。它既不能放宽 gate，也不能计为本轮 user action、control、route 或 HIL。

## 验证结果

- `action_identity.json`、`direct_upper_request.json`、`pre_gate_decision.json`、manifest：`json.tool` exit `0`。
- 完整结构断言：exit `0`，输出 `o7_direct_upper_live_route_action_structure_ok`。
- Workstation targeted：`Test Files 1 passed (1)`、`5 passed | 254 skipped`。
- Workstation full：`Test Files 4 passed (4)`、`532 passed`。
- Build：exit `0`，`34 modules transformed`、`built in 1.91s`，仅既有 chunk warning。
- Lint：exit `0`，无 diagnostics。
- Engineer scoped diff：通过；范围外测试生成副作用已恢复，最终无范围外 diff。

Product 未重跑工程 regression；本阶段复用 Engineer artifact，并执行 closeout 文档、OKR、progress log 的结构与 diff 验收。

## OKR、Mission、KR 收口

- O5：约 `85%`，继续暂停 provider/runtime blocker `2/2`，本轮未触达。
- O6：约 `93%`，没有 current action/result，保持 flat。
- O7：约 `93%`，仅新增真实 upper read-only no-go artifact，保持 flat。
- O1：约 `94%`，无 stop/wheel/HIL/safe evidence，保持 flat。
- `current_run_artifact_delta=true`：仅限 fresh read-only no-go evidence。
- `external_artifact_delta=false`
- `user_action_delta=false`
- `live_control_delta=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `nav2_goal_execution_proven=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`
- 主百分比：不调整
- KR：`不归档`
- 历史区：无新增记录；完成条件、证据、验收与剩余风险均未达到 KR 迁移门槛。

## 方向判断

- O7/O6：`暂停 action 重跑`。本 action window 已封存，不能继续消费 health/wrapper/readback。
- O1/O3 readiness：`调整为下一前置`，但只能由 Algorithm/Robot owner 在新 strict no-motion window 恢复 lifecycle/localization/path；Product 不在本 closeout 派发或执行。
- O5：`继续暂停`，provider blocker 已达 2/2。
- Mission Objective 0：仍未满足；本轮方向靠近 mission guardrail，但没有进入 mission attempt。

## 剩余风险与下一轮唯一入口

剩余风险是 current Nav2 runtime、定位 TF、path 与 obstacle-clear 均未 ready；旧 success artifact 还可能被误读为 current；本轮没有 stop feedback、wheel L/R、HIL、delivery/operator acceptance 或 safe-to-control。

禁止在本 sprint 重跑 execute/stop，也禁止再开 health、wrapper、summary 或回执包装。唯一入口是：Algorithm/Robot owner 在新的 no-motion readiness window 证明 lifecycle running、planner/controller active、localization/TF clean、current path generated；operator 重新摆位/清场并获得 clean obstacle-clear readback；随后 CEO 给出新的 fresh bounded-motion authorization。三项缺一不可。

本 Product closeout 不计 business worker recovery，也不授权 Algorithm/Hardware 或任何 motion action。

# O7 Direct Upper Live Route Action - Side-by-side Check

## Sprint metadata

- `sprint_type: epic`
- Product status：`accepted_fresh_read_only_no_go_evidence_no_mission_credit`
- Product owner：`product-okr-owner`
- Implementation owner：`full-stack-software-engineer`
- Proof boundary：`direct_upper_current_read_only_pre_gate_blocked_nav2_lifecycle_not_running`
- Gate result：`pre_gate_pass=false`
- Action result：execute invocation=`0`、stop invocation=`0`、`no.retry=true`

## Product acceptance verdict

Product 接受本轮为真实上位机 current read-only no-go evidence：SSH 内 `127.0.0.1:8787` 的 health、status 与 Nav2 latest 均返回可解析 JSON，证明上一轮 7072 handler 前拦截已被绕开；但 current runtime 明确不满足运动 pre-gate，所以拒绝用户动作、live control、route execution、HIL、delivery、safe-to-control、Mission Objective 0 和 OKR credit。

本轮用户价值是把“网络是否可达”收敛成“为什么现在不能发车”的 current 事实，并在传感器与 runtime 反证存在时诚实不发车。它不是一次 route attempt，也不是完成送达闭环。

## Side-by-side 核对

| 验收项 | 计划口径 | 实际证据 | Product 裁决 |
| --- | --- | --- | --- |
| 非 loopback-interceptor transport | SSH 内 remote curl 访问 upper `127.0.0.1:8787` | `/health`、`/api/health`、`/api/status`、Nav2 latest 均 SSH/curl exit `0`、HTTP `200`、JSON parse ok | 接受真实 upper read-only transport；不计业务结果 |
| Current runtime attribution | status/latest 必须可归因 current upper | current status response fresh；Nav2 lifecycle `running=false/state=stopped`，proof state `blocked_with_root_cause` | 接受 current no-go blocker |
| Route readiness | lifecycle、planner/controller、localization/TF/path、obstacle-clear 必须 clean | `nav2_lifecycle_not_running`；planner/controller inactive；localization false；`map_to_odom=false`、`map_to_base_link=false`；path 未尝试/未生成 | 拒绝 execute gate |
| 障碍条件 | operator 清场声明还须由 current readback 支持 | `lidar_min_distance_m=0.03500000014901161`，`obstacle_clear=false/not_proven` | 现场声明不能覆盖传感器反证；拒绝 execute gate |
| Pre-gate decision | 任一 unsafe/unknown 必须 fail closed | `explicit_unsafe_blocker_present=true`、`pre_gate_pass=false`、`decision=no_go_fail_closed` | 接受 fail-closed |
| Exactly-one action | 仅 pre-gate pass 后 execute 一次 | execute invocation=`0`，upper handler 未接收本 action | 接受未发车；`user_action_delta=false` |
| Stop rule | execute 后最多一次 stop；无 execute 不发 stop | stop invocation=`0`，`no.retry=true` | 接受；不宣称 stop 已执行或底盘已停 |
| Historical latest | 旧结果不能放宽 current gate | nested `goal_succeeded` 比 current response 老 `1414019199ms`，`current_for_this_action_window=false` | 完全排除本轮计分 |
| 禁止动作 | manual/free-roam/keyboard/cmd_vel/initialpose/UART/delivery/mock 均为 0 | manifest 对应 invocation count 全为 `0`，mock fallback=`0` | 接受安全边界 |
| Artifact 结构 | identity/request/decision/manifest 可解析且结构断言通过 | 四个 JSON `json.tool` exit `0`；`o7_direct_upper_live_route_action_structure_ok` | 接受 |
| Workstation regression | targeted/full/build/lint 不漂移 | targeted `5 passed`；full `532 passed`；build `34 modules`；lint clean | 接受；不等于 live acceptance |
| 文件范围 | run-only artifacts + tech-done；无产品代码 | 无 product/test/ROS2/hardware/vendor/runtime config diff | 接受 |

## Proof、Mission 与 delta 裁决

- `current_run_artifact_delta=true`：仅表示本轮形成 fresh upper read-only status/latest 与 no-go decision。
- `external_artifact_delta=false`：真实 upper readback 仍只是 gate artifact，没有 action/mission result。
- `user_action_delta=false`：execute=`0`。
- `live_control_delta=false`：没有 current control action。
- `robot_control_executed=false`
- `route_execution_success=false`
- `nav2_goal_execution_proven=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

旧 nested result 的 `goal_succeeded/robot_control_executed=true` 属于历史窗口，不能覆盖上述 current-run false 裁决。

## OKR、KR 与历史区

- O5：保持约 `85%`，provider blocker 已消费 `2/2`，继续暂停，不开第三轮 wrapper。
- O6：保持约 `93%`，没有同 task action/result 可归档。
- O7：保持约 `93%`，接受真实 read-only no-go 解释，但没有用户动作或 route terminal。
- O1：保持约 `94%`，无 stop、wheel feedback、current HIL 或 safe-to-control 证据。
- 主百分比：全部 flat，不调整。
- KR：`不归档`。
- 历史区：无新增完成、取消、替换或过期 KR；本 sprint 只在 `final.md`、`OKR.md` flat note 与 progress log 留下 no-go 事实和剩余风险。

## 责任边界与下一轮唯一入口

本 Product closeout 只是验收与记录，不是 Algorithm/Robot business worker recovery，也不授权任何 runtime 修改或运动。当前 action window 以 no-go 收口，禁止在本 sprint 重跑 execute/stop，也禁止再开 health、status、summary 或 wrapper sprint。

下一步只能由 Algorithm/Robot owner 在新的 strict no-motion readiness window 中消除并证明以下 current blockers：Nav2 lifecycle running、planner/controller active、localization 与 `map->odom`/`map->base_link` clean、path current generated。现场 operator 还必须重新摆位/清场，并让 current obstacle-clear readback clean。上述条件全部形成新证据后，CEO 再给 fresh bounded-motion authorization，才可新开 action window。

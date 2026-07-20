# O7 Direct Upper Live Route Action - Tech Done

## Sprint metadata

- `sprint_type: epic`
- 状态：`blocked_at_read_only_pre_gate_no_motion_post_invoked`
- 唯一主责：`full-stack-software-engineer`
- Sprint：`sprints/2026.07.20_12-20_o7_direct_upper_live_route_action/`
- Proof boundary：`direct_upper_current_read_only_pre_gate_blocked_nav2_lifecycle_not_running`
- 最终动作约束：`no.retry=true`；execute invocation=`0`；stop invocation=`0`

## 用户旅程变化和触点收益

本轮已从开发机 loopback 隔离问题前移到真实上位机本机 API：通过
`ssh root@192.168.1.11 -p 37878` 在远端访问 `127.0.0.1:8787`，health、status 与 Nav2 latest
均拿到真实 JSON。用户现在能得到明确的“不发车”解释，而不是把网络可达误当成路线 ready：当前上位机明确报告 Nav2
lifecycle stopped、planner/controller inactive、定位/TF/path 未 ready，并且传感器摘要没有证明障碍清空。

由于 pre-gate fail closed，本轮没有向用户制造“已开始”或“已停止”的虚假回执。fresh motion authorization 没有被动作
endpoint 消费；本 sprint 也没有通过换 goal、mode、endpoint、mock 或 product code 来绕过 gate。

## 实际改动文件

仅创建/修改本 sprint 允许范围：

- `tech-done.md`
- `artifacts/full-stack/action_identity.json`
- `artifacts/full-stack/direct_upper_request.json`
- `artifacts/full-stack/stop_request.json`
- `artifacts/full-stack/pre_gate_health_compat.raw`
- `artifacts/full-stack/pre_gate_api_health.raw`
- `artifacts/full-stack/pre_gate_status.raw`
- `artifacts/full-stack/pre_gate_nav2_latest.raw`
- `artifacts/full-stack/pre_gate_decision.json`
- `artifacts/full-stack/live_sequence_invocation_manifest.json`
- `artifacts/full-stack/json_assertion_result.txt`
- `artifacts/full-stack/workstation_regression.txt`

未创建 `direct_execute_response.raw`、`direct_stop_response.raw`、`post_nav2_latest.raw` 或
`post_base_feedback_latest.raw`，因为对应 endpoint invocation 均为 `0`；不以 synthetic body 伪造未发生的 raw response。

全量 workstation 测试生成器曾只刷新两个范围外历史 DOM smoke artifact 的 `checked_at`。这两个文件在本轮开始时 clean，
已用精确 `apply_patch` 恢复为 HEAD 原值，最终不保留范围外 diff。没有修改 planning docs、OKR、progress log、产品代码、
测试、ROS2、硬件/vendor 或上位机/runtime 配置。

## 冻结 identity 与 request

- `task_id=task_o3_28_pose_fixed_route_consumer_20260713_0402`
- `run_id=run_o7_direct_upper_live_route_20260720_02`
- `route_intent_id=route_intent_20260713_0402_from_20260713_0300_28_pose_structured_path`
- `action_id=action_o7_direct_upper_nav_20260720_02`
- `authorization_ref=ceo_20260720_1220_bounded_motion_operator_watch_route_clear_v2`
- identity SHA256：`9af41bfd43d99e8d47c6c91e69e5176ce2288b8a3824da9d67bf2bf9fae25f54`
- request SHA256：`9cfc75dee43e4c0b7b2fd556c2dc1d2774fff8fa740a11b996fc501164027e27`
- request 明确 `confirm_navigation_execution=true`、`base_command_mode=ros`、goal `(0.8, 0.25, 0.0)`、route counts `28/28`。

三个冻结 JSON 均先于 remote probe 落盘；`motion_post_invocation_count_before_gate=0`。

## Remote read/action/stop/readback 结果

| 阶段 | endpoint | invocation count | SSH exit | curl exit | HTTP | JSON parse | artifact |
|---|---|---:|---:|---:|---:|---|---|
| pre-gate compatibility health | `GET /health` | 1 | 0 | 0 | 200 | ok | `pre_gate_health_compat.raw` |
| pre-gate canonical health | `GET /api/health` | 1 | 0 | 0 | 200 | ok | `pre_gate_api_health.raw` |
| pre-gate status | `GET /api/status` | 2 | 0 | 0 | 200 | ok on saved response | `pre_gate_status.raw` |
| pre-gate Nav2 latest | `GET /api/nav2/goal/execution/latest` | 1 | 0 | 0 | 200 | ok | `pre_gate_nav2_latest.raw` |
| direct execute | `POST /api/nav2/goal/execute` | 0 | n/a | n/a | n/a | not invoked: pre-gate failed | absent |
| direct stop | `POST /api/base/stop` | 0 | n/a | n/a | n/a | not invoked without execute | absent |
| post Nav2 latest | `GET /api/nav2/goal/execution/latest` | 0 | n/a | n/a | n/a | not invoked without execute | absent |
| post base feedback latest | `GET /api/base/feedback-samples/latest` | 0 | n/a | n/a | n/a | not invoked without execute | absent |

`/api/status` 首次真实响应约 149KB，工具显示层在 artifact 写入前截断，因此只补做一次 read-only capture；第二次
HTTP `200` / curl `0`，完整 `149281 bytes` body 已保存且 JSON parse ok。该额外 read 不是 action retry，manifest
如实记录 status invocation count=`2` 与首轮 capture failure，未隐藏或覆盖失败。

## Pre-gate decision

`pre_gate_decision.json` 最终为：

- `operator_watch=true`、`route_clear=true`、`physical_position_bounded=true`；
- 两个 health route 均为 schema `trashbot.upper_robot_api.v1.health`、status `ready`；
- `existing_motion_active=false`：current status/readback 均未显示正在发布 motion，free-roam 也为 external stop requested；
- `explicit_unsafe_blocker_present=true`；
- `pre_gate_pass=false`、`decision=no_go_fail_closed`。

决定 no-go 的 current upper facts：

1. Nav2 `status/proof_state=blocked_with_root_cause`，`blocked_reasons=[nav2_lifecycle_not_running]`，lifecycle
   `running=false/state=stopped`；
2. `planner_server_active=false`、`controller_server_active=false`；
3. `localization_ready=false`，`map_to_odom=false`、`map_to_base_link=false`；
4. `path_generation_attempted=false`、`path_generated=false`；
5. current free-roam sensor summary 为 `lidar_min_distance_m=0.03500000014901161`，`obstacle_clear=not_proven`。

pre-gate Nav2 latest endpoint 当前响应生成时间为 `1784522062612`，但 nested latest execution 的
`generated_at_ms=1783108043413`，相差 `1414019199ms`，属于历史 readback，不是本 action window。其旧
`goal_succeeded/robot_control_executed=true` 不得用于放宽 current gate 或本轮计分。

## 接口与联调影响

- 真实联调 transport：SSH 内 remote curl；开发机没有直接访问自己的 `127.0.0.1:8787`。
- 上位机现有 endpoint/schema 未改；无 additive/破坏性接口变更。
- 没有调用 manual、free-roam、keyboard、direct `/cmd_vel`、`/initialpose`、UART 或 delivery complete。
- 已读 `docs/vendor/VENDOR_INDEX.md`；没有更改或推断 WAVE ROVER/UART/波特率/底盘配置。

## 验证结果

### JSON 与结构断言

- `python3 -m json.tool action_identity.json`：exit `0`。
- `python3 -m json.tool direct_upper_request.json`：exit `0`。
- `python3 -m json.tool pre_gate_decision.json`：exit `0`。
- `python3 -m json.tool live_sequence_invocation_manifest.json`：exit `0`。
- tech-plan 第 7 节完整 Python 断言：exit `0`，输出
  `o7_direct_upper_live_route_action_structure_ok`。

### Workstation regression

- targeted `npm run test -- test/catalog.test.ts -t "Nav2 goal execution"`：exit `0`；`1 passed`，
  `5 passed | 254 skipped`。
- full `npm run test`：exit `0`；`4 passed`，`532 passed`，duration `49.64s`。
- `npm run build`：exit `0`；`34 modules transformed`，`built in 1.91s`；仅有既存 `>500 kB` chunk warning。
- `npm run lint`：exit `0`；无 diagnostics。

## 首轮失败、根因、修复与复验

唯一采集失败是第一次 `/api/status` body 在工具显示层被截断，无法诚实落成完整 raw。根因不是上位机/API 失败：该请求
本身 SSH `0`、curl `0`、HTTP `200`；是约 149KB JSON 超过显示回传预算。修复只补做一次 read-only status capture，直接将
remote stdout 保存到允许的 `.raw`，没有 motion、副作用、mock 或产品代码修改。复验 JSON parse ok，SHA256 为
`0eb4dd603da6deced5479a73cbd19b65f59ad975c402f13fa2f2e61f2987f0f0`。

合同回归没有首轮失败。全量测试产生的两个范围外 `checked_at` 副作用已按测试前 clean/HEAD 内容精确恢复，最终范围外 diff
为零。

## Proof / delta 建议与不证明项

- `current_run_artifact_delta=true`：产生了新的真实上位机 current read-only pre-gate artifact 与明确 no-go decision。
- `external_artifact_delta=false`：虽来自真实 upper 8787，但仅为 read-only gate，未形成 action/mission delta。
- `user_action_delta=false`：execute 没有调用，upper handler 没有接收本 action。
- `live_control_delta=false`：本轮没有 current control action。
- `route_execution_success=false`、`nav2_goal_execution_proven=false`、`hil_pass=false`、
  `wheel_feedback_lr_nonzero_proven=false`、`delivery_success=false`。
- `okr_credit_allowed=false`；建议 O7/O6/O1 百分比保持 flat、KR `不归档`，最终由 Product acceptance 裁决。

本轮不证明当前路线执行、真实 robot motion、stop 已执行或反馈确认、同窗口 wheel L/R、HIL、safe-to-control、delivery/operator
acceptance 或 production cloud。health 200 只证明 transport/API ready，不证明 Nav2 route ready。

## 剩余风险与下一步配合

1. 当前 Nav2 lifecycle stopped，planner/controller/localization/TF/path gate 均不满足；需要 Robot/Algorithm owner 在新的非本动作
   窗口恢复并只读证明 current route readiness。
2. sensor summary 的 `0.035m` 最近障碍没有通过 obstacle-clear gate；现场 route clear 声明不能覆盖 current sensor 反证，需要
   operator 重新摆位/清场并由新 read-only gate 验证。
3. pre-gate latest nested execution 是历史结果；下一次不得把旧 `goal_succeeded` 当 current action evidence。
4. 本 sprint 以 no-go 收口。`no.retry=true`；最终 execute invocation count=`0`、stop invocation count=`0`；禁止在本 sprint
   追加 execute/stop 补证据。后续只有 Product/CEO 在 readiness blocker 被消除后开新的 action window 才可再次评估。

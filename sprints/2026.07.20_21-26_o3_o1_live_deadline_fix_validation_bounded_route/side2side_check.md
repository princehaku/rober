# O3/O1 Live Deadline Fix Validation + Bounded Route - Side-to-Side Check

## Sprint metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Product decision：`ACCEPT_NO_GO`
- `READINESS_GO=false`
- proof boundary：`current_live_deadline_validation_plus_start_transport_no_go_not_readiness_or_route`
- `okr_credit=false`
- KR：`不归档`

## 用户价值与北极星核对

北极星仍是普通用户把垃圾交给小车后，机器人可验证地沿固定路线送达并安全收口。本轮用户价值不是“车已能
送达”，而是同时得到两条可行动真相：absolute-deadline 修复已在真实板自然 final；当前 start transport 在
runtime 前损坏，安全门正确保持 NO-GO，没有用 HTTP `200`、旧路线材料或 fresh 运动授权越过 readiness。

## Side-to-side acceptance

| 对照项 | 冻结事实 | Product 判定 |
| --- | --- | --- |
| Phase 0 | remote SHA/py_compile/service/health clean，新 PID=`693117` | 接受 deployment gate |
| Phase A 调用纪律 | start/proof/latest/owned-stop=`1/1/1/1`，no retry | 接受 exactly-once 与封存 |
| Start transport | HTTP `200`、parse clean，但 `invalid_nav2_start_json`、remote invocation=`0` | 接受 NO-GO，拒绝 runtime start |
| Deadline | wrapper `77717ms`，final/final/null，absolute monotonic，无 timeout/partial/fallback | `DEADLINE_LIVE_VALIDATED=true` |
| Readiness | map/amcl/planner/controller、pose/persisted pose、TF/path/obstacle 未 ready | `READINESS_GO=false` |
| Phase B / motion | pre-stop/goal/post-stop=`0/0/0`，T1001/manual/cmd_vel/UART/delivery=`0` | 拒绝 route/HIL/user action/delivery |
| Cleanup | lifecycle stopped、PID null、owned residual=`0` | 接受 clean cleanup |
| Artifact 完整性 | wrapper raw 未完整持久化；canonical latest `343156` bytes 完整 | 接受 natural final，保留 transport unknown 风险 |

## 两个必须并存的事实

1. 上一 sprint 的 `parent_helper_monotonic_clock_origin_mismatch` 已被 current board natural-final 证据关闭。
   Algorithm frozen review=`ACCEPT_NO_GO`，并确认 `DEADLINE_LIVE_VALIDATED=true`。
2. Mission Objective 0 仍未达到。唯一 start 在 remote handler invocation 前失败，runtime/lifecycle 未启动，
   `READINESS_GO=false`，没有 route execution、HIL、user action 或 delivery。

文档新增 frozen request + `jq -c` + stdin 防 quoting 复发合同，只是下一轮执行约束，不是本轮 live transport
validation，也不能把 start semantic false 改写成成功。

## Blocker 与消费计数

- 新 root blocker：`phase_a_start_json_transport_corrupted_before_remote_handler`。
- 本轮消费：`1/2`。
- 该 blocker 不与已关闭的 absolute-deadline blocker混合，也不归类为 ROS readiness 或 hardware blocker。
- 当前授权已被 endpoint attempt 消费；即使 remote command invocation=`0`，也不得重试或复用授权。

## Delta 与 proof boundary

- `current_run_artifact_delta=true`：只对应 current live deadline validation 与 current safe NO-GO。
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `robot_control_executed=false`
- `route_execution_success=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

统一 proof boundary 为 `current_live_deadline_validation_plus_start_transport_no_go_not_readiness_or_route`。

## OKR / KR 对照

- O5：约 `85%`，provider/runtime blocker `2/2`，继续暂停，不第三次消费。
- O6/O7：各约 `93%`，无 current action/terminal/receipt，flat。
- O1：约 `94%`，无 Phase B、T1001 或 HIL，flat。
- O3：只新增 supporting live deadline 与 current NO-GO 事实，不单独计主分。
- 所有主百分比不调整；KR `不归档`，历史区无新增。

由 O5 切到 O3 readiness supporting + O1/O6/O7 bounded route 的方向仍成立，但当前在 start transport 前
fail closed，尚未构成 mission attempt。Product 结论为继续该 mission lane，但必须通过新的授权和修正后的 transport
入口，不得再开 deadline、wrapper、readback 或 docs-only sprint。

## 验证证据与 Product 执行边界

Engineer 留档：targeted `1`、Upper `119`（skip1）、O10 `170`、combined `289`（skip1），并记录
py_compile、JSON、SHA、required `rg` 和 scoped diff checks pass。Product 本阶段仅以 `python3 -m json.tool`
与只读 `jq` / `python3 -c` 交叉核对冻结 artifact；没有重跑工程测试、SSH、live endpoint 或 control。
Phase B execute=`0`，因此没有派 Hardware review；没有 user action receipt 上游，因此没有派 Full-stack。

## 下一轮唯一入口

1. 取得新的 fresh authorization；不得复用当前 authorization。
2. 复核 remote target SHA、service health 与 initial stopped/no-motion。
3. 冻结新 request，对 `frozen_requests.json` 做 parse/structure assertion。
4. 使用 `jq -c` 取单个 start body，经 stdin pipe 到远端 `curl --data-binary @-`；不得使用 inline JSON。
5. exactly-one Phase A；GO 才进入 Phase B，NO-GO 立即封存。

剩余风险是修正后的 stdin transport 尚未 live 验证、current readiness 全套仍 false、wrapper raw transport 完整性永久
unknown；它们均不得被 canonical latest、文档修正或历史路线材料替代。

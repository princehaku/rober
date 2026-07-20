# O3/O1 Current Readiness + Bounded Route - Final

## Sprint metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Final status：`accepted_current_no_go_cleanup_and_offline_deadline_fix_no_mission_credit`
- `READINESS_GO=false`
- proof boundary：`software_proof_plus_current_no_go_not_live_fix_validation`
- `PRODUCT_CLOSEOUT_COMPLETE=yes`
- `okr_credit=false`
- KR：`不归档`

## Product final decision

Product 接受唯一 current Phase A 的诚实 NO-GO、strict-no-motion 合同、owned cleanup、精确 root cause，以及 Robot/Algorithm 完成的 absolute monotonic deadline 离线端到端软件合同；拒绝 current localization/path readiness、route/user action、live control、HIL、delivery、safe-to-control、Mission success 和 OKR credit。

用户价值是两层事实被同时保留：现场没有因 fresh 运动授权而越过 readiness gate，NO-GO 后 lifecycle 安全停止；同时，`2026.07.20_17-23` 离线合同在本轮真实板暴露的 parent/helper clock-origin 缺口已被具体修复并回归。软件修复尚未在新 live window 验证，不能包装成 readiness success。

## Current Phase A 与 cleanup

- 唯一 live 调用：start/proof/latest/owned-stop=`1/1/1/1`。
- Start effective contract：strict-no-motion、base/lidar=`false/false`、new serial open=`0/0`。
- Proof parent elapsed=`80395ms`，process timeout=`80s`，只保留 partial/interrupted；没有 natural final。
- `initialpose_publish_attempts=0`；current pose/persisted pose、planner/controller、path final 与 obstacle clear 均未证明。
- Path requested=true，但 attempted/succeeded/generated=`false/false/false`，point count=`0`。
- `READINESS_GO=false`，因此 Phase B pre-base-stop/goal/post-base-stop=`0/0/0`，`T=1001=0`，`physical_motion=false`。
- Owned stop 后 lifecycle stopped、PID file absent、owned residual=`0`；没有第二次 live、第二次 stop 或 retry。

Product 接受 NO-GO 与 cleanup，不接受旧 artifact、历史 operator report、HTTP 200、partial TF inventory 或软件测试替代 current final readiness。

## Root cause 与实际工程改动

Algorithm 将现场 parent `80395ms` 与 helper start-to-SIGINT `76764ms` 对齐，确认 parent 比 helper-relative deadline 早约 `3631ms` 开始计时；这段 bash/source/Python startup 消耗使 4 秒 reserve 实际只剩约 `0.764s`。精确根因为 `parent_helper_monotonic_clock_origin_mismatch`，不是 package probe 顺序或简单加大 timeout。

Algorithm 已实现 `--outer-process-deadline-monotonic-s` consumer：使用同机 `time.monotonic()`，取 parent absolute 与 legacy relative deadline 的更早值，无效值 fail closed。Robot Software 已在 helper argv 构造和 `Popen` 前生成同一 absolute deadline，并让 parent `communicate()` 只消费 remaining；pre-Popen budget exhaustion 不启动子进程，post-Popen exhaustion 只清理 owned process group。HTTP schema、relative timeout 与旧调用兼容，预算没有扩大。

同步更新了 `field_route_evidence_preflight.md` 与 `fixed_route_workflow.md`，明确 absolute deadline、clock domain、fail-closed 和 no-live proof boundary；测试覆盖自然 final、no partial fallback/no signal、pre/post-Popen exhaustion 与 legacy compatibility。

## Engineer 验证与 Product 验收范围

- `py_compile`：exit `0`。
- Upper API：`Ran 119 tests ... OK (skipped=1)`。
- O10 helper：`Ran 170 tests ... OK`。
- 集成：`Ran 289 tests ... OK (skipped=1)`。
- JSON、required `rg`、scoped `git diff --check`：Engineer 记录均为 exit `0`。
- 中文注释：Robot `75/317=23.66%`；Algorithm integration audit `36/163=22.09%`，Algorithm 自身 final audit `38/168=22.619%`，均严格 `>20%`。

Product 只读检查 planning、`tech-done.md`、全部 Robot/Algorithm structure artifacts、工程 diff、docs/tests 变更；本阶段明确不跑工程测试、不跑 SSH/live/control。

## Proof boundary 与拒绝项

本轮 evidence ledger 固定为：

- `current_run_artifact_delta=true`，仅表示 current safe NO-GO 和 clean cleanup；
- `external_artifact_delta=false`
- `live_control_delta=false`
- `user_action_delta=false`
- `route_execution_success=false`
- `hil_pass=false`
- `delivery_success=false`
- `safe_to_control=false`
- `robot_control_executed=false`
- `mission_objective_0_satisfied=false`
- `okr_credit=false`

因此统一 proof boundary 为 `software_proof_plus_current_no_go_not_live_fix_validation`。它不证明 absolute-deadline 修复已在真实板自然 final，也不证明 current AMCL/TF/path、obstacle clear、route、user action、WAVE ROVER feedback、HIL、delivery 或 safe-to-control。

## OKR、KR 与方向判断

- O5：约 `85%`，provider/runtime blocker `2/2`，继续暂停且不第三次消费。
- O6/O7：各约 `93%`，没有 current action/terminal/receipt，flat。
- O1：约 `94%`，没有 Phase B stop/T1001/HIL，flat。
- O3：只新增 supporting current NO-GO 与 offline deadline software contract，不单独计主分。
- Mission Objective 0：继续 `blocked_before_attempt_on_current_localization_readiness`。
- 所有主百分比不调整，KR `不归档`，历史完成区无新增 KR。

从 O5 合法切换到 O3 readiness supporting + O1/O6/O7 bounded-route evidence 的方向仍成立，但本轮在 Phase A fail closed，未进入 mission attempt。不得因为 root cause 更清楚或 business worker 恢复而抬高完成度。

## Agent 恢复事实

Planning 阶段 Product worker 两次零文件 stall，不是 mission result；主节点按白名单补齐 planning。真实 business Robot/Algorithm worker随后已恢复，产出业务代码、测试、docs、结构 artifact 与验证结果。该事实只解除“业务 worker 未执行”的编排疑问，不解除 current readiness blocker，也不产生 route/HIL/OKR credit。

## 剩余风险与下一轮唯一建议

- Absolute deadline 只经过 fake-monotonic/offline end-to-end 验证；真实板 source、ROS CLI、filesystem atomic write 和调度仍可能在相同预算内触发其他 blocker。
- Current pose、persisted pose、formal TF freshness、planner/controller、path final 与 obstacle clear 仍未得到同一 final artifact。
- Phase B 没有执行，stop/T1001、route terminal、operator outcome、delivery 与 HIL 全部缺失。
- Proof refresh streamed body 没有独立 raw 副本；canonical latest 与 transport 摘要已保存，但不得为补副本重跑。

本 fresh 授权窗口已经消费，**不得重跑**。下一轮唯一入口是重新确认**新的 current operator/route/obstacle/readiness 条件**并取得**新的 fresh 授权**，部署已修复版本后 exactly once 执行新的 Phase A；只有新的 final artifact 明确 `READINESS_GO=true`，才可进入 Phase B。否则继续 NO-GO，Phase B invocation=`0`。

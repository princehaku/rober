# O3 Offline Runtime Budget Fix - Side2Side Check

## Product acceptance metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Product decision：`accept_offline_runtime_budget_contract_reject_live_readiness_and_okr_credit`
- proof boundary：`software_proof_o3_o10_offline_runtime_budget_contract_only`
- `okr_credit=false`
- KR：`不归档`

## 用户价值与产品北极星

用户获得的是一个可预测的 O10/API runtime budget 合同：helper 能在 Upper API 发出外层 timeout signal 前主动保护 final artifact 收口窗口，并把非关键 package inventory 收敛或跳过。它清除了上一轮 `80s` process budget 与 helper probe order 的确定性软件不相容，使未来新授权下的一次 current no-motion proof 不必再依赖 SIGINT/partial artifact 才能读到结论。

北极星仍是可信 current localization、planner-only path、受看护 route execution 和 delivery。当前交付仅是离线软件合同，不是现场 readiness、route 或 delivery 结果。

## 计划与最终事实 side-by-side

| 验收项 | 计划口径 | 最终事实 | Product 裁决 |
| --- | --- | --- | --- |
| API outer budget | 实际 `process_timeout_s` 同值传给 helper，不扩大外层 timeout | API 通过 `--outer-process-timeout-s` 传入公式计算值；80s fixture 锁定 helper argv 与 process wait 同为 `80.0s` | 接受 |
| Helper 全局预算 | monotonic deadline，并预留 final artifact 时间 | 新增共享 monotonic deadline，固定 `4.0s` final artifact reserve；直接 CLI 未传参数时保持兼容 | 接受 |
| Probe 优先级 | critical readiness 在前，非关键 `ros2 pkg list` 不得挤占 final | package inventory 后移；timeout clamp 到 `remaining - reserve`，预算不足返回 `package_check_skipped_to_preserve_final_artifact_budget` | 接受 |
| Package 三态 | budget skip 不得伪装成 installed/missing/success | skip 时 `executed=false`、`timeout_s=null`、availability=`null`，明确 not-proven | 接受 |
| Hostile fixture | slow command 仍需在 outer budget 前自然 final | fake-monotonic fixture 覆盖 package clamp + reserve skip，最终 `artifact_kind=final`、`last_phase=final`、`current_command=null` | 接受 |
| Offline fixture | ROS/source 缺失也自然 blocked final | 真实本地子进程 offline fixture 自然写 blocked final，不依赖 SIGINT、partial preservation 或 fallback | 接受 |
| API natural final | fail-closed return code 2 不得误走 timeout path | API test 证明不读取 partial、不写 failure fallback、不调用 `os.killpg` | 接受 |
| Race 修复 | package 边界必须稳定 | fork 前第二次 clamp 进入 reserve 的 race 已映射为 `package_check_skipped_to_preserve_final_artifact_budget` | 接受 |
| Live/Mission | 软件测试不得转算现场成功 | 未运行 SSH/ROS/live/control；current localization/path/route/HIL/delivery/safe/control/Mission 均未证明 | 拒绝现场与 OKR credit |

## 工程验证证据

- Robot Software：`py_compile` exit `0`；两个新增 targeted tests 均 `Ran 1 test ... OK`；全量 `Ran 116 tests in 0.250s`、`OK (skipped=1)`；scoped diff check exit `0`。
- Robot Software 相关修改新增行中文注释比例：`3/11 = 27.3%`，严格 `>20%`。
- Algorithm：`py_compile` exit `0`；hostile 与 offline targeted tests 均 `Ran 1 test ... OK`；全量 `Ran 169 tests in 2.437s`、`OK`；scoped diff check exit `0`。
- Algorithm 相关代码中文注释比例：`76/302 = 25.166%`，严格 `>20%`；新增非中文技术注释为 `0`。
- 集成：联合 `py_compile` exit `0`；`Ran 285 tests in 2.706s`、`OK (skipped=1)`；contract `rg` 与全范围 `git diff --check` exit `0`。
- Product 本阶段只读核对 `tech-done.md` 与当前 diff；没有重跑上述工程 tests，也没有执行 SSH、ROS、Nav2、live 或 control。

## 失败定位与修复验收

Lane A 与集成首轮无失败。Lane B 复核发现 package deadline race：首次预算检查允许执行，但真正 fork 前第二次 monotonic clamp 可能已进入 4s reserve；若原样返回通用 `outer_process_budget_final_reserve_reached`，会丢失 PRD 指定的 package skip 语义。

Algorithm 已将该 race-window 映射到 `package_check_skipped_to_preserve_final_artifact_budget`，并固定 `executed=false`、`timeout_s=null`、availability=`null`、保留 remaining/reserve 诊断。修复后的 169 项 Algorithm tests 与合并 285 tests 均通过，Product 接受该修复。

## OKR 映射与方向判断

- Objective 5：约 `85%`，provider/runtime blocker `2/2` 仍成立；本轮没有第三次消费，继续暂停。
- Objective 3：只接受 supporting software contract；历史软件侧约 99% 不变，现场验证 lane 不单独计分。
- Objective 1：约 `94%`，flat；没有 current HIL、route execution 或 safe-to-control 证据。
- Objective 6 / Objective 7：各约 `93%`，flat；本轮没有 cloud/archive/PC live 增量。
- Mission Objective 0：保持 `blocked_before_attempt_on_current_localization_readiness`。
- `current_run_artifact_delta=false`、`external_artifact_delta=false`、`live_control_delta=false`、`user_action_delta=false`。
- `route_execution_success=false`、`hil_pass=false`、`delivery_success=false`、`safe_to_control=false`、`robot_control_executed=false`、`okr_credit=false`。
- KR `不归档`；完成 KR 历史区无新增记录。

`tech-plan.md` 的 OKR 最低优先级切换理由在收口时仍成立：Objective 5 仍是最低总体 Objective，但 provider/runtime 同根 blocker 已消费 `2/2`，本轮合法转向可离线修复且直接解锁下一现场命令的 Objective 3 supporting lane，没有用第三个 O5 wrapper/diagnostic 消费同一 blocker。

## Proof boundary 与剩余风险

- `software_proof_o3_o10_offline_runtime_budget_contract_only` 只证明 deterministic 本地 budget/finalization 合同。
- fake monotonic 和 offline fixture 不证明真实 ROS CLI、DDS、AMCL、TF、planner、真实板调度或 atomic write/cleanup 能稳定落在 4s reserve。
- package availability 现在包含 `null=not-proven` 三态；范围外消费者仍需在未来真实 readback 前复核。
- SIGINT/partial fallback 继续保留为异常兜底，但不是本轮 happy-path 验收证据。

## 下一步唯一入口

禁止把本轮软件合同直接用于第三个旧窗口。下一步只允许在重新确认 current operator、route、obstacle、readiness gate，并取得**新授权**后，开启一个新的 no-motion current proof；旧两窗口授权不能直接复用。新 proof 仍须先证明 current pose/TF freshness、persisted pose、planner/controller 与 path，再决定是否进入任何 route/HIL/delivery 讨论。

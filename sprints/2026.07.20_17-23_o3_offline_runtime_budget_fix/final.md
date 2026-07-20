# O3 Offline Runtime Budget Fix - Final

## Sprint metadata

- `sprint_type: epic`
- Product owner：`product-okr-owner`
- Engineer owners：`robot-software-engineer`、`robot-algorithm-engineer`
- Final status：`accepted_offline_runtime_budget_contract_no_live_or_okr_credit`
- proof boundary：`software_proof_o3_o10_offline_runtime_budget_contract_only`
- `PRODUCT_CLOSEOUT_COMPLETE=yes`
- `okr_credit=false`
- KR：`不归档`

## Product final decision

Product 接受 Upper API/O10 helper 的离线 runtime budget 合同、hostile/offline natural-final 测试、两份 navigation 文档和 package deadline race 修复；拒绝 current-live localization/path readiness、route execution、HIL、delivery、safe-to-control、robot control、Mission success 和 OKR credit。

用户价值是 helper 不再必须等到 API 80s outer timeout 发 SIGINT 后，靠 partial artifact 才留下诊断。API 现在把实际 `process_timeout_s` 原样传给 helper；helper 使用 monotonic deadline 与 `4.0s` final artifact reserve，在进入 reserve 前收敛或跳过非关键 `ros2 pkg list`，自然写出可判定 final artifact。

## 实际交付

Robot Software：

- `upper_robot_api.py` 将同一个实际 process timeout 同时用于外层 wait 与 helper `--outer-process-timeout-s`；80s case 未扩大。
- natural blocked final、return code `2` 直接返回；不会读取 partial、写 timeout fallback 或调用 `os.killpg`。
- `test_upper_robot_api.py` 和 field-route preflight 文档同步合同与异常兜底边界。

Algorithm：

- `o10_amcl_nav2_runtime_proof.py` 新增共享 monotonic deadline、固定 4s reserve、所有阶段命令 remaining-budget clamp 与 final metadata。
- critical localization/TF/lifecycle/planner/path 判定优先；`ros2 pkg list` 后移并采用 budget-aware skip/clamp。
- budget skip 输出 `package_check_skipped_to_preserve_final_artifact_budget`、`executed=false`、`timeout_s=null`、availability=`null`，不伪造包存在/缺失。
- hostile fake-monotonic 与本地 offline 子进程都自然形成 `artifact_kind=final`、`last_phase=final`、`current_command=null`，不依赖 SIGINT 或 partial fallback。
- `test_nav2_runtime_proof_helper.py` 和 fixed-route workflow 文档同步。

## 验证证据

- Robot Software：`py_compile` exit `0`；新增 targeted tests `1+1` 均 OK；全量 `Ran 116 tests in 0.250s`、`OK (skipped=1)`；中文注释比例 `27.3%`。
- Algorithm：`py_compile` exit `0`；hostile/offline targeted tests `1+1` 均 OK；全量 `Ran 169 tests in 2.437s`、`OK`；中文注释比例 `25.166%`，新增非中文技术注释 `0`。
- 集成：联合 `py_compile` exit `0`；`Ran 285 tests in 2.706s`、`OK (skipped=1)`；contract `rg` 与全范围 `git diff --check` exit `0`。
- Product 仅只读核对 `tech-done.md` 与当前工程 diff，不重跑 tests，不执行 SSH、ROS、Nav2、live 或 control。

## Package deadline race

Algorithm 实现复核发现 package race：首次预算检查允许 package probe，但 fork 前第二次 monotonic clamp 可能已经进入 final reserve。若直接透传通用 reserve boundary，会丢失 package-specific skip 合同。

修复后该窗口统一映射为 `package_check_skipped_to_preserve_final_artifact_budget`，固定 `executed=false`、`timeout_s=null`、availability=`null` 并保留 remaining/reserve。修复后的 169 项 Algorithm tests 和合并 285 tests 通过，Product 接受。

## Proof boundary 与拒绝项

本轮未执行 SSH、SCP、远端部署、ROS live、Nav2 lifecycle/action、`/initialpose`、goal、`/cmd_vel`、UART、base manual/stop 或任何运动，也没有产生新的现场 artifact。

因此以下事实全部保持：

- `current_run_artifact_delta=false`
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

`software_proof_o3_o10_offline_runtime_budget_contract_only` 不能升级为 current localization、current path、route、HIL、delivery、safe/control 或 Mission 证据。

## OKR、KR 与历史归档

- Objective 5：约 `85%`，provider/runtime blocker `2/2` 仍成立；本轮没有第三次消费，继续暂停。
- Objective 1：约 `94%`，flat。
- Objective 6 / Objective 7：各约 `93%`，flat。
- Objective 3：只新增 supporting software contract；历史软件侧约 99% 与现场验证不单独计分口径均保持。
- Mission Objective 0：继续 `blocked_before_attempt_on_current_localization_readiness`。
- 所有主百分比 flat；KR `不归档`；历史完成区无新增 KR。

最低优先级复核结论：`tech-plan.md` 中从 Objective 5 切换到 Objective 3 supporting lane 的理由仍成立。O5 仍是最低总体 Objective，但同一 provider/runtime blocker 已到 `2/2`；本轮选择可在本地完成、且直接清除下一现场命令 blocker 的 runtime budget 修复，没有制造第三个 O5 wrapper/readback/diagnostic。

## 剩余风险

- fake monotonic/offline fixture 不证明真实 ROS CLI、DDS、AMCL、TF、planner 或板端调度时延。
- 4s reserve 在真实板上的 atomic write、cleanup 与 shell exit 稳定性仍未验证。
- package availability 的 `null=not-proven` 三态需要范围外消费者在未来真实 readback 前复核。
- SIGINT/partial fallback 仍是异常兜底；未来若再次触发，必须按当次 current command 与 remaining budget 重新定位。

## 下一步唯一入口

禁止直接复用旧两窗口授权开启第三个 proof/window。下一步只允许在重新确认 current operator、route、obstacle、readiness gate，并取得**新授权**后，开启一个新的 no-motion current proof。该新窗口必须先形成 current pose/TF freshness、persisted pose、planner/controller 与 path 的 final artifact；不足时继续 NO-GO，不得进入 route/HIL/delivery。

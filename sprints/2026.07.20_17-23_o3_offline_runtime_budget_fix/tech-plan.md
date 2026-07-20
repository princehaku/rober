# O3 Offline Runtime Budget Fix - Tech Plan

## Plan metadata

- `sprint_type: epic`
- 状态：`planning_complete_ready_for_parallel_implementation`
- Product owner：`product-okr-owner`
- 主责集成：`robot-software-engineer`
- 并行 owner：`robot-software-engineer`、`robot-algorithm-engineer`
- production interface：`upper_robot_api process_timeout_s -> helper --outer-process-timeout-s -> monotonic deadline/final reserve`
- proof boundary：`software_proof_o3_o10_offline_runtime_budget_contract_only`

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 当前推进区完成度最低的 Objective：Objective 5（约 `85%`）。
- 本 sprint 是否针对该最低 Objective：否。
- 合法切换理由：Objective 5 provider/runtime blocker 已消费 `2/2`；第三轮同 blocker 被红线禁止。上一轮 final 明确下一入口为 Objective 3 supporting lane 的 `next_offline_runtime_budget_fix`，其 80s runtime incompatibility 可在当前本地环境推进，并直接解锁未来 current localization/path proof。
- 切换后的目标：Objective 3 supporting lane；只修 O10 helper/API 的本地离线 runtime budget，不产生第三个上车 proof/window。
- `final.md` 收口复核：O5 blocker 2/2 是否仍成立；本轮是否只有 software proof；若无 route/HIL/delivery/current-live evidence，所有主百分比保持 flat、KR 不归档。

## 接口设计

### API 侧

`nav2_runtime_proof_process_timeout_budget()` 继续计算外层 `process_timeout_s`，保留 cap 与 PC proxy 关系。`run_nav2_runtime_proof_helper()` 在 helper argv 中追加：

```text
--outer-process-timeout-s <process_timeout_s>
```

外部 HTTP body/response 不新增必填字段。80s current case 仍为 80s，不允许通过放大 timeout 通过验收。API timeout fallback 和 owned process-group cleanup 保留为异常兜底。

### Helper 侧

- CLI 增加可选 `--outer-process-timeout-s`；缺省时保留直接 CLI 使用兼容路径。
- helper 启动即计算 monotonic deadline，并定义足以完成 root-cause assembly、atomic JSON write 与正常退出的 final reserve。
- 所有新增非关键 probe 在启动前查询 remaining budget；command timeout clamp 到可用预算。
- `package_checks()` 接受 budget/deadline context。预算不足时不运行 `ros2 pkg list`，返回明确 skipped boundary；预算可用时只获得 `remaining - final_reserve` 的 bounded timeout。
- 最终 proof 继续保留 package availability/result 形状，但 skipped 必须显式 not-proven，不能误报 installed/missing。
- critical readiness 数据完成或预算进入 reserve 后，立即进入 final assembly；正常 blocked outcome 也要写 final artifact 并自然退出。

### Artifact contract

至少提供以下可断言信息，具体字段命名可由 Engineer 保持现有 schema 风格，但不得缺失语义：

- outer process timeout；
- final artifact reserve；
- finalization reason（normal completion 或 budget reserve reached）；
- package batch `executed/ok/boundary/timeout_s`；
- `artifact_kind=final`、`last_phase=final`、`current_command=null`；
- 安全字段固定 false，且没有 signal-before-final root cause。

## 并行 owner 与文件范围

### Lane A — `robot-software-engineer`

允许修改：

- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`
- `sprints/2026.07.20_17-23_o3_offline_runtime_budget_fix/tech-done.md`（仅在收到双方证据后由主节点 follow-up，Algorithm 不修改）

任务：

1. 冻结并传递实际 outer process timeout，不改变 HTTP surface。
2. 新增 `test_nav2_runtime_proof_passes_outer_process_timeout_to_helper`，覆盖 80s case 与 argv。
3. 新增 `test_nav2_runtime_proof_natural_final_result_does_not_use_timeout_fallback`，证明 helper 正常返回时不读取 partial、不发送 signal。
4. 保持现有 timeout/partial fallback regression 与安全字段。
5. 同步 API/preflight 文档；集成阶段运行双方全量测试并写 `tech-done.md`。

### Lane B — `robot-algorithm-engineer`

允许修改：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`

任务：

1. 实现 monotonic budget context 与 final reserve，不使用 wall-clock 判定 remaining budget。
2. 将 package inventory 标为非关键 probe，按 remaining budget skip/clamp；禁止仅把固定 package timeout 调小冒充全局修复。
3. 确保 budget reserve 触发后不再启动新非关键命令，并自然进行 final assembly/atomic write。
4. 新增 `test_hostile_slow_package_check_skips_or_clamps_and_writes_final_artifact`。
5. 新增 `test_offline_budget_fixture_writes_final_without_sigint_or_partial_fallback`。
6. 同步 fixed-route workflow 文档并向主节点返回完整验证日志；不修改 `tech-done.md`。

两个 lane 首轮必须同消息并行启动；不得串行把一个 owner 的工程工作交给另一个 owner。接口耦合由以上 CLI/semantic contract 消除，最终集成归 Robot Software。

## 实现顺序

1. 主节点并行派发 Lane A/B，两个 owner 各自在限定文件内实现、测试、修复。
2. Algorithm 返回代码与测试证据；主节点将结果交给 Robot Software 做集成 follow-up。
3. Robot Software 在不改 Algorithm 文件的前提下运行集成验收；若失败，把失败按归属退回对应 owner 修复。
4. 集成全绿后 Robot Software 创建 `tech-done.md`，记录实际改动、命令输出、proof boundary、失败修复和剩余风险。
5. Product 只读验收后依次创建 `side2side_check.md`、`final.md`；只有实际证据支持时才更新 `OKR.md` 和 progress log。本轮预期百分比 flat、KR 不归档。

## 验收命令

Lane A：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py
python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_passes_outer_process_timeout_to_helper
python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_natural_final_result_does_not_use_timeout_fallback
python3 -m unittest onboard/tests/test_upper_robot_api.py
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py docs/navigation/field_route_evidence_preflight.md
```

Lane B：

```bash
python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper.Nav2RuntimeProofHelperTests.test_hostile_slow_package_check_skips_or_clamps_and_writes_final_artifact
python3 -m unittest onboard.tests.test_nav2_runtime_proof_helper.Nav2RuntimeProofHelperTests.test_offline_budget_fixture_writes_final_without_sigint_or_partial_fallback
python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py
git diff --check -- onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/fixed_route_workflow.md
```

集成验收：

```bash
python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py
python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py
rg -n "outer-process-timeout|final.*reserve|package_check_skipped_to_preserve_final_artifact_budget|artifact_kind|current_command" onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md
git diff --check -- onboard/scripts/upper_robot_api.py onboard/tests/test_upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py onboard/tests/test_nav2_runtime_proof_helper.py docs/navigation/field_route_evidence_preflight.md docs/navigation/fixed_route_workflow.md sprints/2026.07.20_17-23_o3_offline_runtime_budget_fix
```

注释验收：两个 owner 必须在 `tech-done.md` 分别报告相关修改代码的中文注释行数、代码行数与比例，比例严格 `>20%`；所有新增技术注释必须为中文。

## Hostile/offline fixture 必须断言

- 使用 fake clock/stub runner 或短 budget 缩放，不真实 sleep 80s。
- 80s outer contract 从 API 传入 helper，helper final deadline 严格早于 outer kill boundary。
- slow `ros2 pkg list` 不得吞掉 final reserve；结果只能是 bounded completion 或显式 skipped boundary。
- 最终 JSON 可解析，`artifact_kind=final`、`last_phase=final`、`current_command=null`。
- 自然退出；不调用 `os.killpg`/SIGINT 路径，不出现 `sigint_before_final_artifact` 或 `helper_process_timeout_after_partial_artifact`。
- `partial_artifact_preserved` 不能作为通过条件；route/HIL/delivery/safe/control/OKR 字段保持 false。

## 禁止命令与 proof boundary

本 sprint 禁止 SSH/SCP、远端文件写入、`ros2` live command、Nav2 lifecycle/action、`/initialpose`、goal、`/cmd_vel`、UART、base manual/stop，以及任何第三个 proof/window。测试 fixture 即使命名为 ROS command，也只能走 stub，不得访问真实 graph。

验收通过只表示 O10/API 离线 runtime budget contract ready；不证明 current localization、planner/controller active、path、route execution、HIL、delivery、safe-to-control、robot control 或 Mission Objective 0，`okr_credit=false`。

## 风险与回退

- 若 final assembly 自身超出 reserve，Algorithm 必须缩减 final 前非关键工作或扩大内部 reserve，但不得扩大 API outer timeout。
- 若新增 artifact 字段破坏 latest response，Robot Software 负责保持向后兼容；不得删掉既有安全/partial fallback 字段。
- 若 full suites 暴露旧测试依赖固定 package execution，应调整为显式 executed/skipped boundary，不得把 skipped 断言成 package present。
- 若 deterministic fixture 只能靠 signal 结束，本 sprint 验收失败，必须退回相应 owner 修复后复验。

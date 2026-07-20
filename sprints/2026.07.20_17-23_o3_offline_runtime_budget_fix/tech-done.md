# O3 Offline Runtime Budget Fix - Tech Done

## Sprint metadata

- `sprint_type: epic`
- 状态：`engineering_complete_ready_for_product_acceptance`
- Product owner：`product-okr-owner`
- 主责集成 owner：`robot-software-engineer`
- 并行 owner：`robot-software-engineer`、`robot-algorithm-engineer`
- proof boundary：`software_proof_o3_o10_offline_runtime_budget_contract_only`
- OKR 建议：Objective 3 / Objective 1 / Objective 5 与 Mission Objective 0 全部保持 flat，KR `不归档`

## 实际改动

### Lane A - Upper API outer budget contract

改动文件：

- `onboard/scripts/upper_robot_api.py`
- `onboard/tests/test_upper_robot_api.py`
- `docs/navigation/field_route_evidence_preflight.md`

`nav2_runtime_proof_process_timeout_budget()` 继续作为 outer process timeout 的唯一计算入口；既有公式、
最小值、cap 和 PC proxy 关系没有扩大。`run_nav2_runtime_proof_helper()` 现在把公式计算出的同一个
`process_timeout_s` 通过 `--outer-process-timeout-s <process_timeout_s>` 传给 O10 helper，并继续把
该值用于 `run_helper_bash_process_group()` 的外层等待。外部 HTTP body、response schema、安全字段与
异常 timeout/partial fallback 保持兼容。

新增 API 单测锁定两类行为：

- 现有公式计算为 `80.0s` 时，helper argv 与外层进程 timeout 都严格等于 `80.0s`；
- helper 自然写出 blocked final 且以合法 fail-closed return code `2` 返回时，不读取 partial、不写
  failure fallback，也不发送 `os.killpg` signal。

field-route preflight 文档同步了内部预算参数、正常 final 与异常 fallback 的边界，并明确没有新增
HTTP surface 或运动许可。

### Lane B - O10 monotonic deadline and final reserve

改动文件：

- `onboard/scripts/o10_amcl_nav2_runtime_proof.py`
- `onboard/tests/test_nav2_runtime_proof_helper.py`
- `docs/navigation/fixed_route_workflow.md`

helper 新增可选 `--outer-process-timeout-s`。Upper API 传入该参数时，从进程开始建立 monotonic
deadline，并固定预留 `4.0s` final artifact reserve；直接 CLI 未传参数时继续保持既有无 outer
deadline 的兼容路径。所有带 phase writer 的命令在启动前按 `remaining - final reserve` clamp，
进入 reserve 后不再启动新子进程。

关键 localization、TF、lifecycle、planner 与 planner-only path probe 保持在前；非关键
`ros2 pkg list` 后移。预算不足时 package batch 输出
`boundary=package_check_skipped_to_preserve_final_artifact_budget`、`executed=false`，各 package
availability 保持 `null`，不会伪装成 installed、missing 或 command success。自然收口同时在 envelope
与 proof 写入 `artifact_kind=final`、`last_phase=final`、`current_command=null`、outer budget、reserve、
remaining 和 finalization reason。

新增 hostile fake-monotonic fixture 覆盖 package timeout clamp 与 reserve skip；新增真实本地子进程
offline fixture，证明 ROS/source 缺失时也能自然写 blocked final，而不是依赖 SIGINT 或 partial
fallback。fixed-route workflow 同步了预算、三态 package 语义和 proof boundary。

## 接口影响与兼容性

- 生产者：Upper API 仍负责计算实际 `process_timeout_s`，只新增内部 helper argv 传递。
- 消费者：O10 helper 可消费 outer budget；直接 CLI 不传参数时行为兼容。
- HTTP：request body、response schema 与 timeout cap 不变，没有新增必填字段。
- Artifact：新增 budget/finalization 字段；既有字段保留。package budget skip 使用 `null` 表示
  not-proven，消费者不能把它当作 `false/missing`。
- 异常路径：外层 timeout、SIGINT process-group cleanup、partial preservation 与结构化 failure artifact
  继续保留，只作为异常兜底。
- 安全边界：所有新增路径保持 `safe_to_control=false`、`robot_control_executed=false`，不产生 route、
  HIL 或 delivery success 声明。

## 验证结果

### Lane A 独立验证

- `python3 -m py_compile onboard/scripts/upper_robot_api.py`：exit `0`。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_passes_outer_process_timeout_to_helper`：`Ran 1 test`，`OK`。
- `python3 -m unittest onboard.tests.test_upper_robot_api.UpperRobotApiFeedbackAckTests.test_nav2_runtime_proof_natural_final_result_does_not_use_timeout_fallback`：`Ran 1 test`，`OK`。
- `python3 -m unittest onboard/tests/test_upper_robot_api.py`：`Ran 116 tests in 0.250s`，`OK (skipped=1)`。
- scoped `git diff --check`：exit `0`。
- `upper_robot_api.py` 修改新增行统计：中文注释 `3` 行 / 代码 `11` 行 = `27.3%`，严格 `>20%`。

### Lane B 独立验证

- `python3 -m py_compile onboard/scripts/o10_amcl_nav2_runtime_proof.py`：exit `0`。
- hostile package fixture：`Ran 1 test`，`OK`。
- offline budget fixture：`Ran 1 test`，`OK`。
- `python3 -m unittest onboard/tests/test_nav2_runtime_proof_helper.py`：`Ran 169 tests in 2.437s`，`OK`。
- scoped `git diff --check`：exit `0`。
- `o10_amcl_nav2_runtime_proof.py` 相关代码统计：中文注释 `76` 行 / 代码 `302` 行 = `25.166%`，严格 `>20%`；新增非中文 `#` 技术注释为 `0`。

### 主责集成验证

- `python3 -m py_compile onboard/scripts/upper_robot_api.py onboard/scripts/o10_amcl_nav2_runtime_proof.py`：exit `0`。
- `python3 -m unittest onboard/tests/test_upper_robot_api.py onboard/tests/test_nav2_runtime_proof_helper.py`：
  `Ran 285 tests in 2.706s`，`OK (skipped=1)`。
- contract `rg`：exit `0`；API argv、helper parser、final reserve、package skip boundary、
  `artifact_kind` 与 `current_command` 均在代码、测试及两份 navigation 文档中命中。
- 全范围 `git diff --check`：exit `0`。

## 失败定位与修复

本轮 Lane A 与最终集成测试没有失败。Lane B 实现复核发现一个 package deadline race：首次预算检查
尚允许执行，但在真正 fork 前的第二次 monotonic clamp 可能已进入 final reserve；如果直接透传通用
`outer_process_budget_final_reserve_reached`，package consumer 会丢失 PRD 指定的 skip boundary。

修复方式是把该 race-window 的通用 skip 映射为
`package_check_skipped_to_preserve_final_artifact_budget`，同时固定 `executed=false`、`timeout_s=null`、
package availability=`null` 并保留 remaining/reserve 诊断。修复后 Lane B `169` 项全量测试和双方
`285` 项集成测试均通过。

上一轮真实窗口的 `helper_process_timeout_after_partial_artifact` / `sigint_before_final_artifact` 是本次
软件修复的输入问题，不是本轮新测试的通过条件；本轮没有改写或包装上一轮 partial artifact。

## 未执行边界

本轮严格只做本地离线软件实现与测试，未执行 SSH、SCP、远端部署、ROS live、Nav2 action、
`/initialpose`、`/cmd_vel`、`/api/base/manual`、UART、底盘控制或任何运动，也没有开启第三个现场窗口。
没有生成现场 artifact，没有证明 current ROS graph、定位、TF、planner/path、route execution、HIL、
delivery、operator acceptance、safe-to-control、robot control 或 Mission Objective 0 success。

## OKR 与 KR 建议

Objective 5 的 provider/runtime blocker 仍为 `2/2`，本轮没有继续消费。该工程增量只清除了
Objective 3 supporting lane 的 API/helper runtime budget 软件不相容；它没有 current-live、route、
HIL、delivery 或 production external evidence。因此建议 Objective 3、Objective 1、Objective 5 与
Mission Objective 0 的百分比全部保持 flat，本轮 KR `不归档`，只接受 proof boundary
`software_proof_o3_o10_offline_runtime_budget_contract_only`。

## 剩余风险

- fake monotonic 与 offline fixture 不能证明真实 ROS CLI、DDS、AMCL、TF、planner 或板端进程调度时延。
- 固定 `4.0s` reserve 已有离线覆盖，但真实板 atomic write、cleanup 和 shell 退出能否稳定落在该窗口，
  仍需未来独立授权后的新 no-motion current proof 验证。
- SIGINT/partial fallback 仍是必要异常兜底；若未来现场仍进入 fallback，需要按当次 current command 与
  remaining budget 定位，不能把本轮软件测试当作 live success。
- package availability 新增 `null` 三态；范围外消费者若错误假设纯布尔，需要在未来真实 readback 前
  复核，但当前仓内分类逻辑与测试已按 `None=not-proven` 兼容。
- 下一步只能在重新确认 current readiness、operator 与现场 gate 后开一个新的 no-motion proof；不能
  直接复用旧授权开启第三窗口，更不能据此进入 route、HIL 或 delivery。

## 协同需求

- Product：按软件 proof boundary 做只读验收，并保持 OKR flat、KR 不归档。
- Autonomy：后续现场前复核 helper budget/final artifact，并只在新授权窗口采集 current proof。
- Hardware：本轮无需介入；只有后续进入 WAVE ROVER/UART/HIL gate 时再按 vendor 文档复核。
- Full-Stack：本轮无需介入；HTTP surface 与既有 response schema 未变。

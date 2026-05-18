# Sprint 2026.05.18_14-15 Route Task Acceptance Execution Callback Review Handoff - Tech Plan

## 1. 目标和架构

本轮实现 `route_task_field_retest_acceptance_execution_callback_review_handoff`：在上一轮 `route_task_field_retest_acceptance_execution_callback_review_decision` 之后增加一个 handoff layer，把复核决策转成 PC gate artifact/summary、Robot diagnostics safe alias 和 mobile/web 只读“现场复核交接” panel。

架构原则:

- Autonomy 是主 artifact 生产者，读取上一轮 review decision artifact/summary，输出 handoff artifact/summary。
- Robot 只做 diagnostics safe alias，不重新解释现场业务语义。
- Full-stack 只做 phone-safe 只读消费，不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- Product closeout 只做证据核对、OKR 边界和 sprint/docs 收口。

## 2. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective: Objective 5，约 68%。
- 本 sprint 是否针对该 Objective: 否。
- 不针对理由: Objective 5 的下一步真实进展需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 外部材料；当前本机只有 Docker，O5 stop rule 成立。Objective 1 约 81%，但近期 WAVE ROVER HIL packet intake/review/execution-pack 等 sprint 已重复消费同一真实 WAVE ROVER/UART/HIL blocker，本机无真实硬件，不继续本地包装同一 blocker。PR #4 route/elevator acceptance execution callback review decision 已完成，当前最可执行且不重复消费 blocker 的抓手是把 review decision 转成 handoff package。
- final.md 收口时需复核: O5 外部材料或 O1 真实硬件材料是否在本轮期间出现；若出现，下一轮应重新排序。若没有，本轮仍按 O2/O3 route/elevator handoff 收口。

## 3. 证据边界和禁止声明

本轮统一证据边界:

- `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

禁止声明:

- real route/elevator field pass
- Nav2/fixed-route proof
- task record/completion signal
- dropoff/cancel completion
- delivery result
- delivery success
- HIL
- 真实手机/browser
- Objective 5 external proof

## 4. Task A - Autonomy

Owner: `autonomy-engineer`

### 文件范围

- Create: `pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py`
- Create: `tests/test_route_task_field_retest_acceptance_execution_callback_review_handoff.py`

### 需要做什么

- 新增 PC gate `route_task_field_retest_acceptance_execution_callback_review_handoff.py`。
- 读取上一轮 review decision artifact/summary，支持 artifact 文件输入和 summary 文件输入。
- 校验 source schema/status/evidence boundary，拒绝 unsupported wrapper、缺失 `evidence_ref`、不安全 raw copy、成功误导文案、delivery success claim、primary actions enabled。
- 输出 handoff artifact/summary，schema 建议:
  - `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1`
  - `trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1`
- 状态建议:
  - `ready_for_acceptance_execution_callback_review_handoff`
  - `needs_owner_follow_up`
  - `needs_acceptance_execution_callback_rerun`
  - `evidence_ref_mismatch_rerun`
  - `blocked_unsafe_review_handoff`
- Summary 至少包含 safe `evidence_ref`、source review decision/status、owner handoff、next required evidence、safe rerun hint、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

### 验收命令

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_callback_review_handoff.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_handoff
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py --help
rg -n "route_task_field_retest_acceptance_execution_callback_review_handoff|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_callback_review_handoff.py
git diff --check -- pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_callback_review_handoff.py
```

### 接口边界

- 不读取真实硬件、串口、网络、Nav2 runtime 或 mobile runtime。
- 不把 artifact/summary pass 写成 field pass。
- 不输出 raw artifact path、absolute path、checksum、credential、traceback、ROS topic、`/cmd_vel`、serial/UART、baudrate 或 hardware raw detail 到 phone-safe summary。

## 5. Task B - Robot

Owner: `robot-software-engineer`

### 文件范围

- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`

### 需要做什么

- 在 operator gateway diagnostics 中增加 safe alias:
  - `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary`
- 消费 Task A 主 summary 或兼容嵌套 summary，输出 sanitized diagnostics alias。
- 保持 alias 只读、phone-safe、metadata-only。
- diagnostics test 覆盖:
  - 主 summary 可映射到 alias。
  - alias 保留 boundary/status/evidence_ref/owner handoff/next evidence flags。
  - unsafe raw details 被过滤或拒绝。
  - `delivery_success=false` 与 `primary_actions_enabled=false` 不被改写。

### 验收命令

```bash
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary|route_task_field_retest_acceptance_execution_callback_review_handoff|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
```

### 接口边界

- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 行为。
- 不新增 robot command、ACK、cursor 或 action gating。
- 不把 diagnostics alias 当真实 route/elevator field result。

## 6. Task C - Full-stack

Owner: `full-stack-software-engineer`

### 文件范围

- Modify: `mobile/web/app.js`
- Modify: `mobile/fixtures/mobile_web_status.fixture.json`
- Modify: `mobile/web/test_mobile_web_entrypoint.py`

### 需要做什么

- 在 `mobile/web/app.js` 新增只读“现场复核交接” panel。
- Panel 消费主 summary 或 Robot safe alias:
  - `route_task_field_retest_acceptance_execution_callback_review_handoff`
  - `route_task_field_retest_acceptance_execution_callback_review_handoff_summary`
  - `robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary`
- 展示字段只限 phone-safe metadata: handoff status、source review decision/status、safe `evidence_ref`、owner handoff、next required evidence、safe rerun hint、boundary、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- fixture 增加 handoff summary 样例。
- mobile unittest 覆盖 panel 渲染、主 summary 与 safe alias 兼容、unsafe copy 不出现、Start/Confirm/Cancel gating 不变。

### 验收命令

```bash
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "现场复核交接|route_task_field_retest_acceptance_execution_callback_review_handoff|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py
```

### 接口边界

- 不改变 Start Delivery、Confirm Dropoff、Cancel gating。
- 不发送 diagnostics fetch、robot command、ACK 或 cursor。
- 不暴露 raw ROS topic、`/cmd_vel`、raw JSON、serial/UART、baudrate、WAVE ROVER details、credentials、DB/queue URLs、OSS AK/SK、local paths、checksums、complete artifacts 或 tracebacks。

## 7. Task D - Product Closeout

Owner: `product-okr-owner`

### 文件范围

- Create/Modify: `sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/tech-done.md`
- Create/Modify: `sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/side2side_check.md`
- Create/Modify: `sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`
- Modify as needed: `docs/product/mobile_user_flow.md`, `docs/interfaces/*`, `pc-tools/README.md`

### 需要做什么

- 汇总 Autonomy、Robot、Full-stack worker 的实际改动和验证输出。
- 核对所有 docs 与 code contract 是否同步。
- 更新 OKR 4.1 当前 sprint、证据边界和剩余缺口。
- 更新 `docs/process/okr_progress_log.md`。
- 写清本轮不提升 O5，不解除 O1/O5/PR #5 blocker。
- 写清本轮 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate` 只证明 handoff layer 可复核。

### 验收命令

```bash
test -f sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/tech-done.md && test -f sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/side2side_check.md && test -f sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff/final.md
rg -n "route_task_field_retest_acceptance_execution_callback_review_handoff|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs
```

### 接口边界

- Product closeout 不写产品代码、测试代码或硬件配置。
- 若任一 worker 验证失败，Product 必须把失败定位和重试任务派回对应 owner，不得口头收口。
- 不提交 git；本轮计划阶段已明确提交由后续 closeout 统一处理。

## 8. 并行启动要求

本 sprint 是 Epic，涉及 4 个 owner。Task A、Task B、Task C 文件范围互不重叠，必须并行启动；Task D 在三位工程 owner 返回后收口。若运行时降级为单线，`final.md` 必须说明流程违规原因和纠正策略。

建议启动顺序:

1. 并行启动 Task A Autonomy、Task B Robot、Task C Full-stack。
2. 等待三方结果后启动 Task D Product closeout。
3. 若 Task B/C 需要 Task A 的最终字段名，可采用计划中的 schema/status 作为合同；若最终字段名变化，由 Task A 在输出中列明，Task B/C 只做兼容更新。

## 9. 整体验收围栏

本轮总体验收只使用 focused fences，不跑 broad tests:

```bash
python3 -m py_compile pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py tests/test_route_task_field_retest_acceptance_execution_callback_review_handoff.py
python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_handoff
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py --help
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
rg -n "route_task_field_retest_acceptance_execution_callback_review_handoff|robot_diagnostics_route_task_field_retest_acceptance_execution_callback_review_handoff_summary|software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_14-15_route-task-acceptance-execution-callback-review-handoff pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs
```

## 10. 完成前反思清单

- 是否只改本 sprint 允许和各 task 文件范围内的文件。
- 是否保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。
- 是否没有把 handoff、ACK、diagnostics/mobile summary、review decision 写成真实现场通过或 delivery success。
- 是否没有扩大到 O5 external proof、O1 HIL 或 PR #5 hardware material proof。
- 是否同步更新 `docs/` 相关说明。
- 是否用 focused fences 验证，而不是 broad tests。

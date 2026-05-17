# Sprint 2026.05.17_19-20 Route Task Result Callback Review Decision - Tech Plan

sprint_type: epic

## 1. 技术目标

实现 `route_task_field_retest_result_callback_review_decision`，承接上一轮 `route_task_field_retest_result_callback_intake` 的 accepted/missing/rejected updates、owner follow-up 和 review-decision handoff，把 callback intake 的结果转成下一步可执行的复核决策。

目标 evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`。所有 PC / Robot / mobile 输出必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 文件范围和 owner

Task A / Autonomy Algorithm Engineer：

- 允许改动：
  - `pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py`
  - `pc-tools/evidence/test_route_task_field_retest_result_callback_review_decision.py`
  - `docs/interfaces/evidence_contracts.md`
- 责任：
  - 定义 callback review decision gate 输入 / 输出 schema。
  - 支持上一轮 callback intake artifact / summary 的 top-level 或 known safe wrapper 输入。
  - 输出 `trashbot.route_task_field_retest_result_callback_review_decision.v1` / `_summary.v1`。
  - 对 missing / rejected / mismatch / unsafe / success-control claim fail closed。

Task B / Robot Platform Engineer：

- 允许改动：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 责任：
  - 增加 diagnostics metadata-only consumer。
  - 支持 file/env/top-level/nested callback review decision summary。
  - 对 unsafe / missing / unsupported summary fail closed。
  - 不改变 ROS2 action、task_orchestrator、Start / Dropoff / Cancel / ACK / Nav2 / HIL 控制路径。

Task C / User Touchpoint Full-Stack Engineer：

- 允许改动：
  - `mobile/web/app.js`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- 责任：
  - 增加只读 callback review decision panel。
  - 显示 review decision、material status、owner handoff、next required evidence、safe evidence ref、boundary flags。
  - copy/export 只使用 `safe_copy`，缺失时显示 `blocked copy unavailable`。
  - 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Task D / Product Manager / OKR Owner：

- 允许改动：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/tech-done.md`
  - `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/side2side_check.md`
  - `sprints/2026.05.17_19-20_route-task-result-callback-review-decision/final.md`
- 责任：
  - 仅在 A/B/C durable work landed 且验证通过后更新 OKR 和 closeout。
  - 明确本轮不是 real field pass、真实手机/browser、HIL 或 Objective 5 external proof。

## 3. 接口 contract

输入：

- `trashbot.route_task_field_retest_result_callback_intake.v1`
- `trashbot.route_task_field_retest_result_callback_intake_summary.v1`

输出：

- artifact schema：`trashbot.route_task_field_retest_result_callback_review_decision.v1`
- summary schema：`trashbot.route_task_field_retest_result_callback_review_decision_summary.v1`
- evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_review_decision_gate`
- decision values：
  - `ready_for_result_review`
  - `needs_material_backfill`
  - `needs_callback_rerun`
  - `evidence_ref_mismatch_rerun`
  - `rejected_unsafe_callback`

Required flags：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`

## 4. 子 agent 启动要求

本 sprint 为跨 owner Epic。A/B/C 必须并行启动；Product closeout 在 A/B/C 返回后执行。主节点不得直接写产品代码、测试代码或硬件配置。

## 5. 验收命令

Task A / Autonomy：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_callback_review_decision.py
python3 pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py --help
rg -n "route_task_field_retest_result_callback_review_decision|software_proof_docker_route_task_field_retest_result_callback_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_result_review|needs_material_backfill|evidence_ref_mismatch_rerun" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_callback_review_decision.py pc-tools/evidence/test_route_task_field_retest_result_callback_review_decision.py docs/interfaces/evidence_contracts.md
```

Task B / Robot：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_callback_review_decision|software_proof_docker_route_task_field_retest_result_callback_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_evidence_ref" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C / Full-stack：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_callback_review_decision|software_proof_docker_route_task_field_retest_result_callback_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|blocked copy unavailable|safe_evidence_ref|ready_for_result_review|needs_material_backfill" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task D / Product closeout：

```bash
rg -n "route_task_field_retest_result_callback_review_decision|software_proof_docker_route_task_field_retest_result_callback_review_decision_gate|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/tech-done.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/side2side_check.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/final.md
```

Planning docs acceptance：

```bash
test -f sprints/2026.05.17_19-20_route-task-result-callback-review-decision/pre_start.md && test -f sprints/2026.05.17_19-20_route-task-result-callback-review-decision/prd.md && test -f sprints/2026.05.17_19-20_route-task-result-callback-review-decision/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_result_callback_review_decision|OKR 最低优先级核对|Objective 5|PR #4|PR #5|software_proof_docker_route_task_field_retest_result_callback_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_19-20_route-task-result-callback-review-decision
git diff --check -- sprints/2026.05.17_19-20_route-task-result-callback-review-decision/pre_start.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/prd.md sprints/2026.05.17_19-20_route-task-result-callback-review-decision/tech-plan.md
```

## 6. OKR 最低优先级核对

当前 `OKR.md` 4.1 数值最低 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。

本 sprint 不针对 Objective 5。

理由：Objective 5 要继续提升，必须拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。当前主机只有 Docker；继续做本地 metadata、sample、fixture 或 callback review decision 不会产生 Objective 5 external proof。根据最新 sprint final，本轮可行动作是接 PR #4 route/elevator 主线，从 callback intake 推进到 callback review decision。

## 7. 风险和边界

- 本轮不处理真实 WAVE ROVER、UART、HIL 或 PR #5 2D LiDAR / ToF 真实硬件材料。
- 本轮不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 dropoff/cancel completion 或 delivery success。
- 本轮不证明真实手机/browser、production app、PWA prompt/user choice 或 Objective 5 external proof。
- 若 callback intake 使用不同 `safe_evidence_ref`，或者存在 missing/rejected/unsafe updates，输出必须 blocked / backfill / rerun，而不是 ready。
- 若任何面出现 raw artifact、local path、checksum、secret、ROS topic、serial/UART、WAVE ROVER 参数、success phrasing 或 control claim，验收失败。

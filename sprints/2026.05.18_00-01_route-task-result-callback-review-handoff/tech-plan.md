# Sprint 2026.05.18_00-01 Route Task Result Callback Review Handoff - Tech Plan

sprint_type: epic

## 1. 技术目标

实现 `route_task_field_retest_result_callback_review_handoff`，承接上一轮 `route_task_field_retest_result_callback_review_decision` 的 result-review decision、owner handoff、next required evidence 和 rerun path，把它转成 result review 前可执行的 handoff status、owner follow-up、review-ready package 和 rerun package。

目标 evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`。所有 PC / Robot / mobile 输出必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 文件范围和 owner

Task A / Autonomy Algorithm Engineer：

- 允许改动：
  - `pc-tools/evidence/route_task_field_retest_result_callback_review_handoff.py`
  - `pc-tools/evidence/test_route_task_field_retest_result_callback_review_handoff.py`
  - `pc-tools/evidence/fixtures/route_task_field_retest_result_callback_review_handoff/`
  - `docs/interfaces/evidence_contracts.md`
- 责任：
  - 定义 callback review handoff gate 输入 / 输出 schema。
  - 支持上一轮 callback review decision artifact / summary 的 top-level 或 known safe wrapper 输入。
  - 输出 `trashbot.route_task_field_retest_result_callback_review_handoff.v1` / `_summary.v1`。
  - 对 missing decision、rejected decision、unsafe copy、success-control claim、evidence-ref mismatch fail closed。

Task B / Robot Platform Engineer：

- 允许改动：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 责任：
  - 增加 diagnostics metadata-only consumer。
  - 支持 file/env/top-level/nested callback review handoff summary。
  - 对 unsafe / missing / unsupported summary fail closed。
  - 不改变 ROS2 action、task_orchestrator、Start Delivery、Confirm Dropoff、Cancel、ACK、Nav2 或 HIL 控制路径。

Task C / User Touchpoint Full-Stack Engineer：

- 允许改动：
  - `mobile/web/app.js`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- 责任：
  - 增加只读 callback review handoff panel。
  - 显示 handoff status、owner follow-up、review-ready package、rerun package、next required evidence、safe evidence ref、boundary flags。
  - copy/export 只使用 `safe_copy`，缺失时显示 `blocked copy unavailable`。
  - 不改变 Start Delivery、Confirm Dropoff、Cancel、ACK 或 primary action gating。

Task D / Product Manager / OKR Owner：

- 允许改动：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/tech-done.md`
  - `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/side2side_check.md`
  - `sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/final.md`
- 责任：
  - 仅在 A/B/C durable work landed 且验证通过后更新 OKR 和 closeout。
  - 明确本轮不是 real field pass、真实手机/browser、HIL、WAVE ROVER 或 Objective 5 external proof。

## 3. 接口 contract

输入：

- `trashbot.route_task_field_retest_result_callback_review_decision.v1`
- `trashbot.route_task_field_retest_result_callback_review_decision_summary.v1`

输出：

- artifact schema：`trashbot.route_task_field_retest_result_callback_review_handoff.v1`
- summary schema：`trashbot.route_task_field_retest_result_callback_review_handoff_summary.v1`
- evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate`
- handoff status：
  - `ready_for_result_review_handoff`
  - `needs_owner_follow_up`
  - `needs_callback_rerun`
  - `evidence_ref_mismatch_rerun`
  - `blocked_unsafe_review_handoff`

Required fields：

- `safe_evidence_ref`
- `same_evidence_ref_required=true`
- `owner_follow_up`
- `review_ready_package`
- `rerun_package`
- `next_required_evidence`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 4. 子 agent 启动要求

本 sprint 为跨 owner Epic。A/B/C 必须并行启动；Product closeout 在 A/B/C 返回后执行。主节点不得直接写产品代码、测试代码或硬件配置。

下一步 worker prompt 必须完整复制对应 `.codex/agents/<role>.toml` 的 `prompt` 字段，并包含 `[本轮任务]`、`[文件范围]`、`[验收命令]`、`[输出要求]` 五段。

## 5. 验收命令

Task A / Autonomy：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_callback_review_handoff.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_callback_review_handoff.py
python3 pc-tools/evidence/route_task_field_retest_result_callback_review_handoff.py --help
rg -n "route_task_field_retest_result_callback_review_handoff|software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|ready_for_result_review_handoff|needs_owner_follow_up|evidence_ref_mismatch_rerun" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_callback_review_handoff.py pc-tools/evidence/test_route_task_field_retest_result_callback_review_handoff.py docs/interfaces/evidence_contracts.md
```

Task B / Robot：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_callback_review_handoff|software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_evidence_ref|ready_for_result_review_handoff|needs_owner_follow_up" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C / Full-stack：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_callback_review_handoff|software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false|blocked copy unavailable|safe_evidence_ref|ready_for_result_review_handoff|needs_owner_follow_up" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task D / Product closeout：

```bash
rg -n "route_task_field_retest_result_callback_review_handoff|software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate|Objective 5|Objective 1|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_00-01_route-task-result-callback-review-handoff
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/tech-done.md sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/side2side_check.md sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/final.md
```

Planning docs acceptance：

```bash
test -f sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/pre_start.md && test -f sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/prd.md && test -f sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_result_callback_review_handoff|OKR 最低优先级核对|Objective 5|Objective 1|PR #4|PR #5|software_proof_docker_route_task_field_retest_result_callback_review_handoff_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.18_00-01_route-task-result-callback-review-handoff
git diff --check -- sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/pre_start.md sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/prd.md sprints/2026.05.18_00-01_route-task-result-callback-review-handoff/tech-plan.md
```

## 6. OKR 最低优先级核对

当前 `OKR.md` 4.1 数值最低 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。下一低项是 Objective 1：硬件协议可信底盘，约 81%。

本 sprint 不针对 Objective 5。

理由：Objective 5 要继续提升，必须拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。当前主机只有 Docker；继续做本地 metadata、sample、fixture 或 review handoff 不会产生 Objective 5 external proof。

本 sprint 也不继续 Objective 1。

理由：最近 `2026.05.17_21-22_wave-rover-hil-packet-intake`、`2026.05.17_22-23_wave-rover-hil-packet-review-decision`、`2026.05.17_23-24_wave-rover-hil-packet-execution-pack` 已连续围绕同一真实 WAVE ROVER HIL packet blocker 做 intake / review decision / execution pack。本机无真实硬件，继续本地包装会重复消费同一 blocker，且不能声明 `hil_pass`。

本 sprint 针对 Objective 2 / Objective 3 的 route/elevator result callback review handoff。理由：PR #4 要求 elevator-assisted delivery 成为必达能力；上一轮 `route_task_field_retest_result_callback_review_decision` 已完成，下一步最小可行动作是把 review decision 转成 result review 前 handoff/status/owner follow-up/rerun package，服务真实现场材料后续回填链。

## 7. 风险和边界

- 本轮不处理真实 WAVE ROVER、UART、HIL 或 PR #5 2D LiDAR / ToF 真实硬件材料。
- 本轮不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 dropoff/cancel completion 或 delivery success。
- 本轮不证明真实手机/browser、production app、PWA prompt/user choice 或 Objective 5 external proof。
- 若 callback review decision 使用不同 `safe_evidence_ref`，或者存在 missing/rejected/unsafe updates，输出必须 blocked / follow-up / rerun，而不是 ready。
- 若任何输出出现 raw artifact、local path、checksum、secret、ROS topic、serial/UART、WAVE ROVER 参数、success phrasing 或 control claim，验收失败。

## 8. Worker 最小任务摘要

- Autonomy：新增 `route_task_field_retest_result_callback_review_handoff` PC gate、fixture、focused unittest，并更新 evidence contract；保持 Docker-only `not_proven` 边界。
- Robot：新增 diagnostics metadata-only consumer 和 focused unittest，更新 ROS contract；只读消费 summary，不改变控制路径。
- Full-stack：新增 mobile/web 只读 handoff panel、fixture/test，更新 mobile user flow；不改变 primary action gating。
- Product：A/B/C 验证通过后补 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 progress log，保持证据边界。

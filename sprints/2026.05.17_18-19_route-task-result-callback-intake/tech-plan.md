# Sprint 2026.05.17_18-19 Route Task Result Callback Intake - Tech Plan

sprint_type: epic

## 1. 技术目标

实现 `route_task_field_retest_result_callback_intake`，承接上一轮 `route_task_field_retest_result_review_dispatch` 的 owner work orders、callback packet requirements 和 rerun commands。它应在 Docker-only 环境中用 safe sample / fixture 验证 callback packet 摄取规则，并输出可供后续 review decision 使用的安全 summary。

目标 evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_intake_gate`。所有面向 PC / Robot / mobile 的输出必须保留 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 文件范围和 owner

Task A / Autonomy Algorithm Engineer：

- 允许改动：
  - `pc-tools/evidence/route_task_field_retest_result_callback_intake.py`
  - `pc-tools/evidence/test_route_task_field_retest_result_callback_intake.py`
  - `docs/interfaces/evidence_contracts.md`
- 责任：
  - 定义 intake gate 输入 / 输出 schema。
  - 校验 dispatch artifact / summary、callback packet safe sample、`safe_evidence_ref`、work order fulfilment、callback requirements。
  - 输出 `trashbot.route_task_field_retest_result_callback_intake.v1` / `_summary.v1`。

Task B / Robot Platform Engineer：

- 允许改动：
  - `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - `docs/interfaces/ros_contracts.md`
- 责任：
  - 增加 diagnostics metadata-only consumer。
  - 支持 file/env/top-level/nested summary。
  - 对 unsafe / missing / unsupported summary fail closed。
  - 不改变 ROS2 action、task_orchestrator、Start / Dropoff / Cancel / ACK / Nav2 / HIL 控制路径。

Task C / User Touchpoint Full-Stack Engineer：

- 允许改动：
  - `mobile/web/app.js`
  - `mobile/fixtures/mobile_web_status.fixture.json`
  - `mobile/web/test_mobile_web_entrypoint.py`
  - `docs/product/mobile_user_flow.md`
- 责任：
  - 增加只读 callback intake panel。
  - 显示 intake status、accepted / missing / rejected updates、owner follow-up、safe evidence ref、boundary flags、`not_proven`。
  - copy/export 只使用 `safe_copy`，缺失时显示 `blocked copy unavailable`。
  - 不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Task D / Product Manager / OKR Owner：

- 允许改动：
  - `OKR.md`
  - `docs/process/okr_progress_log.md`
  - `sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-done.md`
  - `sprints/2026.05.17_18-19_route-task-result-callback-intake/side2side_check.md`
  - `sprints/2026.05.17_18-19_route-task-result-callback-intake/final.md`
- 责任：
  - 仅在 A/B/C durable work landed 且验证通过后更新 OKR 和 closeout。
  - 明确本轮不是 real field pass、真实手机/browser、HIL 或 Objective 5 external proof。

## 3. 接口 contract

输入：

- 上一轮 dispatch artifact 或 summary：
  - `trashbot.route_task_field_retest_result_review_dispatch.v1`
  - `trashbot.route_task_field_retest_result_review_dispatch_summary.v1`
- callback packet safe sample / fixture：
  - 必须包含 `safe_evidence_ref`。
  - 必须引用 dispatch 的 owner work orders。
  - 必须逐项回应 callback packet requirements。
  - 必须把原始现场材料压缩成 phone-safe / robot-safe metadata。

输出：

- artifact schema：`trashbot.route_task_field_retest_result_callback_intake.v1`
- summary schema：`trashbot.route_task_field_retest_result_callback_intake_summary.v1`
- evidence boundary：`software_proof_docker_route_task_field_retest_result_callback_intake_gate`
- required flags：
  - `not_proven`
  - `delivery_success=false`
  - `primary_actions_enabled=false`

accepted / missing / rejected 更新规则：

- accepted：callback packet 满足同一 `safe_evidence_ref`、对应 owner work order、对应 callback requirement，且没有 raw path / checksum / secret / success claim / control claim。
- missing：dispatch 要求存在，但 callback packet 未提供或未覆盖。
- rejected：callback packet 提供了材料，但 schema、boundary、`safe_evidence_ref`、safe copy、success/control claim 或 material safety 不合格。

## 4. 子 agent 启动要求

本 sprint 为跨 owner Epic，默认并行启动 3 个 Engineer 子 agent：

- Autonomy Algorithm Engineer 执行 Task A。
- Robot Platform Engineer 执行 Task B。
- User Touchpoint Full-Stack Engineer 执行 Task C。

Product Manager / OKR Owner 在 A/B/C 返回后执行 Task D closeout。主节点不得直接写产品代码、测试代码或硬件配置；子 agent 必须按文件范围工作，不得回滚他人改动。

## 5. 验收命令

Task A / Autonomy：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/route_task_field_retest_result_callback_intake.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest pc-tools/evidence/test_route_task_field_retest_result_callback_intake.py
python3 pc-tools/evidence/route_task_field_retest_result_callback_intake.py --help
rg -n "route_task_field_retest_result_callback_intake|software_proof_docker_route_task_field_retest_result_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_evidence_ref|owner_work_orders|callback_packet_requirements" pc-tools/evidence docs/interfaces/evidence_contracts.md
git diff --check -- pc-tools/evidence/route_task_field_retest_result_callback_intake.py pc-tools/evidence/test_route_task_field_retest_result_callback_intake.py docs/interfaces/evidence_contracts.md
```

Task B / Robot：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "route_task_field_retest_result_callback_intake|software_proof_docker_route_task_field_retest_result_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_evidence_ref" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

Task C / Full-stack：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "route_task_field_retest_result_callback_intake|software_proof_docker_route_task_field_retest_result_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false|blocked copy unavailable|safe_evidence_ref" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/fixtures/mobile_web_status.fixture.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md
```

Task D / Product closeout：

```bash
rg -n "route_task_field_retest_result_callback_intake|software_proof_docker_route_task_field_retest_result_callback_intake_gate|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_18-19_route-task-result-callback-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-done.md sprints/2026.05.17_18-19_route-task-result-callback-intake/side2side_check.md sprints/2026.05.17_18-19_route-task-result-callback-intake/final.md
```

Planning docs acceptance：

```bash
test -f sprints/2026.05.17_18-19_route-task-result-callback-intake/pre_start.md && test -f sprints/2026.05.17_18-19_route-task-result-callback-intake/prd.md && test -f sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-plan.md
rg -n "sprint_type: epic|route_task_field_retest_result_callback_intake|OKR 最低优先级核对|Objective 5|PR #4|PR #5|software_proof_docker_route_task_field_retest_result_callback_intake_gate|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_18-19_route-task-result-callback-intake
git diff --check -- sprints/2026.05.17_18-19_route-task-result-callback-intake/pre_start.md sprints/2026.05.17_18-19_route-task-result-callback-intake/prd.md sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-plan.md
```

## 6. OKR 最低优先级核对

当前 `OKR.md` 4.1 数值最低 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。

本 sprint 不针对 Objective 5。

理由：Objective 5 要继续提升，必须拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。当前主机只有 Docker；继续做本地 metadata、sample、fixture 或 callback intake 不会产生 Objective 5 external proof。根据最近 sprint final 和 tech-done，本轮可行动作是接 PR #4 route/elevator 主线，从 review dispatch 推进到 callback intake，并为后续 review decision 准备安全证据链。

## 7. 风险和边界

- 本轮不处理真实 WAVE ROVER、UART、HIL 或 PR #5 2D LiDAR / ToF 真实硬件材料。
- 本轮不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实 route completion signal、真实 task record、真实 dropoff/cancel completion 或 delivery success。
- 本轮不证明真实手机/browser、production app、PWA prompt/user choice 或 Objective 5 external proof。
- 若 callback packet 使用不同 `safe_evidence_ref`，或者未满足 `owner_work_orders` / `callback_packet_requirements`，输出必须 blocked / rejected / missing，而不是 ready。
- 若任何面出现 raw artifact、local path、checksum、secret、ROS topic、serial/UART、WAVE ROVER 参数、success phrasing 或 control claim，验收失败。

## 8. 完成后收口要求

实现完成后必须更新：

- `sprints/2026.05.17_18-19_route-task-result-callback-intake/tech-done.md`
- `sprints/2026.05.17_18-19_route-task-result-callback-intake/side2side_check.md`
- `sprints/2026.05.17_18-19_route-task-result-callback-intake/final.md`

若 A/B/C durable work landed 且验证通过，Product closeout 再更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。OKR 增幅必须保守，并明确 `software_proof_docker_route_task_field_retest_result_callback_intake_gate` 不是 real field pass / HIL / real phone / O5 proof。

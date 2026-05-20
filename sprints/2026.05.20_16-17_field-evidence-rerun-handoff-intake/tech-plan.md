# Field Evidence Rerun Handoff Intake Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use role-specific worker execution through `spawn_agent(agent_type=worker)` and follow the fixed prompt structure from `AGENTS.md`. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `field_evidence_rerun_handoff_intake` as the next field-evidence rerun follow-through after `field_evidence_rerun_callback_review_handoff`, keeping all outputs `software_proof` / `not_proven` / fail-closed.

**Architecture:** Autonomy creates the PC artifact/summary gate. Robot consumes only the safe summary through a diagnostics alias. Full-stack renders the Robot-safe summary in `mobile/web` as a read-only panel. Product closes the sprint and keeps OKR progress conservative.

**Tech Stack:** Python PC evidence gate and unittest; ROS2 behavior diagnostics Python; dependency-free `mobile/web` JavaScript fixtures/tests; Markdown docs.

---

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 数字最低 Objective 是 Objective 5，约 68%。
2. 本 sprint 不主推进 Objective 5。原因：当前 Docker-only 主机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof。继续做本地 O5 metadata depth 不会改变 O5 的真实缺口。
3. 当前下一低项 Objective 1 约 81%，但本 sprint 也不主推进 Objective 1。原因：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending；manual reply comment `3269642220` 是 `software_proof` / `not_proven`，不是 hardware proof；本机没有 WAVE ROVER/UART/HIL 或真实 2D LiDAR / ToF 材料。
4. 本 sprint 推荐并启动 Objective 2 / Objective 3 / Objective 4 的 field evidence handoff-intake follow-through。理由：最近 `12-13 -> 15-16` sprint 已形成 `field_evidence_rerun_material_dispatch -> field_evidence_rerun_callback_intake -> field_evidence_rerun_callback_review_decision -> field_evidence_rerun_callback_review_handoff`，下一步是接收 owner-safe handoff intake packet，而不是重复 O5/O1 blocker。
5. 本轮所有产物必须继续写成 `software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 文件结构和职责

- `pc-tools/evidence/field_evidence_rerun_handoff_intake.py`: 新 PC gate，消费上一轮 `field_evidence_rerun_callback_review_handoff` summary 与 owner-safe handoff intake packet，输出 artifact/summary。
- `tests/test_field_evidence_rerun_handoff_intake.py`: PC gate 单元测试和 CLI fixture tests。
- `pc-tools/README.md`: 记录 gate 用法、输入输出和 evidence boundary。
- `docs/interfaces/evidence_contracts.md`: 记录 artifact schema、summary schema、required fields 和 fail-closed rules。
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`: 新增 `robot_diagnostics_field_evidence_rerun_handoff_intake_summary` safe alias。
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`: diagnostics alias test。
- `docs/interfaces/ros_runtime_contracts.md`: 记录 Robot diagnostics safe summary contract。
- `mobile/web/app.js`: 新增只读“现场证据复跑交接回执”panel。
- `mobile/web/fixtures/status.json` and compatible fixture files: 增加 Robot safe alias fixture。
- `mobile/web/test_mobile_web_entrypoint.py`: 增加 panel 和 gating 不变测试。
- `docs/product/mobile_user_flow.md`: 记录 panel 消费、禁止项和证据边界。
- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/tech-done.md`: Product closeout 实际改动和验证结果。
- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/side2side_check.md`: Product side-by-side 验收。
- `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/final.md`: Product final closeout。
- `OKR.md`: 保守更新 4.1 快照和当前最高优先级。
- `docs/process/okr_progress_log.md`: 追加本轮进展记录。

## 并行启动规则

本 sprint 是 Epic，涉及 4 个 owner，文件范围互不重叠且接口以 safe summary contract 串联。必须在同一轮并行启动 4 个 worker：

1. `autonomy-engineer`
2. `robot-software-engineer`
3. `full-stack-software-engineer`
4. `product-okr-owner`

接口顺序：Autonomy 定义 artifact/summary contract；Robot 和 Full-stack 可以按 tech-plan 的 contract 先实现 fail-closed compatible consumer。若 Autonomy 最终字段名有差异，Robot/Full-stack worker 必须在各自输出中列为 integration risk，由 Product closeout 要求补一次协调修正。

## 全局证据边界

所有 owner 必须保留以下字段和 copy：

- `source=software_proof`
- `software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- evidence boundary: `software_proof_docker_field_evidence_rerun_handoff_intake_gate`

禁止写成：

- HIL pass
- 真实 route/elevator field pass
- 真实 phone/browser
- Objective 5 external proof
- 真实 dropoff/cancel completion
- delivery success
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved

## Task 1: Autonomy PC Gate

**Owner:** `autonomy-engineer`

**Files:**
- Create: `pc-tools/evidence/field_evidence_rerun_handoff_intake.py`
- Create: `tests/test_field_evidence_rerun_handoff_intake.py`
- Modify: `pc-tools/README.md`
- Modify: `docs/interfaces/evidence_contracts.md`

**本轮任务:**
新增 PC gate `field_evidence_rerun_handoff_intake`，消费上一轮 `field_evidence_rerun_callback_review_handoff` summary 和 owner-safe handoff intake packet，输出 artifact/summary。必须 fail closed，必须保留 same safe `evidence_ref` 和全局证据边界。

**Acceptance Commands:**
- `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_handoff_intake.py tests/test_field_evidence_rerun_handoff_intake.py`
- `python3 -m unittest tests.test_field_evidence_rerun_handoff_intake`
- `python3 pc-tools/evidence/field_evidence_rerun_handoff_intake.py --help`
- `rg -n "field_evidence_rerun_handoff_intake|software_proof_docker_field_evidence_rerun_handoff_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" pc-tools/evidence/field_evidence_rerun_handoff_intake.py tests/test_field_evidence_rerun_handoff_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md`
- `git diff --check -- pc-tools/evidence/field_evidence_rerun_handoff_intake.py tests/test_field_evidence_rerun_handoff_intake.py pc-tools/README.md docs/interfaces/evidence_contracts.md`

- [ ] Step 1: Read prior gate patterns for `field_evidence_rerun_callback_review_handoff`, `field_evidence_rerun_callback_review_decision`, and `field_evidence_rerun_callback_intake`.
- [ ] Step 2: Write failing tests for accepted handoff intake, missing prior summary, evidence-ref mismatch, unsafe success claims, and missing required owner packet fields.
- [ ] Step 3: Implement the CLI and pure functions with Chinese technical comments where logic is non-trivial.
- [ ] Step 4: Update PC README and evidence contract docs with schema names and boundary language.
- [ ] Step 5: Run all acceptance commands and return logs.

## Task 2: Robot Diagnostics Safe Alias

**Owner:** `robot-software-engineer`

**Files:**
- Modify: `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- Modify: `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- Modify: `docs/interfaces/ros_runtime_contracts.md`

**本轮任务:**
新增 Robot diagnostics safe alias `robot_diagnostics_field_evidence_rerun_handoff_intake_summary`。该 alias 只能消费 safe summary，metadata-only / fail-closed，不得暴露 raw artifacts、ROS topics、serial/UART、WAVE ROVER 参数、credentials、local paths、checksums 或 success claims。

**Acceptance Commands:**
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `rg -n "robot_diagnostics_field_evidence_rerun_handoff_intake_summary|field_evidence_rerun_handoff_intake|software_proof_docker_field_evidence_rerun_handoff_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md`
- `git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_runtime_contracts.md`

- [ ] Step 1: Read existing diagnostics alias patterns for field evidence rerun callback review handoff.
- [ ] Step 2: Add tests proving the alias appears only with safe fields and fails closed on missing/unsafe summaries.
- [ ] Step 3: Implement alias extraction and sanitization with Chinese technical comments for safety filters.
- [ ] Step 4: Update ROS runtime contract docs.
- [ ] Step 5: Run all acceptance commands and return logs.

## Task 3: Mobile Web Read-Only Panel

**Owner:** `full-stack-software-engineer`

**Files:**
- Modify: `mobile/web/app.js`
- Modify: `mobile/web/fixtures/status.json`
- Modify: compatible mobile/web fixture files if the current test suite requires them.
- Modify: `mobile/web/test_mobile_web_entrypoint.py`
- Modify: `docs/product/mobile_user_flow.md`

**本轮任务:**
在 `mobile/web` 增加只读“现场证据复跑交接回执”panel，优先消费 `robot_diagnostics_field_evidence_rerun_handoff_intake_summary`，兼容 safe summary 字段。Start Delivery、Confirm Dropoff、Cancel gating 必须完全不变。

**Acceptance Commands:**
- `node --check mobile/web/app.js`
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`
- `python3 -m json.tool mobile/web/fixtures/status.json >/dev/null`
- `rg -n "现场证据复跑交接回执|robot_diagnostics_field_evidence_rerun_handoff_intake_summary|field_evidence_rerun_handoff_intake|software_proof_docker_field_evidence_rerun_handoff_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures docs/product/mobile_user_flow.md`
- `git diff --check -- mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py mobile/web/fixtures docs/product/mobile_user_flow.md`

- [ ] Step 1: Read existing mobile panels for field evidence rerun callback review handoff, callback review decision, and callback intake.
- [ ] Step 2: Add fixture data for the Robot diagnostics safe alias.
- [ ] Step 3: Add tests proving the panel renders safe status and primary buttons remain disabled/unchanged.
- [ ] Step 4: Implement the read-only panel with no new commands, fetches, copy/export controls, ACK/cursor calls, or control routes.
- [ ] Step 5: Update mobile user flow docs with consumer rules and not-proven boundary.
- [ ] Step 6: Run all acceptance commands and return logs.

## Task 4: Product Closeout

**Owner:** `product-okr-owner`

**Files:**
- Create: `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/tech-done.md`
- Create: `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/side2side_check.md`
- Create: `sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/final.md`
- Modify: `OKR.md`
- Modify: `docs/process/okr_progress_log.md`

**本轮任务:**
在三个 Engineer worker 完成后，汇总实际改动、验证结果、偏差、剩余风险，保守更新 OKR 和 progress log。最终必须说明 Objective 5 / Objective 1 为什么不提升，Objective 2 / 3 / 4 为什么仍只能保持 `software_proof` / `not_proven`。

**Acceptance Commands:**
- `test -f sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/tech-done.md`
- `test -f sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/side2side_check.md`
- `test -f sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake/final.md`
- `rg -n "Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|3269642220|field_evidence_rerun_handoff_intake|software_proof|not_proven|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake`
- `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_16-17_field-evidence-rerun-handoff-intake`

- [ ] Step 1: Wait for all Engineer worker outputs.
- [ ] Step 2: Verify each worker lists changed files, command outputs, failures if any, and remaining risk.
- [ ] Step 3: Create `tech-done.md` with actual changes and validation evidence.
- [ ] Step 4: Create `side2side_check.md` comparing PRD/tech-plan acceptance against worker outputs.
- [ ] Step 5: Update `OKR.md` 4.1 and current highest priority without increasing O5/O1 from software-only evidence.
- [ ] Step 6: Append `docs/process/okr_progress_log.md`.
- [ ] Step 7: Create `final.md` with OKR impact, evidence boundary, PR #5 state, and next-step risk.
- [ ] Step 8: Run Product acceptance commands and return logs.

## Integration Validation

After all workers finish, the main orchestrator or integration worker must run a narrow, fenced validation set:

- Autonomy PC gate tests and CLI help from Task 1.
- Robot diagnostics tests from Task 2.
- `node --check` and mobile entrypoint tests from Task 3.
- Product closeout checks from Task 4.
- Required `rg` over touched implementation/docs for `field_evidence_rerun_handoff_intake`, `software_proof`, `not_proven`, `safe_to_control=false`, `delivery_success=false`, and `primary_actions_enabled=false`.
- Scoped `git diff --check` over touched files only.

Do not run broad unrelated sweeps unless a worker changes shared behavior beyond this plan.

## Risk and Failure Handling

- If real field materials are absent, output stays blocked/not_proven; do not mark the sprint failed solely because real hardware or external proof is missing.
- If owner-safe handoff intake packet has mismatched `evidence_ref`, PC gate must fail closed and Robot/mobile must surface missing or mismatch state only.
- If mobile panel sees both raw artifact and safe summary, safe summary wins; raw artifact must not be rendered.
- If any implementation tries to enable primary actions from this summary, reject the change and send it back to the responsible worker.
- If PR #5 thread state changes during implementation, Product closeout must re-check live PR #5 before final wording; until verified resolved with real material, treat `PRRT_kwDOSWB9286CJ3tX` as unresolved/material pending.

## Handoff Prompt Requirements

Each worker prompt must include the five sections required by `AGENTS.md`:

1. `[角色 System Prompt]`
2. `[本轮任务]`
3. `[文件范围]`
4. `[验收命令]`
5. `[输出要求]`

Worker output must return:

1. Actual changed file list.
2. Verification command output snippets.
3. Failure localization if any.
4. Remaining risks.

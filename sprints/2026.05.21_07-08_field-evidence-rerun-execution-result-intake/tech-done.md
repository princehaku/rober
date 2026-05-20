# Field Evidence Rerun Execution Result Intake Tech Done

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_07-08_field-evidence-rerun-execution-result-intake`
- Closeout time: 2026-05-21 07:08 Asia/Shanghai
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`
- Product owner: `product-okr-owner`
- Engineering owners: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`

## 用户价值和产品北极星

普通手机用户和现场 owner 不应该把“执行结果回填入口”理解成机器人已经真实送达。本轮价值是把 execution handoff 后的 result packet 变成安全、可复核、可在手机只读展示的状态：`missing`、`accepted`、`rejected` 或 `blocked`。其中 `accepted` 只表示 accepted for review intake，不是 field pass、delivery result 或 delivery success。

产品北极星保持不变：低成本 ROS2 垃圾小车最终要能被普通手机用户操作，并用同一 safe `evidence_ref` 证明路线、电梯、投放和结果。当前 sprint 只补结果回填的软件证明入口。

## OKR 映射与 KR 拆解

- Objective 5：保持约 68%。本轮不是 O5 external proof，不新增公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/cutover。
- Objective 1：保持约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending；PR #6 仍是 docs-only。
- Objective 2/3/4：保守保持约 99%。本轮让 field evidence rerun execution result intake 在 PC、Robot diagnostics 和 mobile/web 三个面形成一致 fail-closed 入口，但不证明真实 field rerun、真实 Nav2/fixed-route runtime、真实 route/elevator field pass、dropoff/cancel completion、delivery result 或 true phone/browser proof。

## 实际改动

Autonomy Algorithm Engineer 已完成：

- `pc-tools/evidence/field_evidence_rerun_execution_result_intake.py`
- `tests/test_field_evidence_rerun_execution_result_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

Autonomy 侧产出：

- 新增 `trashbot.field_evidence_rerun_execution_result_intake.v1` / summary PC gate。
- 承接 `field_evidence_rerun_execution_callback_review_handoff` 后的 owner result packet。
- 输出 `missing` / `accepted` / `rejected` / `blocked`、safe `evidence_ref`、missing/rejected/blocked reason、next required evidence 和 fail-closed safe copy。
- 保持 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

Robot Platform Engineer 已完成：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_runtime_contracts.md`

Robot 侧产出：

- 新增 `robot_diagnostics_field_evidence_rerun_execution_result_intake_summary` safe alias。
- 只读暴露 result intake status、safe `evidence_ref`、owner handoff、missing/rejected/blocked reasons、next required evidence 和 preserved false states。
- 拒绝 raw artifacts、unsafe result material、serial/UART/WAVE ROVER/ROS topic/credential/path/traceback 泄漏。

User Touchpoint Full-Stack Engineer 已完成：

- `mobile/web/app.js`
- `mobile/web/fixtures/status.json`
- `mobile/web/fixtures/robot_diagnostics_field_evidence_rerun_execution_result_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Full-Stack 侧产出：

- 新增只读“现场证据复跑执行结果回填”mobile panel。
- 展示 safe `evidence_ref`、result packet state、next required evidence、evidence boundary、`not_proven` 与 fail-closed flags。
- Start Delivery / Confirm Dropoff / Cancel 保持 disabled，不发送 ACK、cursor、diagnostics fetch、queue/execution/callback/review/handoff/result submission 或 robot command request。

Product Manager / OKR Owner 已完成 closeout：

- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/tech-done.md`
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/side2side_check.md`
- `sprints/2026.05.21_07-08_field-evidence-rerun-execution-result-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Autonomy worker validation:

```text
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_result_intake.py passed
python3 -m unittest tests.test_field_evidence_rerun_execution_result_intake
Ran 5 tests ... OK
CLI --help passed
required rg passed
scoped git diff --check passed
```

Robot worker validation:

```text
python3 -m py_compile operator_gateway_diagnostics.py and test_operator_gateway_diagnostics.py passed
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 251 tests ... OK
required rg passed
scoped git diff --check passed
```

Full-Stack worker validation:

```text
node --check mobile/web/app.js passed
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
Ran 199 tests ... OK
JSON fixture checks passed
required rg passed
scoped git diff --check passed
```

Product closeout validation is recorded in `final.md`.

## 偏差与失败定位

- Engineer workers reported their focused fences passed. Product closeout did not rerun Engineer implementation tests by request; it only ran the closeout acceptance commands.
- No closeout file-missing, required-marker, or whitespace failure remained after Product validation.

## 剩余风险与非证明边界

This sprint closes only `software_proof_docker_field_evidence_rerun_execution_result_intake_gate`. It is not:

- real field rerun
- real Nav2/fixed-route runtime
- real route/elevator field pass
- HIL
- true phone/browser proof
- O5 external proof
- PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved
- PR #6 runtime proof
- dropoff/cancel completion
- delivery result
- delivery success

Objective 5 remains about 68%, Objective 1 remains about 81%, and Objectives 2/3/4 conservatively remain about 99%.

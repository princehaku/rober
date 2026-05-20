# Field Evidence Rerun Execution Callback Intake Final

## Sprint Declaration

- sprint_type: epic
- Sprint: `2026.05.21_01-02_field-evidence-rerun-execution-callback-intake`
- Capability: `field_evidence_rerun_execution_callback_intake`
- Closeout time: 2026-05-21 01:23 Asia/Shanghai
- Evidence boundary: `software_proof_docker_field_evidence_rerun_execution_callback_intake_gate`
- Required preserved states: `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`

## 实际改动

Engineering 已完成：

- Autonomy：新增 PC gate `pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py`、focused test 和 evidence contract docs。
- Robot：新增 diagnostics safe alias `robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary`、focused tests 和 ROS runtime contract docs，并修复 raw status leak。
- Full-Stack：新增 mobile/web 只读“现场证据复跑执行回执入口”panel、fixture/test 和 mobile user flow docs。

Product closeout 本轮更新：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-done.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/side2side_check.md`
- `sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/final.md`

## OKR 进度

- Objective 5 保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实 phone/browser external proof。
- Objective 1 保持约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / material pending；本轮没有 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或真实 2D LiDAR / ToF materials。PR #6 仍是 docs-only。
- Objectives 2/3/4 保持约 99%。本轮只证明 callback intake 的 metadata/read-only software proof，不是真实现场材料、真实 route/elevator field pass、真实 phone/browser、HIL 或 delivery success。

## 验证结果

Product closeout commands 已通过：

```text
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/tech-done.md
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/side2side_check.md
test -f sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake/final.md
rg -n "field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|PR #6" OKR.md docs/process/okr_progress_log.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md docs sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```

集成围栏复验已通过：

```text
python3 -m py_compile pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py
python3 -m unittest tests.test_field_evidence_rerun_execution_callback_intake
PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
node --check mobile/web/app.js
python3 -m unittest mobile/web/test_mobile_web_entrypoint.py
python3 -m json.tool mobile/web/fixtures/status.json >/dev/null
python3 pc-tools/evidence/field_evidence_rerun_execution_callback_intake.py --help
rg -n "robot_diagnostics_field_evidence_rerun_execution_callback_intake_summary|field_evidence_rerun_execution_callback_intake|software_proof_docker_field_evidence_rerun_execution_callback_intake_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven|现场证据复跑执行回执入口" pc-tools/evidence tests onboard/src/ros2_trashbot_behavior mobile/web docs/interfaces docs/product/mobile_user_flow.md sprints/2026.05.21_01-02_field-evidence-rerun-execution-callback-intake
```

## 失败定位

- Engineer 阶段 Robot worker 首轮发现 raw `latest_status` 输入会回显到 diagnostics；已通过剥离 `field_evidence_rerun_execution_callback_intake*` raw status keys 修复，最终 diagnostics suite `Ran 241 tests OK`。
- Product closeout 阶段没有新增验证失败。

## 剩余风险

- 没有真实 field rerun、真实 Nav2/fixed-route runtime、真实 route completion signal、真实现场 task record、真实电梯门/楼层/人工协助、真实 dropoff/cancel completion、真实 delivery result 或真实 phone/browser。
- 没有 WAVE ROVER/UART/HIL、PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved、PR #6 runtime proof 或 Objective 5 external proof。
- `accepted` 只代表 callback packet 的材料分类可进入后续 review，不代表材料真实、现场通过、交付成功或主操作可用。

## 下一步

若继续本链路，下一轮应进入 `field_evidence_rerun_execution_callback_review_decision`，只在收到同一 safe `evidence_ref` 的真实现场 execution callback packet 后做 review decision；没有真实材料时，不应继续把 fixture、summary 或 accepted 分类写成 OKR 百分比提升。

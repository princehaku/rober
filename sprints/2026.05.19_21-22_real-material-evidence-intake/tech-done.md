# Sprint 2026.05.19_21-22 Real Material Evidence Intake - Tech Done

## 1. Sprint 类型和收口边界

- sprint_type: epic
- 本轮完成 `real_material_evidence_intake` 统一真实材料回填入口，覆盖 O5 external、O1 / PR #5 hardware、PR #4 route/elevator、O4 real phone 四类 material group。
- 证据边界：`software_proof_docker_real_material_evidence_intake_gate`。
- 结果保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 本轮不证明真实 external proof、真实 WAVE ROVER UART/HIL、PR #5 hardware materials、PR #4 route/elevator field pass、真实 phone/browser、dropoff/cancel completion 或 delivery success。

## 2. Hardware / Autonomy Owner 结果

实际改动：

- 新增 `pc-tools/evidence/real_material_evidence_intake.py`。
- 新增 `tests/test_real_material_evidence_intake.py`。
- 新增 `docs/interfaces/real_material_evidence_intake.md`。
- 生成 `sprints/2026.05.19_21-22_real-material-evidence-intake/evidence/real_material_evidence_intake.json`。
- 生成 `sprints/2026.05.19_21-22_real-material-evidence-intake/evidence/real_material_evidence_intake_summary.json`。

已完成能力：

- PC gate 支持 material manifest / sample manifest。
- 按 `o5_external`、`o1_pr5_hardware`、`pr4_route_elevator`、`o4_real_phone` 输出 `accepted_items`、`missing_items`、`rejected_items`、safe `evidence_ref`、`next_action` 和 `owner_handoff`。
- 拒绝空或不安全 `evidence_ref`、跨组不一致、success/control 字段、凭证、绝对路径和敏感 token。
- 已查阅 `docs/vendor/VENDOR_INDEX.md` 及其指向的 WAVE ROVER 本地资料；本轮只记录 source boundary，不声明真实 WAVE ROVER UART/HIL、2D LiDAR/ToF 或 PR #5 closure。

Owner 验证：

- `python3 -m unittest tests/test_real_material_evidence_intake.py`：`Ran 5 tests ... OK`。
- CLI help：通过。
- artifact generation：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。
- `py_compile`：通过。

## 3. Robot Owner 结果

实际改动：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`。
- 更新 `docs/interfaces/ros_contracts.md`。

已完成能力：

- 新增 `robot_diagnostics_real_material_evidence_intake_summary` safe alias。
- 只读消费 `trashbot.real_material_evidence_intake_summary.v1` / artifact sanitized summary。
- 缺 summary、schema/boundary mismatch、unsafe `evidence_ref`、raw JSON、checksum、credential、ROS topic、UART/serial、success/control 字段均 fail closed。
- 不改变 Start Delivery、Confirm Dropoff、Cancel 或 robot command 路径。
- 第一轮发现原始字段仍透传，已修复并重跑通过。

Owner 验证：

- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 215 tests ... OK`。
- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。

## 4. Full-Stack Owner 结果

实际改动：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `docs/product/mobile_user_flow.md`。

已完成能力：

- mobile/web 增加只读“真实材料回填入口” panel。
- 优先消费 `robot_diagnostics_real_material_evidence_intake_summary`，兼容 `real_material_evidence_intake_summary` / phone-safe summary。
- 只展示 `intake_status`、`material_group`、safe `evidence_ref`、accepted/missing/rejected items、`next_action`、`owner_handoff`、`evidence_boundary` 和 `not_proven`。
- 不新增控制按钮，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

Owner 验证：

- `python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 139 tests ... OK`。
- `node --check mobile/web/app.js`：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。

## 5. Product 集成验收

Product closeout 复跑跨 owner 验收命令，结果记录在 `side2side_check.md` 和 `final.md`：

- PC gate unittest：通过，`Ran 5 tests ... OK`。
- Robot diagnostics unittest：通过，`Ran 215 tests ... OK`。
- mobile/web entrypoint test：通过，`Ran 139 tests ... OK`。
- `node --check mobile/web/app.js`：通过。
- `py_compile`：通过。
- required `rg`：通过。
- scoped `git diff --check`：通过。
- staged `git diff --cached --check`：通过。

## 6. 偏差和风险

- 偏差：无需要扩大范围的偏差；Product closeout 只补齐 sprint 收口、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- 剩余风险：本轮仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover、真实 WAVE ROVER UART/HIL、PR #5 真实 2D LiDAR / ToF materials、PR #4 route/elevator field pass、真实 phone/browser、真实 dropoff/cancel completion 和 delivery success。
- OKR 影响：Objective 5 保持约 68%；Objective 1 保持约 81%；Objective 2 / 3 / 4 保持约 99%。本轮只增加真实材料回填 intake contract，不提高完成度。

# Sprint 2026.05.19_21-22 Real Material Evidence Intake - Side2Side Check

## 1. 验收结论

本轮跨 owner 验收通过。`real_material_evidence_intake` 已从 readiness board 的缺口展示推进到统一真实材料回填入口；PC gate、Robot diagnostics 和 mobile/web 均保持只读、fail-closed 和 phone-safe 边界。

验收边界仍是 `software_proof_docker_real_material_evidence_intake_gate`，不是任何真实世界能力通过。

## 2. PRD 对照

| PRD 要求 | 验收结果 | 证据 |
| --- | --- | --- |
| PC gate 读取 material manifest 并按 material group 输出 intake artifact | 通过 | `real_material_evidence_intake.py` 支持 `o5_external`、`o1_pr5_hardware`、`pr4_route_elevator`、`o4_real_phone`，输出 accepted/missing/rejected、safe `evidence_ref`、next action 和 owner handoff。 |
| manifest 缺失、不安全或含 success/control/credential/path/token 时 fail closed | 通过 | 单测覆盖 unsafe `evidence_ref`、跨组不一致、success/control 字段、凭证、绝对路径和敏感 token。 |
| Robot diagnostics 只消费 sanitized summary | 通过 | 新增 `robot_diagnostics_real_material_evidence_intake_summary`；缺 summary、schema/boundary mismatch、unsafe `evidence_ref`、raw JSON/checksum/credential/ROS topic/UART/serial/success/control 字段 fail closed。 |
| mobile/web 增加只读回填入口 panel | 通过 | panel 只展示 intake status、material group、safe `evidence_ref`、accepted/missing/rejected、next action、owner handoff、boundary 和 `not_proven`。 |
| 不改变 Start Delivery、Confirm Dropoff、Cancel gating | 通过 | Full-Stack 测试和代码检查确认未新增控制按钮，primary action gating 不变。 |
| docs 同步更新 | 通过 | `docs/interfaces/real_material_evidence_intake.md`、`operator_gateway_diagnostics.md`、`ros_contracts.md`、`docs/product/mobile_user_flow.md` 已同步。 |

## 3. 跨 owner 验收命令

Product closeout 复跑以下命令：

```bash
python3 -m unittest tests/test_real_material_evidence_intake.py
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
python3 mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m py_compile pc-tools/evidence/real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
rg -n "real_material_evidence_intake|robot_diagnostics_real_material_evidence_intake_summary|Objective 5|Objective 1|PR #5|PRRT_kwDOSWB9286CJ3tX|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false|Ran 5 tests|Ran 215 tests|Ran 139 tests" pc-tools/evidence/real_material_evidence_intake.py tests/test_real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/test_mobile_web_entrypoint.py docs/interfaces/real_material_evidence_intake.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_21-22_real-material-evidence-intake OKR.md docs/process/okr_progress_log.md
git diff --check -- pc-tools/evidence/real_material_evidence_intake.py tests/test_real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/interfaces/real_material_evidence_intake.md docs/interfaces/operator_gateway_diagnostics.md docs/interfaces/ros_contracts.md docs/product/mobile_user_flow.md sprints/2026.05.19_21-22_real-material-evidence-intake OKR.md docs/process/okr_progress_log.md
git diff --cached --check
```

结果：

- `tests/test_real_material_evidence_intake.py`：`Ran 5 tests ... OK`。
- `test_operator_gateway_diagnostics.py`：`Ran 215 tests ... OK`。
- `mobile/web/test_mobile_web_entrypoint.py`：`Ran 139 tests ... OK`。
- `node --check mobile/web/app.js`：exit 0。
- `py_compile`：exit 0。
- required `rg`：命中关键 contract、schema、boundary、OKR 风险和测试结果记录。
- scoped `git diff --check`：exit 0。
- staged `git diff --cached --check`：exit 0。

## 4. 不通过项和风险

- 不通过项：无。
- 风险：所有真实能力仍等待现场材料。当前结果不证明真实 external proof、HIL、PR #5 hardware materials、PR #4 route/elevator field pass、真实 phone/browser、dropoff/cancel completion 或 delivery success。
- OKR 验收：Objective 5 保持约 68%；Objective 1 保持约 81%；Objective 2 / 3 / 4 保持约 99%。本轮只允许记录 `software_proof_docker_real_material_evidence_intake_gate`。

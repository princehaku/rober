# Sprint 2026.05.19_21-22 Real Material Evidence Intake - Final

## 1. 收口结论

本轮 Epic sprint 已完成。`real_material_evidence_intake` 把上一轮 readiness board 的四类真实材料缺口推进为统一回填入口：现场 owner 可以按 material group 提交 manifest，PC gate 输出 accepted/missing/rejected，Robot diagnostics 和 mobile/web 只读消费 sanitized summary。

本轮证据边界是 `software_proof_docker_real_material_evidence_intake_gate`。它只证明 repo 内 intake、diagnostics 和 mobile 展示链路可 fail closed，不证明真实 external proof、真实 WAVE ROVER UART/HIL、PR #5 hardware materials、PR #4 route/elevator field pass、真实 phone/browser、dropoff/cancel completion 或 delivery success。

## 2. 实际交付

- Hardware/Autonomy：新增 `real_material_evidence_intake` PC gate、围栏单测、接口文档和 sprint evidence artifact；按 `o5_external`、`o1_pr5_hardware`、`pr4_route_elevator`、`o4_real_phone` 输出 intake 状态；拒绝 unsafe `evidence_ref`、跨组不一致、success/control 字段、凭证、绝对路径和敏感 token。
- Robot：新增 `robot_diagnostics_real_material_evidence_intake_summary` safe alias；只读消费 sanitized summary；缺 summary、schema/boundary mismatch、unsafe `evidence_ref`、raw JSON/checksum/credential/ROS topic/UART/serial/success/control 字段 fail closed；不改变 robot command 路径。
- Full-Stack：mobile/web 增加只读“真实材料回填入口” panel；优先消费 Robot safe alias，兼容 phone-safe summary；只展示 intake status、material group、safe `evidence_ref`、accepted/missing/rejected、next action、owner handoff、boundary 和 `not_proven`；不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- Product：补齐 `tech-done.md`、`side2side_check.md`、`final.md`，更新 `OKR.md` 4.1 / 6 / 7 和 `docs/process/okr_progress_log.md`。

## 3. 验证结果

Product closeout 复跑跨 owner 验收：

- `python3 -m unittest tests/test_real_material_evidence_intake.py`：`Ran 5 tests ... OK`。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 215 tests ... OK`。
- `python3 mobile/web/test_mobile_web_entrypoint.py`：`Ran 139 tests ... OK`。
- `node --check mobile/web/app.js`：exit 0。
- `python3 -m py_compile pc-tools/evidence/real_material_evidence_intake.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：exit 0。
- required `rg`：通过，覆盖 `real_material_evidence_intake`、Robot safe alias、Objective 5、Objective 1、PR #5、`PRRT_kwDOSWB9286CJ3tX`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` 和三组测试结果记录。
- scoped `git diff --check`：exit 0。
- staged `git diff --cached --check`：exit 0。

## 4. OKR 进度同步

- Objective 5 保持约 68%。本轮提供 O5 external material intake，但没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或真实 external proof。
- Objective 1 保持约 81%。本轮提供 O1 / PR #5 hardware material intake，但没有真实 WAVE ROVER UART/HIL、`feedback_T1001.log`、`/odom`、`/imu/data`、`/battery`、operator HIL report 或真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry；`PRRT_kwDOSWB9286CJ3tX` 仍不得关闭。
- Objective 2 / 3 / 4 保持约 99%。本轮只把 PR #4 route/elevator、Nav2/fixed-route、dropoff/cancel 和 real phone materials 纳入回填入口，不证明真实 field pass、真实手机/browser、dropoff/cancel completion 或 delivery success。

## 5. 剩余风险和下一步

- 剩余风险：真实材料仍未到位；任何 OKR 百分比提升都必须等现场 owner 用同一 safe `evidence_ref` 回填真实材料，并完成后续 review decision / handoff / execution pack 或对应 external proof。
- 下一步优先级：若 O5 external proof、O1 / PR #5 hardware materials、PR #4 route/elevator field materials 或 O4 real phone evidence 中任一类真实材料到位，先走本轮 intake，再进入对应 material review decision；如果仍无真实材料，不应继续重复 local metadata wrapper。
- 提交状态：本轮 closeout 已随 owner 变更一起 stage、commit 并 push 到 `origin/master`。

# Sprint 2026.05.16_08-09 Mobile Field Material Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_mobile_field_material_review_decision_gate`，把上一轮 `mobile_field_material_intake` 材料转换为 phone-safe review decision、blocker、next-required-evidence 和 owner handoff。A/B/C 三个 Engineer 文件范围已按 `tech-plan.md` 完成，D Product closeout 负责本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 收口。

Task A Full-stack：

- 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/fixtures/mobile_web_status.fixture.json`、`mobile/test_mobile_web_entrypoint.py`、`docs/product/mobile_user_flow.md`。
- 新增只读“现场材料评审决策”panel，展示 review decision、blocker、next-required-evidence、owner handoff、safe `evidence_ref`、same-evidence-ref、`not_proven` 和 boundary。
- Copy/export 保持 whitelist-only；Start Delivery、Confirm Dropoff、Cancel gating 未改变。

Task B Robot：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`、`docs/interfaces/ros_contracts.md`。
- 新增 `mobile_field_material_review_decision` / `mobile_field_material_review_decision_summary` diagnostics metadata-only consumer。
- 支持 explicit ref、`TRASHBOT_MOBILE_FIELD_MATERIAL_REVIEW_DECISION`、summary env 和 diagnostics source；schema/boundary enforce；bad/missing/unsafe/success claim fail closed。
- command、ACK、cursor、persistence、Nav2、HIL、dropoff/cancel、delivery-success flags 均保持 false。

Task C Autonomy：

- 新增/更新 `pc-tools/evidence/mobile_field_material_review_decision.py`、`pc-tools/evidence/test_mobile_field_material_review_decision.py`、`pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`。
- 新增 pc-tools gate，把 `mobile_field_material_intake` artifact/summary 转成 `mobile_field_material_review_decision` artifact/summary。
- owner handoff 映射 Full-stack、Robot、Autonomy、Product closeout；保留 same `evidence_ref`；missing / mismatch / placeholder / unsafe success wording fail closed。

Task D Product Closeout：

- 创建本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 当前快照和最高优先级。
- 追加 `docs/process/okr_progress_log.md` 08-09 进度记录。

## 2. 验证结果

Task A Full-stack 验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py`：`Ran 50 tests ... OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py`：OK。
- `node --check mobile/web/app.js`：OK。
- required `rg`：OK。
- scoped `git diff --check`：OK。

Task B Robot 验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 89 tests ... OK`。
- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：OK。
- required `rg`：OK。
- scoped `git diff --check`：OK。

Task C Autonomy 验证结果：

- `PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/mobile_field_material_review_decision.py pc-tools/evidence/test_mobile_field_material_review_decision.py`：OK。
- `PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_mobile_field_material_review_decision.py`：`Ran 4 tests ... OK`。
- `python3 pc-tools/evidence/mobile_field_material_review_decision.py --help`：OK。
- required `rg`：OK。
- scoped `git diff --check`：OK。

Task D Product Closeout 验收结果见本轮最终执行记录：

- `rg -n "mobile_field_material_review_decision|Objective 5|Objective 2|Objective 3|software_proof_docker_mobile_field_material_review_decision_gate|not_proven|delivery_success=false|primary_actions_enabled=false|不证明|真实公网|只有docker|PR|评审" sprints/2026.05.16_08-09_mobile-field-material-review-decision OKR.md docs/process/okr_progress_log.md`：exit 0，命中 OKR 当前快照、sprint closeout 和进度日志中的 schema、Objective、边界和评审词。
- `git diff --check -- sprints/2026.05.16_08-09_mobile-field-material-review-decision OKR.md docs/process/okr_progress_log.md`：exit 0。

## 3. 偏差和失败定位

- 本轮没有真实手机/PWA observation、真实 route/elevator field pass、真实 Nav2/fixed-route runtime、真实 dropoff/cancel completion、真实 delivery success、真实 WAVE ROVER/UART/HIL 或 Objective 5 external proof。
- A/B/C 验证结果均为 targeted fence 通过；Product closeout 未重复运行 Engineer 侧全量测试，只核对并记录 A/B/C 返回的验证证据，再运行 Task D 指定文档验收命令。
- 本轮 OKR 只按 software proof 保守上调 Objective 2、Objective 3 和 Objective 4；Objective 5 保持约 66%，Objective 1 保持约 73%。

## 4. 剩余风险

- `software_proof_docker_mobile_field_material_review_decision_gate` 只证明 Docker/local review-decision artifact、Robot diagnostics metadata-only consumption、mobile read-only panel 和 phone-safe copy/export，不证明真实手机/PWA、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。
- 下一步需要把 review decision 指出的 blocker 转为真实现场材料：真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice；真实电梯门状态、目标楼层确认、人工协助记录；真实 Nav2/fixed-route runtime log；同一 `evidence_ref` task record/completion signal；dropoff/cancel completion 或 delivery result。
- Objective 5 仍只能在拿到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料后再继续上调。

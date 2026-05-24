# Tech Done - Cloud external evidence review decision

- sprint_type: epic
- sprint: `2026.05.24_22-23_cloud-external-evidence-review-decision`
- capability: `cloud_external_evidence_review_decision`
- proof boundary: `software_proof_docker_cloud_external_evidence_review_decision_gate`
- source capability: `trashbot.external_evidence_intake`
- closeout time: 2026-05-24 22:32 Asia/Shanghai
- closeout owner: `product-okr-owner`

## 实际改动

Engineer Task A 已完成 Full-Stack 范围：

- 新增 PC review-decision gate：`pc-tools/evidence/cloud_external_evidence_review_decision.py`
- 新增 PC gate tests 和 fixtures：`pc-tools/evidence/test_cloud_external_evidence_review_decision.py`、`pc-tools/evidence/fixtures/cloud_external_evidence_review_decision/*`
- 新增 mobile read-only panel 和 fixture：`mobile/web/app.js`、`mobile/web/test_mobile_web_entrypoint.py`、`mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_decision.json`
- 同步产品/云端/mobile docs：`docs/product/cloud_4g_infrastructure.md`、`docs/product/remote_4g_mvp.md`、`docs/product/mobile_user_flow.md`、`cloud-relay/README.md`

Engineer Task B 已完成 Robot 范围：

- 新增 Robot diagnostics safe alias：`robot_diagnostics_cloud_external_evidence_review_decision_summary`
- 更新 diagnostics implementation 和 focused tests：`onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`、`onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- 同步 runtime contract docs：`docs/interfaces/ros_runtime_contracts.md`

Product closeout 本轮只更新允许的收口文件：

- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/tech-done.md`
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/side2side_check.md`
- `sprints/2026.05.24_22-23_cloud-external-evidence-review-decision/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Combined Engineer validation 已由 Product closeout 复跑通过：

```text
python3 -m py_compile pc-tools/evidence/cloud_external_evidence_review_decision.py
exit 0

python3 -m unittest pc-tools/evidence/test_cloud_external_evidence_review_decision.py
Ran 5 tests in 0.004s
OK

node --check mobile/web/app.js
exit 0

python3 -m json.tool mobile/web/fixtures/robot_diagnostics_cloud_external_evidence_review_decision.json >/tmp/cloud_external_evidence_review_decision_fixture.json
exit 0

python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k cloud_external_evidence_review_decision
Ran 2 tests in 0.054s
OK

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
exit 0

PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k cloud_external_evidence_review_decision
Ran 1 test in 0.019s
OK
```

Closeout validation 在 Product closeout 文档和 OKR 更新后执行，结果记录在 `final.md`。

## 验收口径核对

- `cloud_external_evidence_review_decision` 已作为 `trashbot.external_evidence_intake` 之后的 review decision 能力落地。
- 支持并测试的状态包括 `accepted_external_evidence_not_proven`、`needs_external_evidence_backfill_not_proven`、`rejected_unsafe_external_evidence_not_proven`、`blocked_missing_external_evidence_intake_not_proven`、`external_evidence_ref_mismatch_not_proven`。
- `mobile/web` panel 和 Robot diagnostics 都保持 read-only；Start Delivery、Confirm Dropoff、Cancel 继续 disabled。
- 关键 false-state flags 保留：`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- Task A 修复过 unsafe `authorization` leak 后，最终验证通过；当前安全边界仍以 tests、fixture、Robot summary 和 docs 中的 redaction contract 为准。

## OKR 最低优先级核对

Objective 5 仍是 `OKR.md` 4.1 中最低 Objective，约 68%。本 sprint 针对 Objective 5，但本轮 closeout 决策是 `no OKR percentage lift`：结果只是 Docker/local `software_proof`，没有真实 external evidence。

## 剩余风险

- 本轮不是 true phone/browser proof。
- 本轮不是 O5 external proof、public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或 verified terminal result。
- 本轮不是 HIL、WAVE ROVER/UART proof、PR #5 resolved、route/elevator field pass 或 delivery success。
- PR #5 thread `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `hardware_material_pending`；PR #7 仍 open with no review threads/comments。

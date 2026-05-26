# Field Evidence Material Resolution Review Decision Tech Done

Run time: 2026-05-22 07:19 Asia/Shanghai

## Sprint Type

- `sprint_type: epic`
- Sprint folder: `sprints/2026.05.22_07-08_field-evidence-material-resolution-review-decision/`
- Product closeout owner: `product-okr-owner`
- Implementation owners: `autonomy-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- Consultation owner: `robot-hardware-engineer`

## User Value And Product North Star

用户价值：support / field owner 现在能把上一轮 `field_evidence_material_resolution_intake` 的 sanitized summary 转成明确 review decision，区分可以进入 owner review、仍需补证据、unsafe resolution 被拒绝，或缺 intake 而阻塞。普通手机用户只看到只读、脱敏、可行动的下一步，不会因为 `accepted` 或 `accepted_for_owner_review_not_proven` 误触主操作。

产品北极星：手机端和 Robot diagnostics 只展示安全的材料复核状态；Docker-only 软件证明阶段必须保持 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`，不启用 Start Delivery、Confirm Dropoff、Cancel，也不把 review decision 写成真实送达或真实材料闭环。

## OKR Mapping And KR Breakdown

| Objective | Mapping | 本轮判断 |
| --- | --- | --- |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 当前最低，约 68%。本轮把 external / terminal-result / field-material resolution intake 推进到 review-decision metadata。 | 保持约 68%，因为没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/cutover、真实手机/browser 或 verified terminal delivery/dropoff/cancel result material。 |
| Objective 1：硬件协议可信底盘 | 约 81%。PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / hardware_material_pending，comment `3269642220` 仍只是 software-proof reply publication。 | 保持约 81%，因为没有真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，也没有 WAVE ROVER powered bench/UART/HIL logs。 |
| Objective 2/3/4 | 约 99%。本轮只让 route/elevator/phone 相关材料 resolution 进入安全 review decision。 | 保持约 99%，因为没有真实 task record、Nav2/fixed-route runtime、route/elevator field pass、真实手机/browser、dropoff/cancel completion 或 delivery success。 |

KR 拆解结果：

- KR-A Autonomy PC Gate：完成 `field_evidence_material_resolution_review_decision` CLI、测试、contract docs 与 `pc-tools/README.md` 更新。
- KR-B Robot Diagnostics Alias：完成 `robot_diagnostics_field_evidence_material_resolution_review_decision_summary` safe alias、测试与接口文档更新。
- KR-C Full-Stack Mobile/Web Read-Only Panel：完成 `mobile/web` 只读 panel、fixture、测试与 `docs/product/mobile_user_flow.md` 更新。
- KR-D Hardware Vendor / PR #5 Boundary Consultation：完成只读 vendor/PR #5 边界咨询，未改硬件配置或 vendor docs。
- KR-E Product Closeout：本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 保守收口。

## Actual Changes

Autonomy Worker A:

- Added `pc-tools/evidence/field_evidence_material_resolution_review_decision.py`.
- Added `pc-tools/evidence/test_field_evidence_material_resolution_review_decision.py`.
- Updated `docs/interfaces/evidence_contracts.md`.
- Updated `pc-tools/README.md`.
- Supported decisions: `accepted_for_owner_review_not_proven`, `needs_more_evidence_not_proven`, `rejected_unsafe_resolution_not_proven`, `blocked_missing_resolution_intake_not_proven`.

Robot Worker B:

- Updated `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`.
- Updated `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`.
- Updated `docs/interfaces/operator_gateway_diagnostics.md`.
- Updated `docs/interfaces/ros_contracts.md`.
- First test round failed because unsafe scanner overmatched `delivery_success=false` wording; worker narrowed truthy/success claim matching and reran successfully.

Full-Stack Worker C:

- Updated `mobile/web/app.js`.
- Added `mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_review_decision_summary.json`.
- Updated `mobile/web/test_mobile_web_entrypoint.py`.
- Updated `docs/product/mobile_user_flow.md`.
- First unittest round failed because fixture coverage missed `rejected_unsafe_resolution_not_proven`; worker added `review_decision_options` and reran successfully.

Hardware Worker D:

- Changed files: none.
- Read `docs/vendor/VENDOR_INDEX.md` and WAVE ROVER vendor files: `base_ctrl.py`, `config.yaml`, `json_cmd.h`, `uart_ctrl.h`, `movtion_module.h`, `WAVE_ROVER.wiki.html`.
- Confirmed local vendor material supports WAVE ROVER/UART/newline JSON source context only. It does not prove project 2D LiDAR/ToF SKU/source/receipt/procurement/mounting/wiring/power/calibration/HIL-entry, PR #5 `PRRT_kwDOSWB9286CJ3tX` reviewer resolution, HIL, field pass, or delivery success.

Product Worker E:

- Created this `tech-done.md`.
- Created `side2side_check.md`.
- Created `final.md`.
- Updated `OKR.md`.
- Updated `docs/process/okr_progress_log.md`.

## Validation Results From Workers

Autonomy Worker A:

```text
python3 -m py_compile pc-tools/evidence/field_evidence_material_resolution_review_decision.py
PASS

python3 -m unittest pc-tools.evidence.test_field_evidence_material_resolution_review_decision
Ran 7 tests in 0.038s
OK

python3 pc-tools/evidence/field_evidence_material_resolution_review_decision.py --help
PASS

required rg
PASS

git diff --check -- pc-tools/evidence/field_evidence_material_resolution_review_decision.py pc-tools/evidence/test_field_evidence_material_resolution_review_decision.py docs/interfaces pc-tools/README.md
PASS
```

Robot Worker B:

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PASS

python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_operator_gateway_diagnostics
Ran 280 tests in 1.473s
OK

required rg
PASS

scoped git diff --check
PASS
```

Full-Stack Worker C:

```text
node --check mobile/web/app.js
PASS

python3 -m json.tool mobile/web/fixtures/robot_diagnostics_field_evidence_material_resolution_review_decision_summary.json
PASS

python3 -m unittest mobile.web.test_mobile_web_entrypoint
Ran 247 tests in 1.923s
OK

required rg
PASS

scoped git diff --check
PASS
```

Hardware Worker D:

```text
test -f docs/vendor/VENDOR_INDEX.md
PASS

required rg over docs/vendor docs/interfaces docs/product pc-tools/README.md
PASS

git diff --check -- docs/vendor docs/interfaces docs/product pc-tools/README.md
PASS
```

## Product Acceptance

- Capability `field_evidence_material_resolution_review_decision` is implemented across PC gate, Robot diagnostics safe alias, and mobile/web read-only panel.
- Evidence boundary is `software_proof_docker_field_evidence_material_resolution_review_decision_gate`.
- All accepted surfaces retain `source=software_proof`, `not_proven`, `delivery_success=false`, `primary_actions_enabled=false`, and `safe_to_control=false`.
- `accepted_for_owner_review_not_proven` means owner review may proceed. It is not delivery success, HIL, field pass, real phone/browser proof, real public cloud proof, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolution, dropoff/cancel completion, verified terminal result, or OKR completion lift.
- Docs sync is covered by implementation owners in `docs/interfaces/evidence_contracts.md`, `docs/interfaces/operator_gateway_diagnostics.md`, `docs/interfaces/ros_contracts.md`, `docs/product/mobile_user_flow.md`, and `pc-tools/README.md`.

## Failure Diagnosis

- No Product closeout validation failure yet at this stage.
- Implementation failures were localized and fixed by the owning workers before closeout: Robot unsafe scanner overmatched false-state wording, and Full-Stack fixture coverage initially missed the rejected decision path.

## Remaining Risks

- This sprint is Docker/local software proof only; it does not prove real external cloud, real phone/browser, WAVE ROVER/UART/HIL, Nav2/fixed-route runtime, route/elevator field pass, dropoff/cancel completion, verified terminal delivery/dropoff/cancel result, PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved, or delivery success.
- Objective percentages remain unchanged: Objective 5 about 68%, Objective 1 about 81%, Objective 2/3/4 about 99%.
- Next OKR lift requires real materials under the same safe `evidence_ref`, not another local wrapper around the same blocker.

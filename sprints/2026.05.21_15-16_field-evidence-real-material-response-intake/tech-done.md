# Field Evidence Real Material Response Intake Tech Done

Run time: 2026-05-21 15:23 CST

## Sprint Type

- sprint_type: epic
- capability: `field_evidence_real_material_response_intake`
- evidence boundary: `software_proof_docker_field_evidence_real_material_response_intake_gate`
- closeout owner: Product Manager / OKR Owner

## User Value And Product North Star

本轮用户价值是把现场 owner 的回执变成可复核的产品证据状态，而不是继续追加一个材料请求。现场同学可以看到每类材料是 `accepted`、`missing`、`rejected` 还是 `blocked`；支持和手机端只看到 safe summary，不会把局部材料误判为送达成功。

产品北极星保持不变：普通手机用户交付垃圾后，机器人必须用同一 safe `evidence_ref` 证明 route/task、电梯/人工协助、终端 dropoff/cancel、真实手机/browser、diagnostics/mobile summary 与硬件边界一致，才能声明真实 route/elevator field pass 或 delivery success。

## OKR Mapping And KR Breakdown

| Objective | 本轮判断 | KR 影响 |
| --- | --- | --- |
| Objective 1 | 保持约 81%，不提升。 | PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending；comment `3269642220` 不是 reviewer resolution；无真实 2D LiDAR / ToF、WAVE ROVER、UART 或 HIL 材料。 |
| Objective 2 | 保守保持约 99%。 | 只新增 response-intake 分类入口；`accepted` 只代表 ready_for_later_review_only，不是真实电梯、dropoff/cancel completion、delivery result 或 delivery_success。 |
| Objective 3 | 保守保持约 99%。 | 可分类 `task_record`、`nav2_fixed_route_runtime_log`、`route_completion_signal` 回执，但没有真实 route runtime、route completion signal 或上车实机复账。 |
| Objective 4 | 保守保持约 99%。 | mobile/web 新增只读 response-intake panel，Start/Confirm/Cancel 保持 disabled；不是真实 iPhone/Android device behavior、production app 或 true phone/browser proof。 |
| Objective 5 | 保持约 68%，不提升。 | 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、production app/device 或真实外部 phone/browser proof。 |

## Core Lever

本轮核心抓手是 `field_evidence_real_material_response_intake`：消费上一轮 field-owner request dispatch 的 safe state，把九类真实材料回执分类为 `accepted`、`missing`、`rejected`、`blocked`，并强制保留 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## Actual Changes By Owner

- Autonomy Algorithm Engineer:
  - 新增 `pc-tools/evidence/field_evidence_real_material_response_intake.py`
  - 新增 `pc-tools/evidence/test_field_evidence_real_material_response_intake.py`
  - 更新 `docs/interfaces/evidence_contracts.md`
- Robot Platform Engineer:
  - 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
  - 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
  - 更新 `docs/interfaces/ros_runtime_contracts.md`
- User Touchpoint Full-Stack Engineer:
  - 更新 `mobile/web/app.js`
  - 新增 `mobile/web/fixtures/robot_diagnostics_field_evidence_real_material_response_intake.json`
  - 更新 `mobile/web/test_mobile_web_entrypoint.py`
  - 更新 `docs/product/mobile_user_flow.md`
- Hardware Infra Engineer:
  - read-only consultation 已读取 `docs/vendor/VENDOR_INDEX.md` 和 WAVE ROVER vendor files；结论是 `accepted` 只能写成 ready_for_later_review_only，不能写成真实 2D LiDAR/ToF、WAVE ROVER/UART/HIL、route/elevator field pass、delivery success 或 PR #5 resolution。
- Product Manager / OKR Owner:
  - 本文件、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md` 收口更新。

## Acceptance Results

Engineer 返回的验证摘要：

- Autonomy：`py_compile` pass；focused unittest `Ran 6 tests in 0.131s OK`；CLI help pass；required `rg` 和 scoped `git diff --check` pass。
- Robot：`py_compile` pass；diagnostics unittest `Ran 258 tests OK`；required `rg` 和 scoped `git diff --check` pass。
- Full-Stack：`node --check` pass；fixture JSON pass；mobile unittest `Ran 215 tests OK`；required `rg` 和 scoped `git diff --check` pass。

Product closeout 需要继续运行本轮指定小范围集成围栏，并把结果写入最终回复。

## Scope Boundary And Remaining Risks

- 本轮是 `software_proof_docker_field_evidence_real_material_response_intake_gate`，不是 HIL、不是真实串口/UART、不是 WAVE ROVER proof、不是真实 route/elevator field pass、不是真实手机/browser proof、不是 O5 external proof、不是 PR #5 reviewer resolution。
- `accepted` 只表示材料 present/safe/same-evidence-ref 且 ready for later review；还需要后续真实 review decision 才能进入实地通过判断。
- 若 field-owner response 缺失，应分类为 `missing` 或 `blocked`；不得伪造 accepted。
- 仍缺真实 task record、真实 Nav2/fixed-route runtime log、route completion signal、真实电梯门/楼层证据、人工协助记录、dropoff/cancel completion、delivery result、true phone/browser evidence、真实 2D LiDAR / ToF 来源/采购/安装/标定/HIL、真实公网/4G/OSS/CDN/DB/queue/worker/cutover 证据。

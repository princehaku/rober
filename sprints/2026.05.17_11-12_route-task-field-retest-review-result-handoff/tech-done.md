# Sprint 2026.05.17_11-12 Route Task Field Retest Review Result Handoff - Tech Done

sprint_type: epic

## 1. 实际改动

本轮完成 `software_proof_docker_route_task_field_retest_review_result_handoff_gate`，把上一轮现场回执复核决策转成 result-intake 前的只读交接层。固定边界保持：

- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `same_evidence_ref_required=true`

### Task A - Autonomy

改动文件：

- `pc-tools/evidence/route_task_field_retest_review_result_handoff.py`
- `pc-tools/evidence/test_route_task_field_retest_review_result_handoff.py`
- `pc-tools/README.md`
- `docs/navigation/fixed_route_workflow.md`

实现结果：

- 新增 PC metadata-only handoff gate。
- Artifact schema：`trashbot.route_task_field_retest_review_result_handoff.v1`。
- Summary schema：`trashbot.route_task_field_retest_review_result_handoff_summary.v1`。
- 支持 artifact、summary、wrapper、nested JSON。
- 将 `ready_for_result_intake`、backfill、mismatch、unsupported、unsafe、success claim 映射为 fail-closed handoff/readiness 状态。
- 保持 `not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`。

### Task B - Robot

改动文件：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

实现结果：

- 新增 `route_task_field_retest_review_result_handoff` / `_summary` diagnostics metadata-only consumer。
- 支持 direct artifact、summary wrapper、nested diagnostics。
- 输出 safe `evidence_ref`、source review decision、handoff status、result-intake readiness、required materials、owner handoff、blocked reasons、boundary、`not_proven` 和 control boundary。
- missing、unsupported、unsafe、success、weak same-ref、action-enabled 均 fail closed。
- 未新增 ROS action/topic/service、ACK、cursor、Nav2、dropoff/cancel、delivery result 或 primary action。

### Task C - Full-stack

改动文件：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

实现结果：

- 新增只读“现场复测结果交接” panel。
- 消费 `route_task_field_retest_review_result_handoff` / `_summary` 和 Robot diagnostics compatible summary。
- 展示 safe `evidence_ref`、handoff status、source review decision、result-intake readiness、required materials、owner handoff、blocked reasons 和 boundary。
- copy/export whitelist-only。
- 不改变 Start Delivery、Confirm Dropoff、Cancel gating，不新增 result-intake、ACK、cursor 或 robot command。

## 2. 验证结果

Task A 验证：

- `python3 -m py_compile pc-tools/evidence/route_task_field_retest_review_result_handoff.py`：exit 0。
- `python3 -m unittest pc-tools/evidence/test_route_task_field_retest_review_result_handoff.py`：`Ran 5 tests in 0.028s OK`。
- `python3 pc-tools/evidence/route_task_field_retest_review_result_handoff.py --help`：OK。
- required `rg`：exit 0。
- scoped `git diff --check`：exit 0。
- 新增文件 no-index whitespace check：exit 0。

Task B 验证：

- `python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass。
- `python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 144 tests OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Task C 验证：

- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 40 tests OK`。
- `node --check mobile/web/app.js`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

Product closeout 已在本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 更新后运行：

```bash
rg -n "route_task_field_retest_review_result_handoff|software_proof_docker_route_task_field_retest_review_result_handoff_gate|Objective 2|Objective 3|Objective 5|PR #4|PR #5|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.17_11-12_route-task-field-retest-review-result-handoff OKR.md docs/process/okr_progress_log.md
```

结果：

- required `rg`：exit 0，覆盖 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 中的 gate、Objective、PR 和边界关键词。
- scoped `git diff --check`：exit 0。

## 3. 偏差和边界

本轮符合 tech-plan 的 owner 拆分和文件范围：Autonomy、Robot、Full-stack 三个实现范围互不覆盖，Product 仅做 closeout、OKR 和 process log。

本轮证据边界是 Docker/local metadata-only software proof：

- 是 `software_proof_docker_route_task_field_retest_review_result_handoff_gate`。
- 是 result-intake 前交接状态说明。
- 是 PC / Robot diagnostics / mobile/web 的只读对齐。

本轮不是：

- 真实 route/elevator field pass。
- HIL、真实 WAVE ROVER、真实 UART/serial。
- 真实 Nav2/fixed-route 运行。
- 真实手机/browser 或 production app proof。
- Objective 5 external proof。
- 真实投放、dropoff/cancel completion 或 delivery success。

## 4. 剩余风险

- 仍缺真实 Nav2/fixed-route runtime log、route completion signal、task record 和 same-`evidence_ref` 上车复账。
- 仍缺真实电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion 和 delivery result。
- 仍缺 PR #5 相关 2D LiDAR / ToF SKU、source、receipt、install、wiring、calibration 和 HIL-entry。
- 仍缺 Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 和真实手机/browser 证据。

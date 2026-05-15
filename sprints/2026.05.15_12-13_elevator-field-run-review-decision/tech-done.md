# Sprint 2026.05.15_12-13 Elevator Field Run Review Decision - Tech Done

sprint_type: epic

## 1. 实际改动

Task A `autonomy-engineer` 已完成 PC 侧复核决策 gate：

- 新增 `pc-tools/evidence/elevator_field_run_review.py`。
- 新增 `pc-tools/evidence/test_elevator_field_run_review.py`。
- 更新 `pc-tools/README.md`、`docs/product/elevator_assisted_delivery.md`、`docs/navigation/fixed_route_workflow.md`。
- 输出 `schema=trashbot.elevator_field_run_review.v1` 与 `summary_schema=trashbot.elevator_field_run_review_summary.v1`，证据边界为 `software_proof_docker_elevator_field_review_decision_gate`。
- 将上一轮 validation 的 missing/template/mismatch/unsafe/success-claim 状态转成 `review_decision`、`blocked_categories`、`operator_next_steps`、`commands_to_rerun` 和 `capture_checklist`。
- 固定 `delivery_success=false`、`primary_actions_enabled=false`、`not_proven`，并过滤 raw artifact、内部路径、ROS topic、serial/UART、WAVE ROVER、credential 和成功文案。

Task B `robot-software-engineer` 已完成 diagnostics 只读消费：

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- 支持 explicit ref 以及 `TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW` / `TRASHBOT_ELEVATOR_FIELD_RUN_REVIEW_SUMMARY`。
- 暴露 `elevator_field_run_review` 与 `elevator_field_run_review_summary`，保持 metadata-only、schema/boundary/redaction 校验和控制动作不放行。

Task C `full-stack-software-engineer` 已完成 mobile 只读解释：

- 更新 `mobile/web/app.js`。
- 更新 `mobile/test_mobile_web_entrypoint.py`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读“电梯现场复核决策” panel，兼容 top-level、`phone_readiness`、diagnostics summary 与 nested diagnostics summary。
- 展示 review decision、safe `evidence_ref`、blocked categories、operator next steps、commands to rerun、`not_proven` 和 boundary，不改变 Start/Confirm/Cancel gating。

Task D `product-okr-owner` 已完成 closeout：

- 新建本文件、`side2side_check.md` 与 `final.md`。
- 更新 `OKR.md` 当前快照：Objective 2 约 71% -> 约 72%，Objective 3 约 70% -> 约 71%，Objective 5 保持约 66%。
- 更新 `docs/process/okr_progress_log.md`，追加本 sprint 的证据与边界。

## 2. 验证结果

工程线回传的验证结果：

- Autonomy：`PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/test_elevator_field_run_review.py` 输出 `Ran 5 tests ... OK`；`py_compile`、CLI `--help`、required `rg`、scoped `git diff --check` 均通过。
- Robot：`PYTHONDONTWRITEBYTECODE=1 python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 77 tests ... OK`；`py_compile`、required `rg`、scoped `git diff --check` 均通过。
- Full-stack：`PYTHONDONTWRITEBYTECODE=1 python3 mobile/test_mobile_web_entrypoint.py` 输出 `Ran 43 tests ... OK`；`py_compile`、`node --check mobile/web/app.js`、required `rg`、scoped `git diff --check` 均通过。

Task D 本地 closeout 验收命令：

```bash
rg -n "elevator_field_run_review|software_proof_docker_elevator_field_review_decision_gate|not real|不证明|delivery_success=false|Objective 5" sprints/2026.05.15_12-13_elevator-field-run-review-decision OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.15_12-13_elevator-field-run-review-decision OKR.md docs/process/okr_progress_log.md
```

最终执行结果见本轮对话输出：required `rg` 命中 closeout、OKR 和 progress log 的 schema/boundary/not-proven/O5 边界；scoped `git diff --check` 通过。

## 3. 偏差与边界

- 本轮是 `software_proof_docker_elevator_field_review_decision_gate`，只证明 Docker/local review decision artifact、Robot diagnostics metadata-only consumption、mobile read-only panel 和安全文案围栏可工作。
- 本轮不证明真实电梯、真实楼层确认、真实人协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- Objective 5 仍约 66%，没有因本轮上调。

## 4. 剩余风险

- 仍缺真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实喇叭/TTS、真实 Nav2/fixed-route runtime、真实路线采集和同一 `evidence_ref` 的上车实机复账。
- 仍缺 WAVE ROVER/UART/HIL、真实串口 feedback、真实 dropoff completion、真实 cancel completion 和 delivery success。
- 仍缺真实手机设备/browser、production app、真实 PWA prompt/user choice、外部公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。

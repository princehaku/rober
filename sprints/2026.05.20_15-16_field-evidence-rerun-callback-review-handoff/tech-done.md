# Sprint 2026.05.20_15-16 Field Evidence Rerun Callback Review Handoff - Tech Done

## 1. Sprint 类型

- sprint_type: epic
- 收口时间：2026-05-20 15:18 Asia/Shanghai
- 主受益 OKR：Objective 2 / Objective 3 / Objective 4 field evidence rerun handoff follow-through
- 非目标：Objective 5 external proof、Objective 1 WAVE ROVER/UART/HIL 或 PR #5 material closure

## 2. 实际改动

### Autonomy Task A

- 改动 `pc-tools/evidence/field_evidence_rerun_callback_review_handoff.py`。
- 改动 `tests/test_field_evidence_rerun_callback_review_handoff.py`。
- 改动 `pc-tools/README.md`。
- 改动 `docs/interfaces/evidence_contracts.md`。
- 新增 PC-only handoff gate，支持 artifact / summary / wrapper / nested JSON 输入，输出 `trashbot.field_evidence_rerun_callback_review_handoff.v1` 和 `trashbot.field_evidence_rerun_callback_review_handoff_summary.v1`。

### Robot Task B

- 改动 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 改动 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 改动 `docs/interfaces/ros_status_contract.md`。
- 新增 `robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary` safe alias，清理 raw `latest_status` 字段，保持 `software_proof` / `not_proven` 和 fail-closed flags。

### Full-Stack Task C

- 改动 `mobile/web/app.js`。
- 改动 `mobile/web/styles.css`。
- 改动 `mobile/web/test_mobile_web_entrypoint.py`。
- 改动 `mobile/web/fixtures/status.json`。
- 改动 `mobile/fixtures/mobile_web_status.fixture.json`。
- 改动 `docs/product/mobile_user_flow.md`。
- 新增只读“现场证据复跑复核交接”panel，优先消费 `robot_diagnostics_field_evidence_rerun_callback_review_handoff_summary`，兼容 direct / nested summary，不启用 Start / Confirm / Cancel。

## 3. 验证结果

### Autonomy Task A

- `py_compile`：pass。
- `python3 -m unittest tests.test_field_evidence_rerun_callback_review_handoff`：`Ran 5 tests in 0.090s OK`。
- CLI `--help`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

### Robot Task B

- `py_compile`：pass。
- `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 231 tests in 0.711s OK`。
- required `rg`：pass。
- scoped `git diff --check`：pass。

### Full-Stack Task C

- `node --check mobile/web/app.js`：OK。
- `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 169 tests in 1.198s OK`。
- `python3 -m json.tool mobile/web/fixtures/status.json`：OK。
- `python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json`：OK。
- required `rg`：pass。
- scoped `git diff --check`：pass。

## 4. 证据边界

- 本轮证据边界是 `software_proof_docker_field_evidence_rerun_callback_review_handoff_gate`。
- 固定声明：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 本轮不触发 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。
- 本轮不证明真实 route/elevator field pass、真实 dropoff/cancel completion、真实 delivery result、真实手机/PWA 验收、HIL 或真实投放。

## 5. PR #5 Live Evidence

- `PRRT_kwDOSWB9286CJ3tQ`：resolved。
- `PRRT_kwDOSWB9286CJ3tU`：resolved。
- `PRRT_kwDOSWB9286CJ3tX`：unresolved / `is_resolved=false` / material pending。
- manual reply `3269642220` 是保守 GitHub reply，不是硬件 proof，不是 reviewer resolved，不允许写成 O1 进度提升。

## 6. 剩余风险

- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration/cutover 和真实手机/browser external proof。
- Objective 1 仍缺真实 WAVE ROVER/UART/HIL、真实 `feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery`、operator HIL report，以及 PR #5 `PRRT_kwDOSWB9286CJ3tX` 所需真实 2D LiDAR / ToF SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry 材料。
- Objective 2 / 3 / 4 仍缺真实现场 task record、真实 route completion signal、真实 Nav2/fixed-route runtime log、真实电梯门/楼层/人工协助记录、真实 dropoff/cancel completion、delivery result 和真实手机/browser evidence。

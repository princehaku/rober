# Sprint 2026.05.20_14-15 Field Evidence Rerun Callback Review Decision - Tech Done

## 1. Sprint 声明

- `sprint_type: epic`
- 当前时间：2026-05-20 14:55 CST。
- 本轮主题：`field_evidence_rerun_callback_review_decision`。
- 证据边界：`software_proof_docker_field_evidence_rerun_callback_review_decision_gate`。
- 固定安全状态：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 实际改动

### Task A - Autonomy Algorithm Engineer

- 新增 `pc-tools/evidence/field_evidence_rerun_callback_review_decision.py`。
- 新增 `tests/test_field_evidence_rerun_callback_review_decision.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/interfaces/evidence_contracts.md`。

实际交付：PC gate 只读消费 `field_evidence_rerun_callback_intake` output，将 accepted / missing / rejected / blocked intake material groups 转成 callback review decision、owner handoff、next required evidence、rerun guidance、blocker summary 和 same-evidence-ref status。

### Task B - Robot Platform Engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。

实际交付：新增 `robot_diagnostics_field_evidence_rerun_callback_review_decision_summary` safe alias，只读暴露 review decision summary，不触发 collect/dropoff/cancel、ACK、cursor、Nav2 runtime、serial/UART、WAVE ROVER 或 HIL 控制路径。

### Task C - User Touchpoint Full-Stack Engineer

- 更新 `mobile/web/app.js`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。

实际交付：mobile/web 新增只读“现场证据复跑回执复核”panel，展示 review decision、safe `evidence_ref`、owner handoff、next required evidence、rerun guidance、blocker summary、same-evidence-ref status 和 proof boundary；Start Delivery / Confirm Dropoff / Cancel gating 不变。

### Task D - Product Manager / OKR Owner Closeout

- 新增本文件 `tech-done.md`。
- 新增 `side2side_check.md`。
- 新增 `final.md`。
- 更新 `OKR.md` 4.1 当前快照和当前最高优先级。
- 更新 `docs/process/okr_progress_log.md`。

Product 只做 sprint closeout、OKR 和 progress log；未修改产品代码、测试代码、硬件配置或 launch 参数。

## 3. 验证结果

### Worker 自验

- Task A Autonomy：`py_compile` pass；`python3 -m unittest tests.test_field_evidence_rerun_callback_review_decision` 输出 `Ran 5 tests in 0.062s OK`；CLI `--help` pass；required `rg` pass；scoped `git diff --check` pass。
- Task B Robot：`py_compile` pass；`PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 230 tests in 0.713s OK`；required `rg` pass；scoped `git diff --check` pass。
- Task C Full-Stack：`node --check mobile/web/app.js` pass；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 167 tests ... OK`；fixture JSON checks pass；required `rg` pass；scoped `git diff --check` pass。

### Integration worker 围栏

- PC py_compile pass。
- PC unittest 输出 `Ran 5 tests in 0.060s OK`。
- Robot diagnostics unittest 输出 `Ran 230 tests in 0.706s OK`。
- `node --check mobile/web/app.js` pass。
- mobile unittest 输出 `Ran 167 tests in 1.141s OK`。
- 两份 fixture JSON tool pass。
- required `rg` exit 0。
- scoped `git diff --check` exit 0。

### Product closeout 围栏

Product closeout 运行：

```bash
test -f sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/tech-done.md && test -f sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/side2side_check.md && test -f sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision/final.md
rg -n "field_evidence_rerun_callback_review_decision|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|software_proof_docker_field_evidence_rerun_callback_review_decision_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_14-15_field-evidence-rerun-callback-review-decision
```

实际结果见最终回复；本文件记录 closeout intent 和 worker/integration 已交付证据。

## 4. 偏差与边界

- 本轮没有真实硬件、真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF 材料、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、真实 delivery result、真实手机/browser、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/cutover。
- `accepted` review decision 只表示 callback packet 在 software-proof gate 内被复核为材料形态可接受，不等于真实交付成功。
- Objective 5 保持约 68%；Objective 1 保持约 81%；Objective 2/3/4 保守保持约 99%。
- PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending；manual reply 或本轮 review decision 不关闭该 thread。

## 5. 文档同步

- PC README / evidence contract 已随 Task A 更新。
- ROS contract 已随 Task B 更新。
- mobile user flow 已随 Task C 更新。
- OKR 当前快照、当前最高优先级和 progress log 已由 Product closeout 同步。

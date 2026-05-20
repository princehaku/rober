# Sprint 2026.05.20_13-14 Field Evidence Rerun Callback Intake - Final

## 1. 收口结论

本轮 `field_evidence_rerun_callback_intake` epic 已完成 Product closeout。三位 Engineer worker 分别完成 PC gate、Robot diagnostics safe alias、mobile/web 只读 panel，并同步 PC README / evidence contracts、ROS contracts、mobile user flow。Product closeout 已把实际改动、验证结果、OKR 边界和 progress log 收口到 sprint 文档。

本轮是 `software_proof_docker_field_evidence_rerun_callback_intake_gate`，固定状态为 `source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和核心抓手

用户价值：现场 owner 现在可以把上一轮 dispatch 后的 callback packet 交给统一入口，系统把十类真实现场材料归类为 accepted / missing / rejected / blocked，并把下一步材料要求安全地传给 Robot diagnostics 和 mobile/web。普通手机用户和现场支持同学看到的是回执状态和下一步证据要求，不是 raw JSON、ROS topic、串口、WAVE ROVER 或控制授权。

核心抓手：从“材料派发”推进到“回执入口”。这不是新的控制能力，也不是 field pass；它只减少真实材料回填、复核和再次复跑之间的产品/工程摩擦。

## 3. OKR 最低优先级核对

tech-plan 中的最低优先级判断仍成立：

1. `OKR.md` 4.1 数字最低仍是 Objective 5，约 68%。
2. 本 sprint 未直接针对 Objective 5，因为真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser external proof 仍不在 Docker-only 主机内。
3. 下一低项 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending；`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved，manual reply `3269642220` 不是硬件 proof。
4. 本轮选择 O2/O3/O4 field evidence rerun callback intake，是因为上一轮已派发真实材料要求，下一步需要统一接收和校验回执，而不是重复包装同一 blocker。

## 4. Repeated Blocker Rationale

O5 外部 proof blocker 已被多轮识别，继续做同义本地 cloud metadata 不会改变 68% 的主要缺口。O1 / PR #5 的主要 blocker 仍是真实 2D LiDAR / ToF 和 WAVE ROVER/UART/HIL 材料缺失。上一轮 O2/O3/O4 已完成 material dispatch；本轮推进 callback intake 属于同一证据链的下一步，而不是第三次消费同一“缺真实材料”结论。

因此，本轮没有上调 Objective 5 或 Objective 1，也没有把 O2/O3/O4 写成真实完成。

## 5. 实际改动摘要

- Autonomy：新增 `pc-tools/evidence/field_evidence_rerun_callback_intake.py`、测试、PC README 和 evidence contract。
- Robot：新增 `robot_diagnostics_field_evidence_rerun_callback_intake_summary`、测试和 ROS contract。
- Full-Stack：新增 mobile/web “现场证据复跑回执入口”panel、fixtures、测试和 mobile user flow 文档。
- Product：新增/更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 6. 验证结果

Engineer worker 原始结果：

- Autonomy：`py_compile` exit 0；`python3 -m unittest tests.test_field_evidence_rerun_callback_intake` -> `Ran 5 tests in 0.051s OK`；CLI `--help` exit 0；required `rg` exit 0；scoped `git diff --check` exit 0。
- Robot：`py_compile` passed；`PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` -> `Ran 229 tests in 0.695s OK`；required `rg` passed；scoped diff check passed。
- Full-Stack：`node --check mobile/web/app.js` passed；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` -> `Ran 165 tests in 1.157s OK`；fixture JSON checks passed；required `rg` passed；scoped diff check passed。

Product closeout 复跑结果：

- Required file check：exit 0。
- Closeout required `rg`：exit 0，覆盖 `field_evidence_rerun_callback_intake`、Objective 5 / Objective 1 / Objective 4、`PRRT_kwDOSWB9286CJ3tX`、`software_proof_docker_field_evidence_rerun_callback_intake_gate`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`、`not_proven`。
- Closeout scoped `git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake`：exit 0。
- Integration `python3 -m py_compile pc-tools/evidence/field_evidence_rerun_callback_intake.py tests/test_field_evidence_rerun_callback_intake.py`：exit 0。
- Integration `python3 -m unittest tests.test_field_evidence_rerun_callback_intake`：`Ran 5 tests in 0.047s OK`。
- Integration `PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`：`Ran 229 tests in 0.734s OK`。
- Integration `node --check mobile/web/app.js`：exit 0。
- Integration `python3 -m unittest mobile/web/test_mobile_web_entrypoint.py`：`Ran 165 tests in 1.167s OK`。
- Integration fixture JSON checks：both `mobile/fixtures/mobile_web_status.fixture.json` and `mobile/web/fixtures/status.json` exit 0.
- Integration required `rg`：exit 0。
- Integration scoped `git diff --check -- OKR.md docs/process/okr_progress_log.md pc-tools tests onboard/src/ros2_trashbot_behavior mobile/web mobile/fixtures docs sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake`：exit 0。
- CLI help smoke `python3 pc-tools/evidence/field_evidence_rerun_callback_intake.py --help`：exit 0，usage printed.

## 7. OKR 更新

- Objective 5 保持约 68%：本轮不是 external cloud proof。
- Objective 1 保持约 81%：本轮不是 WAVE ROVER/UART/HIL，也不是 PR #5 `PRRT_kwDOSWB9286CJ3tX` resolved。
- Objective 2 / Objective 3 / Objective 4 保持约 99%：本轮只证明 callback-intake software proof，不证明真实 route/elevator field pass、真实 phone/browser、dropoff/cancel completion 或 delivery success。

## 8. 剩余风险

- 真实现场材料仍未出现：route completion signal、field task record、Nav2/fixed-route runtime log、电梯门/楼层/人工协助 summaries、dropoff/cancel completion、delivery result、真实手机/browser evidence 仍需回填。
- `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending；manual reply `3269642220` 不得当作硬件 proof。
- 本机没有真实硬件、电梯、路线、手机/browser 或外部云环境；所有本轮证据都必须继续写成 `not_proven`。

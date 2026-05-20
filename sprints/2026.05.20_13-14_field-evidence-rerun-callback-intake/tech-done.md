# Sprint 2026.05.20_13-14 Field Evidence Rerun Callback Intake - Tech Done

## 1. Sprint 声明

- `sprint_type: epic`
- 收口时间：2026-05-20 13:40 Asia/Shanghai。
- 本轮主题：`field_evidence_rerun_callback_intake`。
- 证据边界：`software_proof_docker_field_evidence_rerun_callback_intake_gate`。
- 固定安全状态：`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。

## 2. 用户价值和产品北极星

本轮用户价值是把上一轮“现场证据复跑材料派发”推进到“现场 owner 回执可接收、可校验、可复盘”。普通手机用户和现场支持同学不用理解 ROS2、Nav2、GitHub review thread 或低层日志，也能看到真实 route/elevator/mobile 材料哪些已 accepted、哪些仍 missing、哪些 rejected 或 blocked。

产品北极星不变：让普通手机用户把垃圾交给小车后，小车可验证地沿固定路线、电梯辅助、投放或人工取走，并且失败时清楚知道谁需要补什么证据。本轮只降低证据回填摩擦，不新增控制授权。

## 3. OKR 映射和 KR 拆解

| Objective | 本轮结果 | KR 影响 |
| --- | --- | --- |
| Objective 1 | 保持约 81% | 未触碰 WAVE ROVER/UART/HIL、硬件桥或真实 2D LiDAR / ToF 材料；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending。 |
| Objective 2 | 保持约 99% | 回执入口可校验电梯门、楼层、人工协助、dropoff/cancel 和 delivery result 材料状态；不证明真实 delivery。 |
| Objective 3 | 保持约 99% | 回执入口可校验 route completion signal、field task record、Nav2/fixed-route runtime log 和同一 safe `evidence_ref`；不证明路线实跑。 |
| Objective 4 | 保持约 99% | mobile/web 新增只读“现场证据复跑回执入口”panel，展示 safe summary，不改变 Start/Confirm/Cancel gating；不证明真实手机/browser。 |
| Objective 5 | 保持约 68% | 不改 cloud commands/status/ack、不新增公网/4G/OSS/CDN/DB/queue/worker 外部 proof。 |

## 4. 实际改动

### Autonomy Algorithm Engineer

- `pc-tools/evidence/field_evidence_rerun_callback_intake.py`
- `tests/test_field_evidence_rerun_callback_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/evidence_contracts.md`

完成 `trashbot.field_evidence_rerun_callback_intake.v1` / `trashbot.field_evidence_rerun_callback_intake_summary.v1` PC gate。该 gate 只读上一轮 dispatch summary 和现场 callback packet，把十类材料归类为 `accepted`、`missing`、`rejected` 或 `blocked`，并在缺输入、bad JSON、schema/boundary 不支持、same-evidence-ref 不一致、unsafe copy 或成功/控制字段出现时 fail closed。

### Robot Platform Engineer

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

完成 `robot_diagnostics_field_evidence_rerun_callback_intake_summary` safe alias。Robot diagnostics 只读暴露 intake status、safe `evidence_ref`、accepted/missing/rejected/blocked counts、same-evidence-ref status、next required evidence 和 proof boundary，不触发 collect/dropoff/cancel、ACK、cursor、Nav2 runtime、serial/UART、WAVE ROVER 或 HIL。

### User Touchpoint Full-Stack Engineer

- `mobile/web/app.js`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

完成 mobile/web 只读“现场证据复跑回执入口”panel。页面优先消费 Robot safe alias，再兼容 callback-intake summary / artifact nested summary / diagnostics summary，只展示白名单字段；Start Delivery、Confirm Dropoff、Cancel gating 不变。

### Product Manager / OKR Owner

- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/tech-done.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/side2side_check.md`
- `sprints/2026.05.20_13-14_field-evidence-rerun-callback-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

完成 sprint closeout、OKR 4.1 当前快照、当前最高优先级和 progress log 同步。

## 5. 验证结果

Engineer worker 报告：

- Autonomy：`python3 -m py_compile pc-tools/evidence/field_evidence_rerun_callback_intake.py tests/test_field_evidence_rerun_callback_intake.py` exit 0；`python3 -m unittest tests.test_field_evidence_rerun_callback_intake` 输出 `Ran 5 tests in 0.051s OK`；CLI `--help` exit 0；required `rg` exit 0；scoped `git diff --check` exit 0。
- Robot：`py_compile` passed；`PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 229 tests in 0.695s OK`；required `rg` passed；scoped diff check passed。
- Full-Stack：`node --check mobile/web/app.js` passed；`python3 -m unittest mobile/web/test_mobile_web_entrypoint.py` 输出 `Ran 165 tests in 1.157s OK`；fixture JSON checks passed；required `rg` passed；scoped diff check passed。

Product closeout 复跑结果记录在 `final.md`：required file check、required `rg`、scoped `git diff --check`、integration fence 和 CLI help smoke 均已通过。

## 6. 文档同步

- PC README 已补 `field_evidence_rerun_callback_intake` 使用方式、schema、required material classes 和 fail-closed mapping。
- `docs/interfaces/evidence_contracts.md` 已补 PC evidence contract。
- `docs/interfaces/ros_contracts.md` 已补 Robot diagnostics safe alias contract。
- `docs/product/mobile_user_flow.md` 已补 mobile/web 只读 panel 和证据边界。

## 7. 偏差和剩余风险

- 无真实现场 callback packet 被证明为 accepted；本轮只证明 callback intake gate、Robot alias 和 mobile panel 的本地 software proof。
- `PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` 已 resolved；`PRRT_kwDOSWB9286CJ3tX` 仍 unresolved/material pending。manual reply `3269642220` 不是硬件 proof。
- 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、真实 WAVE ROVER/UART/HIL、真实 Nav2/fixed-route、route completion signal、field task record、电梯门/楼层/人工协助材料、dropoff/cancel completion 和 delivery success。

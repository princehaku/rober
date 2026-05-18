# Sprint 2026.05.19_07-08 Elevator Field Evidence Material Backfill Intake - Tech Done

## sprint_type: epic

收口时间：2026-05-19 07:58 Asia/Shanghai。

## 1. 实际改动

本轮按 `tech-plan.md` 的 3 owner 拆分完成 implementation，并由 Product closeout 只记录验收与 OKR 边界。

### Autonomy Algorithm Engineer

- 新增 `pc-tools/evidence/elevator_field_evidence_trace_material_backfill_intake.py`。
- 新增 `tests/test_elevator_field_evidence_trace_material_backfill_intake.py`。
- 新增 `docs/interfaces/elevator_field_evidence_trace_material_backfill_intake.md`。
- 输出和文档边界：`software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate` only。
- 作用：消费上一轮 handoff summary 与 operator material packet/file refs 的安全摘要，校验 same safe `evidence_ref`、required materials、unsafe copy、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`，并把安全材料回填入口映射为 blocked / backfill / `ready_for_material_review_not_proven`。

### Robot Platform Engineer

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/operator_gateway_diagnostics.md`。
- 新增 diagnostics safe alias：`robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary`。
- 作用：只读消费 Autonomy summary，缺失、unsupported、unsafe copy、success/control claim 或 boundary mismatch 时 fail closed，不把 raw refs、本机路径、ROS topic、hardware/UART/WAVE ROVER 细节下发给 mobile。

### User Touchpoint Full-Stack Engineer

- 更新 `mobile/web/app.js`。
- 更新 `mobile/web/styles.css`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `mobile/web/fixtures/status.json`。
- 更新 `docs/product/mobile_user_flow.md`。
- 作用：在 mobile/web 增加 `elevator_field_evidence_trace_material_backfill_intake` 只读 panel，展示 intake status、accepted material refs、missing required materials、next required evidence 和 evidence boundary。
- Start Delivery / Confirm Dropoff / Cancel gating 不变，仍由既有安全条件控制。

### Product Manager / OKR Owner

- 新增本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 与 `docs/process/okr_progress_log.md`。
- 只记录 Objective 2 / Objective 3 / Objective 4 的 software-proof 可回填性进展；Objective 5 保持约 68%，Objective 1 保持约 81%，Objective 2 / Objective 3 / Objective 4 保守保持约 99%。

## 2. 验证结果

### Worker 验证证据

Autonomy worker：

```text
python3 -m py_compile pc-tools/evidence/elevator_field_evidence_trace_material_backfill_intake.py
pass

python3 -m unittest tests/test_elevator_field_evidence_trace_material_backfill_intake.py
Ran 7 tests in 0.084s
OK

required rg
pass

scoped git diff --check
pass
```

Robot worker：

```text
python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
pass

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
Ran 198 tests in 0.482s
OK

required rg
pass

scoped git diff --check
pass
```

Full-Stack worker：

```text
python3 mobile/web/test_mobile_web_entrypoint.py
Ran 112 tests
OK

python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

scoped git diff --check
pass
```

### Product closeout 验收命令

Product closeout 已运行：

```bash
test -f sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/tech-done.md && test -f sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/side2side_check.md && test -f sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake/final.md
rg -n "elevator_field_evidence_trace_material_backfill_intake|robot_diagnostics_elevator_field_evidence_trace_material_backfill_intake_summary|software_proof_docker_elevator_field_evidence_trace_material_backfill_intake_gate|software_proof|not_proven|delivery_success=false|primary_actions_enabled=false|Ran 7 tests|Ran 198 tests|Ran 112 tests|Objective 5|Objective 1|Objective 2|Objective 3|Objective 4" OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.19_07-08_elevator-field-evidence-material-backfill-intake
```

结果：三条命令 exit 0；required `rg` 命中本轮 gate、diagnostics alias、software-proof 边界、worker test counts 和 Objective 1/2/3/4/5 记录；scoped `git diff --check` 无输出。

## 3. 偏差与失败定位

- 未发现 worker 验证失败需要 Product 退回。
- 本轮没有复跑全仓库 smoke、Docker/Humble colcon、真实手机浏览器、真实电梯、真实 WAVE ROVER/UART/HIL 或 Objective 5 external proof；这是本轮验收围栏的边界，不是失败。
- Product 未改动 worker 实现文件；只按 worker 返回证据做 closeout 留档。

## 4. 剩余风险

- `ready_for_material_review_not_proven` 只表示 required material refs 安全且齐全到可进入后续 review，不是真实 route/elevator field pass。
- 仍缺真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 Nav2/fixed-route runtime log、真实 route completion signal、真实 field task record、真实 dropoff/cancel completion 和真实 delivery result。
- 仍缺真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 和现场 phone behavior。
- 仍缺真实 WAVE ROVER/UART/HIL、`feedback_T1001.log`、真实 `/odom`、`/imu/data`、`/battery` 和 PR #5 2D LiDAR / ToF 真实 SKU/source/receipt/procurement/installation/wiring/power/calibration/HIL-entry。
- 仍缺 Objective 5 的真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration/cutover 或其他 external proof。

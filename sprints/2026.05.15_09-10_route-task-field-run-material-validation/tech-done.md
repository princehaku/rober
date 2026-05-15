# Sprint 2026.05.15_09-10 Route Task Field Run Material Validation - Tech Done

sprint_type: epic

## 1. 实际改动

本轮建立 `software_proof_docker_route_task_field_run_material_validation_gate`，把上一轮 material bundle 从“目录和模板已生成”推进到“材料状态可校验、可被 Robot diagnostics 和 mobile/web 安全只读消费”。

- Task A / Autonomy Algorithm Engineer：新增 `pc-tools/evidence/route_task_field_run_material_validation.py` 与 `pc-tools/evidence/test_route_task_field_run_material_validation.py`，更新 `pc-tools/README.md` 和 `docs/navigation/fixed_route_workflow.md`。输出 schema 为 `trashbot.route_task_field_run_material_validation.v1` / summary，证据边界为 `software_proof_docker_route_task_field_run_material_validation_gate`。
- Task B / Robot Platform Engineer：更新 `operator_gateway_diagnostics.py`、diagnostics test 与 `docs/interfaces/ros_contracts.md`。diagnostics metadata-only 消费 validation artifact / summary，支持 `TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION` 和 `TRASHBOT_ROUTE_TASK_FIELD_RUN_MATERIAL_VALIDATION_SUMMARY`，schema/boundary/unsafe claim 不匹配时 fail closed。
- Task C / User Touchpoint Full-Stack Engineer：更新 `mobile/web`、fixture、mobile entrypoint test 与 `docs/product/mobile_user_flow.md`。新增只读“路线材料校验”panel，展示 validation status、safe `evidence_ref`、missing/placeholder/mismatch materials、operator next steps、`not_proven` 和 boundary，不改变 Start / Confirm / Cancel gating。
- Task D / Product Manager / OKR Owner：本文件、`side2side_check.md`、`final.md`、`OKR.md` 与 `docs/process/okr_progress_log.md` 收口。Objective 2 / Objective 3 基于 software proof 从约 68% 保守上调到约 69%；Objective 5 保持约 66%。

## 2. 验证结果

Engineer 回传验证：

- Autonomy：`python3 -m py_compile pc-tools/evidence/route_task_field_run_material_validation.py pc-tools/evidence/test_route_task_field_run_material_validation.py` pass；`python3 pc-tools/evidence/test_route_task_field_run_material_validation.py` 输出 `Ran 7 tests in 0.035s OK`；CLI `--help` pass；required `rg` pass；scoped `git diff --check` pass。
- Robot：`python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 73 tests ... OK`；required `rg` pass；scoped `git diff --check` pass。
- Full-stack：`python3 mobile/test_mobile_web_entrypoint.py` 输出 `Ran 40 tests ... OK`；`python3 -m py_compile mobile/test_mobile_web_entrypoint.py` pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped `git diff --check` pass。

Product closeout 验收由 Task D 运行：

```bash
rg -n "software_proof_docker_route_task_field_run_material_validation_gate|Objective 2|Objective 3|not real|不证明" sprints/2026.05.15_09-10_route-task-field-run-material-validation OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.15_09-10_route-task-field-run-material-validation OKR.md docs/process/okr_progress_log.md
```

结果：required `rg` exit 0，命中 sprint closeout、`OKR.md` 与 `docs/process/okr_progress_log.md` 中的 validation gate、Objective 2/3、not real / 不证明边界；scoped `git diff --check` exit 0，无 whitespace error。

## 3. 偏差与边界

本轮没有真实 route/task field run、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实 dropoff completion、真实 cancel completion、delivery success、真实手机/browser 或 Objective 5 外部 proof。

`software_proof_docker_route_task_field_run_material_validation_gate` 只证明 Docker/local material validation artifact、Robot diagnostics metadata-only 消费、mobile/web 只读展示和 fail-closed 控制边界可验证；不证明真实固定路线运行、真实底盘运动、真实投放或真实交付。

## 4. 剩余风险

- Objective 2 仍缺真实送达任务闭环、真实 dropoff/cancel completion、失败恢复实测和 delivery success。
- Objective 3 仍缺真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据和同一 `evidence_ref` 的上车复账。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 与 worker/migration 证据；没有这些外部材料时，不应继续重复消费 O5 blocker。

# Sprint 2026.05.15_11-12 Elevator Field Material Validation - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_elevator_field_material_validation_gate`。电梯 assisted delivery 的下一次受控楼宇现场补证材料，现在已有 PC CLI validation artifact、Robot diagnostics metadata-only summary 和 mobile/web 只读 panel 三端一致消费链路。

本轮不是实机闭环，也不是 delivery success。它只证明 Docker/local 环境中可以提前校验 door state、target floor confirmation、human assistance/operator note、Nav2/fixed-route runtime log、task record、completion signal、diagnostics/mobile safe summary 的材料完整性和安全边界。

## 2. 工程结果

- Task A Autonomy：新增 `elevator_field_run_material_validation` CLI/test，输出 `trashbot.elevator_field_run_material_validation.v1` 和 `trashbot.elevator_field_run_material_validation_summary.v1`，覆盖缺失、模板、坏 JSON、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` fail closed。
- Task B Robot：`operator_gateway_diagnostics.py` 只读消费 explicit ref 和 env summary，暴露 `elevator_field_run_material_validation` / `_summary`，固定 `delivery_success=false`、`primary_actions_enabled=false`。
- Task C Full-stack：`mobile/web/app.js` 新增只读“电梯现场材料校验” panel，兼容 top-level、`phone_readiness`、diagnostics 和 nested diagnostics，不改变 Start/Confirm/Cancel gating。
- Task D Product：更新 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md`。

## 3. 验证结果

- Autonomy：py_compile pass；`test_elevator_field_run_material_validation.py` `Ran 7 tests ... OK`；CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Robot：py_compile pass；`test_operator_gateway_diagnostics.py` `Ran 75 tests ... OK`；required `rg` pass；scoped diff check pass。
- Full-stack：`mobile/test_mobile_web_entrypoint.py` `Ran 42 tests ... OK`；py_compile pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。
- Product：required `rg` pass；scoped `git diff --check` pass。
- Browser render check 未运行，原因是 Browser runtime reported `Browser is not available: iab`。

## 4. OKR 影响

- Objective 2 从约 70% 保守上调到约 71%。理由：本轮把电梯 assisted delivery 现场材料校验纳入同一 `evidence_ref` 的 fail-closed 软件链路，覆盖门状态、目标楼层、人工协助、任务记录、完成信号、诊断和手机安全摘要，能直接支撑 KR6/KR7 的现场补证。
- Objective 3 从约 69% 保守上调到约 70%。理由：本轮将 Nav2/fixed-route runtime log 作为电梯现场材料链的必填项，并让 PC validation、Robot diagnostics、mobile panel 对同一 `evidence_ref` 的路线运行材料保持一致的 blocked/not_proven 边界。
- Objective 5 保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 材料；not real O5 external proof。

## 5. OKR 最低优先级核对回顾

- 当前 `OKR.md` 4.1 数值最低 Objective 仍是 Objective 5，约 66%。
- 本 sprint 是否针对最低 Objective：否。
- 理由仍成立：O5 下一步需要真实外部材料，当前本机只有 Docker，缺真实公网、4G/SIM、OSS/CDN live traffic、production DB/queue 和 worker/migration evidence。继续做本地 O5 metadata depth 会重复消费同一外部材料 blocker。
- 本轮改投 Objective 2/O3 是为了把上一轮默认电梯 assisted delivery dry-run 主链路推进到下一次现场实测前的可校验材料链，而不是替代真实 O5 proof。

## 6. 剩余风险

- 不证明真实电梯、真实楼层确认、真实人工协助、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER/UART/HIL、同一 `evidence_ref` 上车实机复账、真实 dropoff completion、真实 cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。
- Browser runtime 不可用，本轮没有浏览器渲染补验截图或真实手机设备证据。
- 下一步若继续推进 O2/O3，应使用本轮 validation artifact 回填真实现场材料；若推进 O5，必须先提供真实外部云/4G/OSS/CDN/DB/queue 材料。

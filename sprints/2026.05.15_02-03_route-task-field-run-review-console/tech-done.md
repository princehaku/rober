# Sprint 2026.05.15_02-03 Route Task Field Run Review Console - Tech Done

sprint_type: epic

## 1. 用户价值和产品北极星

本轮面向北极星“普通手机用户可验证地完成低成本垃圾投递闭环”中的证据复盘环节：现场人员不再只拿到多份 route/task JSON，而是能看到一个 operator/support 可读的复核报告，知道当前材料是否可进入人工复核、哪些材料缺失或不一致、下一轮应重跑什么命令，以及为什么当前仍不能宣称 delivery success。

这不是新的真实送达能力，而是把下一次真实 route/task field run 的材料复账入口做扎实，降低现场复盘成本。

## 2. OKR 映射和 KR 拆解

- Objective 2：推进 KR5“每次任务产出可复盘记录”。本轮把 intake/crosscheck 结果转成 review decision、operator next steps 和 phone-safe summary。
- Objective 3：推进 KR2/KR5“固定路线流程与 PC/复核展示”。本轮新增 review console artifact，并通过 diagnostics 和 mobile 只读 panel 暴露给 operator/support。
- Objective 5：仍是最低约 68%，但本轮没有真实外部材料，不提升。

本轮核心抓手是 `software_proof_docker_route_task_field_run_review_console_gate`：将 field-run intake/crosscheck 的同一 `evidence_ref` 软件复账，推进到可读 review console、Robot diagnostics metadata-only summary 和 mobile read-only review panel。

## 3. 实际改动

Task A `autonomy-engineer`：

- 新增 `pc-tools/evidence/route_task_field_run_review.py`。
- 新增 `pc-tools/evidence/test_route_task_field_run_review.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/navigation/fixed_route_workflow.md`。
- 交付 schema `trashbot.route_task_field_run_review_console.v1`，boundary `software_proof_docker_route_task_field_run_review_console_gate`。

Task B `robot-software-engineer`：

- 更新 `operator_gateway_diagnostics.py`。
- 更新 `test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_contracts.md`。
- diagnostics 新增 `route_task_field_run_review` / `route_task_field_run_review_summary` metadata-only summary，支持 explicit ref、`TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW_CONSOLE`、`TRASHBOT_ROUTE_TASK_FIELD_RUN_REVIEW`。

Task C `full-stack-software-engineer`：

- 更新 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`。
- 更新 `mobile/fixtures/mobile_web_status.fixture.json`。
- 更新 `test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增只读 route task field-run review panel，消费 `trashbot.route_task_field_run_review_summary.v1` 并保留 source artifact `trashbot.route_task_field_run_review_console.v1`。

Task D `product-okr-owner`：

- 更新 `OKR.md` 4.1。
- 更新 `docs/process/okr_progress_log.md`。
- 创建本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。

## 4. 验证结果

Task A：

- `py_compile` pass。
- `test_route_task_field_run_review.py`：`Ran 6 tests OK`。
- `python3 pc-tools/evidence/route_task_field_run_review.py --help` pass。
- required `rg` pass。
- scoped `git diff --check` pass。
- 中途失败：mismatch decision reason 未明确包含 same `evidence_ref`，已修复并复验。

Task B：

- `py_compile` pass。
- diagnostics unittest：`Ran 59 tests OK`。
- required `rg` pass。
- scoped `git diff --check` pass。

Task C：

- mobile unittest：`Ran 10 tests OK`。
- `py_compile` pass。
- `node --check` pass。
- required `rg` pass。
- scoped `git diff --check` pass。
- 集成返工：mobile schema 从 `trashbot.route_task_field_run_review.v1` 对齐到 Robot diagnostics summary schema `trashbot.route_task_field_run_review_summary.v1`，复验通过。

Task D closeout 验收命令已运行，结果记录在 `final.md`。

## 5. 偏差和修复

- Task A 首轮 mismatch decision reason 缺少 same `evidence_ref` 明确语义；已修复并复验。
- Task C 首轮 schema 对齐到旧 `trashbot.route_task_field_run_review.v1`；已改为 Robot diagnostics summary schema `trashbot.route_task_field_run_review_summary.v1` 并复验。
- 本轮没有访问硬件、串口、ROS graph、Nav2 runtime、外部云、OSS/CDN、DB/queue 或 4G。

## 6. 剩余风险和未完成事项

- `software_proof_docker_route_task_field_run_review_console_gate` 只证明 Docker/local review console、diagnostics summary、mobile read-only review 和控制边界。
- 仍未证明真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、同一 `evidence_ref` 上车复账、dropoff/cancel completion、delivery success 或 O5 external proof。
- Objective 5 仍是最低约 68%，但无真实外部材料，不应因本轮本地软件 proof 上调。

# Sprint 2026.05.16_16-17 Route Task Terminal Completion Rehearsal - Tech Done

sprint_type: epic

## 1. 实际改动

Task A Robot 完成 `route_task_terminal_completion_rehearsal` 的 task record / orchestrator / diagnostics 串接：

- `task_record.py` 写入 terminal completion rehearsal 摘要，覆盖 final status/state、dropoff/cancel material、failure/recovery reason、same `evidence_ref`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
- `task_orchestrator.py` 在 dry-run、manual-confirm、cancel / timeout 终态保守保留 software-proof 上下文，不声明真实投放或真实取消完成。
- `operator_gateway_diagnostics.py` 新增 `route_task_terminal_completion_rehearsal` / `_summary` metadata-only consumer，支持 explicit ref、env source、status/diagnostics nested source；缺失、unsupported、unsafe、same evidence_ref mismatch 均 fail closed。
- `docs/interfaces/ros_contracts.md` 同步记录 Robot diagnostics contract。

Task B Autonomy 完成 dependency-free PC gate：

- 新增 `pc-tools/evidence/route_task_terminal_completion_rehearsal.py` 与 focused tests。
- 读取 route status、task record、existing `route_task_completion_signal`、可选 dropoff/cancel material summary。
- 输出 `trashbot.route_task_terminal_completion_rehearsal.v1` artifact 与 `_summary.v1` summary，统一 boundary 为 `software_proof_docker_route_task_terminal_completion_rehearsal_gate`。
- `pc-tools/README.md` 和 `docs/navigation/fixed_route_workflow.md` 已同步固定路线工作流文档。

Task C Full-stack 完成 mobile/web 只读首屏 panel：

- `mobile/web/app.js` 和 `styles.css` 新增“任务终态复账” panel，展示 terminal verdict、safe `evidence_ref`、dropoff/cancel material status、failure/recovery reason、operator next steps 和 fixed boundary。
- `mobile/web/fixtures/status.json` 与 `test_mobile_web_entrypoint.py` 覆盖 phone-safe 渲染与 copy/export whitelist。
- `docs/product/mobile_user_flow.md` 已同步用户流程说明。
- Start / Confirm Dropoff / Cancel gating 未改变，panel 不授权任何控制动作。

Task D Product Closeout 完成本文件、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` 更新。

## 2. 验证结果

Task A Robot：

- `py_compile` passed。
- `python3 -m unittest ...test_task_record.py ...test_task_orchestrator_collection_execution.py ...test_operator_gateway_diagnostics.py` 输出 `Ran 127 tests in 0.257s OK`。
- required `rg` passed。
- scoped `git diff --check` passed。
- 首轮失败定位：missing source 状态仍返回 `missing`；已修正为 `blocked_missing_route_task_terminal_completion_rehearsal` 并复验通过。

Task B Autonomy：

- `py_compile` passed。
- `python3 -m unittest pc-tools/evidence/test_route_task_terminal_completion_rehearsal.py` 输出 `Ran 8 tests in 0.016s OK`。
- CLI `--help` passed。
- required `rg` passed。
- scoped `git diff --check` passed。
- 新文件已用 `git add -N` 让 diff check 覆盖，但本 closeout 未执行 staging / commit。

Task C Full-stack：

- `python3 -m unittest mobile.web.test_mobile_web_entrypoint` 输出 `Ran 6 tests OK`。
- `node --check mobile/web/app.js` passed。
- required `rg` passed。
- scoped `git diff --check` passed。

Task D Product Closeout：

- `rg -n "route_task_terminal_completion_rehearsal|software_proof_docker_route_task_terminal_completion_rehearsal_gate|Objective 5|Objective 2|Objective 3|Docker|not_proven|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal OKR.md docs/process/okr_progress_log.md` passed。
- `git diff --check -- sprints/2026.05.16_16-17_route-task-terminal-completion-rehearsal OKR.md docs/process/okr_progress_log.md` passed。

## 3. 偏差与失败定位

- Robot 首轮状态归类过宽：missing source 曾被表达为 `missing`，不符合本 sprint fail-closed contract；修正后统一为 `blocked_missing_route_task_terminal_completion_rehearsal`。
- 本轮没有运行全量 Docker/Humble build，符合 tech-plan 的围栏验证口径。
- 本轮没有真实硬件、真实手机设备、真实 route/elevator field session 或 Objective 5 external materials。

## 4. 剩余风险

- 本轮证据边界仅为 `software_proof_docker_route_task_terminal_completion_rehearsal_gate`。
- `not_proven` 仍包括真实 Nav2/fixed-route、真实 route/elevator field pass、真实 dropoff completion、真实 cancel completion、delivery success、真实手机/browser、production app、WAVE ROVER、UART、HIL、真实串口反馈和 Objective 5 external proof。
- `delivery_success=false` 和 `primary_actions_enabled=false` 必须继续贯穿后续 Robot diagnostics 与 mobile/web 消费端，直到同一 `evidence_ref` 下有真实现场材料闭环。

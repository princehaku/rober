# Sprint 2026.05.15_06-07 Route Task Field Run Console - Final

sprint_type: epic

## 1. 最终结论

本 sprint 完成 `software_proof_docker_route_task_field_run_console_gate`。三条工程 worker 已把 route/task completion signal 继续推进为 field-run 准备台：PC/operator CLI 生成现场运行步骤和采集清单，Robot diagnostics metadata-only 消费 summary，`mobile/web` 只读展示“路线现场运行准备”panel。

本轮不是 not real field-run 成功证明；它只说明下一次真实现场路线运行前，软件层已有统一的材料准备、same `evidence_ref` 校验、dropoff/cancel 材料状态和 operator next steps。

## 2. 用户价值与产品北极星

产品北极星：让普通手机用户最终能完成送垃圾任务，并在失败时获得清楚、可操作、可复盘的解释。

本轮实际用户价值：现场操作员不再手动拼散落 JSON/日志/completion signal，而是通过统一 field-run console 获得“该怎么跑、要采什么、同一证据引用是否一致、哪些证明仍缺失”。这把 O2/O3 从 completion verdict 推向真实 field-run 的可执行准备。

## 3. OKR 和 KR 更新

- Objective 2：约 65% -> 约 66%。支撑 KR4/KR5，因为 field-run console 现在能汇总任务状态、dropoff/cancel material status、failure/recovery reason、operator next steps，并保持 `delivery_success=false`。
- Objective 3：约 65% -> 约 66%。支撑 KR2/KR3/KR5，因为 execution pack、route status、task record 和 completion signal 已进入同一 `evidence_ref` 的准备台，并被 diagnostics/mobile 只读消费。
- Objective 1：保持约 73%。本轮没有硬件、WAVE ROVER、UART、Orange Pi、launch 参数、HIL 或真实底盘反馈。
- Objective 4：保持约 73%。本轮只有 mobile 只读 panel，Browser 渲染补验因 `iab` 不可用未运行，不能计真实手机/browser 或 production app。
- Objective 5：保持约 66%。本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 等外部证据。

## 4. 实际交付

- Task A Autonomy：新增 dependency-free `route_task_field_run_console` CLI、测试和导航/PC 文档，输出 `schema=trashbot.route_task_field_run_console.v1`、`software_proof_docker_route_task_field_run_console_gate`、`field_run_plan`、`capture_checklist`、`not_proven`、`delivery_success=false`。
- Task B Robot：diagnostics 新增 `route_task_field_run_console` / `_summary` 只读消费，支持 explicit ref 和环境变量来源，严格阻断 unsafe/schema/boundary/action claim。
- Task C Full-stack：`mobile/web` 新增只读“路线现场运行准备”panel，展示 safe `evidence_ref`、plan/checklist、dropoff/cancel status、operator next steps、`not_proven` 和 boundary。
- Task D Product：补齐 `tech-done.md`、`side2side_check.md`、`final.md`，更新 `OKR.md` 和 `docs/process/okr_progress_log.md`。

## 5. 验证摘要

- Task A：`py_compile` pass；`python3 pc-tools/evidence/test_route_task_field_run_console.py` -> `Ran 6 tests in 0.019s OK`；CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Task B：`py_compile` pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` -> `Ran 67 tests in 0.053s OK`；required `rg` pass；scoped diff check pass。
- Task C：`python3 mobile/test_mobile_web_entrypoint.py` -> `Ran 37 tests in 0.073s OK`；`py_compile` pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。
- Task C Browser 补验未运行：`Browser is not available: iab`，不能计真实手机/browser 证据。
- Task D：closeout required commands 在最终回复中给出摘要。

## 6. 风险、阻塞和补证链

仍需补齐：

- 真实 Nav2/fixed-route 运行。
- 真实路线采集和关键帧实景证据。
- WAVE ROVER、真实串口/UART、`T=1001` feedback、HIL。
- 同一 `evidence_ref` 的上车实机复账。
- 真实 dropoff/cancel completion、失败恢复和 delivery success。
- 真实手机/browser、production app、真实 PWA prompt/user choice。
- Objective 5 external proof：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/migration。

## 7. 下一步建议

下一轮按 `OKR.md` 4.1 重新排序。当前最低完成度仍是 Objective 2、Objective 3 与 Objective 5 并列约 66%；但 O5 下一步需要真实外部材料，若仍不可用，应优先选择 O2/O3 中最接近真实现场运行的动作：准备真实 route/task field-run 的材料目录、执行命令、采集模板和同一 `evidence_ref` 上车复账要求，或在具备硬件/路线条件后直接跑真实 Nav2/fixed-route。

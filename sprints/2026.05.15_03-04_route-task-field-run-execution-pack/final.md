# Sprint 2026.05.15_03-04 Route Task Field Run Execution Pack - Final

sprint_type: epic

## 1. 用户价值和产品北极星

本轮把 route/task field-run review console 推进为现场人员可执行的 execution pack：材料模板、同一 `evidence_ref` 要求、first-run/rerun commands、operator next steps 和 phone-safe summary 已被 artifact、diagnostics 和 mobile 只读触点贯通。

产品北极星仍是低成本 ROS2 垃圾投递机器人完成可验证送达闭环。本轮没有完成真实送达闭环，而是把下一次真实 route/task field run 的材料采集准备向前推进。

## 2. OKR 映射和 KR 更新

- Objective 2：推进 KR5“每次任务产出可复盘记录”。本轮让 task record、robot-side task evidence、dropoff/cancel completion 和失败复盘材料进入 execution pack 清单。
- Objective 3：推进 KR2/KR3/KR5。route status、Nav2/fixed-route runtime log、review console 和现场执行材料现在有同一 `evidence_ref` 执行包入口。
- Objective 5：不推进。没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 证据。

OKR 完成度保守更新：

- Objective 2：约 62% -> 约 63%。
- Objective 3：约 62% -> 约 63%。
- Objective 5：保持约 66%。

## 3. 本轮核心抓手和实际交付

核心抓手：`software_proof_docker_route_task_field_run_execution_pack_gate`。

已完成：

- Task A Autonomy：新增 execution pack CLI 和测试，更新 PC/navigation 文档。
- Task B Robot：新增 diagnostics metadata-only execution pack summary，保持动作、ACK、cursor、HIL、delivery success 隔离。
- Task C Full-stack：新增 `mobile/web` 只读“路线任务现场执行包”panel，缺 summary 时 blocked/not_proven，不改变 Start/Confirm/Cancel gating。
- Task D Product：完成 sprint closeout、`OKR.md` 和 `docs/process/okr_progress_log.md` 更新。

## 4. 验收结果

Worker 验证已完成：

- Task A：py_compile pass；`test_route_task_field_run_execution_pack.py` `Ran 6 tests OK`；`--help` pass；required rg pass；scoped diff check pass。
- Task B：py_compile pass；`test_operator_gateway_diagnostics` `Ran 61 tests OK`；required rg pass；scoped diff check pass。
- Task C：mobile unittest `Ran 12 tests OK`；py_compile pass；`node --check mobile/web/app.js` pass；required rg pass；scoped diff check pass。

Task D closeout 验证：

```text
rg closeout/OKR/process/sprint boundary check
pass; key hits include sprint name, software proof boundary, Objective 2, Objective 3, Objective 5, not_proven, delivery success and HIL

git diff --check -- OKR.md docs/process/okr_progress_log.md tech-done.md side2side_check.md final.md
pass
```

## 5. 风险、阻塞和证据链

本轮证据边界是 Docker/local software proof，不是现场成功：

- 不是真实 Nav2/fixed-route。
- 不是真实路线采集。
- 不是 WAVE ROVER、真实串口/UART 或 HIL。
- 不是同一 `evidence_ref` 上车复账。
- 不是 dropoff/cancel completion。
- 不是 delivery success。
- 不是 Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

下一步建议：如果继续推进最低 Objective，应使用本轮 execution pack 采集真实 route/task field run 材料，并以同一 `evidence_ref` 形成上车复账；如果缺现场条件，则不要把本地 artifact 继续包装成 delivery success。

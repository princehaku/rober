# Sprint 2026.05.16_01-02 Elevator Evidence Driven Mainline - Tech Done

sprint_type: epic

## 1. 实际改动

本 sprint 完成 `software_proof_docker_elevator_evidence_driven_mainline_gate`。它只证明 Docker/local rehearsal evidence artifact、Robot dry-run behavior consumption、task record evidence anchor 和 mobile read-only summary 的软件链路，不证明真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。

### Task A - Autonomy Algorithm Engineer

- 新增 `pc-tools/evidence/elevator_assist_rehearsal_evidence.py` 与测试，产出 `schema=trashbot.elevator_assist_rehearsal_evidence.v1`。
- artifact 与 summary 固定 `evidence_boundary=software_proof_docker_elevator_evidence_driven_mainline_gate`、`source=software_proof`、`delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`。
- `phase_evidence` 覆盖等待电梯开门、进入电梯、请求按目标楼层、等待目标楼层、驶出电梯；failure path 包含 `manual_takeover_reason`，用于 Robot fail-closed rehearsal。
- 同步更新 `pc-tools/README.md`、`docs/navigation/fixed_route_workflow.md`、`docs/product/elevator_assisted_delivery.md`，明确该 gate 是 Robot dry-run 主链路输入，不是现场成功证据。

验证结果：

```text
py_compile pass
pc-tools/evidence/test_elevator_assist_rehearsal_evidence.py: Ran 5 tests in 0.002s OK
CLI --help pass
CLI --once-json pass
required rg pass
scoped git diff --check pass
```

### Task B - Robot Platform Engineer

- `task_orchestrator` 新增 `elevator_assist_evidence_file`，只在 `elevator_assist_mode=dry_run` 下只读 artifact。
- 缺失或空文件保持既有 dry-run fallback；非法 artifact、schema/boundary/boolean/source 不满足 contract 时 fail closed。
- artifact 通过时按 `phase_evidence` 驱动 `machine.elevator_phase(...)`，并把 artifact `evidence_ref` 提升到 task record 顶层 `evidence_ref` / `result_path`。
- 继续固定 `delivery_success=false`、`primary_actions_enabled=false`、`source=software_proof` 和 `not_proven`，不触发真实 Nav2/HIL/ACK/delivery success claim。

验证结果：

```text
py_compile pass
onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py: Ran 15 tests in 0.017s OK
required rg pass
scoped git diff --check pass
```

### Task C - User Touchpoint Full-Stack Engineer

- `mobile/web` 的电梯辅助 panel 兼容 `elevator_assist_rehearsal_evidence` / summary。
- 展示 safe `evidence_ref`、phase evidence、failure/manual takeover、same evidence ref requirement、boundary、`delivery_success=false`、`primary_actions_enabled=false` 和 `not_proven`。
- Start Delivery、Confirm Dropoff、Cancel gating 未改；raw ROS topic、serial/UART、WAVE ROVER、local path、credential、raw artifact、success phrasing 仍被过滤或不展示。
- 同步更新 `docs/product/mobile_user_flow.md`，说明 evidence-driven panel 是只读解释面。

验证结果：

```text
mobile/test_mobile_web_entrypoint.py: Ran 44 tests in 0.130s OK
py_compile pass
node --check mobile/web/app.js pass
required rg pass
scoped git diff --check pass
```

### Task D - Product Manager / OKR Owner

- 新建本文件、`side2side_check.md`、`final.md`，收口工程改动、验收结论、OKR 最低优先级复核和剩余风险。
- 更新 `OKR.md` 4.1 当前快照与第 6 节最高优先级，最新 sprint 改为 `2026.05.16_01-02_elevator-evidence-driven-mainline`。
- 在 `docs/process/okr_progress_log.md` 顶部追加本 sprint 摘要，保持 `software_proof` only、not real elevator/Nav2/HIL/delivery/O5 proof 边界。

验证结果：

```text
Product closeout required rg pass
scoped git diff --check pass
```

## 2. OKR 影响

| Objective | 本轮后进度 | 判断 |
| --- | --- | --- |
| Objective 1：硬件协议可信底盘 | 约 73% | 本轮未改硬件、WAVE ROVER、UART、Orange Pi 或真实串口证据；`not_proven` 仍包含 HIL，不上调。 |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 约 74% | Robot 主链路现在能在 dry-run 下消费同一 `evidence_ref` 的 rehearsal evidence artifact，并把阶段证据写入 task record；这推进 O2 KR6/KR7，因此从约 73% 保守上调到约 74%。 |
| Objective 3：可验证导航与固定路线 | 约 73% | artifact 与 task record 对齐同一 `evidence_ref`，把 Nav2/fixed-route runtime 后续复账材料接入主链路 evidence anchor，因此从约 72% 保守上调到约 73%。 |
| Objective 4：手机用户体验与低成本量产边界 | 约 74% | 手机端能解释 evidence-driven 电梯阶段、失败和人工接管原因，且保持主操作 fail-closed，因此从约 73% 保守上调到约 74%。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 约 66% | 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration；not real Objective 5 external proof，不上调。 |

## 3. 剩余风险

- 真实电梯门状态、目标楼层确认、人工协助记录、真实喇叭/TTS、真实 Nav2/fixed-route runtime 和真实路线采集仍缺。
- WAVE ROVER/UART/HIL、真实串口 feedback、同一 `evidence_ref` 上车实机复账仍缺。
- 真实 dropoff completion、真实 cancel completion、delivery success 仍缺。
- 真实手机设备/browser、production app、真实 PWA prompt/user choice 仍缺。
- Objective 5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。

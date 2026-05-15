# Sprint 2026.05.16_01-02 Elevator Evidence Driven Mainline - Final

sprint_type: epic

## 1. 收口结论

本 sprint 完成 `software_proof_docker_elevator_evidence_driven_mainline_gate`。电梯 assisted delivery 现在不仅有 execution pack，还新增了 Robot dry-run 主链路可消费的 rehearsal evidence artifact：Autonomy 生成 `trashbot.elevator_assist_rehearsal_evidence.v1`，Robot 只读消费并把同一 `evidence_ref` 提升到 task record，Mobile 只读展示 phase evidence、failure/manual takeover 和 boundary。

这条链路的产品价值是把下一次真实现场/上车复账前的“门状态、目标楼层、人工协助、Nav2/fixed-route runtime、task record、completion signal 必须同一 `evidence_ref`”压进主链路，而不是继续停留在 execution pack 文档层。它不证明真实电梯、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实手机/browser、真实 dropoff/cancel completion、delivery success 或 Objective 5 external proof。

## 2. OKR 影响

| Objective | 本轮后进度 | 判断 |
| --- | --- | --- |
| Objective 1：硬件协议可信底盘 | 约 73% | 本轮未改硬件、WAVE ROVER、UART、Orange Pi 或真实串口证据；`software_proof_docker_elevator_evidence_driven_mainline_gate` 明确不证明 HIL，不上调。 |
| Objective 2：可送垃圾任务 + 电梯 assisted delivery 必达闭环 | 约 74% | Robot 主链路可消费同一 `evidence_ref` 的 elevator rehearsal evidence，并把 phase/failure/manual takeover 写入 task record；O2 KR6/KR7 从执行包推进到 evidence-driven dry-run 主链路，因此从约 73% 保守上调到约 74%。 |
| Objective 3：可验证导航与固定路线 | 约 73% | 同一 `evidence_ref` 已进入 task record 顶层 anchor，为后续把 Nav2/fixed-route runtime log 接入真实现场复账链路提供软件主线，因此从约 72% 保守上调到约 73%。 |
| Objective 4：手机用户体验与低成本量产边界 | 约 74% | 手机端能展示 evidence-driven elevator assist 的阶段证据、失败原因、人工接管和边界，且主操作保持 fail-closed，因此从约 73% 保守上调到约 74%。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | 约 66% | 本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料；not real Objective 5 external proof，不上调。 |

## 3. 验收结果

工程线回传：

- Task A Autonomy：py_compile pass；`pc-tools/evidence/test_elevator_assist_rehearsal_evidence.py` `Ran 5 tests in 0.002s OK`；CLI `--help` pass；CLI `--once-json` pass；required `rg` pass；scoped diff check pass。
- Task B Robot：py_compile pass；`onboard/src/ros2_trashbot_behavior/test/test_task_orchestrator_collection_execution.py` `Ran 15 tests in 0.017s OK`；required `rg` pass；scoped diff check pass。
- Task C Full-stack：`mobile/test_mobile_web_entrypoint.py` `Ran 44 tests in 0.130s OK`；py_compile pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。

Product closeout 验收：

```bash
rg -n "elevator_assist_rehearsal_evidence|software_proof_docker_elevator_evidence_driven_mainline_gate|not real|不证明|delivery_success=false|Objective 5" sprints/2026.05.16_01-02_elevator-evidence-driven-mainline OKR.md docs/process/okr_progress_log.md
git diff --check -- sprints/2026.05.16_01-02_elevator-evidence-driven-mainline OKR.md docs/process/okr_progress_log.md
```

结果：`rg` 覆盖 sprint closeout、`OKR.md` 与 `docs/process/okr_progress_log.md` 中的 evidence schema、boundary、`delivery_success=false`、`不证明` / `not real` 和 Objective 5 边界；scoped `git diff --check` 无输出，exit 0。

## 4. OKR 最低优先级核对

本轮启动时最低 Objective 是 Objective 5，约 66%；final 复核后仍是最低。由于没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration，继续推进本地 O5 metadata 会重复消费 external blocker。因此本 sprint 继续切到 Objective 2/3/4 的电梯 evidence-driven 主链路，符合 `OKR.md` 第 6 节规则。

## 5. 风险和未完成事项

- 真实电梯门状态、目标楼层确认、人工协助记录、真实喇叭/TTS、真实 Nav2/fixed-route runtime、真实路线采集仍缺。
- WAVE ROVER/UART/HIL、真实串口 feedback、同一 `evidence_ref` 上车实机复账仍缺。
- 真实 dropoff completion、真实 cancel completion、delivery success 仍缺。
- 真实手机设备/browser、production app、真实 PWA prompt/user choice 仍缺。
- Objective 5 external proof 仍缺：公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。

## 6. 下一步建议

若下一轮仍没有 O5 外部材料，不要继续叠本地 O5 gate。最高可行动作是把 `elevator_assist_rehearsal_evidence` 主链路交给真实现场/上车复账：补真实电梯门状态、目标楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record、completion signal、WAVE ROVER/UART/HIL、dropoff/cancel completion 和 delivery success，并保持同一 `evidence_ref`。

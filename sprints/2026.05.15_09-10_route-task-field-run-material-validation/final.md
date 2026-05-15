# Sprint 2026.05.15_09-10 Route Task Field Run Material Validation - Final

sprint_type: epic

## 1. 收口结论

本轮完成 `software_proof_docker_route_task_field_run_material_validation_gate`。上一轮 material bundle 只能说明材料目录和模板可生成；本轮新增 validation gate 后，可以在 Docker/local 环境校验 route/task/completion/operator notes/diagnostics/mobile summary 是否仍是模板、是否缺失、是否同一 `evidence_ref`、是否出现 unsafe copy 或错误的 `delivery_success=true` / `primary_actions_enabled=true` claim。

用户价值是减少下一次真实 route/task field run 前的材料遗漏和证据错配。产品北极星仍是“普通手机用户交付垃圾后，小车可验证地沿固定路线完成投递”；本轮只是把现场材料准备从 bundle 推进到 validation，不声明投递完成。

## 2. 实际改动与责任人

- Autonomy Algorithm Engineer：交付 PC 侧 material validation CLI、test、`pc-tools/README.md` 和 `docs/navigation/fixed_route_workflow.md` 更新。
- Robot Platform Engineer：交付 diagnostics metadata-only 消费 validation artifact / summary、diagnostics tests 和 `docs/interfaces/ros_contracts.md` 更新。
- User Touchpoint Full-Stack Engineer：交付 `mobile/web` 只读“路线材料校验”panel、fixture、mobile tests 和 `docs/product/mobile_user_flow.md` 更新。
- Product Manager / OKR Owner：交付 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md` closeout。

## 3. OKR / KR 更新

- Objective 2：从约 68% 保守上调到约 69%。理由是 material validation gate 已能把 task record、completion、operator notes、diagnostics、mobile summary 的缺失/占位/错配状态转成下一次真实现场联跑前的明确补证动作，推进 KR4/KR5。
- Objective 3：从约 68% 保守上调到约 69%。理由是 validation gate 已把 route status、Nav2/fixed-route runtime log、same `evidence_ref`、placeholder/mismatch materials 和 rerun guidance 统一成可复盘 artifact，推进 KR2/KR3/KR5。
- Objective 5：保持约 66%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部材料，不能重复消费 O5 blocker。

## 4. 验证证据

- Autonomy：py_compile pass；`python3 pc-tools/evidence/test_route_task_field_run_material_validation.py` 输出 `Ran 7 tests in 0.035s OK`；CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Robot：py_compile pass；`python3 onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py` 输出 `Ran 73 tests ... OK`；required `rg` pass；scoped diff check pass。
- Full-stack：`python3 mobile/test_mobile_web_entrypoint.py` 输出 `Ran 40 tests ... OK`；py_compile pass；`node --check mobile/web/app.js` pass；required `rg` pass；scoped diff check pass。
- Product：本轮 closeout 跑 `rg -n "software_proof_docker_route_task_field_run_material_validation_gate|Objective 2|Objective 3|not real|不证明" ...`，命中 sprint closeout、`OKR.md` 与 `docs/process/okr_progress_log.md`；scoped `git diff --check` exit 0，无 whitespace error。

## 5. 风险与未完成事项

本轮不证明真实 route/task field run、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实 dropoff completion、真实 cancel completion、delivery success、真实手机/browser 或 Objective 5 external proof。

下一轮如果仍没有 O5 外部材料，不要继续堆 O5 本地 metadata；应优先把 Objective 2 / Objective 3 的 material validation 用到真实现场材料回填：真实 Nav2/fixed-route run、同一 `evidence_ref` 上车复账、真实 dropoff completion、真实 cancel completion 或 delivery success。只有拿到公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 证据时，才重新推进 Objective 5。

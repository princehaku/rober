# Sprint 2026.05.15_09-10 Route Task Field Run Material Validation - Side2Side Check

sprint_type: epic

## 1. 对照目标

本轮目标是把 `08-09` material bundle 推进为材料校验 gate，让 PC artifact、Robot diagnostics 和 mobile/web 对同一 `evidence_ref` 的材料状态形成一致只读结论。

对照 PRD，核心用户价值已经落在“下一次真实 route/task field run 前，现场同学能提前看到哪些材料缺失、哪些仍是模板、哪些字段会让后续流程 fail closed”。这不是 delivery success，也不是 HIL。

## 2. OKR 对照

- Objective 2：validation gate 能把 task record、completion、operator notes、diagnostics 和 mobile summary 的材料状态变成明确缺口与下一步动作，支持 KR4/KR5 的任务复盘质量，因此可从约 68% 保守上调到约 69%。
- Objective 3：validation gate 能把 route status、Nav2/fixed-route runtime log、same `evidence_ref`、placeholder/mismatch materials 和重跑动作统一成可复盘 artifact，支持 KR2/KR3/KR5，因此可从约 68% 保守上调到约 69%。
- Objective 5：没有真实外部云/4G/OSS/CDN/DB/queue 材料，仍保持约 66%，not real O5 external proof。

## 3. 交付对照

- Autonomy 交付了 material validation CLI、targeted tests 和 navigation/PC 工具文档。
- Robot 交付了 validation artifact / summary 的 metadata-only diagnostics 消费，并保持 fail closed。
- Full-stack 交付了只读“路线材料校验”panel，不改变 Start / Confirm / Cancel gating。
- Product 已将 sprint closeout、OKR 进度和 progress log 统一到 `software_proof_docker_route_task_field_run_material_validation_gate` 边界。

## 4. 不证明清单

本轮不证明真实 route/task field run、真实 Nav2/fixed-route、真实路线采集、WAVE ROVER、真实串口/UART、HIL、真实 dropoff/cancel completion、delivery success、真实手机/browser、Objective 5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。

## 5. 验收结论

本轮满足 Epic sprint 验收口径：三个 Engineer 交付和文档同步均围绕 material validation gate，验证结果为 targeted/fenced pass；Product 收口保守更新 O2/O3 到约 69%，并明确 O5 不上调。

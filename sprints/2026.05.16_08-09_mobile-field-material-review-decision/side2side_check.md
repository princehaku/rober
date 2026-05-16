# Sprint 2026.05.16_08-09 Mobile Field Material Review Decision - Side2Side Check

sprint_type: epic

## 1. 对照结论

本轮 PRD 要求把 `mobile_field_material_intake` 从“收材料”推进到“评审决策”，输出 review decision、blocker、next-required-evidence 和 owner handoff。A/B/C 已完成 PC gate、Robot diagnostics consumer 和 mobile read-only surface，D 已按实际证据更新 closeout、OKR 和进度日志。

对照结果：本轮达到 `software_proof_docker_mobile_field_material_review_decision_gate` 的 sprint 验收口径，但不证明真实手机/PWA、真实 route/elevator field pass、真实 Nav2/fixed-route、dropoff/cancel completion、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。

## 2. PRD 验收对照

| PRD 要求 | 结果 | 证据 |
| --- | --- | --- |
| PC gate 能把 intake 转成 review decision artifact/summary | 通过 | Task C 新增 `mobile_field_material_review_decision` gate，测试 `Ran 4 tests ... OK`，CLI `--help` OK。 |
| Robot diagnostics metadata-only consumer | 通过 | Task B 新增 `mobile_field_material_review_decision` / summary consumer，diagnostics unittest `Ran 89 tests ... OK`。 |
| Mobile 只读 review decision panel | 通过 | Task A 新增现场材料评审决策 panel，mobile entrypoint `Ran 50 tests ... OK`，`node --check` OK。 |
| 输出 blocker、next-required-evidence、owner handoff | 通过 | Task A/B/C 均记录 safe `evidence_ref`、same-evidence-ref、owner handoff、`not_proven` 和 boundary。 |
| Start / Confirm Dropoff / Cancel gating 不改变 | 通过 | Task A 明确未改 gating；Task B flags 保持 command/ACK/cursor/persistence/Nav2/HIL/dropoff/cancel/delivery-success false。 |
| Objective 5 不上调 | 通过 | `OKR.md` 保持 Objective 5 约 66%，并记录缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration。 |

## 3. OKR 对照

- Objective 2：从约 76% 保守上调到约 77%。理由是 review decision 能把 route/elevator intake 材料转成 blocker、next evidence 和 owner handoff，支撑下一次真实送达/电梯材料补证。
- Objective 3：从约 76% 保守上调到约 77%。理由是 fixed-route/Nav2 runtime log、task record/completion signal、same `evidence_ref` 的缺口能被 gate 明确分类和分派。
- Objective 4：从约 78% 保守上调到约 79%。理由是手机入口新增只读评审决策 panel，现场人员能直接看到 phone-safe blocker 和下一步交接。
- Objective 5：保持约 66%。本轮没有真实外部 O5 证据，不能上调。
- Objective 1：保持约 73%。本轮未改 WAVE ROVER、UART、Orange Pi、真实串口、`T=1001` feedback 或 HIL。

## 4. 剩余差距

- `software_proof_docker_mobile_field_material_review_decision_gate` 不证明真实手机/PWA、真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice。
- 不证明真实 route/elevator field pass、真实 Nav2/fixed-route、真实路线采集、真实电梯门状态、真实目标楼层确认、真实人工协助记录、真实 dropoff/cancel completion 或 delivery success。
- 不证明 HIL、WAVE ROVER/UART、真实串口、`T=1001` feedback、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration。

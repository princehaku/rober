# O6/O7 Route Execution Credit Material Side2Side Check

## 验收对象

- Sprint：`sprints/2026.07.10_12-20_o6_o7_route_execution_credit_material/`
- OKR：O6 云端核心后端、O7 PC 端运营调试平台
- 证据边界：`software_proof_o6_o7_route_execution_credit_material_only`

## 对照检查

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| Algorithm packet 产出 credit-aware 字段 | 通过 | `field_route_evidence_manifest.py` 新增 5 个字段，单测 `Ran 67 tests in 0.499s OK` |
| O6 archive/readback 保留字段并 fail-closed | 通过 | `remote_cloud_relay.py` 保留 credit 字段，relay 单测 `Ran 171 tests in 68.289s OK` |
| O7 consumer/UI 消费并展示字段 | 通过 | workstation `Tests 486 passed (486)`，build/lint 通过 |
| Candidate true 不提升 delivery/control/safety | 通过 | 三侧均固定 `delivery_success=false`、`safe_to_control=false`、`primary_actions_enabled=false`、`robot_control_executed=false` |
| O6/O7 合同一致性 | 通过，已返工 | O7 接受 O6 candidate-true 空 `credit_support_only_reason`，candidate-false 仍要求非空 |
| Fail-closed 保留 selected task id | 通过，已返工 | `catalog.test.ts` 覆盖缺字段路径 task id preservation |
| 主节点全局 diff 空白检查 | 通过 | `git diff --check` exit 0 |

## OKR 最低优先级回顾

绝对最低 O5 约 85%，但最近 sprint 已明确下一步必须是真实 production cloud、production DB/queue external probe 或真实 live endpoint evidence；当前环境没有这些外部材料，继续 local/mock probe/readback 只会重复 support-only blocker。O1 约 86%，但缺真实 nonzero L/R、轮向、operator report 与 HIL acceptance，继续软件 gate 包装也不应加分。

因此本轮选择 O6/O7：上轮 11-30 final 要求下一步接 live route execution、delivery record、operator confirmation 或 production cloud readback。本轮把这些材料是否存在、是否具备 credit candidate 形态固化到同一 packet，是对该要求的可验证推进。

## 验收结论

本轮可以把 O6/O7 从约 87% 保守上调到约 88%。上调依据是同一 `task_id` 的 route execution material packet 已从“材料安全摘要”推进到“可计分材料判定合同”，并完成 Algorithm -> O6 -> O7 的端到端软件验证。

本轮不归档任何 KR，不宣称真实送达、真实生产云、真实机器人运动或 HIL 通过。

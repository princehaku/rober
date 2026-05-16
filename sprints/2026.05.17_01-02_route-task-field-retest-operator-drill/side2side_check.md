# Sprint 2026.05.17_01-02 Route Task Field Retest Operator Drill - Side2Side Check

sprint_type: epic

## 1. 对照范围

本检查对照 `prd.md`、`tech-plan.md`、A/B/C worker 交付证据和 Product closeout 要求。验收只覆盖 Docker/local software proof，不覆盖真实硬件、真实手机、真实云端或真实送达。

## 2. 用户价值对照

- 需求：现场人员需要从 material pack summary 明确知道下一步跑什么命令、产出哪些文件、缺哪些材料，以及如何回调结果。
- 结果：PC operator drill 输出 material pack command、result intake command、result reconciliation command、required outputs、missing material prompts、operator callback checklist、rerun notes 和 safe copy；Robot/mobile 只读消费同一 summary。
- 结论：满足“材料包 -> result intake -> result reconciliation 操作演练层”的产品目标，但只证明流程可执行，不证明真实现场已完成。

## 3. OKR 与方向证据对照

- Objective 5 仍是数值最低，约 66%，但 Docker-only 本机没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。因此本轮不提升 Objective 5，也不继续本地 O5 wrapper。
- PR #4 把 elevator-assisted delivery、门状态、楼层确认、人工协助和失败解释推进为主链路要求。
- PR #5 把跨楼层送垃圾和硬件 baseline/source 证据链推成必须材料边界，并暴露硬件 baseline/source 证据需要继续保守追踪。
- 近期 material pack sprint 已完成八类材料目录入口，本轮 operator drill 是 material pack -> result intake -> result reconciliation 的操作演练层。

## 4. 验收口径对照

| 验收项 | 结果 | 说明 |
| --- | --- | --- |
| 输出 `trashbot.route_task_field_retest_operator_drill.v1` / summary | 通过 | Task A 已实现 artifact / summary 输出。 |
| 统一 boundary | 通过 | 使用 `software_proof_docker_route_task_field_retest_operator_drill_gate`。 |
| 保持 `not_proven` | 通过 | PC、Robot、mobile 和 sprint docs 均保留该状态。 |
| 保持 `delivery_success=false` | 通过 | 未声明真实送达成功。 |
| 保持 `primary_actions_enabled=false` | 通过 | mobile 主操作 gating 未改变。 |
| Robot metadata-only | 通过 | 不触发 collect/dropoff/cancel/ACK/Nav2/HIL/delivery success。 |
| mobile 只读 panel | 通过 | “现场操作演练”只展示 safe summary 和下一步动作。 |
| Objective 5 不提升 | 通过 | OKR 和 progress log 保持 Objective 5 约 66%。 |

## 5. 责任 Engineer 对照

- Autonomy Engineer：PC operator drill gate 和导航流程文档。
- Robot Platform Engineer：operator gateway diagnostics metadata-only consumer 和 ROS contract 文档。
- User Touchpoint Full-Stack Engineer：mobile/web 只读 panel 和手机流程文档。
- Product Manager / OKR Owner：sprint closeout、OKR 4.1 快照、progress log。

## 6. 剩余风险

本轮仍缺真实现场材料和真实外部 O5 证据。验收结论不得写成真实 route/elevator field pass、HIL、真实手机/browser、production app、真实投放、delivery success 或 Objective 5 external proof。

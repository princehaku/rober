# Pre Start - O7 Field Evidence Consumer Ingest

## Sprint 元信息

- `sprint_type: epic`
- Sprint 目录：`sprints/2026.06.09_18-19_o7-field-evidence-consumer-ingest/`
- 发起时间：2026-06-09 18:19 CST
- 主责 owner：`full-stack-software-engineer`
- 方向归属：O7 PC 端运营调试与数据训练平台

## 背景与证据

最近两轮现场材料相关 sprint 都把主结论落在同一个 SSH blocker 上：

- [`/Users/m1/apps/rober/sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md`](/Users/m1/apps/rober/sprints/2026.06.09_15-04_board-field-evidence-preflight/final.md)
- [`/Users/m1/apps/rober/sprints/2026.06.09_17-03_field-evidence-artifact-gate/final.md`](/Users/m1/apps/rober/sprints/2026.06.09_17-03_field-evidence-artifact-gate/final.md)

两轮都已经按 `ssh root@192.168.1.11 -p 37878` 入口尝试，但结果仍是 `blocked_ssh_unreachable`。因此本轮不能再把目标定义成“继续等 SSH”或“再次只消费同一 SSH blocker”，必须把上一轮的 `field evidence manifest` 接到一个可运行的产品消费链里。

## 用户价值与北极星

用户需要的不是一份只读的证据清单，而是能直接驱动 O7 工作台的可运行入口：

1. 把现场材料变成可回放、可标注、可筛查的 O7 数据入口。
2. 在真实 SSH 不稳定时，仍能通过 local/mock fixture 完成验证和回归。
3. 让 `field evidence manifest` 不再停留在 gate，而是成为 O7 route replay / labeling 的稳定上游。

北极星没有变化：让现场路线、标注和回放形成可复用的数据闭环，而不是继续堆只读 surface。

## 本轮方向判断

**结论：转向 O7 field evidence consumer ingest。**

不把本轮定义成 live SSH-only sprint，因为最近两轮已经连续消费同一根因 blocker。当前最佳方向是：

- 主线：O7 route replay / labeling consumer ingest
- 上游：接入上一轮生成的 `field_evidence_manifest`
- 兜底：local/mock fixture 验收必须可跑通
- 可选增强：如果 live SSH 恢复，则作为附加输入路径，而不是唯一成功条件

## 升级原因

同一 blocker 已连续出现两轮，继续做 SSH 收口只会重复产出 `blocked_ssh_unreachable`，不会提升 O7 或 O6 的可运行度。

本轮改做 O7 consumer ingest 的原因是：

- 既能消化上一轮现场材料格式化成果
- 又能把 O7 PC 端从只读 preview 推进到可运行的消费链
- 还能保留 live SSH 作为后续增强路径，不依赖它才能完成验收

## 本轮目标

在不改产品代码之前先把设计边界钉死：

1. 明确 O7 consumer ingest 的入口、输出和 fail-closed 行为。
2. 明确 local/mock fallback 和 live SSH fallback 的一致验收口径。
3. 明确未来实现必须先完成的功能点完整性标准，避免写一半就交差。
4. 明确主责工程师、文件范围和验证命令。

## 需要创建或更新的 sprint 文档

- `pre_start.md`：本文件
- `prd.md`：用户价值、需求、范围、验收口径
- `tech-plan.md`：接口边界、文件范围、验收命令、风险和 owner


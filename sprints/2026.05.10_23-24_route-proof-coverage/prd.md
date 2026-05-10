# Sprint 2026.05.10 23-24 Route Proof Coverage - PRD

## 状态

- 阶段：prd completed。
- 时间：2026-05-10 23:24 Asia/Shanghai。
- Product Owner：`product-okr-owner`。
- 实现 owner：`autonomy-engineer`、`full-stack-software-engineer`（并行）。

## 背景

`OKR.md` 当前最低完成度是 Objective 3（约 73%）。已有 fixed-route dry-run 与 visual gate 证明能力，但 route coverage 证据粒度和 operator 可理解性仍不足：

- 导航侧缺少“这条路线覆盖了多少、哪些点位未达标、为何阻塞”的稳定证明输出。
- 触点侧缺少对该证明的统一展示口径，导致运营/调试解释成本高。

## 用户价值和产品北极星

- 用户价值：把“能跑”升级为“能证明可跑 + 失败可解释”，让 operator 快速知道是否可发车、卡在哪。
- 北极星一致性：服务手机用户的固定路线垃圾投递闭环，优先提高路线可验证性与可诊断性。

## OKR 映射

- Objective 3（主）
  - KR2：导航输入输出 contract + 文档固化。
  - KR3：fixed-route dry-run proof 覆盖率与失败证据增强。
  - KR4：fixed-route 与 behavior/operator 参数和状态边界清晰。
- Objective 5（次）
  - diagnostics/operator 提供 route-proof 可读状态，降低人工排查成本。

## KR 拆解或更新

- KR-3A（nav）：新增 `route_proof_summary`（coverage、missing_checkpoints、gate_status、last_block_reason）。
- KR-3B（behavior）：operator/diagnostics 消费 `route_proof_summary`，展示“可发车/待补齐”状态与最近阻塞原因。
- KR-3C（guardrail）：完成 unittest、py_compile、smoke、scoped diff-check 的软件验证证据。

## 本轮核心抓手

- 抓手 1：限定切片只做 route proof coverage，不扩展到硬件或算法大改。
- 抓手 2：双 owner 并行，避免文件冲突，缩短交付时间。
- 抓手 3：接口先行，先定义 contract 再写展示，减少返工。

## 做什么 / 不做什么

做：

- 导航侧输出 route proof coverage 字段并补文档。
- behavior/operator 侧消费并展示 proof 字段，给出可操作状态提示。
- 通过最小护栏测试确保回归可控。

不做：

- 不做硬件实机/HIL。
- 不做跨模块大重构。
- 不做模型训练或视觉模型策略变更。

## 需求定义

1. 导航输出必须包含 route-proof 核心字段：
   - `coverage_rate`
   - `covered_checkpoints`
   - `total_checkpoints`
   - `missing_checkpoints`
   - `gate_status`
   - `last_block_reason`
2. behavior/operator 必须展示 route-proof 摘要，并给出可读诊断语义：
   - `ready`（可发车）
   - `waiting_visual_gate`（待视觉门控）
   - `insufficient_coverage`（覆盖不足）
   - `blocked`（其他阻塞）
3. 文档必须同步接口语义与字段来源。

## 优先级和验收口径

- P0：route-proof summary 在 nav 与 behavior 语义一致。
- P0：两位 owner 分别完成各自护栏验证并提交关键日志。
- P0：不越界改动；双方文件范围无重叠。
- P1：空数据、部分 coverage、缺 checkpoint 场景有明确降级信息。

## 对应责任 Engineer

- `autonomy-engineer`：导航 route-proof 产出与文档固化。
- `full-stack-software-engineer`：operator/diagnostics 消费与展示 contract。

## 风险、阻塞和证据链

- 风险：不同模块对 `coverage_rate` 计算口径不一致。
- 风险：历史状态文件字段缺失时，UI 误判为 `ready`。
- 阻塞：若 nav proof 字段不稳定，behavior 展示只能降级为 `unknown`。
- 证据链缺口：本轮只证明软件 contract，不证明真实运动学与实机可达性。

## Sprint 留档更新要求

实现完成后必须更新：

- `sprints/2026.05.10_23-24_route-proof-coverage/tech-done.md`
- `sprints/2026.05.10_23-24_route-proof-coverage/side2side_check.md`
- `sprints/2026.05.10_23-24_route-proof-coverage/final.md`

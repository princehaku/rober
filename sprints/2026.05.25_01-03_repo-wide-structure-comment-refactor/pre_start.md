# Repo-wide Structure and Comment Refactor Pre-start

sprint_type: epic

## CEO 输入

- 原始目标：`/goal 重构代码 结构化 目录化 注释`
- 方案选择：CEO 在三种方案中选择 `2`，即全仓扫描后分 2-4 个 owner 并行重构。

## 本轮目标

本轮目标是做一次全仓结构化治理：按 owner 边界拆分超大模块、补齐目录职责、保留兼容入口、增加中文“为什么”注释，并用现有测试和 Docker/Humble 构建守住行为兼容。

## Owner 与并行策略

- `robot-software-engineer`：ROS2 behavior 主链路和 action/bridge 兼容入口重构。
- `rober-hardware-engineer`：hardware 包目录化和 vendor-source 注释/文档对齐。
- `autonomy-engineer`：nav/vision 包路线、视觉 proof 与 helper 目录化。
- `full-stack-software-engineer`：operator gateway、diagnostics、cloud relay、mobile/web 触点结构化。

本轮是 4 owner 并行 Epic sprint。文件范围按包/模块拆开，禁止多个子 agent 改同一个文件；若某个 owner 发现必须跨边界改文件，需要先在输出中标记为 `NEEDS_CONTEXT` 或 `BLOCKED`，由主节点重新拆分。

## 前置状态

- 当前最低 OKR Objective：Objective 5（约 68%），见 `OKR.md` 4.1。
- 本轮重构本身不应提升任何 OKR 完成度，除非产生新的可验证外部证据；默认只作为工程质量和可维护性护栏。
- 当前 worktree 已存在 unrelated 删除：`docs/superpowers/plans/2026-05-08-codex-subagents.md`、`docs/superpowers/plans/2026-05-08-project-completion.md`、`docs/superpowers/specs/2026-05-08-project-completion-design.md`。本轮不得恢复、覆盖或混入这些删除。

## Blocker 扫描

最近两轮 sprint：

- `sprints/2026.05.24_23-24_cloud-external-evidence-review-handoff`
- `sprints/2026.05.25_00-01_cloud-external-evidence-review-handoff-followup-escalation-status`

只读扫描未发现本轮会重复消费的相同 blocker root cause。本轮不依赖真实硬件、4G、OSS/CDN live traffic 或 PR #5 review thread resolve。

## 风险边界

- 禁止为了目录化改变 ROS2 topic/action/service 契约。
- 禁止把 local-only software proof 写成真实手机、真实云、真实 HIL 或真实 delivery success。
- 硬件相关文件必须先读 `docs/vendor/VENDOR_INDEX.md` 和其指向资料；没有 vendor 或实测证据时，不能新增硬件事实结论。
- 所有新增/保留技术注释必须使用中文，并解释“为什么”。

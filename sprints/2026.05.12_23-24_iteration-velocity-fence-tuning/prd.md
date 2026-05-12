# Sprint 2026.05.12_23-24 Iteration Velocity Fence Tuning - PRD

## 状态

- 阶段：prd
- 时间：2026-05-12 23:50 Asia/Shanghai
- Product Owner：`product-okr-owner`

## 用户价值

把项目从"高频低产出微迭代"切换到"按 OKR 健康度引导的高密度并行迭代"。让每一轮 sprint 都能：
1. 显式回答"为什么本轮不是去做最低 Objective"。
2. 默认产生 2-4 个并行 owner 工作流，而不是 1 owner 单线串行。
3. 区分 Epic（六文档全套）与 Micro（仅 tech-done）两种 sprint 类型，让 30 分钟微切片不再被同样的文档负担拖累。
4. 同一 blocker 卡 ≥ 2 轮立刻强制切换，避免反复消费已知阻塞。

## 北极星对齐

本 sprint 不直接修改 OKR 内容，但通过流程改进让后续 sprint 更快推动以下 OKR 进展：
- **O5 手机体验与量产边界（30%）**：成为优先抓手，强制纳入并行 sprint。
- **O6 4G 云中转 + OSS/CDN（12%）**：成为优先抓手，强制纳入并行 sprint。
- **O1~O4（74~77%）**：限制纯 +1pp 软件微证据轮次，必须配套低 Objective 并行或硬件实测推动。

## 改动范围（CEO 已拍板）

| 文件 | 是否新建 | 改动内容摘要 |
| --- | --- | --- |
| `AGENTS.md` | 否 | 重写"并行启动强制规则"、"Sprint 留档原则"、"Tech Plan 自动执行规则"，新增"Epic / Micro Sprint 分层"、"OKR 最低优先级软提醒"、"同一 blocker 重复消费红线" 三个章节 |
| `.codex/agents/registry.toml` | 否 | 在 `[execution_policy]` 增加 `parallel_default = "2-4"`、`epic_micro_doc_policy`、`okr_lowest_objective_rule`、`repeated_blocker_cap` 字段；其他章节按需对齐 |
| `docs/process/iteration_velocity.md` | 是 | 总规则文档：Epic vs Micro 判定、并行强制矩阵、最低 Objective 软提醒、blocker 切换流程、违规处置 |
| `OKR.md` | 否 | 第 4.1 节末尾追加一段"本轮是否针对最低 Objective"软提醒规则，**不修改任何 Objective 完成度数字** |

## 不做事项

- 不修改 `OKR.md` 任一 Objective/KR 的完成度数字、定义或证据快照。
- 不修改 `OKR.md` 4.1 节以外的章节。
- 不修改任何 ROS2 产品代码、测试代码、launch 参数、硬件配置、vendor 文件。
- 不修改任何已收口 sprint 的留档文件。
- 不修改其他 IC role 的 `.codex/agents/*.toml`（只动 `registry.toml` 的 execution policy 段）。
- 不"追溯"过去的 sprint 是否符合新规则；新规则只对未来 sprint 生效。

## 验收口径

1. `AGENTS.md` 增加章节后通过 scoped `git diff --check` 且无破坏既有引用。
2. `.codex/agents/registry.toml` 新增字段后能被 TOML 解析（`python3 -c "import tomllib; tomllib.load(open('.codex/agents/registry.toml','rb'))"` 或等效 `tomli` 路径）。
3. `docs/process/iteration_velocity.md` 新建并被 `AGENTS.md`、`registry.toml` 双向引用。
4. `OKR.md` 4.1 节新增段落与既有 18 个进度快照表保持不冲突。
5. 全套 markdown 通过 scoped `git diff --check`。
6. final.md 明确：本轮不抬 OKR 完成度、不声明硬件证据；本 sprint 自身按 Epic 类型走六文档全套。

## 责任 Engineer

实质改动由 `product-okr-owner` 子 agent 单线闭环执行；本轮没有 IC engineer 任务（流程文件没有 IC 范围）。

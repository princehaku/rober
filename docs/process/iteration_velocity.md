# Iteration Velocity Fence — Epic/Micro 分层、并行规则、OKR 软提醒与 Blocker 红线

本文件是 `ros_rbs` 迭代节奏与并行研发的总规则，对应 `AGENTS.md` 中的"并行启动强制规则 / Epic / Micro Sprint 分层 / OKR 最低优先级软提醒 / 同一 Blocker 重复消费红线 / Tech Plan 自动执行规则 / Sprint 留档原则"，以及 `.codex/agents/registry.toml` `[execution_policy]` 中的 `parallel_default / parallel_solo_exemptions / epic_micro_doc_policy / okr_lowest_objective_rule / repeated_blocker_cap / process_doc_reference` 字段。

引入时间：2026-05-12。生效范围：本文首次落地之后启动的所有 sprint；既有 sprint 不追溯。

## 1. 背景

> 引用 `sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/pre_start.md` 的诊断证据。

主节点在引入本文前对 `OKR.md`、`AGENTS.md`、`.codex/agents/registry.toml` 和近 60 个 sprint 留档做了只读复盘，得出以下结论：

1. **迭代节奏过快但单轮产出过小**：05-10 当天产出 17 个 sprint，05-11 产出 13 个，05-12 已经 4 个，绝大多数 30-60 分钟。OKR 近 10 个进度快照大量写"无新增，仅护栏"或"+1pp"。
2. **真实硬件实测几乎没碰**：连续多轮 Docker preflight 卡在同一 `registry mirror/proxy returns text/html` 根因；HIL 系列在 `/tmp` synthetic fixture 上反复验证 bridge 逻辑，没有真实串口 / WAVE ROVER 证据。
3. **OKR 完成度严重不均**：O1=75%、O2=74%、O3=76%、O4=75%、O5=30%、O6=12%。近 20 轮针对最低 O5/O6 的不到 1/4。
4. **并行规则名存实亡**：除 `2026.05.12_02-03_remote-4g-command-loop` 外，绝大多数 sprint 1 owner 单线，未发挥并行潜力。
5. **六文档契约对微切片过重**：30 分钟 sprint 写 6 个 markdown 让"留档时间 ≥ 实现时间"。
6. **主节点 dispatch 成本**：5-50 行单文件改动也走完整 dispatch SOP，沟通成本明显高于实际编码成本。

因此本文用四把硬尺子收紧迭代纪律：默认并行、Epic/Micro 分层、最低 Objective 软提醒、Blocker 重复消费红线。

## 2. Epic / Micro Sprint 判定矩阵

每个 sprint 必须在 `pre_start.md` 第一节（或 Micro sprint 的 `tech-done.md` 第一节）显式标注：

```
sprint_type: epic
```

或

```
sprint_type: micro
```

判定矩阵：

| 维度 | Epic Sprint | Micro Sprint |
| --- | --- | --- |
| Owner 数 | 2+ 个 | 1 个 |
| 预计耗时 | ≥ 2 小时 | < 1 小时 |
| 预计 OKR 推进 | ≥ +3pp 或新增一个完整能力模块 | 无 OKR 推进 / 仅护栏 / 单点缺陷修复 |
| 接口/契约变化 | 是 | 否 |
| 需要 PRD 对齐用户价值 | 是 | 否 |
| 验收链路 | 需要 side2side + final | 仅 tech-done |
| 文档要求 | 完整六文档 | 仅 `tech-done.md` |

任一 Epic 维度命中（owner / 时长 / OKR 推进 / 接口变化）即视为 Epic。**只有同时满足"单 owner + < 1 小时 + 单点改动 + 无接口变化"四条**才允许标 Micro。

### 2.1 升级与降级

- **误判 Micro 为 Epic**：不算违规。多写的文档保留即可。
- **误判 Epic 为 Micro**：违规。事后一旦发现需要 PRD 对齐或 tech-plan 设计，必须立即升级为 Epic 并补齐 `pre_start.md / prd.md / tech-plan.md / side2side_check.md / final.md` 五个文档，**不得把 `tech-done.md` 扩成事实上的全套文档**。
- 升级触发条件示例：接口契约变化、跨 owner、需要 CEO 验收、需要 OKR 完成度调整、需要硬件二次确认。

### 2.2 Micro Sprint 的 `tech-done.md` 最小三段

Micro sprint 只省去其他五个文档，**不省略 tech-done.md 的三段内容**：

1. **实际改动**：列出改的文件路径和关键 diff 摘要。
2. **验证结果**：至少一条可机器执行的验证命令及其输出（构建、测试、smoke、`git diff --check` 任一适用）。
3. **剩余风险**：未完成事项、遗留 TODO、证据边界。

Micro sprint 完成后，如果事后发现需要复盘、side2side 验收对齐或 final 收口，必须立即升级为 Epic 并补齐缺失文档。

## 3. 并行强制规则

### 3.1 默认 2-4 并行

- **默认每个 sprint 启动 2-4 个并行子 agent**。tech-plan 有清晰文件范围且任务互不重叠时，主节点必须在同一条消息里并行发起 2-4 个 `Task` / `spawn_agent` 调用。
- 主节点严禁直接写产品代码、测试代码或硬件配置；本规则覆盖 Epic 和 Micro 两种 sprint。

### 3.2 并行三豁免（允许 1 owner 单线）

只有以下三种情况之一成立时，sprint 才允许标"1 owner 单线"：

1. **硬件 blocker 锁死**：当前没有可并行的软件工作，所有可推进 Objective 都被同一硬件 blocker 锁定。`pre_start.md` 必须写明哪个 blocker 锁死了哪些 Objective。
2. **严格单文件单 owner**：任务严格只动一个文件、只属于一个 owner，且与其他在跑 sprint 完全无接口耦合。`tech-plan.md`（或 Micro 的 `tech-done.md`）必须列出该文件路径并声明无耦合。
3. **CEO 明确要求 read-only 或单线**：必须在 `pre_start.md`（或 Micro `tech-done.md`）引用 CEO 原话。

不符合任一豁免却采用 1 owner 单线视为违规。

### 3.3 接口耦合任务的并行方式

2+ owner 但接口耦合、共享文件或验收链路强相关时：

- 指定 1 个主责 owner 负责实现和集成（默认 `robot-software-engineer`）。
- 其他 owner 以**并行**只读咨询或事实补充方式介入，**不得串行等待主责 owner 收口**。
- 咨询/事实补充任务也必须用 `Task` / `spawn_agent` 派发，prompt 注入对应 role TOML。

### 3.4 违规处置

- 降级为 1 个子 agent 完成 2+ owner sprint：违规。`final.md` 必须解释为何降级（运行时缺少子 agent 工具、全员同步阻塞等），并在下一轮 `pre_start.md` 写明纠正策略。
- 主节点亲自下场写代码：严重违规，立即停止并改派子 agent；既有改动需要列入下一轮 sprint 复核。

## 4. OKR 最低优先级软提醒

### 4.1 软提醒规则

每轮 **Epic** sprint 的 `tech-plan.md` 必须包含一节 `## OKR 最低优先级核对`，写明：

1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective（按数字排序，含并列时一起列出）；
2. 本 sprint 是否针对该最低 Objective；
3. 如不针对，必须给出具体理由。

合法理由示例：

- 最低 Objective 当前无可推进的软件工作（如依赖前置硬件 blocker 未解，且 blocker 已升级 CEO）；
- 依赖前置硬件 / 凭证 / 网络 blocker 未解；
- CEO 明确指定其他优先级；
- 并行 sprint 已覆盖最低 Objective；
- 当前最低 Objective 在最近 2 轮 sprint 已被覆盖，本轮轮换到次低 Objective 平衡进度。

### 4.2 软提醒 vs 硬规则

- 这是**软提醒**，不阻塞实现：tech-plan 没写"OKR 最低优先级核对"段是流程违规，但不阻断子 agent 派发。
- `final.md` 收口时必须回顾：本轮选定的理由在本轮结束时是否仍然成立？如果发现理由失效（如硬件 blocker 已经在并行 sprint 中解决），下一轮 pre_start.md 必须把最低 Objective 列为优先抓手。

### 4.3 Micro Sprint 不强制

Micro sprint 因为只产出一个 `tech-done.md`，不强制写"OKR 最低优先级核对"段，但鼓励在 `tech-done.md` 末尾用一句话说明本轮属于护栏 / 单点修复 / 临时支持，并指出对最低 Objective 的影响（如有）。

### 4.4 段落模板

Epic sprint 的 tech-plan.md 推荐使用以下模板：

```markdown
## OKR 最低优先级核对

- 当前 OKR.md 4.1 节完成度最低的 Objective：{Objective X (Y%)}
- 本 sprint 是否针对该 Objective：{是 | 否}
- 如不针对，理由：{从上述合法理由列表挑选一条或多条，并写出具体上下文}
- final.md 收口时需复核：理由是否仍然成立？是否在并行 sprint 中已被覆盖？
```

## 5. Blocker 重复消费红线

### 5.1 定义

- **Blocker 根因**：导致 sprint 主结论为"blocked"的具体根因，例如 `docker_registry_mirror_returns_text_html`、`no_serial_device_available`、`cdn_unreachable`、`no_oss_credentials`、`no_real_wave_rover`。
- **消费一轮**：某 sprint 的 `final.md` 主要结论是 blocked 在该根因。

### 5.2 计数与切换

- 同一根因 blocker **最多消费 2 轮 sprint**。
- 从第 3 轮起，必须二选一：
  1. **切换 Objective**：本轮放弃该 blocker，转去做不依赖该 blocker 的低完成度 Objective。`pre_start.md` 必须写明切换原因、切换前的 blocker、切换后的目标 Objective 和验证命令。
  2. **升级 CEO 求决策**：在 `pre_start.md` 新增"升级原因"段，明确告知 CEO 该 blocker 已连续 2 轮无法解决，请求方向决策（提供硬件、更换策略、暂停该 KR 等）。CEO 决策记录必须以原话引用方式写入 `pre_start.md`。
- 例外：CEO 在升级后明确"继续攻坚同一 blocker"，则计数重置但需要在 `pre_start.md` 引用 CEO 原话作为依据。

### 5.3 主节点扫描义务

- 主节点在派发新 sprint 前**必须扫描最近 2 轮 sprint final.md 的 blocker 字段**，避免无意识重复消费。
- 扫描方式：使用 `Grep` 检索 `sprints/<最近 2 轮>/final.md` 的 `blocker` 或 `main conclusion` 字段；如根因相同则触发本节切换 / 升级流程。

### 5.4 同一 blocker 跨 sprint 关联标识

- 推荐每个 blocker 在 `final.md` 用一致的 `blocker_root_cause: <slug>` 字段标识，便于后续 grep 计数。例如：
  ```
  blocker_root_cause: docker_registry_mirror_text_html
  ```

## 6. 与既有规则的关系

本文是 `AGENTS.md` 与 `.codex/agents/registry.toml` 的**总规则补充**，**不取代**任何既有规则：

- **AGENTS.md 红线（含"全员红线"和"硬件红线"）继续有效**：必须先读 AGENTS.md、硬件相关查 `docs/vendor/VENDOR_INDEX.md`、给验证证据、失败定位修复、按迭代推进。
- **子 Agent 启动 SOP 与 Role → Runtime 映射继续有效**：主节点依然只负责读文件、拆任务、派子 agent、验收、留档；编码 / 测试 / 修复一律由子 agent 完成。
- **Sprint 留档原则继续有效**，本文仅增加 Epic / Micro 分层：Epic 走完整六文档，Micro 仅 tech-done.md。
- **`.codex/agents/registry.toml` `[execution_policy]` 字段是机器可读契约**，本文是人类可读说明；两者矛盾时以本文 + AGENTS.md 表述为准，但务必同步修订 registry.toml。
- **OKR.md 是产品方向与完成度的唯一权威**；本文的"最低 Objective 软提醒"是流程引导，不修改任何 Objective / KR / 完成度数字。

### 6.1 引用一致性

修改本文规则时必须同步更新：

- `AGENTS.md`：并行启动强制规则、Epic / Micro Sprint 分层、OKR 最低优先级软提醒、同一 Blocker 重复消费红线、Tech Plan 自动执行规则、Sprint 留档原则共六个小节。
- `.codex/agents/registry.toml`：`[execution_policy]` 表里 `tech_plan_execution_rule`、`parallel_default`、`parallel_solo_exemptions`、`epic_micro_doc_policy`、`okr_lowest_objective_rule`、`repeated_blocker_cap`、`process_doc_reference` 七个字段。
- `OKR.md` 4.1 节末尾追加的"最低 Objective 软提醒规则"短段（只引用本文，不引入完成度数字、不修改既有快照）。

### 6.2 自指风险与首个示范用例

本文规则的引入本身就是一个 Epic sprint：`sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/`。该 sprint 走完整六文档，作为新分层规则的首个示范用例。新规则只覆盖未来 sprint，**不追溯过往 sprint**。

# Sprint 2026.05.12_23-24 Iteration Velocity Fence Tuning - Tech Plan

## 状态

- 阶段：tech-plan
- 时间：2026-05-12 23:52 Asia/Shanghai
- Product Owner：`product-okr-owner`
- Engineering Owner：`product-okr-owner`（本轮唯一 owner，单线闭环）
- Sprint 类型：Epic（六文档全套，是新分层规则的首个示范用例）

## 临时授权

`product-okr-owner` 默认 `owner_paths` 是 `OKR.md`、`sprints/`、`docs/product/`。本 sprint 明确临时授权 `product-okr-owner` 改动以下文件：

| 路径 | 是否新建 | 授权理由 |
| --- | --- | --- |
| `AGENTS.md` | 否 | agent 工作纪律/治理规则，属于产品负责人元层职责 |
| `.codex/agents/registry.toml` | 否 | agent 注册表与执行策略，与 `AGENTS.md` 一一对应 |
| `docs/process/iteration_velocity.md` | 是 | Epic/Micro 分层、并行规则、OKR 优先级软提醒、blocker 切换总规则 |
| `OKR.md`（仅 4.1 节末尾追加一段） | 否 | 软提醒规则，**不修改任何 Objective 完成度数字** |
| `sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/tech-done.md` | 是 | 本 sprint 必交付的实现留档 |

授权边界：除上述 5 个路径外，子 agent 不得改动任何其他文件。

## 具体改动设计

### 1. `AGENTS.md` 改动清单

**A. 重写"并行启动强制规则"章节（位于"#### 子 Agent Prompt 固定结构" 之后、"### 组织层级" 之前）：**

新版要点：
- 默认每个 sprint 启动 **2-4** 个并行子 agent；1 owner 单线 sprint 仅在以下三种情况合法：
  1. 硬件 blocker 锁死，无可并行的软件工作；
  2. 任务严格单文件、单 owner、与其他在跑 sprint 完全无接口耦合；
  3. CEO 明确要求 read-only 或单线。
- 当 sprint 含 2+ 互不重叠 owner task 时，主节点必须在同一条消息里并行派发，不得序列化等待。
- 只派 1 个子 agent 完成有 2+ owner 的 sprint 视为流程违规，sprint final.md 必须解释为何降级。

**B. 重写"Sprint 留档原则"章节，引入 Epic/Micro 分层：**

- **Epic Sprint**：跨 owner、预计 ≥ 2 小时、预计推动 OKR ≥ +3pp 或新增一个完整能力模块。必须走完整六文档：`pre_start.md → prd.md → tech-plan.md → tech-done.md → side2side_check.md → final.md`。
- **Micro Sprint**：单 owner、< 1 小时、单一改动（如修一个 bug、加一个测试、补一个文档段落）。必须创建 sprint 目录，但**只需 `tech-done.md`**，不必产出其他五个文档。
- **判定时机**：pre_start.md 必须显式标注 `sprint_type: epic` 或 `sprint_type: micro`。误判 micro 为 epic 不算违规；误判 epic 为 micro（事后发现需要 PRD/tech-plan）必须立即升级为 epic 并补齐缺失文档。
- 既有 sprint 不追溯。

**C. 新增"OKR 最低优先级软提醒"章节：**

- 每轮 Epic sprint 的 `tech-plan.md` 必须包含一节 `## OKR 最低优先级核对`，写明：
  1. 当前 `OKR.md` 4.1 节里完成度最低的 Objective（按数字排序）；
  2. 本 sprint 是否针对该最低 Objective；
  3. 如不针对，必须给出具体理由（如：最低 Objective 当前无可推进工作、依赖前置硬件 blocker、CEO 明确指定其他优先级、并行 sprint 已覆盖最低 Objective）。
- Micro sprint 不强制此节。
- 这是软提醒，不阻塞实现；但 final.md 收口时需要回顾该理由是否成立。

**D. 新增"同一 Blocker 重复消费红线"章节：**

- 同一根因 blocker（如 Docker registry mirror、缺真实串口设备、CDN 不可达）**最多消费 2 轮 sprint**；
- 第 3 轮起，必须切换到不依赖该 blocker 的 Objective，或显式升级到 CEO 求决策（写入 sprint pre_start.md "升级原因"段）；
- "消费"定义：该 sprint 的 `final.md` 主要结论是 blocked 在同一根因。
- 例外：CEO 在升级后明确"继续攻坚同一 blocker"。

**E. 微调"Tech Plan 自动执行规则"以承接上述新规：**

- 删除"1 owner 任务由主责 Engineer 子 agent 直接实现"的优先描述，改为"1 owner 任务仅在符合并行豁免三条件之一时合法"。
- 增加引用：`docs/process/iteration_velocity.md` 是总规则。

### 2. `.codex/agents/registry.toml` 改动清单

在 `[execution_policy]` 表内增加：

```toml
parallel_default = "2-4 sub agents per sprint when 2+ non-overlapping owners exist"
parallel_solo_exemptions = [
  "hardware blocker locks all parallel software work",
  "single-file, single-owner, no interface coupling with other in-flight sprints",
  "CEO explicitly requests read-only or solo lane",
]
epic_micro_doc_policy = "Epic sprint: full six docs. Micro sprint: tech-done.md only. Sprint type declared in pre_start.md as sprint_type=epic|micro."
okr_lowest_objective_rule = "Each Epic sprint tech-plan.md must include section 'OKR 最低优先级核对' justifying whether current sprint targets the lowest-completeness Objective in OKR.md section 4.1, and if not, why."
repeated_blocker_cap = "Same root-cause blocker may consume at most 2 sprints. From sprint 3 onward, switch Objective or escalate to CEO."
process_doc_reference = "docs/process/iteration_velocity.md"
```

不修改 `[mission]`、`[org_hierarchy]`、`[core_team]`、`[routing]`、`[red_lines]`、`[[roles]]` 等其他表（避免连锁影响）。

### 3. `docs/process/iteration_velocity.md`（新建）

必含章节：

1. **背景**：为什么引入这套规则（指向本 sprint pre_start.md 的诊断证据）。
2. **Epic / Micro Sprint 判定矩阵**：用表格列出判定维度（owner 数、预计时长、预计 OKR 推进、是否新增能力模块）。
3. **并行强制规则**：默认 2-4 并行，单线豁免三条件，违规处置。
4. **OKR 最低优先级软提醒**：tech-plan 必含的"OKR 最低优先级核对"段模板。
5. **Blocker 重复消费红线**：定义、计数、切换/升级流程。
6. **与既有规则的关系**：明确本文是 `AGENTS.md`/`registry.toml` 的总规则补充，不取代既有 AGENTS.md 红线、SOP 和六文档契约。

### 4. `OKR.md` 4.1 节末尾追加段落

在第 4.1 节末（"补充：`2026.05.11_21-22_..."` 之后，| Objective 表之前；或在 1.0 节 4.1 已有表后追加一段），追加（不修改既有表/快照）：

```text
**最低 Objective 软提醒规则（2026-05-12 引入）**：每轮 Epic sprint 的 tech-plan.md 必须在"OKR 最低优先级核对"段说明本轮是否针对当前完成度最低的 Objective，如不针对必须给出具体理由。详细判定见 `docs/process/iteration_velocity.md`。
```

实际段落措辞由 `product-okr-owner` 微调，但必须满足：
- 不引入任何完成度数字；
- 不修改既有快照表；
- 与 `AGENTS.md`、`docs/process/iteration_velocity.md` 表述一致。

## 接口影响

- 不变更 ROS2 topic/action/service。
- 不变更硬件协议、串口参数、launch 参数或 vendor 事实。
- 不变更 `OKR.md` 任一 Objective/KR 完成度。
- 不变更 IC role 的 `.codex/agents/*.toml`。

## 验收命令

实现完成后子 agent 必须运行：

```bash
git diff --check -- AGENTS.md .codex/agents/registry.toml docs/process/iteration_velocity.md OKR.md sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/tech-done.md
```

预期：exit 0，无 trailing whitespace 错误。

```bash
python3 -c "import sys; \
try:\n    import tomllib\nexcept ImportError:\n    import tomli as tomllib\nwith open('.codex/agents/registry.toml','rb') as f:\n    tomllib.load(f)\nprint('toml OK')"
```

预期：输出 `toml OK`，exit 0。**或者** 等效 bash 单行 fallback：

```bash
python3 - <<'PY'
try:
    import tomllib
except ImportError:
    import tomli as tomllib
with open('.codex/agents/registry.toml','rb') as f:
    tomllib.load(f)
print('toml OK')
PY
```

```bash
test -f docs/process/iteration_velocity.md && echo "process doc exists"
```

预期：输出 `process doc exists`。

```bash
grep -c "sprint_type" AGENTS.md
grep -c "iteration_velocity" .codex/agents/registry.toml
grep -c "iteration_velocity.md" AGENTS.md
```

预期：每个 grep 至少 1 次匹配。

## 风险边界

- 本轮只动 4 个授权文件 + 1 个 sprint tech-done.md，超出范围视为违规。
- 不得借机修改任何 ROS2 产品代码、测试代码、launch、vendor、硬件配置。
- 不得修改 `OKR.md` 既有快照或完成度。
- 不得修改其他 IC role TOML。
- 不"追溯"既有 sprint 是否符合新规则；旧 sprint 留档保持现状。
- 本轮证据边界：纯流程文档改动，不声明任何 OKR 提升、不声明硬件证据、不声明 HIL。

## 子 Agent 启动指令

派发 1 个 `product-okr-owner` 子 agent 单线执行本轮全部 4 处改动。Prompt 必须包含：
1. 角色 System Prompt（从 `.codex/agents/product-okr-owner.toml` 的 `prompt` 字段完整复制）；
2. 本轮任务（本 tech-plan 摘要）；
3. 文件范围（上述 5 个授权路径，明确禁止其他文件）；
4. 验收命令（本节"验收命令"四条全部）；
5. 输出要求（实际改动文件列表、验收命令输出、失败定位、剩余风险）。

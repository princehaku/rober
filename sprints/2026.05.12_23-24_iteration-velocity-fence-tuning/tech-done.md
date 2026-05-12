# Sprint 2026.05.12_23-24 Iteration Velocity Fence Tuning - Tech Done

## 状态

- 阶段：tech-done
- 时间：2026-05-12 23:54 Asia/Shanghai
- Sprint 类型：`sprint_type: epic`（本 sprint 是 Epic / Micro 分层规则的首个示范用例，按 Epic 走完整六文档）
- 主责 Owner：`product-okr-owner`（单线闭环，符合"并行启动强制规则"的豁免条件 3——CEO 明确要求由 product-okr-owner 主导这次治理变更，且任务范围严格限定在 5 个流程/治理文件，与其他在跑 sprint 无接口耦合）
- 证据边界：**process_doc_only**。不声明任何 OKR 完成度提升、不声明硬件证据、不声明 HIL、不声明 ROS2 主链路改动。

## 实际改动

### 1. `AGENTS.md`（修改）

- **重写"并行启动强制规则"**：新增"默认 2-4 并行"、引入三条并行豁免（硬件 blocker 锁死 / 严格单文件单 owner / CEO 明确要求 read-only 或单线），并把"降级为 1 个子 agent 完成 2+ owner sprint"明确为流程违规。开头新增对 `docs/process/iteration_velocity.md` 的总规则引用。
- **新增"Epic / Micro Sprint 分层"小节**：明确 `pre_start.md` 必须写 `sprint_type: epic|micro`；Epic 走完整六文档，Micro 只需 `tech-done.md`；误判 epic 为 micro 必须升级补齐；既有 sprint 不追溯。
- **新增"OKR 最低优先级软提醒"小节**：Epic sprint 的 `tech-plan.md` 必须包含 `## OKR 最低优先级核对` 段；软提醒、不阻塞实现；Micro 不强制。
- **新增"同一 Blocker 重复消费红线"小节**：同一根因 blocker 最多消费 2 轮，第 3 轮起必须切换 Objective 或升级 CEO；主节点派发新 sprint 前必须扫描最近 2 轮 final.md 的 blocker 字段。
- **微调"Tech Plan 自动执行规则"**：1 owner 任务必须符合并行豁免三条件之一才合法；2+ owner 必须按 `parallel_default` 并行（2-4 个）；Epic sprint 的 tech-plan 缺"OKR 最低优先级核对"段视为计划未完成；段首新增对 `docs/process/iteration_velocity.md` 的引用。
- **微调"Sprint 留档原则"**：把六文档顺序拆分为 Epic 全套 / Micro 仅 `tech-done.md` 两层，并在每个文档项里点明 `sprint_type` 声明位置；说明 Micro sprint 若事后需要复盘/验收对齐必须升级 Epic。

### 2. `.codex/agents/registry.toml`（修改）

`[execution_policy]` 表新增 6 个字段：

- `parallel_default`：默认 2-4 个并行子 agent，主节点单条消息内派发，禁止串行。
- `parallel_solo_exemptions`：1 owner 单线三条豁免（硬件 blocker、严格单文件、CEO 明确要求）。
- `epic_micro_doc_policy`：Epic 走六文档 / Micro 仅 tech-done.md；分类必须显式声明；误判 epic 为 micro 必须升级补齐。
- `okr_lowest_objective_rule`：Epic tech-plan 必须包含 OKR 最低优先级核对段；软提醒、不阻塞但需 final 复核。
- `repeated_blocker_cap`：同一根因 blocker 最多消费 2 轮，第 3 轮起切换 Objective 或升级 CEO。
- `process_doc_reference`：指向 `docs/process/iteration_velocity.md`。

同时微调既有 `tech_plan_execution_rule` 字段措辞，承接新的 `parallel_solo_exemptions` / `parallel_default` 语义，并引用 `process_doc_reference`。其他表（`[mission]`、`[org_hierarchy]`、`[core_team]`、`[routing]`、`[red_lines]`、`[[roles]]` 等）未动。

### 3. `docs/process/iteration_velocity.md`（新建）

总规则文档，按 tech-plan.md 设计包含六节：

1. **背景**：引用 `pre_start.md` 的诊断证据（高频低产出微迭代、硬件实测几乎没碰、OKR 完成度严重不均、并行规则名存实亡、六文档对微切片过重、主节点 dispatch 成本）。
2. **Epic / Micro Sprint 判定矩阵**：表格列出 owner 数、预计耗时、预计 OKR 推进、接口/契约变化、PRD 必要性、验收链路、文档要求；明确"任一 Epic 维度命中即视为 Epic，只有同时满足四条 Micro 条件才允许标 Micro"；含升级降级、Micro `tech-done.md` 三段（实际改动 / 验证结果 / 剩余风险）。
3. **并行强制规则**：默认 2-4 并行、三条豁免详写、接口耦合任务的并行咨询方式、违规处置。
4. **OKR 最低优先级软提醒**：软提醒规则、合法理由示例、软/硬区别、Micro 不强制、段落模板。
5. **Blocker 重复消费红线**：根因定义、计数与切换、CEO 升级条件、主节点扫描义务、`blocker_root_cause` 一致 slug 推荐。
6. **与既有规则的关系**：本文是补充不是取代；引用一致性清单（AGENTS.md / registry.toml / OKR.md 4.1 三处同步修订点）；自指风险说明（本 sprint 本身是首个示范用例，按 Epic 走全套六文档）。

### 4. `OKR.md`（修改 4.1 节末尾追加 1 段）

在 4.1 节 Objective 6 表格行之后、`## 5. 2026 H2 前瞻路线` 之前追加一段"最低 Objective 软提醒规则（2026-05-12 引入）"。

- **未修改任何 Objective / KR / 完成度数字**。
- **未修改任何既有快照表**（O1=75%、O2=74%、O3=76%、O4=75%、O5=30%、O6=12% 等数字均保持原样）。
- 仅在 4.1 节末尾追加 2 行（1 段正文 + 1 空行）。`git diff --stat -- OKR.md` 输出 `1 file changed, 2 insertions(+)`，无删除。
- 段落内容引用 `docs/process/iteration_velocity.md` 作为详细判定矩阵入口，与 AGENTS.md / registry.toml 表述一致。

### 5. `sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/tech-done.md`（新建）

即本文件。

## 验证结果

### 5.1 `git diff --check` on scoped files

```bash
git diff --check -- AGENTS.md .codex/agents/registry.toml docs/process/iteration_velocity.md OKR.md sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/tech-done.md
```

输出：

```
warning: in the working copy of '.codex/agents/registry.toml', LF will be replaced by CRLF the next time Git touches it
```

exit code 0。仅一条 Windows LF/CRLF 警告，非 trailing whitespace 错误；`git diff --check` 报错的是行尾空白 / 混合空白，本输出未出现 `: trailing whitespace.` 或 `: indent with non-tab.` 字样，**视为通过**。

### 5.2 TOML 解析

```bash
python3 -c "import tomllib; tomllib.load(open('.codex/agents/registry.toml','rb')); print('toml OK')"
```

输出：

```
toml OK
```

exit code 0。`registry.toml` 新增的 6 个字段（含 list / 多行字符串）均可被 Python 3.13 tomllib 解析。

### 5.3 process doc 存在性

```bash
# bash 等效：test -f docs/process/iteration_velocity.md && echo "process doc exists"
# PowerShell 实跑：
if (Test-Path docs/process/iteration_velocity.md) { Write-Output "process doc exists" }
```

输出：

```
process doc exists
```

### 5.4 grep 必备字符串

```bash
grep -c "sprint_type" AGENTS.md           # 期望 ≥ 1，实测 3
grep -c "iteration_velocity" .codex/agents/registry.toml   # 期望 ≥ 1，实测 1
grep -c "iteration_velocity.md" AGENTS.md # 期望 ≥ 1，实测 5
```

输出：

```
--- sprint_type in AGENTS.md ---
3
--- iteration_velocity in registry.toml ---
1
--- iteration_velocity.md in AGENTS.md ---
5
```

三项全部 ≥ 1，满足预期。

### 5.5 自检：未误改授权范围外文件

```bash
git status --short
```

输出：

```
 M .codex/agents/registry.toml
 M AGENTS.md
 M OKR.md
?? docs/process/
?? sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/
```

三项 `M` + 两项 `??` 全部落在授权 5 个路径范围内：

- `M AGENTS.md` ✅
- `M .codex/agents/registry.toml` ✅
- `M OKR.md` ✅
- `?? docs/process/`（含新建 `docs/process/iteration_velocity.md`）✅
- `?? sprints/2026.05.12_23-24_iteration-velocity-fence-tuning/`（含本 tech-done.md 以及之前由主节点写好的 pre_start / prd / tech-plan）✅

未出现授权范围外任何 ROS2 包、vendor、IC role TOML 或其他 sprint 目录的改动。

### 5.6 OKR 改动范围核对

```bash
git diff --stat -- OKR.md
```

输出：

```
 OKR.md | 2 ++
 1 file changed, 2 insertions(+)
```

仅 4.1 节末尾追加 2 行（1 段正文 + 1 空行），**未修改任何既有 Objective / KR / 完成度数字 / 既有快照表**。`git diff -- OKR.md` 逻辑上只 hit 4.1 节末尾 `## 5. 2026 H2 前瞻路线` 之前的位置，符合 tech-plan.md 的"仅在 4.1 节末尾追加一段"要求。

## 剩余风险

1. **自指风险（已显式声明）**：本 sprint 修改的是规则本身，是新规则的首个示范用例。规则文本在本 sprint 内通过文字一致性自查，但未经其他 sprint 实战压测；首个按本文规则跑的下一个 sprint 是真正的"线上验证"，预期可能暴露：
   - `parallel_default` 2-4 在某些 read-only sprint 实际过头；
   - Epic / Micro 判定矩阵在边界情况下争议（例如"修一个 bug 但接口契约动了一行"应当归 Epic 还是 Micro）；
   - "OKR 最低优先级核对"段在并行 sprint 已覆盖最低 Objective 时是否会变成形式主义。
   缓解：本文 6.2 节已说明"新规则只覆盖未来 sprint，不追溯过往"；建议下一轮真正应用规则的 Epic sprint 在 `final.md` 提交规则压测反馈。
2. **未追溯过往 sprint**：既有 60+ sprint 留档没有被改写，部分 sprint 没有 `sprint_type` 字段，且 final.md 的 blocker 标识不统一。`blocker_root_cause` slug 是本文新引入的推荐做法，主节点的"扫描最近 2 轮 final.md"在未补 slug 前需要靠语义判断，存在误判风险。缓解：未来 sprint 严格用 `blocker_root_cause: <slug>` 字段，逐步形成机器可读历史。
3. **OKR.md 完成度仍未更新**：本轮明确不抬任何 Objective 完成度。如果未来 sprint 按新规则确实提速并解锁硬件证据，需要在那一轮 sprint 单独评估 OKR 调整，与本轮无关。
4. **PowerShell / bash 验证差异**：`docs/process/iteration_velocity.md` 与 tech-plan.md 的 `验收命令` 节都按 bash 语法写（`test -f && echo`、`python3 - <<'PY'`），在 Mac Docker / Linux CI 上能直接跑，在 Windows PowerShell 上需要等效改写（已在 5.3 节给出 Test-Path fallback）。这是流程文档执行环境的口径差异，不影响规则有效性。
5. **运行时缺少子 agent 时的规则失效场景**：本文 3.4 节说"主节点亲自下场写代码是严重违规"，但当前运行时若没有子 agent 工具，主节点目前只能 fallback 到 read-only/planning。本轮按 tech-plan.md 指定"product-okr-owner 单线"执行属于豁免条件 3，是合规的 1 owner 单线，但这本身也提示"主节点写代码 vs 子 agent 写代码"的边界在某些运行时退化时需要再次校准。

## 不声明事项（证据边界自查）

本 sprint 是流程治理变更，**不包含**以下任何证据：

- 不声明任何 Objective（O1-O6）完成度上升或下降；
- 不声明 HIL（hardware-in-the-loop）通过；
- 不声明真实 WAVE ROVER / UART / 串口 / 反馈 / IMU / 电池数据；
- 不声明 ROS2 主链路改动；
- 不声明 Nav2 / SLAM / 视觉 / fixed-route 实跑；
- 不声明手机端 UI 真实浏览器或普通用户实测；
- 不声明云端 4G / OSS / CDN 真实部署。

证据边界标记：`process_doc_only`。

## 是否仍为流程文档改动证据

是。本轮改动只触及 5 个流程/治理文件，未触及任何产品代码、测试代码、launch 参数、vendor 文件或硬件配置。

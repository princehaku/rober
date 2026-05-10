# Sprint 2026.05.10 13-14 - tech-done

## 状态

- 阶段：已完成配置修复集成
- 本文档记录真实已完成事项；不把本轮流程修复冒充为业务代码或硬件验证。

## 已完成：只读排查证据

本轮已并行启动 3 个只读 explorer 子agent，排查为什么近期写代码没有充分使用子agent。已知结论：

- `AGENTS.md` 绑定 Cursor Task / `generalPurpose`，与 Codex `spawn_agent(worker)` 的实际调度模型不完全适配。
- 主节点职责要求“任务拆解、子 agent 启动、集成验收、sprint 文档更新”，但同时禁止主节点改文件/跑测试，和当前 Codex 实际执行职责存在冲突。
- `registry.toml` 缺少 `enabled`、`capabilities`、关键调度字段，导致角色发现、启用和能力路由不够明确。
- 近期 sprint 多是单 owner 闭环，没有在互不重叠文件范围下持续并行派发。
- `2026.05.10_12-13` 已 final，本轮应新开 `2026.05.10_13-14`。

## 已完成：Sprint 留档改动

本轮留档 worker 创建并维护以下文件：

- `sprints/2026.05.10_13-14/pre_start.md`
- `sprints/2026.05.10_13-14/tech-plan.md`
- `sprints/2026.05.10_13-14/tech-done.md`
- `sprints/2026.05.10_13-14/final.md`

这些文件只记录流程修复 sprint 的真实状态，不声称业务代码完成，也不修改 `AGENTS.md`、`registry.toml`、角色 toml 或业务代码。

## 已完成：配置修复 worker 结果

配置修复 worker 已落地，coordinator 接管完成集成验收。

实际改动文件：

- `AGENTS.md`
- `.codex/agents/registry.toml`
- `.codex/agents/product-okr-owner.toml`
- `.codex/agents/robot-software-engineer.toml`
- `.codex/agents/hardware-engineer.toml`
- `.codex/agents/autonomy-engineer.toml`
- `.codex/agents/full-stack-software-engineer.toml`

修复内容：

- `AGENTS.md` 新增可机械执行决策树：`read-only`、`planning`、`implementation`、`acceptance`。
- `AGENTS.md` 明确 Cursor 使用 `Task(subagent_type=generalPurpose)`，Codex 使用 `spawn_agent(agent_type=worker)`，无子 agent 工具时只能降级为只读/计划。
- `AGENTS.md` 明确主节点白名单和禁区：主节点负责读文件、拆任务、派发/等待子 agent、集成验收、更新 sprint 留档和最终汇总；产品代码、测试代码、硬件配置、实现/测试/修复命令必须交给子 agent。
- `AGENTS.md` 将 `product-okr-owner` 纳入 runtime 映射，并限制其可改范围为 `OKR.md`、`sprints/`、`docs/product/`。
- `AGENTS.md` 明确 1 owner 必须派 1 个子 agent；2+ owner 且文件范围互不重叠时必须并行派多个子 agent；接口耦合或共享文件时指定 1 个主责 owner，其他 owner 只读咨询。
- `.codex/agents/registry.toml` 新增 `[runtime_adapters]`，补齐 Cursor/Codex 调度适配和缺失子 agent 工具时的 fallback。
- `.codex/agents/registry.toml` 的每个 `[[roles]]` 补齐 `enabled`、`codex_agent_type`、`capabilities`、`tags`、`read_first`、`owner_paths`、`requires_vendor_source`、`can_edit`。
- 5 个角色 TOML 均补齐 `enabled = true` 和 `capabilities = [...]`，保留原有 prompt 正文。

## 本轮验证

已运行：

```bash
find sprints/2026.05.10_13-14 -maxdepth 1 -type f -print | sort
grep -RIn "待集成\|子agent\|spawn_agent\|并行" sprints/2026.05.10_13-14
```

结果：

- `python3` + `tomllib` 成功解析 `.codex/agents/*.toml`，共 6 个 TOML 文件均为 OK。
- `grep` 确认 `AGENTS.md` 和 `registry.toml` 已包含 `spawn_agent(agent_type=worker)`、Cursor Task、`product-okr-owner`、`1 owner`、`2+ owner`、`read-only/planning/implementation/acceptance` 等关键规则。
- `find sprints/2026.05.10_13-14 -maxdepth 1 -type f -print | sort` 确认本轮 4 个 sprint 文档存在。
- `grep -RIn "待集成\|子agent\|spawn_agent\|并行" sprints/2026.05.10_13-14` 确认本轮留档包含并行子 agent、spawn_agent 和集成状态证据。

## 剩余风险

- 本轮没有触碰业务代码，因此不能用本轮结果证明 ROS2 构建、运行或硬件链路健康。
- 本轮修复的是 repo 内的 agent 规则和 registry 可发现性；外部运行时是否自动读取这些字段，仍取决于 Cursor/Codex 的实际加载机制。
- 后续功能 sprint 必须用真实工程任务继续验证：多 owner 文件范围互不重叠时，是否真的并行派多个 worker 并留下独立输出。

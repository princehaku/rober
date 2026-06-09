# sprint_type: micro

## 实际改动

- 更新 `.codex/agents/product-okr-owner.toml`：新增 Mission 执行偏置和 WIP 限制，要求停止连续 review/handoff/status surface 小切片，改排能产生 `task_id`、地图、路线、关键帧、回放或 delivery result 的 sprint。
- 更新 `.codex/agents/robot-software-engineer.toml`：新增真实可用即实跑、阻塞时先 mock/stub/dry-run 推进、每轮留下可复核产物的要求。
- 更新 `.codex/agents/robot-algorithm-engineer.toml`：明确 SLAM 建图、路线采集、路线回放、关键帧和传感器 topic smoke 是默认第一优先级。
- 更新 `.codex/agents/robot-hardware-engineer.toml`：明确硬件 owner 要输出 smoke/HIL/虚拟串口命令和日志，不把未最终 HIL 当作停止开发理由。
- 更新 `.codex/agents/full-stack-software-engineer.toml`：要求 UI/接口优先消费送达任务证据链，不把孤立 dashboard/fixture preview 当 mission 进展。
- 更新 `.codex/registry.toml`：新增 `execution_bias` 和 `mission_evidence_rule`，把“真实可用即 live/smoke、每轮必须说明 mission evidence”写入结构化执行策略。

## 验证结果

- `python3` + `tomllib` 解析 `.codex/registry.toml` 与 `.codex/agents/*.toml`：通过。
  - 输出包含：`OK .codex/registry.toml`、`OK .codex/agents/robot-algorithm-engineer.toml`、`OK .codex/agents/robot-software-engineer.toml`。
- `rg` 检索 `Mission 执行偏置`、`真实可用即实跑`、`传感器可用即上主链路`、`mission_evidence_rule`、`map.yaml`、`route.csv`、`replay JSONL`：通过，关键规则均可检索。
- `git diff --check -- .codex/agents .codex/registry.toml sprints/2026.06.09_11-50_agent-execution-bias-config/tech-done.md`：通过，无输出。

## 剩余风险

- 当前运行时的 `multi_agent_v1.spawn_agent` 仍可能因模型解析失败无法启动子 agent；本次配置修正只改变 agent prompt 和 registry 约束，不修复运行时工具问题。
- 这些配置会让 agent 更敢执行，但仍保留 vendor 来源、运动安全、接口兼容和验证边界，避免把真实风险删掉。

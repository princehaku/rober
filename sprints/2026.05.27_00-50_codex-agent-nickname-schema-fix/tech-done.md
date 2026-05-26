# Codex Agent Nickname Schema Fix

sprint_type: micro

## 实际改动

- 修复 `.codex/agents/full-stack-software-engineer.toml`、`.codex/agents/product-okr-owner.toml`、`.codex/agents/robot-algorithm-engineer.toml`、`.codex/agents/robot-hardware-engineer.toml`、`.codex/agents/robot-software-engineer.toml` 的 `nickname_candidates` 类型。
- 按 Codex 官方 schema，`nickname_candidates` 必须是字符串数组；本轮将单字符串写法改为数组写法，例如 `nickname_candidates = ["pd"]`。

## 验证结果

- 已执行 `python -c "... tomllib ..."` 解析 5 个 `.codex/agents/*.toml` 文件，全部通过。
- 已额外检查三项约束：必填 `name` / `description` / `developer_instructions` 均存在，顶层无非官方 schema key，`nickname_candidates` 为 list。
- 已执行 `rg '^nickname_candidates\s*=\s*"' .codex/agents --glob '*.toml'`，确认无字符串形式残留。

## 剩余风险

- 本轮验证覆盖本地 TOML 解析和 schema key 检查；Codex 运行时若仍提示 malformed，优先排查 Codex 缓存、全局 `~/.codex/agents/` 或 WSL 路径下是否存在旧副本。

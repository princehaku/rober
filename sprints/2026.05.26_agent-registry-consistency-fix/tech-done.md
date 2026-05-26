# Agent Registry 全局一致性修复

## sprint_type

micro

## 实际改动

### AGENTS.md（权威来源修正）
- 第 77 行：`""robot-algorithm-engineer""` → `"robot-algorithm-engineer"` （去掉多余双引号）
- 角色映射表：`autonomy-engineer` / `autonomy-engineer.toml` → `robot-algorithm-engineer` / `robot-algorithm-engineer.toml`（磁盘上不存在 `autonomy-engineer.toml`，原映射会导致派单失败）
- 角色映射表：`robot-hardware-engineer.toml` → `robot-hardware-engineer.toml`（修正文件名拼写）

### .codex/agents/full-stack-software-engineer.toml
- 内部 `id = "user-software-engineer"` → `"full-stack-software-engineer"`（与 registry / AGENTS.md 对齐，消除子 agent 注入时 id 不匹配的问题）

### .codex/agents/registry.toml
- `product-okr-owner [[roles]]` capabilities 同步新增的 `okr-direction-review` / `kr-completion-archive` 和对应 tags
- `parallel_default` 从 `2-6` 改回 `2-4`，与 AGENTS.md 约定一致

### .codex/agents/robot-algorithm-engineer.toml
- `capabilities`：`future-vision` → `vision` + `elevator-floor-perception`（与 registry 对齐）
- typo：`方便后人月度` → `方便后人阅读`；`代码既文档` → `代码即文档`

### .codex/agents/robot-software-engineer.toml
- `owner_paths` 从 `["onboard/", "docs/"]` 收窄到精细路径，与 registry 对齐
- typo：同上修正

### .codex/agents/robot-hardware-engineer.toml
- `owner_paths` 从 `["onboard/", "docs/"]` 收窄到 `ros2_trashbot_hardware/`、`ros2_trashbot_bringup/`、`docs/hardware/`、`docs/vendor/`，防止硬件工程师越权修改无关代码

## 验证结果

```
python .codex/agents/registry-check（内联脚本）

OK  product-okr-owner
OK  robot-software-engineer
OK  robot-hardware-engineer
OK  robot-algorithm-engineer
OK  full-stack-software-engineer
ALL_ALIGNED

所有 6 个 .toml 文件解析通过，registry 声明 id 与文件内 id 字段完全对齐。
```

## 剩余风险

- `robot-hardware-engineer.toml` 文件名与角色 id `robot-hardware-engineer` 仍有命名不一致（`robot-` vs `rober-`），registry 已加注释说明，属于已知历史遗留，不影响功能，后续可统一重命名（需同步 AGENTS.md、registry 和文件名三方）。
- AGENTS.md 中角色描述段（L72-78）的角色名仍然是人工维护的文字，不会自动从 registry 同步；后续 registry 变更时需手工同步。

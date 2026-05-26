# Product OKR Owner Agent Direction Archive Update

## sprint_type

micro

## 实际改动

- 更新 `.codex/agents/product-okr-owner.toml`，将 Product Manager / OKR Owner 的职责扩展为 OKR 方向判断、完成 KR 历史归档、当前 OKR 与历史 OKR 边界维护。
- 增加 `okr-direction-review`、`kr-completion-archive` 能力标签，要求阶段收口时基于 sprint 证据判断继续、调整、暂停或替换 OKR 方向。
- 要求已完成 KR 归档时记录完成时间、证据链接、验收结论、剩余风险和后续影响，避免完成项继续占用当前推进区。
- 修正委派列表中的旧角色 ID，将 `user-software-engineer` 更新为 `full-stack-software-engineer`。

## 验证结果

- 已执行：`python -c "import tomllib; p=r'.codex/agents/product-okr-owner.toml'; d=tomllib.load(open(p,'rb')); print('OK', d['id'], d['capabilities'])"`。
- 结果：通过，输出 `OK product-okr-owner ['okr-planning', 'okr-direction-review', 'kr-breakdown', 'kr-completion-archive', 'scope-control', 'acceptance-criteria', 'sprint-documentation']`。

## 剩余风险

- 本轮只更新 Product OKR Owner 的 agent 定义，没有实际迁移 `OKR.md` 中的 KR 历史内容。
- 后续真正整理已完成 KR 时，仍需读取 `OKR.md` 和相关 sprint 证据后再移动条目。

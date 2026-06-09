# Side2Side Check - 板载 evidence 到 O6 archive / O7 consumer detail

## sprint_type

`sprint_type: epic`

## 验收对照框架（待验收）

### 1) 设计完整性

- manifest schema 入口是否明确且可复核：`trashbot.field_evidence_manifest.v1`。
- manifest->archive/consumer 转换边界是否定义清晰：artifact status、manifest gate、task/evidence 追溯链路。
- O7 consumer detail 对 manifest 来源与边界字段是否具备展示约束：not_proven / delivery_success / safe_to_control / primary_actions_enabled。
- O6 与 O7 分工是否不重复 join 的主要数据路径。

### 2) SSH 预检策略

- 有界 SSH 预检命令已写入：`timeout 8s ssh root@192.168.1.11 -p 37878 ...`。
- live 不可达不阻塞本轮验收：需保证 local/mock 与 fail-closed 分支可覆盖主要验收命令。

### 3) 交付边界

- 是否明确禁止把 local/mock 产物解释为真实交付成功。
- 是否保持 `delivery_success=false` 与 `primary_actions_enabled=false` 的固定边界。
- 是否明确下一位工程师的文件范围、执行命令、owner、验收口径。

## 初审结论（待工程实现）

1. 设计闭环完整，能够支撑直接下发实现；未发现“同一 blocker 消费”回归点。
2. 待验收项：`full-stack-software-engineer` 按 `tech-plan.md` 完成实现后，补齐执行日志/截图/命令输出。


# Side2Side Check - 板载 evidence 到 O6 archive / O7 consumer detail

## sprint_type

`sprint_type: epic`

## 验收对照框架

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

## 对照结果

1. `consumer detail` 已把 `manifest_gate`、`artifact_status`、`not_proven`、`delivery_success`、`safe_to_control`、`primary_actions_enabled` 提升为显式字段和 UI 可见项。
2. 上游 field evidence 输入现在只接受：
   - `trashbot.field_evidence_manifest.v1`
   - `trashbot.pc_tools_workstation.o7_field_evidence_consumer_ingest.v1`
3. 缺 contract、schema mismatch、unsafe claim、bad shape 时，`consumer detail` 直接 `fail_closed`，不再回退到未标记 raw join。
4. SSH 不可达时，preflight 仍写出 `blocked_ssh_unreachable` JSON；本地完整 fixture 仍能完成 manifest->consumer detail 的 software proof 闭环。

## 验收结论

1. 本轮实现满足 `tech-plan.md` 的 FP1-FP4，且 O7 detail 主路径已消费 field evidence contract。
2. 验证证据完整覆盖 Python 脚本、单元测试、workstation build/test/lint、local/mock manifest smoke、`rg` 和 `git diff --check`。
3. 唯一环境偏差是 macOS 缺少 `timeout` 命令；该偏差已被记录，未阻断 preflight JSON 与 local/mock 软件闭环。

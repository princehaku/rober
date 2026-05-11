# Sprint 2026.05.12_09-10 Remote Cloud Backup Restore Drill - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据边界：目标为 `software_proof_docker_backup_restore_drill`

## 用户价值和产品北极星

本轮要把 O6 从“SQLite-backed state store 可恢复”推进到“state store 可备份、可恢复、可演练”。对普通手机用户的价值是：未来云中转服务发生容器重建、节点迁移或本地 state 损坏时，系统具备一条可审计的恢复路径，手机命令、机器人状态和 ACK 轨迹不应被无声丢失。

北极星仍是普通用户只用手机，通过 4G 云中转完成 trash delivery。当前 PRD 不把 backup/restore drill 包装成真实云灾备完成，不把 ACK 包装成真实送达，不把 Docker-only evidence 包装成 4G、OSS/CDN、Nav2、WAVE ROVER 或 HIL 证据。

## 背景和证据

1. `OKR.md` 最新快照：
   - O6 约 32%，是当前最低完成度目标。
   - O5 约 33%，主要缺正式手机 UI 和普通用户验收；本轮只提供 phone-safe restore/readiness 支撑。
   - O1/O2/O3/O4 完成度约 74%-76%，但当前主机无真实硬件、真实路线、真实相机、真实 4G 或 HIL，不适合作为本轮主线。
2. `sprints/2026.05.12_08-09_remote-cloud-sqlite-state-proof/final.md`：
   - 已有 `software_proof_docker_sqlite_state_store`。
   - 明确 SQLite 只证明单实例 command/status/ack recovery。
   - 明确 production DB/queue、多实例一致性、backup/restore 和 disaster recovery 仍未证明。
3. 近期评审反复强调：
   - Docker/local proof 必须保持 evidence boundary。
   - blocked/warning 不能写成 production ready。
   - 不能把软件证明写成真实云、真实 4G、HIL 或正式手机 UI。

## OKR 映射

| KR | 本轮产品诉求 |
| --- | --- |
| O6 KR1 云中转服务端最小契约 | Restore 后 commands/status/ack HTTP API shape 不变。 |
| O6 KR2 云服务端基线 | 为后续 staging/production 提供单实例 backup/restore drill 软件证据。 |
| O6 KR5 凭证管理 contract | Backup artifact、restore output 和 preflight 不泄露 bearer、Authorization header、OSS secret 或敏感路径。 |
| O6 KR6 graceful degradation | Backup 缺失、restore 失败、metadata/checksum 不匹配时输出 phone-safe blocked/warning。 |
| O5 支撑项 | 沉淀用户可读恢复状态和 retry hint，不交付正式手机 UI。 |

## KR 拆解或更新

### P0 - Backup artifact

- 支持从 SQLite state 生成 backup artifact。
- Backup artifact 应包含足够恢复 commands/status/acks 的数据和最小 metadata。
- Metadata 必须标注 source state backend、created_at、evidence boundary 和 artifact format/version。
- Artifact 不得包含 bearer token、Authorization header、OSS secret、root password、raw traceback、ROS topic、串口、baudrate、WAVE ROVER 参数或 `/cmd_vel`。

### P0 - Restore drill

- 支持从 backup artifact 恢复到新的 SQLite state path。
- Restore 后 API shape 兼容既有 contract。
- Restore 后至少能读取最近 status、已入队 command、terminal ACK 或 cursor 所需 ACK 记录。
- Restore 不得把 command envelope ACK 解释为真实 trash delivery result。

### P0 - Disaster recovery gate

- Preflight 或 CLI gate 能识别 backup/restore drill 是否执行过。
- Docker-only drill pass 只允许标注为 `software_proof_docker_backup_restore_drill`。
- Production DR、多实例一致性、生产 DB/queue、真实云备份策略仍必须保持 blocked 或 warning。
- 缺 backup、restore 失败、artifact schema 不匹配或 checksum/metadata 不一致时，输出 phone-safe reason。

### P0 - Phone-safe restore output

- 输出字段应适合手机端或 operator 页面未来消费，例如 `backup_status`、`restore_status`、`drill_status`、`safe_summary`、`retry_hint`、`evidence_boundary`。
- 错误输出不得回显本地绝对路径、token、credential-bearing URL、硬件设备名或 raw exception。
- 用户可读文案必须说明“当前是软件演练，不是生产云灾备完成”。

### P0 - Robot compatibility

- Robot remote bridge 的 post_status、get_next_command、post_ack 语义不变。
- Restore 后 command/status/ack response shape 不迫使 robot client 改协议。
- auth/cloud/malformed response、restore blocked 和 preflight blocked 不能推进 cursor，不能触发本地 action。

## 做什么 / 不做什么

做：

- 定义并实现 SQLite state backup artifact。
- 定义并实现 restore drill，并验证 commands/status/acks 恢复后仍可读。
- 在 preflight 或 CLI gate 中加入 backup/restore/DR drill 状态。
- 用 targeted relay tests/smoke 覆盖 backup、restore、phone-safe failure 和 evidence boundary。
- 用 robot compatibility fence 确认 remote bridge status-command-ack 与 cursor/ACK 语义不退化。
- 后续收口中保守更新 O6；O5/O1/O2/O3/O4 不因本轮软件 drill 提升。

不做：

- 不部署真实云，不购买域名，不申请证书，不实配防火墙。
- 不接真实 4G/SIM，不跑 carrier 弱网实测。
- 不完成 OSS/CDN 上传、STS 发放、CDN 回源、生命周期或 rotate 实流量。
- 不迁移生产 DB/queue，不验证多实例一致性、跨可用区灾备或生产运维。
- 不做正式手机 UI、美观验收、普通用户实机验收。
- 不修改硬件、Nav2、fixed-route、WAVE ROVER 或 HIL 相关实现。

## 优先级和验收口径

| 优先级 | 用户可感知价值 | 验收口径 |
| --- | --- | --- |
| P0 backup artifact | 云端状态有可审计恢复源 | SQLite state 可生成 backup artifact，metadata 和脱敏通过。 |
| P0 restore drill | 重建后仍可复盘命令和状态 | Restore 到新 state path 后 commands/status/acks 仍按既有 API shape 可读。 |
| P0 DR gate | 避免把演练写成生产灾备 | Preflight/CLI 输出 software proof、生产 DR 缺口和 phone-safe warning。 |
| P0 phone-safe failure | 用户看到可行动的恢复提示 | 缺 artifact、schema mismatch、restore failure 输出 safe_summary/retry_hint。 |
| P0 compatibility fence | robot bridge 不被恢复机制破坏 | status-command-ack tests 通过，失败不推进 cursor。 |
| P1 docs/sprint evidence | 后续团队能接力真实 staging | `tech-done.md` 记录命令、输出、失败定位和剩余风险。 |

## 对应责任 Engineer

- 主责：`full-stack-software-engineer`
  - Backup artifact。
  - Restore drill。
  - Preflight/CLI DR gate。
  - Targeted relay tests/smoke。
  - 必要 `docs/product/` 同步和当前 sprint `tech-done.md`。
- 支撑：`robot-software-engineer`
  - Remote bridge compatibility acceptance。
  - 确认 status-command-ack 与 cursor/ACK conservative semantics 未变。
- Product Acceptance：`product-okr-owner`
  - 检查 O6 证据边界。
  - 维护后续 `side2side_check.md`、`final.md` 和必要 OKR 保守更新。

## 风险、阻塞和需要补齐的证据链

- Backup/restore drill 是 local/Docker 单实例 proof，不等于生产 DB/queue、多实例一致性、跨地域或跨可用区灾备。
- 如果 backup/restore 只能在真实云资源下运行，说明本轮设计过重，应退回 Docker-only 可执行闭环。
- 如果 restore 改变 HTTP API shape 或 robot polling semantics，必须优先修复兼容性。
- 如果 preflight 输出把 drill pass 写成 production ready，必须改回 software proof 边界。
- O5 只能获得 phone-safe restore/readiness 支撑；正式手机 UI 不在本轮验收范围。
- O1/O2/O3/O4 不因本轮 backup/restore drill 变化提升。

## 需要创建或更新的 sprint 文档

- 本轮已创建：`pre_start.md`
- 本轮已创建：`prd.md`
- 本轮前置必须创建：`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`、`final.md`
- 验收后按证据保守更新：`OKR.md`

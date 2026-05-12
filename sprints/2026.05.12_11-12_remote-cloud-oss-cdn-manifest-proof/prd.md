# Sprint 2026.05.12_11-12 Remote Cloud OSS/CDN Manifest Proof - PRD

## 状态

- 阶段：prd
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 兼容性围栏：`robot-software-engineer`
- Product acceptance boundary：`software_proof_docker_oss_cdn_manifest`

## 背景

O6 已经完成 local/mock cloud command loop、independent relay、Docker deploy、production preflight gate、SQLite state proof 和 backup/restore drill。当前剩余关键缺口中，OSS/CDN 仍停留在配置形态检查：文档里有 bucket、region、prefix 和 CDN base URL，但没有可生成、可校验、可被 preflight 消费的对象引用 manifest artifact。

本轮要补的不是生产 OSS/CDN，而是正式链路前的产品 contract：未来任务诊断大对象如何被引用、如何组合 CDN URL、如何证明 artifact 未被篡改、如何保证手机/诊断输出不泄露凭证，以及如何在 Docker/local preflight 中把这类证据和真实上传能力区分开。

## 用户价值

普通用户最终只需要在手机上看到“任务诊断可查看/不可查看、原因是什么、下一步怎么恢复”，而不是看到 OSS bucket、AK/SK、ROS topic 或底层命令。manifest proof 能提前固定这条用户可见链路的数据形态，让后续真实云接入时不把大对象路径、密钥、CDN URL 和诊断摘要混在一起临时实现。

## OKR 映射

- Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化。
- KR3：对象前缀 `rober/<robot_id>/<date>/<task_id>/` 和凭证边界进入可校验 artifact。
- KR4：CDN base URL `https://cdn.bytegallop.com/rober/` 和对象引用 URL 组合进入可验证 shape。
- KR5：凭证管理和脱敏 contract 进入 manifest/preflight 输出检查。
- KR6：为后续 OSS 写失败、CDN 不可达的 graceful degradation 留出 machine-readable artifact 字段，但本轮不证明真实降级。

## KR 拆解

KR6.1 Manifest artifact shape：

- 生成 artifact 包含 `schema`, `schema_version`, `evidence_boundary`, `created_at`, `robot_id`, `task_id`, `date`, `bucket`, `region`, `prefix`, `cdn_base_url`, `objects`, `checksum`, `not_proven`。
- `objects` 至少覆盖一个诊断引用样例，包含 logical name、object key、content type 或 media type、byte size/hash 占位、CDN URL 和 redacted metadata。
- artifact checksum 覆盖除 checksum 自身以外的稳定 payload。

KR6.2 Preflight gate：

- preflight 可通过 env 或参数读取 manifest artifact。
- artifact schema/version/checksum/prefix/CDN URL 组合正确时，preflight 输出 manifest check passed。
- 输出 evidence boundary 必须是 `software_proof_docker_oss_cdn_manifest` 或等价清晰边界。
- 即使 manifest passed，也必须保留真实 OSS/CDN/4G/云未证明的 `not_proven`。

KR6.3 Phone-safe redaction：

- artifact 和 preflight 输出不得包含 bearer token、Authorization header、OSS secret、AK/SK、root password、raw state path、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- 错误信息必须使用 phone-safe code、safe summary 和 retry hint，避免 traceback 和凭证路径。

KR6.4 Robot compatibility fence：

- `remote_bridge` 仍按 `trashbot.remote.v1` command/status/ack 轮询。
- ACK 仍只表示 robot bridge 已处理 command envelope，不表示真实 delivery success。
- manifest/preflight work 不得改变 command idempotency、status stale/missing、terminal ACK 或 cursor 保守语义。

## 范围

做：

- OSS/CDN manifest artifact 生成。
- manifest artifact 校验。
- preflight 接入 manifest artifact gate。
- O6 产品文档同步更新。
- `remote_bridge` command/status/ack compatibility fence。
- 当前 sprint `tech-done.md` 留档。

不做：

- 真实 OSS upload、STS、受限 AK 发放、CDN 回源、对象生命周期、生产账号或 rotate。
- 真实云部署、HTTPS/TLS、公网入口、4G/SIM、弱网 carrier 测试。
- 生产 DB/queue、多实例一致性或真实灾备。
- 手机 UI 正式接入 manifest。
- Nav2/fixed-route、真实送达、硬件串口、WAVE ROVER、HIL。

## 验收口径

P0 acceptance：

- 能在 Docker/local 环境生成一个 manifest artifact。
- 校验命令或 preflight 能拒绝 schema/version/checksum/prefix/CDN URL 错误的 artifact。
- preflight 对有效 artifact 输出 `evidence_boundary=software_proof_docker_oss_cdn_manifest` 或等价边界。
- artifact/preflight 明确列出 `not_proven`：real OSS upload、STS issuance、CDN origin fetch、lifecycle policy、production account、real cloud、real 4G/SIM、HTTPS/TLS public ingress、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL。
- phone-safe redaction 检查通过。
- `remote_bridge` compatibility targeted tests 通过。
- scoped `git diff --check` 通过。

P0 不通过条件：

- 输出暗示 `production_ready=true`、真实云 ready、OSS uploaded、CDN reachable 或 delivery success。
- artifact 中出现真实或占位形态的 secret 值、Authorization header、AK/SK、root password、串口、baudrate、ROS topic 或 `/cmd_vel`。
- manifest pass 破坏 command/status/ack 或 ACK/cursor 保守语义。

## Engineer 分工

- `full-stack-software-engineer`
  - 主责实现 manifest artifact generator/checker 和 preflight 接入。
  - 同步 `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md` 中的 O6 manifest proof 口径。
  - 更新本 sprint `tech-done.md`。
- `robot-software-engineer`
  - 执行 remote bridge compatibility fence。
  - 只在发现 manifest work 破坏 robot polling/ACK/status 契约时提出最小修复建议或补丁。

## 风险和阻塞

- 本机只有 Docker，没有真实硬件；本轮不能产生 HIL 或真实机器人运动证据。
- 没有真实云/OSS/CDN/4G 账号链路；本轮不能证明上传、回源、HTTPS、公网或 carrier 网络。
- Manifest artifact 如果过度接近生产配置，容易被误读为 production ready；必须在 schema 和 preflight 输出中保留证据边界。
- 如果后续正式手机 UI 要消费 manifest，还需要定义 artifact 过期、刷新、权限和私有对象引用策略。

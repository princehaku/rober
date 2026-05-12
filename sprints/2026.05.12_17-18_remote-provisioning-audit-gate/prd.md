# Sprint 2026.05.12_17-18 Remote Provisioning Audit Gate - PRD

## 1. 用户价值和产品北极星

本轮面向普通手机用户和支持/运维人员，不面向云平台管理员。

用户价值：

- 手机用户只看到“远程能力还缺什么”和“下一步该怎么恢复/联系支持”，不看到 raw JSON、token、OSS secret、AK/SK、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- 支持/运维可以通过本地 preflight 和 diagnostics 摘要确认 robot provisioning、STS issuance、audit log 哪一项缺证据，避免把所有失败都归为“云不可用”。
- 产品团队能把 O6 的生产前置缺口拆成可追踪 KR 证据，而不是继续堆 mock 字段。

产品北极星：

- 小车通过 4G outbound polling 云端 API，手机通过云端下发命令并查看状态。
- 本轮只推进远程控制生产化之前的本地可执行 proof，仍保持 Docker/local software proof 边界。

## 2. OKR 映射

主 OKR：Objective 6 - 4G 云中转 + OSS/CDN 数据通路产品化。

KR 映射：

- KR1：新增 gate 不能破坏 `trashbot.remote.v1` command/status/ack；仍不暴露 `/cmd_vel`，不接受 inbound 直连小车。
- KR3：STS issuance gate 只证明 STS/受限 AK 的 request/result artifact shape 和权限边界，不证明真实 STS。
- KR5：robot provisioning、STS issuance、audit log 从文档缺口推进为可执行 artifact/preflight/phone-safe gate。
- KR6：diagnostics 能区分 provisioning missing、STS missing/invalid/stale、audit-log missing/invalid/stale，并给出普通用户 retry hint。

非主 OKR：

- Objective 5：只消费 phone-safe 摘要素材，不提升 O5 进度。
- Objective 1/2/3/4：本轮不触碰硬件、导航、行为送达或视觉能力，不提升进度。

## 3. KR 拆解或更新

本轮建议把 O6 进展拆成三条可验收 evidence item：

1. Robot provisioning artifact gate：
   - Artifact schema 建议为 `trashbot.robot_provisioning_gate`。
   - 输出 robot identity/provisioning request 的本地 proof state、safe summary、retry hint、not_proven 和 checksum。
   - Preflight 缺失为 warning；schema/version/checksum/redaction 失败为 blocked。

2. STS issuance artifact gate：
   - Artifact schema 建议为 `trashbot.sts_issuance_gate`。
   - 输出 credential mode、requested scope、expiry window、least privilege status、safe summary、retry hint、not_proven 和 checksum。
   - 本轮不得输出真实 STS token、AK/SK、secret、credential-bearing URL 或 OSS secret。

3. Audit log artifact gate：
   - Artifact schema 建议为 `trashbot.provisioning_audit_gate`。
   - 输出 provisioning/STS/preflight 事件 shape、event_count、redaction status、checksum status、safe summary、retry hint 和 not_proven。
   - 本轮只证明本地 audit event shape 和脱敏消费，不证明真实审计系统。

若三条 gate 全部完成并通过本地验证，Product 后续可把 O6 从约 43% 保守小幅上调到约 45%。若只完成其中一到两条，O6 进度最多只能按证据保守小幅调整，且必须保留 blocked 项。

## 4. 本轮核心抓手

本轮核心抓手是“把生产前置缺口做成可执行 gate”：

- 不是继续增加泛化 `not_proven` 文案。
- 不是接真实云账号或真实 OSS。
- 不是改手机 UI 主流程。
- 是让 relay/preflight/operator diagnostics 能以 phone-safe 摘要展示 robot provisioning、STS issuance、audit log 的本地 proof 状态。

## 5. 需要做什么

Task A - Full-stack owner：

- 在 remote relay/preflight 层新增 robot provisioning、STS issuance、audit log 三类本地 artifact 生成和校验入口。
- 在 `/preflightz` / `--preflight` 中消费 artifact，并输出 machine-readable check status。
- 在 operator status/diagnostics 中输出 phone-safe 摘要。
- 同步更新 `docs/product/cloud_4g_infrastructure.md` 和 `docs/product/remote_4g_mvp.md`，明确新边界、CLI/env 入口、non-goals 和 redaction 规则。

Task B - Robot owner：

- 增加 `remote_bridge` compatibility fence。
- 确认 command/status/ack 响应出现 provisioning/STS/audit metadata 时，robot bridge 不触发新 action、不误判 ACK 为 delivery success、不推进错误 cursor、不持久化未成功 ACK。
- 如现有实现已兼容，可只新增测试，不强行改 `remote_bridge.py`。

Task C - Product owner：

- 实现完成后验收 Task A/Task B 证据。
- 更新 `tech-done.md`、`side2side_check.md`、`final.md` 和 `OKR.md`。
- 严格标注证据边界为 Docker/local software proof。

## 6. 优先级和验收口径

P0：

- Artifact/preflight/phone-safe gate 必须全部脱敏。
- `production_ready=false` 和 `overall_status=blocked` 必须保持，直到真实云和生产证据存在。
- 新 metadata 不得改变 remote bridge 的 command/status/ack 保守语义。
- 文档必须同步更新 `docs/product/cloud_4g_infrastructure.md` 与 `docs/product/remote_4g_mvp.md`。

P1：

- CLI 输出建议带 `evidence_boundary=software_proof_docker_provisioning_audit_gate`。
- Operator diagnostics 文案应区分 provisioning、STS、audit-log 三类问题。
- Artifact freshness/staleness 应有可配置或固定窗口，并在 phone-safe summary 中显示。

验收通过标准：

- Full-stack targeted tests 通过。
- Robot compatibility targeted tests 通过。
- 相关 Python 文件 `py_compile` 通过。
- 至少一个 CLI artifact generate smoke 通过。
- Preflight consumption smoke 输出三类 check 的 pass/missing/blocked 语义。
- Scoped `git diff --check` 通过。

## 7. 对应责任 Engineer

- 主责：`full-stack-software-engineer`
- 兼容围栏：`robot-software-engineer`
- 验收和 OKR 收口：`product-okr-owner`

本轮不需要 `hardware-engineer` 或 `autonomy-engineer`，因为不涉及硬件、WAVE ROVER、UART、Nav2、fixed-route 或视觉实机能力。

## 8. 风险、阻塞和需要补齐的证据链

风险：

- 把 STS issuance gate 写成真实 STS 已签发，造成证据越界。
- Phone-safe 摘要泄露 token、AK/SK、secret、credential URL、本地路径或 traceback。
- Preflight pass 被误读为 production-ready。
- Robot bridge 因新增 metadata 误触发 action、ACK 或 cursor 变化。

阻塞：

- 当前主机没有真实硬件。
- 当前没有真实云账号 provisioning、真实 STS、真实 OSS upload、真实 CDN origin fetch、真实 4G/SIM 或生产 audit system。

需要补齐的证据链：

- Docker/local artifact schema、checksum、freshness 和 redaction evidence。
- Preflight check pass/missing/invalid/stale evidence。
- Operator/API phone-safe summary evidence。
- Robot bridge metadata compatibility evidence。
- Product acceptance evidence，明确不能升级为真实云或生产 ready。

## 9. 需要创建或更新的 sprint 文档

本计划阶段创建：

- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/pre_start.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/prd.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-plan.md`

后续实现/验收阶段必须更新：

- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/tech-done.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/side2side_check.md`
- `sprints/2026.05.12_17-18_remote-provisioning-audit-gate/final.md`
- `OKR.md`

# Sprint 2026.05.13_17-18 O5 External Evidence Intake Gate - PRD

## 用户价值

普通用户最终只关心手机端能否可靠控制和诊断机器人；但 O5 当前卡在真实云、OSS/CDN、DB/queue、4G/SIM 外部证据缺失。工程团队需要一个安全入口接收未来外部材料，把“材料是否存在、是否脱敏、是否足以推进 O5”变成可验证 JSON 和 phone-safe summary，而不是靠口头说明或散落截图。

## 产品北极星

手机用户不需要理解云账号、OSS、CDN、数据库、队列或 4G 细节。系统应该把这些上线前证据转译成清晰、脱敏、可交接的 readiness 状态：能否继续、缺什么、下一步找谁补证。

## OKR 映射

- Objective 5 KR1：云中转服务端最小契约继续保持 command/status/ack 边界，新增外部证据 intake 时不得暴露 `/cmd_vel` 或 inbound robot control。
- Objective 5 KR3/KR4：OSS/CDN 外部材料要以脱敏摘要进入 readiness，不暴露 AK/SK、完整对象 key、credential-bearing URL 或响应体。
- Objective 5 KR5：凭证管理 contract 要求 tracked 文件不得包含真实 secret；intake gate 必须主动拒绝或红线标记敏感字段。
- Objective 5 KR6：网络、OSS/CDN、DB/queue、4G 缺口需要 graceful blocked summary，而不是假装 ready。

## 本轮核心抓手

新增 `trashbot.external_evidence_intake` gate：

- 接收未来真实外部证据材料的枚举化状态，而不是保存原始凭证或完整响应。
- 对 OSS/CDN、public HTTPS/TLS、4G/SIM、production DB/queue 四类材料形成统一 summary。
- 进入 preflight 和 phone-safe readiness 时默认 `production_ready=false`，除非外部材料类型、脱敏和必要字段均满足本轮定义。
- 在没有真实材料的 Docker-only 环境下输出 blocked evidence，作为后续外部补证清单。

## 非目标

- 不申请云账号、不开真实公网、不中转真实 4G/SIM。
- 不真实连接 production DB/queue，不跑 migration/worker。
- 不上传 OSS，不访问真实 CDN 回源，不保存真实 URL 或凭证。
- 不触发机器人任务、不推进 ACK cursor、不声明送达完成。

## 验收口径

- Full-stack task 产出 intake artifact writer、validator、preflight consumption 和文档。
- Robot task 证明 intake metadata-only responses 不触发 backend action、不 POST ACK、不推进或持久化 cursor。
- Product closeout 只按实际证据更新 OKR；如果仍无真实外部材料，O5 不上调，只记录 blocked-by-design 能力。

## 剩余证据链

真实推进 O5 仍需要至少一种外部材料：真实 OSS/CDN live traffic、真实 HTTPS/TLS 公网入口、真实 4G/SIM、真实 production DB/queue connectivity 或 production worker/migration 证据。本轮 intake gate 只是让这些材料后续能被安全接入和验收。

# Sprint 2026.05.12_07-08 Remote Cloud Production Preflight - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主责 Engineer：`full-stack-software-engineer`
- 支撑 Engineer：`robot-software-engineer`
- 证据目标：`software_proof_docker_preflight_gate`
- 环境边界：本机只有 Docker；没有真实云主机、域名、公网 TLS、真实 4G/SIM、OSS/CDN 账号验证、生产 DB/queue、真实硬件或 HIL。

## 用户价值和产品北极星

本轮用户价值是把 O6 从 Docker deploy proof 推进到“真实云部署前不会带病上线”的 production preflight gate。它面向未来手机用户的间接价值是：在接入真实云、HTTPS、TLS、公网入口、OSS/CDN、生产凭证和持久化队列前，团队可以先用 Docker-only 主机检查配置、凭证注入、TLS/公网准备度、对象存储引用、state store 可恢复性和手机安全输出，避免把敏感信息或不可解释故障暴露给普通用户。

产品北极星保持不变：普通手机用户通过 4G 云中转控制小车完成 trash delivery，不接触 ROS2、SSH、串口、硬件参数或 raw JSON。本轮只做真实云前置 gate，不声明真实云、真实 4G、OSS/CDN、正式手机 UI、Nav2/fixed-route、WAVE ROVER 或 HIL 完成。

## 当前仓库证据

- `OKR.md` 2026-05-12 07:00 快照显示 O6 约 27%，O5 约 33%，O1/O2/O3/O4 更高；按“优先推进 OKR 完成度低的部分”，本轮选择 O6。
- `sprints/2026.05.12_06-07_remote-cloud-entry-docker-deploy/final.md` 确认 Docker relay 已达到 `software_proof_docker_deploy`，但真实云 HTTPS/TLS、公网入口、防火墙、production secret provisioning、OSS/CDN、真实 4G/SIM、生产 DB/queue 仍缺。
- 当前主机只有 Docker，可推进 O6 preflight/gate；不能补真实 HIL、真实 4G 或真实云实配证据。
- 近期 O6 链路已经有 relay service、bearer auth、file-backed persistence、phone-safe errors、Dockerfile/compose、`/healthz`、`/readyz` 和 Docker smoke；下一步应把这些能力收敛为上线前 gate，而不是继续堆宽泛测试。

## OKR 映射

| Objective | 本轮处理 |
| --- | --- |
| O6 4G 云中转 + OSS/CDN | 主线推进。把真实云上线前的配置、凭证、TLS/公网、OSS/CDN、state store、phone-safe 输出做成可执行 preflight gate。 |
| O5 手机体验与量产边界 | 只作为 phone-safe 输出支撑：确保未来手机端看到的是可解释状态和 retry hint，不暴露 token、OSS secret、ROS topic 或硬件参数。 |
| O1/O2/O3/O4 | 不作为本轮主线。无真实硬件、真实路线、真实相机、Nav2/fixed-route 实跑或 HIL，不能提升这些目标完成度。 |

## 上轮未完成项和本轮继承

- 真实云主机、域名、公网 HTTPS/TLS、防火墙策略仍未实配；本轮只检查配置是否准备好、缺什么、是否能给出阻断原因。
- production secret provisioning、rotate、最小权限账号仍未完成；本轮只做 env/schema/gate 和敏感字段泄露检查。
- OSS/CDN、STS、受限 AK、对象生命周期和 CDN 回源仍未真实验证；本轮只做配置 contract、URL/prefix 形态和不可用时的 phone-safe 阻断。
- production DB/queue、多实例一致性、备份和灾备仍未完成；本轮只验证 state store 配置、可写性、恢复边界和生产缺口提示。
- 06-07 Docker smoke 证明容器入口可运行；本轮 preflight gate 必须明确“ready to deploy prerequisites”与“真实生产已通过”不同。

## 本轮核心抓手

核心抓手是 O6 `remote_cloud_production_preflight_gate`：

1. 将 relay 的真实云上线前置项整理为一个可执行 gate。
2. Gate 至少覆盖配置完整性、bearer/secret 注入边界、TLS/公网入口准备度、OSS/CDN 配置形态、state store readiness 和 phone-safe 输出。
3. 输出必须 machine-readable + phone/operator-readable，能明确 `pass`、`blocked`、`warning` 和剩余证据缺口。
4. Docker-only 环境下允许 gate 因真实云/证书/OSS/生产 DB 未提供而返回 blocked；blocked 是正确结果，不得包装成真实云通过。
5. 验收只用少而准的 targeted checks，不新增宽泛测试矩阵。

## 做什么 / 不做什么

做：

- 创建 production preflight/gate 的产品和技术边界。
- 要求 Engineer 在后续实现中提供可执行 gate 或脚本/endpoint，输出配置、凭证、TLS/公网、OSS/CDN、state store、phone-safe 结果。
- 要求 gate 不泄露真实密钥、Authorization header、OSS AK/SK、root password、串口、baudrate、WAVE ROVER 参数、ROS topic 或底层速度入口。
- 要求当前 sprint 后续 `tech-done.md` 记录命令、输出摘要、失败定位和剩余风险。

不做：

- 不部署真实云主机，不申请或配置域名、公网 HTTPS/TLS、防火墙。
- 不接真实 4G/SIM，不做 carrier 或弱网实测。
- 不实现完整 OSS/CDN 上传链路、STS 发放、CDN 回源或生命周期策略。
- 不迁移生产 DB/queue，不做多实例一致性或灾备验证。
- 不做正式手机 UI、美观验收或普通用户实机验收。
- 不补 HIL、Nav2/fixed-route、WAVE ROVER 或真实送达证据。

## 优先级和验收口径

| 优先级 | 验收口径 |
| --- | --- |
| P0 配置 gate | 能检查生产必需 env/config 是否存在、是否为占位、是否可解释缺口。 |
| P0 凭证 gate | `.env.example` 只保留占位；输出不泄露 bearer token、OSS secret、Authorization header 或 root password。 |
| P0 TLS/公网 gate | 能区分 Docker local、TLS 未配置、公网入口未配置、防火墙未验证，且不把 local proof 当 production ready。 |
| P0 OSS/CDN gate | 能检查 bucket/region/prefix/CDN base URL/credential mode 是否成形；缺 STS/受限 AK 时返回 blocked 或 warning。 |
| P0 state store gate | 能检查 state store 配置、可写性、恢复边界，并明确 file-backed proof 不等于生产 DB/queue。 |
| P0 phone-safe 输出 | gate 输出适合手机/运维呈现，错误分类清晰且不暴露底层敏感信息。 |
| P1 文档同步 | 当前 sprint `tech-done.md` 必须记录实际命令和结果；涉及产品文档变更时再同步 `docs/product/`。 |

## 责任 Engineer

- `full-stack-software-engineer`：主责 production preflight/gate、配置/凭证/TLS/OSS/state/phone-safe 输出，以及后续必要文档同步。
- `robot-software-engineer`：支撑确认 robot client、ACK/cursor 和 conservative failure 语义不因 gate 引入而退化。
- `product-okr-owner`：负责 OKR 边界、验收口径、side-by-side acceptance、final 和必要 OKR 保守更新。

## 风险、阻塞和证据链缺口

- 本轮最高只能形成 `software_proof_docker_preflight_gate`。
- Gate blocked 不代表失败；如果真实云、证书、OSS/CDN 或生产 DB 未提供，blocked 是正确、可交付的风险拦截证据。
- Gate pass 也不等于真实云公网、HTTPS/TLS、防火墙、4G/SIM、OSS/CDN 实流量或生产 DB 已通过。
- O5 只能获得 phone-safe readiness 支撑；正式手机 UI 和普通用户验收不在本轮范围。
- O1/O2/O3/O4 不因本轮 preflight gate 提升。

## 需要创建或更新的 sprint 文档

- 本轮创建：`pre_start.md`
- 本轮前置必须创建：`prd.md`、`tech-plan.md`
- 实现后必须更新：`tech-done.md`
- 验收后必须更新：`side2side_check.md`、`final.md`

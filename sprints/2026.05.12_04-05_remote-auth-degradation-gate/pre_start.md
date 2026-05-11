# Sprint 2026.05.12_04-05 Remote Auth Degradation Gate - Pre Start

## 状态

- 阶段：pre_start
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主 Objective：O6 4G 云中转 + OSS/CDN 数据通路产品化
- 支撑 Objective：O5 手机用户体验与量产边界
- 证据边界：`software_proof_docker_only` / local mock cloud

## 用户价值和产品北极星

北极星仍是：普通用户只用手机，通过 4G 云中转控制小车送垃圾，并能看懂远程链路是否可用、为什么不可用、下一步该怎么处理。

本轮用户价值不是继续扩大 operator debug 功能，而是在真实云上线前补齐最小安全与降级口径：手机端不能看到 token、串口、ROS topic 或硬件参数；云端鉴权失败、云不可达、响应格式异常时，robot 侧必须给出 phone/cloud 可消费状态，不能误推进 cursor，也不能把 ACK 冒充真实送达结果。

## 当前证据

- `OKR.md` 2026-05-12 01:52 快照显示最低 Objective 是 O6 约 16%，其次 O5 约 31%；O1/O2/O3/O4 均约 74%-76%。
- `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/final.md` 已完成 local mock cloud persistence、remote bridge cursor recovery 和 phone-readable readiness，边界为 `software_proof_docker_only`。
- `sprints/2026.05.12_03-04_remote-cloud-persistence-and-phone-readiness/final.md` 指向下一步：O6 进入真实云前 server-side contract，包括 HTTPS/TLS、公网入口、生产 bearer/token rotate、部署配置、云端持久化和弱网恢复验证；O5 将 `remote_readiness` 接入正式手机状态页/异常提示。
- `sprints/2026.05.12_02-03_remote-4g-command-loop/final.md` 反复记录真实云部署、生产鉴权、OSS/CDN、弱网/断网恢复、正式手机 UI 仍未完成。
- 本机没有真实硬件、真实 4G/SIM 或公网云环境；O1/HIL 不能提升，本轮不能声明真实云、4G 或 HIL 通过。

## OKR 映射

| Objective | 本轮作用 | 不提升边界 |
| --- | --- | --- |
| O6 4G 云中转 + OSS/CDN | 主线推进 bearer auth gate、phone-safe remote readiness/degradation、cloud outage/auth failed/malformed response 的 ACK 与 cursor 安全语义 | 不声明真实 HTTPS/TLS、公网入口、SIM/4G、OSS/CDN、生产云部署或弱网实测完成 |
| O5 手机体验与量产边界 | 支撑手机端异常提示：普通用户能看懂远程不可用、鉴权失败、状态过期、等待 robot 状态、需要重试等状态 | 不声明正式美观手机 UI 或普通用户实机验收完成 |
| O1/O2/O3/O4 | 本轮不作为主目标 | 无真实硬件、真实 fixed-route/Nav2、真实相机或 HIL evidence packet，不提升完成度 |

## KR 拆解

| KR | 本轮抓手 | Owner |
| --- | --- | --- |
| O6 KR1 command/status/ack 契约 | local/mock cloud API 增加 bearer auth gate；remote_bridge 对云不可达、auth failed、malformed response 给出保守 ACK/status 语义 | `full-stack-software-engineer` + `robot-software-engineer` |
| O6 KR5 凭证管理 contract | 敏感信息过滤：状态、diagnostics、mock persisted state、phone payload 不得包含 bearer token、串口、ROS topic、硬件参数或云 URL 凭证 | `full-stack-software-engineer` |
| O6 KR6 graceful degradation | cloud outage/auth failed/malformed response 时不推进 cursor，不伪造 delivery result，状态可被手机解释 | `robot-software-engineer` |
| O5 KR1/KR5/KR7 手机可用流程 | `remote_readiness` 增加 phone-safe auth/degradation 字段，为正式手机状态页/异常提示提供 contract | `full-stack-software-engineer` |

## 本轮核心抓手

1. Full-stack owner 为 local/mock cloud API 补齐 bearer auth gate、phone-safe auth/remote readiness/degradation 字段、敏感信息过滤，并同步产品和接口文档。
2. Robot owner 为 `remote_bridge` 补齐 cloud outage / auth failed / malformed response 的 degraded status/ACK 语义，使它能把失败解释为 phone/cloud 可消费状态，不误推进 cursor，不冒充 delivery result。
3. 两条任务文件范围互不重叠，可以并行执行；最终集成只验证契约是否一致，不扩大到真实云、4G、HIL 或正式手机 UI。

## 做什么 / 不做什么

做：

- 在 local/mock cloud 与 remote bridge 的现有 O6 software proof 上继续向真实云前 contract 推进。
- 以 bearer auth gate、状态降级、cursor 安全和敏感信息过滤作为本轮最小可验证闭环。
- 更新 `docs/product/mobile_user_flow.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md`，确保 docs 与代码执行口径同步。
- 测试只做围栏：owner 各自 targeted unittest、`py_compile`、scoped `git diff --check`。

不做：

- 不写真实云部署脚本，不配置公网域名、TLS 证书、生产 token rotate 或云数据库。
- 不接 SIM/4G，不做弱网真实运营商测试。
- 不做 OSS/CDN 图片上传链路。
- 不做正式美观手机 UI 实现或普通用户实机验收。
- 不做 WAVE ROVER、UART、Nav2/fixed-route 实跑、相机或 HIL 验证。

## 优先级和验收口径

| 优先级 | 验收点 |
| --- | --- |
| P0 | bearer auth gate 启用时，缺失或错误 token 不能提交/读取受保护 command/status/ack；返回 phone-safe auth state |
| P0 | cloud outage/auth failed/malformed response 不推进 `last_terminal_ack_id`，不持久化 cursor，不声明 delivery result |
| P0 | remote readiness/degradation 字段能区分 `auth_required`、`auth_failed`、`cloud_unreachable`、`malformed_response`、`status_stale`、`ok` 等手机可读状态 |
| P0 | phone/status/diagnostics/mock state 不泄露 bearer token、串口设备名、ROS topic、baudrate、WAVE ROVER 参数或硬件配置 |
| P1 | 文档同步更新，明确 local/Docker proof 与真实云、4G、HIL 的边界 |

## 对应责任 Engineer

- `full-stack-software-engineer`：local/mock cloud API、operator gateway HTTP/status/diagnostics 的 auth/readiness/degradation 字段与文档同步。
- `robot-software-engineer`：`remote_bridge` cloud outage/auth failed/malformed response 的 ACK、status、cursor 安全语义与文档同步。

## 风险、阻塞和证据链

- 真实云、真实 4G/SIM、HTTPS/TLS、公网入口、生产鉴权 rotate、OSS/CDN 仍缺，不得把本轮结果写成 O6 生产完成。
- 本机无真实硬件和 `/dev/ttyUSB0`，O1/HIL 不提升。
- ACK 只代表 command envelope 被处理、失败或忽略，不代表垃圾送达、Nav2/fixed-route 成功或底盘运动完成。
- 若两个 owner 对 `remote_readiness` 字段命名不一致，最终集成必须优先修 contract，不允许手机端解析 raw exception。

## 需要创建或更新的 sprint 文档

本阶段创建并填写：

- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/pre_start.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/prd.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-plan.md`

执行完成后必须继续更新：

- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/tech-done.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/side2side_check.md`
- `sprints/2026.05.12_04-05_remote-auth-degradation-gate/final.md`

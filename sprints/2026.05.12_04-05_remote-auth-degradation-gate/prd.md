# Sprint 2026.05.12_04-05 Remote Auth Degradation Gate - PRD

## 状态

- 阶段：prd
- 创建时间：2026-05-12 Asia/Shanghai
- Product Owner：`product-okr-owner`
- 主 Objective：O6
- 支撑 Objective：O5
- 证据边界：`software_proof_docker_only`

## 用户价值和产品北极星

普通用户不关心 cloud API、ACK、cursor 或 bearer token；他们只需要知道手机是否还能安全控制机器人、机器人是否仍在线、如果远程链路不可用应该等待、重试还是转人工。本轮 PRD 的价值是把 remote control 从“能跑 local mock”推进到“失败时也可解释且不误报成功”。

产品北极星保持不变：普通用户只用手机，通过 4G 云中转控制小车送垃圾；手机和小车不要求同一 WiFi；远程入口不暴露 `/cmd_vel`、串口、ROS topic、硬件参数或密钥。

## 问题陈述

近期 O6 sprint 已证明 local mock command/status/ack、持久化和 cursor recovery，但仍有三个产品缺口：

1. auth 缺口：当前 local/mock contract 只表达 bearer token 字段，缺少明确的 auth required/auth failed 手机状态与敏感信息过滤验收。
2. degradation 缺口：cloud outage、auth failed、malformed response 需要变成 phone/cloud 可消费状态，而不是 raw exception 或 silent cursor advance。
3. 手机口径缺口：`remote_readiness` 需要覆盖 auth/degradation 字段，支持正式手机状态页和异常提示，而不是只服务 operator debug。

## OKR 映射

| OKR | 本轮产品要求 |
| --- | --- |
| O6 KR1 | command/status/ack 继续保持 `trashbot.remote.v1`，新增 bearer auth gate 与错误状态契约 |
| O6 KR5 | 凭证与敏感信息不进入 tracked 文件、persisted mock state、phone payload 或 diagnostics |
| O6 KR6 | 4G/云链路失败有 graceful degradation：状态可恢复、任务不丢、远程诊断能区分网络/鉴权/机器人问题 |
| O5 KR1/KR5/KR7 | 手机端能用普通语言展示远程 readiness、auth failure、cloud unreachable、status stale、command pending 等状态 |

## KR 拆解或更新

本轮不直接修改 `OKR.md` 的 KR 文本；只建立下一步可用于 O6/O5 保守提升的软件证据。

| 子目标 | 产品验收 |
| --- | --- |
| Auth gate | bearer gate 打开时，未授权请求返回稳定错误结构和 phone-safe `auth_state`；授权请求保持原 command/status/ack 语义 |
| Sensitive field filter | phone/status/diagnostics/persisted proof 不出现 bearer token、串口、ROS topic、baudrate、WAVE ROVER 参数或硬件配置 |
| Degradation status | cloud outage/auth failed/malformed response 被映射为稳定 machine-readable reason 与中文/英文 phone copy |
| Cursor safety | terminal ACK 只有成功提交到 cloud 后才推进/持久化 cursor；失败不误推进、不误报送达 |
| Docs sync | 手机流程、4G remote MVP、ROS contracts 明确软件证明边界与生产缺口 |

## 本轮核心抓手

核心抓手是 `remote_auth_degradation_gate`：在进入真实云部署、TLS、公网入口和生产 token rotate 前，先把 local/mock API 与 robot bridge 的鉴权失败和降级语义固定下来。

成功标准不是“云已上线”，而是工程团队可以在 Docker/local 环境中证明：

- 有 token gate。
- 有 phone-safe status。
- 有敏感信息过滤。
- 有云失败/鉴权失败/响应异常的保守处理。
- 有 cursor 不误推进的回归证据。

## 做什么 / 不做什么

做：

- Full-stack：为 local/mock cloud API 补 bearer auth gate、phone-safe auth/degradation/readiness 字段、敏感信息过滤。
- Robot：为 `remote_bridge` 补 cloud outage/auth failed/malformed response 的 degraded status/ACK 语义与 cursor safety。
- Docs：同步 `docs/product/mobile_user_flow.md`、`docs/product/remote_4g_mvp.md`、`docs/interfaces/ros_contracts.md`。
- Validation：只跑 targeted unittest、`py_compile`、scoped `git diff --check`。

不做：

- 不做真实云部署、公网 TLS、生产数据库、生产 token rotate。
- 不做正式手机 UI 页面实现，只定义 phone-safe contract。
- 不做真实 4G/SIM、弱网实测、OSS/CDN 上传。
- 不做硬件/HIL、Nav2/fixed-route 或真实送达验证。

## 优先级和验收口径

### P0 - Full-stack Owner

- `remote_readiness.auth_state` 至少能表达 `mock_not_required`、`required`、`authorized`、`auth_failed`。
- `remote_readiness.degradation_state` 至少能表达 `ok`、`status_stale`、`command_pending`、`auth_failed`、`cloud_unreachable`、`malformed_response`。
- 受保护 endpoint 在 bearer gate 开启时拒绝缺失/错误 token，并返回 phone-safe error payload。
- phone/status/diagnostics/mock persisted state 不泄露敏感字段。
- 文档说明这些字段只是 local/mock software proof，不证明真实云或 4G。

### P0 - Robot Owner

- `remote_bridge` 遇到 cloud outage 时发布/保留 degraded status，避免 raw exception 破坏轮询循环。
- `remote_bridge` 遇到 auth failed 时将 command envelope 处理为可解释失败状态，不推进 terminal cursor。
- `remote_bridge` 遇到 malformed command/status/ack response 时不提交本地 action、不推进 cursor、不伪造 ACK 成功。
- ACK 语义继续限定为 command-processing state，不代表 delivery result。

### P1 - Integration

- 两个 owner 的字段命名、状态枚举、phone copy/diagnostic reason 一致。
- 最终 smoke 可以同时覆盖 local/mock API auth/readiness 与 remote_bridge degradation，不需要真实云。

## 对应责任 Engineer

| Owner | 责任 |
| --- | --- |
| `full-stack-software-engineer` | local/mock cloud API、operator gateway HTTP/status/diagnostics、phone-safe payload、产品和接口文档 |
| `robot-software-engineer` | `remote_bridge` polling/ACK/status/cursor safety、robot-side degraded state、接口文档 |

## 风险、阻塞和需要补齐的证据链

- 真实云、4G、TLS、公网入口、生产鉴权 rotate、OSS/CDN 仍未验证。
- 本轮没有真实硬件，不得提升 O1/HIL。
- auth/degradation 字段如果只在文档中出现而无 targeted tests，不足以作为 O6 software proof。
- phone-safe copy 不能替代正式 UI；O5 只能记录状态 contract 支撑，不可声明美观手机端完成。
- 后续执行完成后，需要在 `tech-done.md` 写明实际 test logs、失败定位、剩余风险，并在 `side2side_check.md` / `final.md` 区分 software proof 与生产缺口。

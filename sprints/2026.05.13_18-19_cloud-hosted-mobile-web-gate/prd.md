# Sprint 2026.05.13_18-19 Cloud-hosted Mobile Web Gate - PRD

## 背景

当前 `mobile/web/` 已经是 dependency-free PWA 静态壳，包含首屏状态、操作确认、operation log、action feedback、cloud readiness、device/browser acceptance 等 phone-safe 面板。`mobile/README.md` 同时把正式入口描述为手机浏览器通过 `cloud-relay` 同源 `/api/*` 消费状态和诊断，但实际本地查看方式仍是独立静态 HTTP server。上一轮 O5 external evidence intake gate 已完成安全收件和 preflight consumption，但没有真实外部材料，不能继续重复 metadata-only 深度。

本轮 PRD 把正式手机入口向前推进一步：在 Docker/local `cloud-relay` 中托管 `mobile/web/` 静态壳，使用户打开 cloud-relay 根路径即可看到同一份 PWA，并用同源 API 继续走 phone-safe contract。

## 用户价值和产品北极星

产品北极星：普通手机用户只需要一个云中转入口，就能看到机器人状态、诊断、恢复建议和可用操作，不需要知道静态文件目录、ROS2 或机器人网络细节。

本轮用户价值：

- 将 PWA 从独立静态目录推进到 cloud-relay phone web shell。
- 为未来真实公网/4G/production app 留出同源入口形态。
- 证明打开手机页面只是静态 GET 和 phone-safe read，不会触发机器人动作或 ACK/cursor。

## OKR 映射

- Objective 5 KR1：云中转服务端最小契约保持 `trashbot.remote.v1` command/status/ack，不暴露 `/cmd_vel`、不接受 inbound 直连小车。本轮新增同源静态壳必须不改变这些语义。
- Objective 5 KR2：服务端基线与 Docker/local 入口需要能承载 phone web shell，为后续公网部署验收留接口形态。
- Objective 5 KR6：弱网和云阻塞状态需要继续 graceful degradation，PWA shell 缺少真实云/4G 时应显示 blocked/recovery copy，而不是开放主操作。
- Objective 4 KR1/KR5/KR7：手机最小流程、普通用户验收和美观可直接使用继续由 `mobile/web/` 承接；本轮支撑 O4，但不把 Docker/local 托管算作真实手机验收。

## KR 拆解或更新

本轮不直接修改 `OKR.md`，后续 closeout 可按实际证据判断是否微调：

- O5 KR1 子证据：cloud-relay 可以托管 PWA 静态壳，同时 `/api/*`、`/robots/*`、command/ACK 路由语义不变。
- O5 KR2 子证据：Docker/local cloud-relay smoke 可证明根路径或明确 phone shell 路径返回 PWA 入口。
- O5 KR6 子证据：没有真实外部材料时，PWA 仍展示 blocked/recovery，不声称 production-ready。
- O4 KR7 支撑证据：同一份 `mobile/web/` shell 被正式云中转入口消费，但真实手机设备/browser 和 production app 仍缺。

## 范围

必须做：

- cloud-relay 在 Docker/local 中服务 `mobile/web/` dependency-free 静态壳。
- 文档写清 cloud-relay hosted PWA 入口、运行方式、证据边界和非声明。
- remote bridge/protocol compatibility fence 证明静态 PWA GET 不触发 `collect`、`confirm_dropoff`、`cancel`、ACK POST、`last_ack_id` 或 persisted cursor。
- 保持 `/api/status`、`/api/diagnostics`、`/healthz`、`/readyz`、`/preflightz` 等既有读接口语义。

不做：

- 不接入真实公网、TLS、4G/SIM、OSS/CDN live traffic、production DB/queue。
- 不改真实机器人运动、Nav2/fixed-route、WAVE ROVER/HIL。
- 不新增 native app，不声明真实 iPhone/Android device 验收或真实 PWA install prompt。
- 不把 ACK、HTTP 200、静态页面可打开写成 delivery success。

## 优先级

- P0：cloud-relay hosted PWA shell 可在 Docker/local 打开，且 `/api/*` 控制面不被静态路由覆盖。
- P0：robot compatibility fence 证明静态 GET 和相关 metadata 不触发 command/action/ACK/cursor。
- P1：cloud-relay/mobile/product docs 同步，明确 `software_proof_docker_cloud_hosted_mobile_web_gate`。
- P2：后续 closeout 根据证据更新 `OKR.md` 和 sprint 收口文档。

## 验收口径

验收通过必须同时满足：

- Docker/local cloud-relay 可返回 PWA 静态入口，页面资产来自 `mobile/web/`，不引入 npm/build dependency。
- `/api/status`、`/api/diagnostics` 继续是 phone-safe JSON；静态托管不吞掉 API 路由。
- `GET /` 或指定 PWA 路径不创建 command、不 POST ACK、不推进 `last_ack_id`、不持久化 `last_terminal_ack_id`。
- 有明确测试或 smoke 输出证明 command/status/ACK envelope 未扩大。
- 文档同步到 cloud-relay docs、mobile docs 和接口/产品文档中相关位置。
- 证据边界仅为 `software_proof_docker_cloud_hosted_mobile_web_gate`；不声明真实云、真实公网 TLS、真实 4G、真实手机设备、production app、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责 cloud-relay static PWA serving gate。
- `robot-software-engineer`：Task B，负责 remote bridge/protocol compatibility fence。
- `product-okr-owner`：阶段验收、OKR 映射和 sprint closeout。

## 风险和证据缺口

- 真实外部材料仍缺：公网/TLS、OSS/CDN、4G/SIM、production DB/queue 不在本轮证明范围。
- 真实手机仍缺：本轮最多是 Docker/local hosted web shell，不是 iPhone/Android 设备验收。
- API 路由冲突风险：静态文件 fallback 必须避开 `/api/*`、`/robots/*`、`/healthz`、`/readyz`、`/preflightz`。
- 安全语义风险：静态页面 GET 不能被 bridge 当成 command metadata，也不能产生 ACK/cursor 副作用。

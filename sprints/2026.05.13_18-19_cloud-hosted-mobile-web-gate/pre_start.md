# Sprint 2026.05.13_18-19 Cloud-hosted Mobile Web Gate - Pre-start

## Sprint 类型

- `sprint_type: epic`
- 时间窗口：2026-05-13 18:00-19:00 Asia/Shanghai
- 主目标：Objective 5 云中转 + OSS/CDN 数据通路产品化
- 支撑目标：Objective 4 手机用户体验与低成本量产边界

## 用户价值和产品北极星

北极星仍是让普通手机用户不接触 SSH、ROS2、串口或本地文件，就能通过正式手机入口发起、查看和恢复送垃圾任务。本轮不继续堆 metadata-only readiness 深度，而是把已有 `mobile/web/` dependency-free PWA 从“独立静态文件”推进到 `cloud-relay` same-origin 托管壳，缩短正式手机入口与云中转控制面的距离。

用户价值：

- 手机入口不再只靠 `cd mobile/web && python3 -m http.server` 的本地静态查看方式。
- `cloud-relay` Docker/local 入口可以服务同一份 PWA 静态壳，并继续通过同源 `/api/*` 消费 phone-safe status/diagnostics。
- PWA 静态 GET 必须被证明不会触发 command/action/ACK/cursor，避免把“打开页面”误变成机器人控制动作。

## 推荐理由和证据

- `OKR.md` 4.1 显示 Objective 5 约 67%，低于 Objective 4 约 70%、Objective 1 约 75%、Objective 2/3 约 77%，是当前最低 Objective。
- 上一轮 `sprints/2026.05.13_17-18_o5_external-evidence-intake-gate/final.md` 明确：external evidence intake gate 已完成，但没有真实外部材料，O5 不上调；下一步若外部材料仍不可用，应避免继续重复本地 metadata 深度。
- `docs/product/mobile_user_flow.md` 已写明 `mobile/web/` 是 dependency-free phone PWA consumer，现有证据仍是 local/static/Docker 边界，不等于真实手机、production app、真实云或 4G。
- `mobile/README.md` 写明正式手机入口应通过 `cloud-relay` 使用同源 `/api/*`，但“当前 mobile/web 入口”仍以独立静态目录方式查看，cloud-relay 托管入口尚未形成可验证 gate。
- 当前主机是 macOS + Docker-only，无真实硬件、无真实公网、无真实 4G/SIM、无真实手机设备验收；本轮必须严格声明 `software_proof_docker_cloud_hosted_mobile_web_gate`，不能冒充 production app、真实云或真实手机。

## 上轮未完成项和阻塞

- 未完成：真实 OSS/CDN live traffic、真实 HTTPS/TLS 公网入口、真实 4G/SIM、production DB/queue connectivity、真实手机设备/browser、production app。
- 本轮主动避开：没有真实外部材料时，不继续加 external evidence metadata-only 深度。
- 本轮可推进：让 `cloud-relay` Docker/local 服务 `mobile/web/` 静态壳，并补 robot compatibility fence。

## 本轮核心抓手

以“cloud-relay same-origin phone web shell”为本轮抓手：

- Task A 由 `full-stack-software-engineer` 实现 cloud-relay static PWA serving gate。
- Task B 由 `robot-software-engineer` 补 remote bridge/protocol compatibility fence，证明静态 PWA GET 不扩大 robot command envelope。
- Product closeout 后续再更新 `OKR.md`、`tech-done.md`、`side2side_check.md`、`final.md`，并保持证据边界不虚增。

## 责任 Engineer

- `full-stack-software-engineer`：cloud-relay 静态托管、Docker/local smoke、cloud-relay/mobile docs。
- `robot-software-engineer`：remote bridge/protocol compatibility fence、ROS contract 文档、ACK/cursor 非触发证明。
- `product-okr-owner`：本 sprint 规划、验收口径、后续 OKR 与收口文档。

## 风险、阻塞和证据链

- 风险：静态托管若与 `/api/*`、`/robots/*`、command/ACK 路由冲突，可能扩大云中转控制面。
- 风险：PWA GET 被误写入 bridge metadata 或 status/ACK，可能污染 robot command envelope。
- 阻塞：无真实公网、TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、真实手机设备/browser、WAVE ROVER/HIL。
- 必须补齐证据：Docker/local GET PWA shell 成功、同源 API 路由仍保留、静态 GET 不触发 collect/confirm/cancel/ACK/cursor、文档明确非声明边界。

## 需要创建或更新的 sprint 文档

本任务创建：

- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/pre_start.md`
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/prd.md`
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/tech-plan.md`

后续实现与 Product closeout 必须继续创建或更新：

- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/tech-done.md`
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/side2side_check.md`
- `sprints/2026.05.13_18-19_cloud-hosted-mobile-web-gate/final.md`

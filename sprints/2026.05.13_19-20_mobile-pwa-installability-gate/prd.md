# Sprint 2026.05.13_19-20 Mobile PWA Installability Gate - PRD

## 用户价值和产品北极星

用户价值：普通用户未来只需要打开云中转入口，就能进入同一份手机 PWA；在真实手机、真实公网和 production app 还没闭环前，工程团队和售后支持至少可以用 Docker/local cloud-hosted URL + 本地 Chromium-family browser 证明这份入口具备安装型 PWA 的关键静态条件、离线壳边界和 fail-closed 手机控制面。

产品北极星：`rober` 是一台面向普通手机用户的低成本 ROS2 自主垃圾投递机器人。手机入口必须可安装、可解释、可交接、默认安全，而不是要求用户理解 ROS2、SSH、串口、命令行或云端内部 route。

## OKR 映射

- Objective 4 KR1：手机端最小流程继续以 `mobile/web/` 作为主入口，保持选择/确认垃圾站、确认放入垃圾、一键发车、状态查看、异常处理的 phone-safe 模型。
- Objective 4 KR5：普通用户不接触命令行、ROS2 或硬件知识，也能理解当前手机入口为什么可以看、为什么不能发车。
- Objective 4 KR7：推进手机端 UI 的 browser/PWA acceptance 证据，覆盖 manifest、service worker、offline shell、touch/browser gate 和 fail-closed 主操作。
- Objective 5 KR1/KR6：沿用 cloud-relay same-origin 托管能力，但本轮只作为 O4 手机入口承载面，不新增真实云、4G、OSS/CDN 或 production DB/queue claim。

## KR 拆解或更新

本轮不直接修改 `OKR.md`，只定义后续 closeout 的 KR 判定口径：

- KR4.7-a：cloud-hosted PWA installability gate 能从 cloud-relay URL 读取 manifest、service worker、offline shell、icon 和主页面，并输出机器可读 evidence summary。
- KR4.7-b：gate 验证 service worker 不缓存、不排队、不重放 `/api/*`、`/robots/*`、commands、ACK、diagnostics 和非 GET 控制请求。
- KR4.7-c：browser acceptance bundle 中保留 `software_proof` 证据边界和 `not_proven` 列表，明确不是真实手机设备、不是真实 PWA install prompt、不是真实送达。
- KR4.7-d：robot compatibility fence 证明 PWA installability/browser metadata 是 metadata-only，不会触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance 或 terminal cursor persistence。

## 本轮核心抓手

核心抓手是 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`：

- 在 cloud-relay hosted PWA 上建立 installability/browser acceptance gate，而不是继续新增本地 O5 readiness metadata。
- gate 只围栏关键用户路径：manifest、service worker、offline shell、asset route、first-screen fail-closed、ACK copy、browser evidence bundle。
- Robot 侧只做 metadata-only compatibility fence，不改真实 command contract。

## 需要做什么

### Task A：Full-stack cloud-hosted PWA installability/browser gate

责任人：`full-stack-software-engineer`

需要交付：

- 新增或扩展一个围栏脚本，用 cloud-relay Docker/local hosted URL 验证 `mobile/web/` PWA installability metadata。
- 验证 `manifest.webmanifest` 至少包含 `name`、`short_name`、`start_url`、`scope`、`display`、`theme_color`、`background_color`、icons 和 evidence boundary。
- 验证 service worker 静态 shell 只覆盖 HTML/CSS/JS/manifest/icons/offline shell，并对 `/api/*`、`/robots/*`、commands、ACK、diagnostics、非 GET 控制请求保持 no-store 或 network-only。
- 验证 offline shell 没有 Start/Confirm/Cancel 可用状态，不缓存或重放控制请求。
- 输出 evidence summary 到本 sprint `evidence/` 目录，边界为 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`。
- 更新 `docs/product/mobile_user_flow.md` 与 `mobile/README.md`，把本 gate 的能力和非能力写清楚。

### Task B：Robot metadata-only compatibility fence

责任人：`robot-software-engineer`

需要交付：

- 在 remote bridge/protocol 测试中加入 `cloud_hosted_mobile_pwa_installability_gate`、`pwa_installability_metadata`、`browser_installability_bundle` 等 metadata-only response 样本。
- 证明这些 metadata-only 字段不会触发 collect、confirm_dropoff、cancel。
- 证明不会 POST ACK，不推进 in-memory `last_ack_id`，不持久化 `last_terminal_ack_id`，不写 cursor override。
- 保留 valid collect command mixed metadata 的行为：只执行 command envelope，metadata 仍不改变 command/ACK/cursor 语义。
- 更新 `docs/interfaces/ros_contracts.md`，明确 installability/browser metadata 是手机/支持证据，不是 robot command、ACK、cursor 或 delivery success。

### Task C：Product closeout

责任人：`product-okr-owner`

需要在 A/B 返回后执行：

- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 如证据成立，更新 `OKR.md` 与 `docs/process/okr_progress_log.md`；建议只谨慎上调 Objective 4，不上调 Objective 5，除非 A/B 返回了真实外部 O5 材料。
- 明确证据边界：Docker/local cloud-hosted browser/PWA software proof，不是真实手机设备、不是真实 PWA install prompt、不是真实生产 app。

## 优先级和验收口径

优先级：

1. P0：manifest、service worker、offline shell 和 hosted route gate 机器可验收。
2. P0：Start/Confirm/Cancel fail-closed 与 ACK copy 不被 installability 证据误开。
3. P0：robot metadata-only compatibility fence 通过。
4. P1：文档同步，避免 `docs/product/mobile_user_flow.md` 落后于代码。

验收口径：

- 通过 targeted unittest、py_compile、browser/installability gate 和 scoped `git diff --check`。
- 不要求 broad regression、不要求真实手机、不要求真实硬件、不要求真实公网。
- 所有输出必须保留 `software_proof` 边界和 `not_proven` 列表。

## 风险、阻塞和证据链缺口

- 本机只有 Docker 和本地浏览器，无法证明真实 iPhone/Android device behavior。
- 没有真实 HTTPS/TLS、公网入口或 4G/SIM，不能证明 production PWA install prompt。
- 没有真实 OSS/CDN live traffic 或 production DB/queue，Objective 5 不应因本轮上调。
- 没有 WAVE ROVER、串口、Nav2/fixed-route、真实投放或真实送达，本轮不碰 Objective 1/2/3 的实机缺口。
- ACK 仍只是 accepted/processing evidence，不是 delivery success。

## 需要创建或更新的 sprint 文档

本阶段已创建：

- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/pre_start.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/prd.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/tech-plan.md`

A/B 完成后必须继续创建或更新：

- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/tech-done.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/side2side_check.md`
- `sprints/2026.05.13_19-20_mobile-pwa-installability-gate/final.md`


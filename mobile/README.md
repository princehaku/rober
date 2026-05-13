# mobile/ — 用户手机 PWA / 触点入口

本目录是 `ros_rbs` 的 **用户手机端部署单位**：把机器人能力产品化成手机能操作、能看状态的入口。

> 当前状态：sprint `2026.05.13_03-04_mobile-web-entrypoint-gate` 已新增 `mobile/web/` dependency-free PWA 静态入口。证据边界是 `software_proof_docker_mobile_web_entrypoint_gate`，不等于真实手机设备、production app、真实云、4G、OSS/CDN、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_07-08_mobile-operation-log-gate` 在静态入口中新增 operation log 面板。证据边界是 `software_proof_docker_mobile_operation_log_gate`，只证明 local/Docker fixture 与 static smoke 可展示 phone-safe 最近事件、恢复提示和支持交接入口；不等于真实手机设备/浏览器、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_09-10_mobile-action-feedback-gate` 在静态入口中新增动作回执面板，并让 Confirm Dropoff / Cancel 携带 generic mobile action confirmation payload。证据边界是 `software_proof_docker_mobile_action_feedback_gate`，只证明 local/static fixture 与 targeted unittest 能展示提交状态、失败原因、恢复建议、client reference 和 ACK 语义；不等于真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_11-12_mobile-cloud-readiness-summary-gate` 在首屏新增“云中转状态”摘要。证据边界是 `software_proof_docker_mobile_cloud_readiness_summary_gate`，只证明 local/static fixture 与 targeted unittest 能展示 cloud/preflight/DB/queue 的 phone-safe 摘要、阻塞恢复建议和 ACK 语义；不等于真实手机设备/browser、production app、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_13-14_mobile-device-acceptance-readiness-gate` 在首屏新增“手机验收准备”摘要。证据边界是 `software_proof_docker_mobile_device_acceptance_readiness_gate`，只证明 local/static fixture 与 targeted unittest 能展示真实手机设备/browser、production app、PWA install prompt、offline、diagnostics 和 cloud gate 的 blocked-by-design 摘要；不等于真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_15-16_mobile-browser-acceptance-bundle-gate` 在首屏新增“浏览器验收包”摘要和复制入口。证据边界是 `software_proof_docker_mobile_browser_acceptance_bundle_gate`，只证明 local/static fixture 与 targeted unittest 能展示/复制 phone-safe browser acceptance bundle，并在 bundle blocked 时让 Start / Confirm / Cancel fail closed；不等于真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、Nav2/fixed-route、真实底盘运动、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_16-17_mobile-web-browser-proof-gate` 将真实 Chrome/Chromium browser acceptance gate 迁移到当前 `mobile/web/` 静态 PWA。证据边界是 `software_proof_docker_mobile_web_browser_proof_gate`，只证明本机 Chromium-family 浏览器可渲染 390x844 与 768x900 viewport、主操作 fail closed、Diagnostics/Support Handoff 与浏览器验收包可用、ACK 文案未变成送达成功、首屏无水平 overflow/不合理 overlap、可见文案不泄漏敏感或机器人内部细节；不等于真实 iPhone/Android device、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_18-19_cloud-hosted-mobile-web-gate` 让 cloud-relay HTTP runtime 托管同一份 `mobile/web/` PWA 静态壳，并提供 phone-safe `/api/status` 与 `/api/diagnostics` fail-closed adapter。证据边界是 `software_proof_docker_cloud_hosted_mobile_web_gate`，只证明本地/Docker relay 可返回静态 shell、同源只读状态/诊断 adapter、API/probe 路由优先、missing static 和 traversal 返回 phone-safe 404；不等于真实公网、TLS、4G/SIM、真实手机设备/browser、production app、真实 PWA install prompt、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 用途（What lives here）

- **手机浏览器入口**（首选）：用户手机直连云端 `https://cloud-relay/api/*` 即可使用，不需要装 app、不需要 SSH、不需要懂 ROS2 topic。
- **未来 native app**（次选）：可基于本目录的 PWA 资产打包 Capacitor / Tauri / Cordova 等 native 壳，复用同一份 UI。

## 子目录

| 目录 | 用途 | P5 完成后承接 |
| --- | --- | --- |
| `mobile/web/` | PWA 前端静态资源 | 当前已有 `index.html` / CSS / JS / `manifest.webmanifest` / `service-worker.js` / `offline.html` / icons |
| `mobile/design/` | 设计稿、原型、phone-safe 中文文案 contract | Figma 链接、文案校对清单、可访问性规范 |
| `mobile/fixtures/` | 离线 fixture / 手机端浏览器验收用 mock 数据 | 当前 fixture 只用于 static smoke，必须显式标注 `fixture=true` |

## 部署目标（Deployment target）

- **设备**：CEO + 操作员的安卓 / iOS 手机浏览器。
- **网络**：手机端 4G / Wi-Fi → 公网 → `cloud-relay`（4C8G 公网部署单位）→ 机器人端 4G 反向连接。
- **运行环境**：现代浏览器（Chrome / Safari / Edge 最近 2 个大版本）；不依赖 native API，但优先利用 PWA 离线缓存 + service worker 提高弱网体验。

## 运行时契约（Runtime contracts）

- **消费方**：手机浏览器通过 `https://cloud-relay/api/*` 拉 phone-safe JSON。
- **schema**：`trashbot.phone_readiness.v1`、`trashbot.command_safety.v1`、`trashbot.phone_offline_resume_readiness.v1` 等字段、值域、`evidence_boundary` **完全由 `cloud-relay/` 维护**，mobile 端只消费、不发明。
- **错误语义**：所有失败必须有可读中文说明、错误码和恢复建议（"重试"、"等待机器人重新上线"、"联系管理员" 等），不允许吞掉错误。
- **控制动作**：所有发送到机器人的命令（如 `collect` / `confirm_dropoff`）必须有二次确认、视觉反馈、失败提示和可恢复路径；涉及真实运动的命令必须和 hardware/robot-engineer 对齐安全边界。

## 当前 mobile/web 入口

`mobile/web/` 是独立静态入口，不需要 npm、打包器或前端运行时依赖。最小本地查看方式：

```bash
cd mobile/web
python3 -m http.server 8088
```

然后打开 `http://127.0.0.1:8088/`。如果没有 operator gateway 提供 `/api/status` 和 `/api/diagnostics`，页面会进入离线/blocked 文案，Start Delivery、Confirm Dropoff、Cancel 保持禁用。

cloud-relay same-origin 查看方式：

```bash
PYTHONPATH=cloud-relay/src:onboard/src/ros2_trashbot_behavior \
TRASHBOT_REMOTE_CLOUD_BEARER_TOKEN=dev-token \
python3 -m ros2_trashbot_cloud_relay.remote_cloud_relay --host 127.0.0.1 --port 8088
```

打开 `http://127.0.0.1:8088/` 会返回 `mobile/web/index.html`，PWA assets 走同一 host；`/api/status` 和 `/api/diagnostics` 会返回 phone-safe blocked 摘要，其他未知 `/api/*`、`/robots/*`、`/healthz`、`/readyz`、`/preflightz`、commands 和 ACK 路由仍优先由 relay JSON/control handler 处理，不会被静态 fallback 覆盖。静态壳与这两个只读 phone API 不需要 bearer token；所有 command/status/ACK 路径仍保留原 bearer 与 `trashbot.remote.v1` 语义。

cloud-relay hosted phone API 规则：

- 默认 robot id 来自 `TRASHBOT_REMOTE_CLOUD_DEFAULT_ROBOT_ID`，否则为 `trashbot-001`。
- 如果 relay store 没有最近 `/robots/{robot_id}/status`，`/api/status` 返回 `state=status_missing`、`overall_status=blocked`，而不是 404。
- 如果 store 有最近 status，`latest_status` 只包含脱敏后的安全字段；主操作仍保持 fail closed。
- `/api/diagnostics` 包含同一 phone-safe summary、`cloud_hosted_mobile_web_gate`、安全 `latest_status`、`evidence_boundary=software_proof_docker_cloud_hosted_mobile_web_gate` 和 `not_proven`。
- 两个 API 都不得暴露 token、Authorization、DB/queue URL、本地路径、ROS topic、serial、WAVE ROVER、`/cmd_vel`、traceback 或 complete artifact。

当前入口消费这些既有字段：

- `/api/status.phone_readiness`
- `/api/status.phone_readiness.command_safety`
- `/api/status.phone_offline_resume_readiness` 或 `/api/status.phone_readiness.phone_offline_resume_readiness`
- 可选：`operation_log`、`phone_operation_log`、`phone_task_flow_readiness`、`phone_support_bundle`、`voice_prompt_readiness`
- 可选：`mobile_action_receipt`、`phone_action_feedback`
- 可选：`phone_cloud_readiness_summary`、`mobile_cloud_readiness_summary`、`cloud_readiness_summary` 或 `/api/status.phone_readiness.cloud_readiness`
- 可选：`mobile_device_acceptance_readiness`、`phone_device_acceptance_readiness`、`mobile_browser_acceptance_readiness` 或 `/api/status.phone_readiness.*_acceptance_readiness`
- 可选：`mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle` 或 `/api/status.phone_readiness.*_acceptance_bundle`
- `/api/diagnostics` 的脱敏摘要字段

云中转摘要规则：

- 首屏“云中转状态”只消费后端提供的 phone-safe 摘要，不展示完整配置、凭证、连接串、路径、traceback、校验材料或机器人硬件细节。
- 支持字段优先级为 `phone_cloud_readiness_summary`、`mobile_cloud_readiness_summary`、`cloud_readiness_summary`、`phone_readiness.cloud_readiness`。
- 摘要缺失时显示等待摘要，Start Delivery、Confirm Dropoff、Cancel 保持禁用；Diagnostics 和 Support Handoff 仍可用。
- `production_ready=false`、`overall_status=blocked` 或未显式 `primary_actions_enabled=true` 时，主操作继续 fail closed。
- `software_proof_docker_cloud_db_queue_config_gate` 只能作为上游 Docker/local 配置证明来源，不代表真实公网、真实 4G、production DB/queue、OSS/CDN live traffic、HIL 或真实送达。
- ACK 文案只能写成 accepted/processing evidence，不得写成真实云就绪、任务成功、投放完成、取消完成或机器人已运动。

手机验收准备规则：

- 首屏“手机验收准备”只消费后端或 diagnostics 提供的 phone-safe 摘要，不从静态 HTML、fixture smoke 或本地浏览器自行推断真实设备验收通过。
- 支持字段优先级为 `mobile_device_acceptance_readiness`、`phone_device_acceptance_readiness`、`mobile_browser_acceptance_readiness`，并兼容同名字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- 摘要缺失时返回 blocked 默认摘要，`evidence_boundary=software_proof_docker_mobile_device_acceptance_readiness_gate`，并明确缺真实手机设备/browser、production app 和真实 PWA install prompt。
- 面板展示 viewport/touch、PWA/offline、diagnostics/cloud gate、production app readiness、recovery hint、ACK 语义和 evidence boundary。
- Start Delivery、Confirm Dropoff、Cancel 只有在该摘要显式 `safe_to_control=true`，或同时满足 `primary_actions_enabled=true` 与 `production_app_ready=true` 时才可能继续通过后续 gate；否则 fail closed。Diagnostics 和 Support Handoff 仍可见。
- ACK 文案只能写成 accepted/processing evidence，不得写成真实手机验收通过、production app ready、delivery success、dropoff success 或 cancel completed。

浏览器验收包规则：

- 首屏“浏览器验收包”优先消费 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle`，并兼容这些字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- schema 为 `trashbot.mobile_browser_acceptance_bundle.v1`，`schema_version=1`，本地证据边界为 `software_proof_docker_mobile_browser_acceptance_bundle_gate`。
- Bundle 白名单字段为 `overall_status`、`production_app_ready`、`safe_to_control`、`viewport`、`touch_target`、`pwa_install_prompt`、`offline_shell`、`diagnostics`、`cloud_gate`、`action_gate`、`ack_semantics`、`client_timestamp`、`safe_phone_copy`、`recovery_hint`、`evidence_boundary`、`not_proven`。
- 缺少 bundle 时，前端只从既有 phone-safe readiness、cloud、offline 和 command_safety 字段派生 blocked 默认摘要；不能自行证明真实手机、真实浏览器、production app 或真实 PWA install prompt。
- Start Delivery、Confirm Dropoff、Cancel 只有在 bundle 显式 `safe_to_control=true`、`production_app_ready=true` 且 `overall_status!=blocked` 后才可能继续通过后续 gate；bundle blocked 或缺失时 fail closed。Diagnostics 和 Support Handoff 仍可用。
- 复制内容只包含脱敏白名单字段，不包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、serial、`/cmd_vel`、WAVE ROVER 参数、本地路径、traceback、checksum 或完整证据文件。
- ACK 文案只能写成 accepted/processing evidence，不得写成 delivery success、dropoff success、cancel completed、真实云就绪、HIL 或真实送达。

operation log 规则：

- 优先展示后端或 fixture 提供的 `operation_log` / `phone_operation_log`。
- 缺少显式日志时，只从既有 phone-safe 字段派生最小事件：`phone_readiness`、`command_safety`、`phone_task_flow_readiness`、`phone_offline_resume_readiness`、`phone_support_bundle`、`voice_prompt_readiness`。
- 派生事件只显示 `safe_phone_copy`、`recovery_hint`、`ack_semantics`、`next_action`、`support_level` 等安全摘要，不展示原始 JSON、ROS topic、硬件参数、凭证、路径、traceback、checksum 或完整 artifact。
- operation log 面板是只读解释入口，不会启用 Start Delivery、Confirm Dropoff 或 Cancel，也不会发送 ACK、推进 cursor 或声明 delivery success。

动作回执规则：

- 首屏动作回执面板展示最近一次用户动作、提交状态、失败/阻塞原因、恢复建议、`client_reference`、ACK 语义和 `evidence_boundary`。
- 面板优先消费后端或 fixture 的 `mobile_action_receipt` / `phone_action_feedback`。如果本地提交失败，则显示本地 `failed` / `blocked` copy；本地 copy 只说明手机提交层失败，不推断机器人执行状态。
- Start Delivery 继续使用 `schema=trashbot.mobile_task_start_confirmation.v1` body，并保留 destination 与 trash-loaded confirmation gate。
- Confirm Dropoff 和 Cancel 使用 `schema=trashbot.mobile_action_confirmation.v1`、`schema_version=1`、`source=mobile_web`、`action`、`user_confirmed=true`、`client_reference`、`client_timestamp`、`safe_phone_copy`、`ack_semantics`、`evidence_boundary=software_proof_docker_mobile_action_feedback_gate`。
- generic action payload 不包含 raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、token、Authorization header、OSS AK/SK、DB/queue URL、本地路径、完整 artifact 或 checksum。
- HTTP accepted、receipt 或 ACK 文案只能写成 accepted/processing evidence，不得写成 delivery success、dropoff success、cancel completed 或真实机器人动作完成。

按钮安全规则：

- `Start Delivery`、`Confirm Dropoff`、`Cancel` 默认禁用。
- 只有 `command_safety.actions.<action>.enabled=true` 且旧权限 `can_collect` / `can_confirm_dropoff` / `can_cancel` 同时允许时才启用。
- blocked、offline、pending ACK、manual takeover 等状态保持禁用。
- Diagnostics 和 Support Handoff 即使在主操作 blocked 时仍可打开或显示入口。

PWA / offline 边界：

- `service-worker.js` 只缓存静态 shell。
- `/api/*`、`/robots/*`、命令、ACK、diagnostics 和所有非 GET 请求都绕过缓存并使用 `no-store`。
- `offline.html` 只显示恢复提示；不会缓存、排队或重放控制请求，主操作全部禁用。
- `mobile/fixtures/mobile_web_status.fixture.json` 只用于静态 smoke，不是真实机器人状态。

## 当前 P1+P2B+PWA 状态

- `mobile/web/` 已有可运行静态入口和离线壳。
- `operator_gateway_static.py` 内嵌的 HTML/CSS/JS 仍留在 onboard `ros2_trashbot_behavior` 包内，作为本地 fallback；`mobile/web/` 是正式手机入口的静态部署单位。
- 手机端验收 gate：`pc-tools/evidence/phone_browser_acceptance_gate.py`（与本目录无 import 耦合，仅文档引用）。
- 当前新增 smoke：`PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint`。
- 当前真实本地浏览器 proof gate：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.13_16-17_mobile-web-browser-proof-gate/evidence
```

该 gate 自带轻量静态 HTTP server，直接服务 `mobile/web/`，并用 `mobile/fixtures/mobile_web_status.fixture.json` 响应 `/api/status` 与 `/api/diagnostics`。它通过 `--browser` 或 `PHONE_BROWSER_CHROME` 指向 Chromium-family 浏览器；成功后在 sprint `evidence/` 下写入 `mobile_web_browser_390x844.json/png`、`mobile_web_browser_768x900.json/png` 和 `mobile_web_browser_acceptance_summary.json`。summary 必须继续声明 `software_proof_docker_mobile_web_browser_proof_gate` 与非声明边界。

## Agent 工作纪律

- 修改本目录前必读 `AGENTS.md`、`OKR.md`、对应 sprint 文档；涉及 phone-safe schema 字段必读 `docs/interfaces/`（若有）和 cloud-relay 测试代码。
- UI 不得发明机器人状态：所有显示的字段必须来自 cloud-relay 输出的 phone-safe JSON，不允许前端 hardcode "模拟状态"。
- 控制按钮必须有确认、反馈、失败提示和可恢复路径。
- 中文注释比例 >20%，注释解释"为什么"而非"做什么"。

## 路线图（Roadmap）

| 阶段 | 工作 |
| --- | --- |
| 本 sprint P2B（当前） | README 脚手架 |
| cloud-relay gate | cloud-relay runtime 入口独立，mobile 继续只消费 phone-safe schema，不发明状态 |
| 当前 mobile-web-entrypoint gate | `mobile/web/` dependency-free PWA 入口、offline shell、manifest、service worker、fixture smoke |
| 当前 mobile-operation-log gate | `mobile/web/` operation log 面板、恢复提示、支持交接入口、fixture smoke |
| 当前 mobile-action-feedback gate | `mobile/web/` 动作回执面板、Confirm/Cancel generic confirmation payload、失败提示和 ACK 语义 fixture smoke |
| 当前 mobile-cloud-readiness-summary gate | `mobile/web/` 云中转状态摘要、blocked recovery、production_ready=false 和 ACK 语义 fixture smoke |
| 当前 mobile-device-acceptance-readiness gate | `mobile/web/` 手机验收准备摘要、blocked-by-design 真机/PWA/product app gate、primary action fail-closed |
| 当前 mobile-browser-acceptance-bundle gate | `mobile/web/` 浏览器验收包显示/复制、blocked-by-design 摘要、bundle 级主操作 fail-closed |
| 当前 mobile-web-browser-proof gate | `mobile/web/` 静态 PWA 的本机 Chromium-family 真实 browser proof、viewport 截图、JSON/summary evidence |
| 当前 cloud-hosted-mobile-web gate | cloud-relay 同源托管 `mobile/web/` 静态壳、API/probe 路由优先、静态路径围栏 |
| 下一个 sprint | 真实手机设备验收、production app、真实 PWA install prompt 和弱网体验 |
| 后续 | 远程控制安全边界（紧急停止、围栏、地理围栏）、native 壳打包 |

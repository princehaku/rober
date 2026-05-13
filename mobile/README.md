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
>
> 当前增量：sprint `2026.05.13_19-20_mobile-pwa-installability-gate` 新增 cloud-relay hosted PWA installability/browser gate。证据边界是 `software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`，只证明 Docker/local relay hosted URL 上的 manifest、icons、service worker 动静分离、offline shell、静态 assets、390x844/768x900 本机 Chromium-family 浏览器和 fail-closed 主操作；不等于真实 iPhone/Android device、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.13_20-21_mobile-primary-journey-gate` 将首屏组织成“目标垃圾站 -> 已放入垃圾确认 -> 发车安全 gate”的三步主路径。证据边界是 `software_proof_docker_mobile_primary_journey_gate`，只证明 Docker/local static fixture 与 targeted unittest 能渲染主路径 summary、保持 Start fail closed、提交 `/api/collect` 的 `target` 兼容 payload 且 ACK 仍是 accepted/processing；不等于真实手机设备/browser、production app、真实 PWA install prompt、真实送达、Nav2/fixed-route、WAVE ROVER 或 HIL。
>
> 当前增量：sprint `2026.05.13_21-22_mobile-recovery-decision-gate` 在三步主路径之后新增“恢复决策”首屏 panel。证据边界是 `software_proof_docker_mobile_recovery_decision_gate`，只证明 Docker/local static fixture 与 targeted unittest 能展示恢复状态、建议下一步、阻塞原因、支持入口、ACK 语义和 not_proven 边界；不等于真实手机设备/browser、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实 cancel completion、真实 dropoff completion 或真实送达。
>
> 当前增量：sprint `2026.05.13_22-23_mobile-terminal-action-confirmation-gate` 给 Confirm Dropoff / Cancel 增加“终端动作二次确认”panel。证据边界是 `software_proof_docker_mobile_terminal_action_confirmation_gate`，只证明 Docker/local static fixture 与 targeted unittest 能做到首次点击不提交 endpoint、用户显式确认后才提交 `trashbot.mobile_action_confirmation.v1` compatible payload、返回不提交、ACK 文案保持 accepted/processing only；不等于真实手机设备/browser、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff completion、真实 cancel completion 或真实 delivery。
>
> 当前增量：sprint `2026.05.13_23-24_mobile-device-evidence-capture-gate` 在首屏新增“手机设备证据采集”panel 和复制入口。证据边界是 `software_proof_docker_mobile_device_evidence_capture_gate`，只证明 Docker/local static fixture 与 targeted unittest 能采集/展示/复制 phone-safe viewport、touch target、display-mode/PWA、service worker/offline shell、client timestamp、ACK 语义和 `not_proven` 边界；不等于真实 iPhone/Android device、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
>
> 当前增量：sprint `2026.05.14_00-01_mobile-device-handoff-session-gate` 在首屏新增“真实手机验收交接会话”panel 和复制入口。证据边界是 `software_proof_docker_mobile_device_handoff_session_gate`，只证明 Docker/local static fixture 与 targeted unittest 能把当前入口 URL/摘要、session id、client reference、真实手机验收步骤、device/browser/PWA/install prompt/offline shell/touch target/viewport 观察项和 `mobile_device_evidence_capture` 引用整理成脱敏 handoff package；不等于真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
>
> 当前增量：sprint `2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate` 在首屏新增“PWA 安装提示证据”panel 和复制入口。证据边界是 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`，只证明 Docker/local static fixture 与 targeted unittest 能展示/复制 phone-safe install prompt capture metadata、user outcome、display-mode/installability/offline shell、manifest/service worker、production app readiness、safe-to-control、ACK 语义和 `not_proven`；不等于真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实用户安装选择、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
>
> 当前增量：sprint `2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh` 刷新当前 `mobile/web/` 的本地 Chromium-family browser proof。证据边界是 `software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`；它覆盖当前首屏的三步主路径、恢复决策、终端动作二次确认、手机设备证据采集、真实手机验收交接会话、PWA 安装提示证据、浏览器验收包、Diagnostics、Support Handoff 和 ACK 文案。旧 `software_proof_docker_mobile_web_browser_proof_gate` 作为兼容边界保留在 summary 中；文件名仍沿用 `mobile_web_browser_*`，但本轮只证明本机 Chromium 渲染当前 PWA，不等于真实 iPhone/Android、production app、真实 PWA install prompt、O5 外部材料、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
>
> 当前增量：sprint `2026.05.14_03-04_mobile-real-device-evidence-intake-gate` 在首屏新增“真实设备验收材料”intake panel。证据边界是 `software_proof_docker_mobile_real_device_evidence_intake_gate`，只证明 Docker/local static fixture 与 targeted unittest 能导入 JSON 摘要、用当前本地浏览器 metadata 生成 blocked-by-design package、输出 redacted phone-safe package，并保持 Start / Confirm / Cancel 不因本 gate 放行；不等于真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、Nav2/fixed-route、WAVE ROVER、HIL 或真实 delivery。
>
> 当前增量：sprint `2026.05.14_05-06_mobile-real-device-review-handoff-gate` 在首屏新增“真实设备评审交接”panel。证据边界是 `software_proof_docker_mobile_real_device_review_handoff_gate`，只证明 Docker/local static fixture 与 targeted unittest 能从 `mobile_real_device_acceptance_decision*` 派生或消费 `mobile_real_device_review_handoff*`，展示 reviewer checklist、decision status、review owner/status、evidence blocker、next required evidence、redaction status、source boundary、ACK-not-delivery 和 `not_proven`，并复制 phone-safe review handoff package；不等于真实设备验收通过、production app、真实 PWA install prompt/user choice、O5 外部 proof、HIL 或真实 delivery。
>
> 当前增量：sprint `2026.05.14_06-07_mobile-real-device-review-execution-gate` 在首屏新增“真实设备评审执行”panel。证据边界是 `software_proof_docker_mobile_real_device_review_execution_gate`，只证明 Docker/local static fixture 与 targeted unittest 能从 `mobile_real_device_review_handoff*` 派生或消费 `mobile_real_device_review_execution*`，展示 review execution checklist、review result/status、evidence items readiness、operator notes、reviewer notes、blocked reason、next evidence request、redaction status、source boundary、ACK-not-delivery 和 `not_proven`，并复制 phone-safe review execution package；不等于真实设备验收通过、production app、真实 PWA install prompt/user choice、O5 外部 proof、HIL 或真实 delivery。
>
> 当前增量：sprint `2026.05.14_07-08_mobile-real-device-retest-request-gate` 在首屏新增“真实设备复测请求”panel。证据边界是 `software_proof_docker_mobile_real_device_retest_request_gate`，只证明 Docker/local static fixture 与 targeted unittest 能从 `mobile_real_device_review_execution*` 派生或消费 `mobile_real_device_retest_request*`，展示 retest checklist、missing evidence list、每项材料 readiness/status、owner/next action、blocked reason、rejection reason、redaction status、source boundary、ACK-not-delivery 和 `not_proven`，并复制 phone-safe retest request package；不等于真实设备验收通过、production app、真实 PWA install prompt/user choice、O5 外部 proof、HIL 或真实 delivery。

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

cloud-relay hosted PWA installability/browser gate：

- 运行命令：`PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/cloud_hosted_pwa_installability_gate.py --output-dir sprints/2026.05.13_19-20_mobile-pwa-installability-gate/evidence`。
- gate 启动本地 `remote_cloud_relay`，只通过 hosted URL 拉取 `/`、`/index.html`、`/app.js`、`/styles.css`、`/manifest.webmanifest`、`/service-worker.js`、`/offline.html` 和 icons。
- manifest 必须保留 `name`、`short_name`、`start_url`、`scope`、`display=standalone`、theme/background color、icons、`evidence_boundary=software_proof_docker_mobile_web_entrypoint_gate`，并声明 `installability_evidence_boundary=software_proof_docker_cloud_hosted_mobile_pwa_installability_gate`。
- service worker 只缓存静态 shell；`/api/*`、`/robots/*`、commands、ACK、diagnostics 和非 GET 请求必须绕过缓存、使用 `no-store`，并且不能离线排队或重放。
- 成功后 evidence 目录包含 `cloud_hosted_pwa_installability_summary.json`、两个 viewport 的 JSON/PNG。summary 的 `not_proven` 必须继续列出真实手机设备、production app、真实 PWA install prompt、真实公网/4G、OSS/CDN、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 和真实送达。

当前入口消费这些既有字段：

- `/api/status.phone_readiness`
- `/api/status.phone_readiness.command_safety`
- `/api/status.phone_offline_resume_readiness` 或 `/api/status.phone_readiness.phone_offline_resume_readiness`
- 可选：`operation_log`、`phone_operation_log`、`phone_task_flow_readiness`、`phone_support_bundle`、`voice_prompt_readiness`
- 可选：`mobile_action_receipt`、`phone_action_feedback`
- 可选：`phone_cloud_readiness_summary`、`mobile_cloud_readiness_summary`、`cloud_readiness_summary` 或 `/api/status.phone_readiness.cloud_readiness`
- 可选：`mobile_device_acceptance_readiness`、`phone_device_acceptance_readiness`、`mobile_browser_acceptance_readiness` 或 `/api/status.phone_readiness.*_acceptance_readiness`
- 可选：`mobile_device_evidence_capture`、`mobile_device_evidence_capture_summary`、`mobile_device_evidence_package` 或 `/api/status.phone_readiness.mobile_device_evidence_*` 作为 phone-safe 设备证据采集包；缺失时前端只从当前浏览器采集白名单元数据，不能证明真实手机验收
- 可选：`mobile_device_handoff_session`、`mobile_device_handoff_session_summary`、`mobile_device_handoff_package` 或 `/api/status.phone_readiness.mobile_device_handoff_*` 作为 phone-safe 真实手机验收交接会话；它可引用 `mobile_device_evidence_capture`，但不能把 evidence capture 写成真实设备验收通过
- 可选：`mobile_pwa_install_prompt_evidence`、`mobile_pwa_install_prompt_evidence_summary`、`mobile_pwa_install_prompt_evidence_package` 或 `/api/status.phone_readiness.mobile_pwa_install_prompt_evidence*` 作为 phone-safe PWA 安装提示证据包；它可引用 handoff session、device evidence capture 和 browser acceptance bundle，但不能写成真实 PWA install prompt 通过
- 可选：`mobile_real_device_evidence_intake`、`mobile_real_device_evidence_intake_summary`、`mobile_real_device_evidence_package` 或 `/api/status.phone_readiness.mobile_real_device_evidence_*` 作为真实设备验收材料 intake；它只输出 redacted phone-safe package，不能写成真实设备验收通过或控制放行来源
- 可选：`mobile_real_device_acceptance_decision`、`mobile_real_device_acceptance_decision_summary`、`mobile_real_device_acceptance_decision_package` 或 `/api/status.phone_readiness.mobile_real_device_acceptance_decision*` 作为真实设备验收决策；它只说明材料是否可进入人工复核，不能写成验收通过
- 可选：`mobile_real_device_review_handoff`、`mobile_real_device_review_handoff_summary`、`mobile_real_device_review_handoff_package` 或 `/api/status.phone_readiness.mobile_real_device_review_handoff*` 作为真实设备人工评审交接；它可从 acceptance decision 派生 reviewer checklist、review owner/status、evidence blocker 和 next required evidence，但不能写成真实设备验收通过、O5 外部 proof 或控制放行来源
- 可选：`mobile_real_device_review_execution`、`mobile_real_device_review_execution_summary`、`mobile_real_device_review_execution_package` 或 `/api/status.phone_readiness.mobile_real_device_review_execution*` 作为真实设备人工评审执行记录；它可从 review handoff 派生 review execution checklist、review result/status、evidence items readiness、operator/reviewer notes、blocked reason 和 next evidence request，但不能写成真实设备验收通过、O5 外部 proof 或控制放行来源
- 可选：`mobile_real_device_retest_request`、`mobile_real_device_retest_request_summary`、`mobile_real_device_retest_request_package` 或 `/api/status.phone_readiness.mobile_real_device_retest_request*` 作为下一轮真实设备 retest request；它可从 review execution 派生 retest checklist、missing evidence list、material readiness/status、owner/next action、blocked/rejection reason、redaction/source boundary、ACK semantics 和 `not_proven`，但不能写成真实设备验收通过、O5 外部 proof 或控制放行来源
- 可选：`mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle` 或 `/api/status.phone_readiness.*_acceptance_bundle`
- 可选：`mobile_primary_journey_gate`、`mobile_primary_journey_summary` 作为 phone-safe 支持摘要；Start 是否允许仍由既有 destination、manual load confirmation、`command_safety`、cloud/device/browser readiness、operation log 和 action feedback 共同决定
- 可选：`mobile_recovery_decision_gate`、`mobile_recovery_decision_summary` 作为 phone-safe 恢复决策摘要；缺失时只能从既有 offline、command safety、operation log、action feedback、support handoff 和 primary journey 字段派生 blocked-by-design 摘要
- 可选：`mobile_terminal_action_confirmation_gate`、`mobile_terminal_action_confirmation_summary` 作为 phone-safe 终端动作确认摘要；缺失时 Confirm Dropoff / Cancel 仍只按本地 gate fail closed，不发明机器人状态
- `/api/diagnostics` 的脱敏摘要字段

三步主路径规则：

- 首屏“三步主路径”固定为：目标垃圾站、已放入垃圾确认、发车安全 gate。
- 目标垃圾站只能来自既有 phone-safe 字段：`phone_task_flow_readiness.destination_summary`、`destination_confirmed` step、`phone_readiness.destination`、`status.destination` 或 `/api/collect` 兼容所需 `target`。
- 已放入垃圾确认必须由用户手动勾选；页面不得写成自动载荷检测、自动称重或自动识别垃圾已放入。
- 发车安全 gate 必须同时消费 `phone_task_flow_readiness`、`command_safety`、cloud readiness、device/browser readiness、`operation_log` / `phone_operation_log`、`mobile_action_receipt` / `phone_action_feedback`。
- 缺少任一安全字段、`overall_status=blocked`、offline/unreachable、pending ACK、manual takeover / human help、missing destination、unchecked load confirmation 都 fail closed。
- `POST /api/collect` 保持 `target` 字段以兼容现有后端，同时使用 `evidence_boundary=software_proof_docker_mobile_primary_journey_gate`；ACK 文案只能表达 accepted/processing evidence，不能表达 delivery success、dropoff success、cancel completed、HIL 或真实送达。
- `mobile_primary_journey_gate` / `mobile_primary_journey_summary` 是手机/支持 summary metadata，不是 robot command、ACK、cursor、delivery success 或 production readiness grant。

恢复决策规则：

- 首屏“恢复决策”优先消费 `mobile_recovery_decision_gate` / `mobile_recovery_decision_summary`，并兼容这些字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- schema 为 `trashbot.mobile_recovery_decision_gate.v1`，本地证据边界为 `software_proof_docker_mobile_recovery_decision_gate`。
- 面板展示恢复状态、建议下一步、阻塞原因、支持入口、ACK 语义、evidence boundary 和 `not_proven` 摘要。
- 缺少显式恢复摘要时，前端只从既有 phone-safe 字段派生 blocked-by-design：`phone_offline_resume_readiness`、`command_safety`、`operation_log` / `phone_operation_log`、`mobile_action_receipt` / `phone_action_feedback`、`phone_support_bundle`、`mobile_primary_journey_gate` / `mobile_primary_journey_summary`。
- pending ACK、offline/status stale、manual takeover / human help、local submit failed、missing primary journey readiness、missing support handoff 都必须给出中文优先恢复建议，并保持 Start、Confirm、Cancel fail closed。
- 恢复决策 panel 是只读解释和支持交接入口，不发送 Start、Confirm、Cancel，不 POST ACK，不推进 cursor，不声明 delivery success、dropoff success、cancel completed、production readiness、HIL 或真实送达。
- ACK、receipt 或 HTTP accepted 只能写成 accepted/processing evidence；不能写成真实送达、真实投放完成、真实取消完成或机器人动作完成。

终端动作二次确认规则：

- Confirm Dropoff / Cancel 首次点击只打开“终端动作二次确认”panel，不调用 `/api/dropoff/confirm` 或 `/api/cancel`。
- Panel 必须展示 action、用户风险、ACK 语义、`not_proven`、`evidence_boundary=software_proof_docker_mobile_terminal_action_confirmation_gate`、`client_reference` 预览/确认引用，以及返回入口。
- 用户点击 panel 内“确认提交终端动作”后，才提交既有 endpoint；payload 继续使用 `schema=trashbot.mobile_action_confirmation.v1`、`schema_version=1`、`source=mobile_web`、`action`、`user_confirmed=true`、`client_reference`、`client_timestamp`、`safe_phone_copy`、`ack_semantics` 和 `evidence_boundary`。
- `safe_phone_copy` 必须中文优先，并明确 ACK/HTTP accepted 只是 accepted/processing evidence，不是 delivery success、dropoff success 或 cancel completed。
- 缺少 `command_safety`、动作级 `enabled` 不是 true、旧权限未放行、cloud/device/browser readiness 未放行、pending ACK、offline/stale、manual takeover / human help、blocked state 或最近回执 failed/blocked 时，确认入口 fail closed。
- 返回/取消只清除本地 pending 确认，不提交 endpoint，不 POST ACK，不推进 cursor，不声明机器人动作完成。
- `mobile_terminal_action_confirmation_gate` / `mobile_terminal_action_confirmation_summary` 是手机/支持 metadata，不是 robot command、ACK、cursor、delivery success、dropoff success、cancel completion、production readiness 或 HIL proof。

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

手机设备证据采集规则：

- 首屏“手机设备证据采集”panel 用于真实手机/browser/PWA 验收前复制 phone-safe evidence package，不是验收通过标志。
- 支持字段优先级为 `mobile_device_evidence_capture`、`mobile_device_evidence_capture_summary`、`mobile_device_evidence_package`，并兼容这些字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- schema 为 `trashbot.mobile_device_evidence_capture.v1`、`trashbot.mobile_device_evidence_capture_summary.v1`、`trashbot.mobile_device_evidence_package.v1`，本地证据边界统一为 `software_proof_docker_mobile_device_evidence_capture_gate`。
- 复制包白名单字段为 viewport CSS 尺寸、device pixel ratio、orientation、touch target 元数据、display-mode、manifest link、install prompt status、production app readiness、service worker/offline shell 状态、client timestamp、safe copy、recovery hint、ACK 语义、evidence boundary 和 `not_proven`。
- 复制包不得包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、serial、`/cmd_vel`、WAVE ROVER 参数、本地路径、traceback、checksum、完整证据文件、raw robot 响应或任何 robot/internal 技术字段。
- 缺真实手机/browser、production app、真实 PWA install prompt 时，Start Delivery、Confirm Dropoff、Cancel 继续依赖既有 readiness / acceptance bundle / command_safety fail closed；设备证据包本身不放行动作。
- ACK、HTTP accepted、receipt 或 evidence package 只能说明 accepted/processing 或可复现元数据，不得写成 delivery success、dropoff success、cancel completed、真实手机验收通过、HIL 或真实送达。

真实手机验收交接会话规则：

- 首屏“真实手机验收交接会话”panel 用于把真实手机验收交接所需信息整理给支持人员和验收人员，不是验收通过标志。
- 支持字段优先级为 `mobile_device_handoff_session`、`mobile_device_handoff_session_summary`、`mobile_device_handoff_package`，并兼容这些字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- schema 为 `trashbot.mobile_device_handoff_session.v1`，复制包 schema 为 `trashbot.mobile_device_handoff_package.v1`，本地证据边界统一为 `software_proof_docker_mobile_device_handoff_session_gate`。
- Panel 必须展示当前入口 URL 或安全入口摘要、`session_id`、`client_reference`、`mobile_device_evidence_capture` / `mobile_device_evidence_package` 引用、真实手机验收步骤清单、device/browser/PWA/install prompt/offline shell/touch target/viewport 观察项、ACK 语义、evidence boundary 和 `not_proven`。
- 复制包白名单字段为 session schema/version、session id、client reference、入口 URL/摘要、overall status、真实设备观察布尔值、production app readiness、真实 PWA install prompt 观察值、safe-to-control、观察清单、设备证据采集引用、设备观察摘要、浏览器验收包引用、safe copy、recovery hint、ACK 语义、evidence boundary 和 `not_proven`。
- 复制包不得包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、serial、`/cmd_vel`、WAVE ROVER 参数、本地路径、traceback、checksum、完整证据文件、raw robot 响应或任何 robot/internal 技术字段。
- `mobile_device_evidence_capture` 只能作为交接会话的输入引用，不能表述为真实手机设备、真实 browser、production app 或真实 PWA install prompt 已验收通过。
- Start Delivery、Confirm Dropoff、Cancel 只有在 handoff session 显式 `safe_to_control=true`、`real_device_observed=true`、`production_app_ready=true`、`pwa_install_prompt_observed=true` 且 `overall_status!=blocked` 后才可能继续通过后续 gate；缺失或 blocked 时 fail closed。
- ACK、HTTP accepted、receipt 或 handoff package 只能说明 accepted/processing 或支持交接 metadata，不得写成 delivery success、dropoff success、cancel completed、真实手机验收通过、HIL 或真实送达。

PWA 安装提示证据规则：

- 首屏“PWA 安装提示证据”panel 用于把 install prompt capture 与用户选择结果整理为 phone-safe evidence package，不是 PWA install prompt 通过标志。
- 支持字段优先级为 `mobile_pwa_install_prompt_evidence`、`mobile_pwa_install_prompt_evidence_summary`、`mobile_pwa_install_prompt_evidence_package`，并兼容这些字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- schema 为 `trashbot.mobile_pwa_install_prompt_evidence.v1`、`trashbot.mobile_pwa_install_prompt_evidence_summary.v1`、`trashbot.mobile_pwa_install_prompt_evidence_package.v1`，本地证据边界统一为 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`。
- Panel 必须展示 install prompt capture status、install prompt user outcome、display-mode、installability、offline shell、manifest/service worker、production app readiness、safe-to-control、ACK 语义、evidence boundary 和 `not_proven`。
- 复制包白名单字段为 schema/version、source、overall status、install prompt capture status、install prompt user outcome、display-mode、installability status、offline shell status、manifest present、service worker status、production app readiness、safe-to-control、`mobile_device_handoff_session` 引用、`mobile_device_evidence_capture` 引用、`mobile_browser_acceptance_bundle` 引用、safe copy、recovery hint、ACK 语义、evidence boundary 和 `not_proven`。
- 复制包不得包含 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、WAVE ROVER、本地路径、traceback、checksum、完整 artifact、raw robot response 或 robot/internal 技术字段。
- `mobile_device_handoff_session`、`mobile_device_evidence_capture` 和 `mobile_browser_acceptance_bundle` 只能作为引用，不能表述为真实 PWA install prompt 已通过。
- 缺真实手机/browser、production app 或真实 PWA install prompt capture/user outcome 时，Start Delivery、Confirm Dropoff、Cancel 继续依赖既有 readiness / acceptance bundle / handoff session / command_safety fail closed；install prompt evidence 本身不新增放行条件。
- ACK、HTTP accepted、receipt 或 install prompt evidence package 只能说明 accepted/processing 或支持复现 metadata，不得写成 delivery success、dropoff success、cancel completed、真实 PWA install prompt 通过、HIL 或真实送达。

真实设备验收材料 intake 规则：

- 首屏“真实设备验收材料”panel 用于导入真实 iPhone/Android、production app、PWA install prompt/user choice、截图摘要、URL 摘要和观察员备注的 JSON 摘要，也可用当前本地浏览器 metadata 生成 blocked-by-design package。
- 支持字段优先级为 `mobile_real_device_evidence_intake`、`mobile_real_device_evidence_intake_summary`、`mobile_real_device_evidence_package`，并兼容这些字段出现在 `phone_readiness` 或 `/api/diagnostics`。
- schema 为 `trashbot.mobile_real_device_evidence_intake.v1`、`trashbot.mobile_real_device_evidence_intake_summary.v1`、`trashbot.mobile_real_device_evidence_package.v1`，本地证据边界统一为 `software_proof_docker_mobile_real_device_evidence_intake_gate`。
- 输出包白名单字段为 device/platform、browser family/version summary、viewport、DPR、orientation、display-mode、PWA install prompt status/user choice、production app readiness/release summary、screenshot summary、URL summary、observer note、redaction status、ACK 语义、evidence boundary 和 `not_proven`。
- 导入和复制路径必须过滤 token、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifacts 和 raw robot response；命中敏感输入时只返回 blocked redaction failure summary。
- 本 gate 不新增控制放行条件；缺失、blocked 或 `not_proven` 时 Start、Confirm、Cancel 继续由既有 command_safety、cloud/device/browser readiness、handoff session、operation log 和 action feedback fail closed。

真实设备验收决策 gate 规则：

- 首屏“真实设备验收决策”panel 消费或派生 `mobile_real_device_acceptance_decision`、`mobile_real_device_acceptance_decision_summary`、`mobile_real_device_acceptance_decision_package`，输入来源是上一轮 `mobile_real_device_evidence_intake` / summary / package。
- schema 为 `trashbot.mobile_real_device_acceptance_decision.v1`、`trashbot.mobile_real_device_acceptance_decision_summary.v1`、`trashbot.mobile_real_device_acceptance_decision_package.v1`，本地证据边界为 `software_proof_docker_mobile_real_device_acceptance_decision_gate`，source boundary 必须保留 `software_proof_docker_mobile_real_device_evidence_intake_gate`。
- decision 只允许 phone-safe 三态：`accepted_for_review`、`blocked_missing_evidence`、`rejected_unsafe_or_unredacted`。`accepted_for_review` 只表示材料可进入人工复核，不表示真实手机验收、production app、PWA install prompt、HIL 或 delivery success 通过。
- 决策包白名单字段为 decision、accepted_for_review、safe_to_control=false、blocker list、next required evidence、redaction status、linked intake package 摘要、safe phone copy、recovery hint、ACK 语义、evidence boundary、source evidence boundary 和 `not_proven`。
- 缺 production app、真实 iPhone/Android device behavior、真实 PWA install prompt/user choice、脱敏截图摘要或 production HTTPS URL 摘要时，输出 `blocked_missing_evidence`；命中未脱敏或敏感字段时输出 `rejected_unsafe_or_unredacted`。
- 本 gate 不新增控制放行条件；Start、Confirm、Cancel 继续只由既有 command_safety、cloud/device/browser readiness、handoff session、operation log 和 action feedback fail closed。ACK、HTTP accepted、receipt、intake package 或 decision package 都不能写成 delivery success、dropoff success、cancel completed、真实设备验收通过或 production app ready。

真实设备 review handoff gate 规则：

- 首屏“真实设备评审交接”panel 消费或派生 `mobile_real_device_review_handoff`、`mobile_real_device_review_handoff_summary`、`mobile_real_device_review_handoff_package`，输入来源是上一轮 `mobile_real_device_acceptance_decision` / summary / package。
- schema 为 `trashbot.mobile_real_device_review_handoff.v1`、`trashbot.mobile_real_device_review_handoff_summary.v1`、`trashbot.mobile_real_device_review_handoff_package.v1`，本地证据边界为 `software_proof_docker_mobile_real_device_review_handoff_gate`，source boundary 必须保留 `software_proof_docker_mobile_real_device_acceptance_decision_gate`。
- 首屏必须展示 reviewer checklist、decision status、review owner/status、evidence blocker、next required evidence、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- review handoff package 白名单字段为 handoff/session schema、handoff session id、decision status、review owner/status、safe_to_control=false、evidence blocker、next required evidence、reviewer checklist、redaction status、linked acceptance decision 摘要、safe phone copy、recovery hint、ACK 语义、evidence boundary、source evidence boundary 和 `not_proven`。
- 复制包必须过滤 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact 和 raw robot response；命中敏感输入时只能显示 blocked/rejected 摘要。
- review handoff package 只表示人工评审交接，不是真实设备验收通过、真实 PWA install prompt、HIL、O5 外部 proof 或 delivery success。缺真实设备材料、production app 或真实 PWA install prompt/user choice 时，Start、Confirm、Cancel 必须继续 fail closed。

真实设备 review execution gate 规则：

- 首屏“真实设备评审执行”panel 消费或派生 `mobile_real_device_review_execution`、`mobile_real_device_review_execution_summary`、`mobile_real_device_review_execution_package`，输入来源是上一轮 `mobile_real_device_review_handoff` / summary / package。
- schema 为 `trashbot.mobile_real_device_review_execution.v1`、`trashbot.mobile_real_device_review_execution_summary.v1`、`trashbot.mobile_real_device_review_execution_package.v1`，本地证据边界为 `software_proof_docker_mobile_real_device_review_execution_gate`，source boundary 必须保留 `software_proof_docker_mobile_real_device_review_handoff_gate`。
- 首屏必须展示 review execution checklist、review result/status、evidence items readiness、operator notes、reviewer notes、blocked reason、next evidence request、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- review execution package 白名单字段为 execution/session schema、execution session id、handoff session id、decision status、review owner/status/result、safe_to_control=false、evidence items readiness、operator notes、reviewer notes、blocked reason、next evidence request、review execution checklist、redaction status、linked review handoff 摘要、safe phone copy、recovery hint、ACK 语义、evidence boundary、source evidence boundary 和 `not_proven`。
- 复制包必须过滤 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact 和 raw robot response；命中敏感输入时只能显示 blocked/rejected 摘要。
- review execution package 只表示人工评审执行记录，不是真实设备验收通过、真实 PWA install prompt、HIL、O5 外部 proof 或 delivery success。缺真实设备材料、production app 或真实 PWA install prompt/user choice 时，Start、Confirm、Cancel 必须继续 fail closed。

真实设备 retest request gate 规则：

- 首屏“真实设备复测请求”panel 消费或派生 `mobile_real_device_retest_request`、`mobile_real_device_retest_request_summary`、`mobile_real_device_retest_request_package`，输入来源是上一轮 `mobile_real_device_review_execution` / summary / package。
- schema 为 `trashbot.mobile_real_device_retest_request.v1`、`trashbot.mobile_real_device_retest_request_summary.v1`、`trashbot.mobile_real_device_retest_request_package.v1`，本地证据边界为 `software_proof_docker_mobile_real_device_retest_request_gate`，source boundary 必须保留 `software_proof_docker_mobile_real_device_review_execution_gate`。
- 首屏必须展示 retest checklist、missing evidence list、每项材料 readiness/status、owner/next action、blocked reason、rejection reason、redaction status、source boundary、ACK-not-delivery 和 `not_proven`。
- retest request package 白名单字段为 request/session schema、retest request id、execution session id、request status、review result/status、owner、next action、safe_to_control=false、material readiness、missing evidence list、blocked reason、rejection reason、retest checklist、redaction status、linked review execution 摘要、safe phone copy、recovery hint、ACK 语义、evidence boundary、source evidence boundary 和 `not_proven`。
- 复制包必须过滤 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact、raw robot response、raw intake JSON 或 robot/internal technical fields；命中敏感输入时只能显示 blocked/rejected 摘要。
- retest request package 只表示下一轮真实设备复测材料请求，不是真实设备验收通过、真实 PWA install prompt、HIL、Objective 5 外部 proof 或 delivery success。缺真实设备材料、production app、真实 PWA install prompt/user choice 或 Objective 5 外部材料时，Start、Confirm、Cancel 必须继续 fail closed。

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
- 当前终端动作二次确认 gate 会在用户显式确认后继续使用同一 `trashbot.mobile_action_confirmation.v1` compatible payload；本轮 payload 的 `evidence_boundary` 为 `software_proof_docker_mobile_terminal_action_confirmation_gate`，动作回执面板仍可显示后端或本地回执的 accepted/processing 语义。
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
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/evidence
```

该 gate 自带轻量静态 HTTP server，直接服务 `mobile/web/`，并用 `mobile/fixtures/mobile_web_status.fixture.json` 响应 `/api/status` 与 `/api/diagnostics`。它通过 `--browser` 或 `PHONE_BROWSER_CHROME` 指向 Chromium-family 浏览器；成功后在 sprint `evidence/` 下写入 `mobile_web_browser_390x844.json/png`、`mobile_web_browser_768x900.json/png` 和 `mobile_web_browser_acceptance_summary.json`。summary 的当前证据边界必须是 `software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`，同时保留旧 `software_proof_docker_mobile_web_browser_proof_gate` 作为兼容说明，方便读取旧 `mobile_web_browser_*` 文件名的流程不漂移。该 gate 只证明本机 Chromium-family browser 渲染当前 PWA，不是真实手机设备、production app、真实 PWA install prompt、O5 外部材料、真实机器人动作或真实送达。

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
| 当前 cloud-hosted-pwa-installability gate | cloud-relay hosted PWA manifest/SW/offline/assets/browser acceptance 软件证明 |
| 当前 mobile-primary-journey gate | 首屏三步主路径 summary、Start fail-closed gate、`/api/collect target` 兼容 payload |
| 当前 mobile-recovery-decision gate | 首屏恢复决策 summary、blocked/offline/pending ACK/manual takeover/local submit failed 的中文恢复建议 |
| 当前 mobile-terminal-action-confirmation gate | Confirm Dropoff / Cancel 首次点击不提交、终端动作 panel 二次确认、返回不提交、ACK 非成功语义 |
| 当前 mobile-device-evidence-capture gate | 首屏手机设备证据采集、phone-safe evidence package 复制、not_proven 边界和主操作 fail-closed |
| 当前 mobile-device-handoff-session gate | 首屏真实手机验收交接会话、phone-safe handoff package 复制、capture 引用和主操作 fail-closed |
| 当前 mobile-pwa-install-prompt-evidence gate | 首屏 PWA 安装提示证据、phone-safe install prompt evidence package 复制、not_proven 边界和主操作 fail-closed |
| 当前 mobile-current-pwa-browser-proof-refresh gate | 当前 `mobile/web/` 首屏 panels 的本机 Chromium-family browser proof refresh；保留旧 browser proof boundary 兼容说明 |
| 当前 mobile-real-device-evidence-intake gate | 首屏真实设备验收材料导入、redacted phone-safe package 复制、not_proven/redaction 边界和非控制放行 |
| 当前 mobile-real-device-retest-request gate | 首屏真实设备复测请求、phone-safe retest request package 复制、missing evidence/owner/next action 边界和非控制放行 |
| 下一个 sprint | 真实手机设备验收、production app、真实 PWA install prompt 和弱网体验 |
| 后续 | 远程控制安全边界（紧急停止、围栏、地理围栏）、native 壳打包 |

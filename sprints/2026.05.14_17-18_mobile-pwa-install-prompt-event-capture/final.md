# Sprint 2026.05.14_17-18 Mobile PWA Install Prompt Event Capture - Final

sprint_type: epic

## 收口结论

本轮完成 `mobile_pwa_install_prompt_event_capture*` 软件闭环：手机端 PWA 入口开始监听 `beforeinstallprompt`、`beforeinstallprompt.userChoice` 和 `appinstalled`，生成 whitelist-only 事件证据包；Robot 侧新增 metadata-only fence，确认该 family 不触发 collect/dropoff/cancel、ACK POST、cursor 持久化、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。

证据边界是 `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`。这不是真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice 现场验收、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。

## OKR 更新

- Objective 4：从约 93% 谨慎上调到约 94%。理由是事件监听、事件 evidence package、whitelist-only copy、Robot metadata-only fence 和 Task A/B 验证均已闭环，推进了真实 PWA prompt/user choice 的手机端准备能力。
- Objective 5：保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。
- Objective 1/2/3：不调整。本轮没有新增硬件协议、真实导航、任务闭环或 HIL 证据。

## O5 Stop Rule 回顾

`tech-plan.md` 的 OKR 最低优先级核对仍成立：Objective 5 仍是最低完成度，但当前运行环境没有真实外部 O5 材料。继续堆本地 O5 metadata 不会产生 O5 completion，因此本轮转向 Objective 4 的 PWA install prompt/user choice 事件捕获缺口是合理的。

下一轮如果仍拿不到真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration，就不应重复消费 O5 blocker；应继续推进 Objective 4 的真实手机设备、production app、真实 PWA prompt/user choice 现场材料，或切到其他低完成度且可执行的软件证据链。

## 验证结果

Task A：

- `mobile.test_mobile_web_entrypoint`：35 tests OK。
- `py_compile`：pass。
- `node --check mobile/web/app.js`：pass。
- required `rg`：pass。
- scoped diff check：pass。
- fixture/evidence JSON parse：pass。

Task B：

- targeted remote bridge/protocol unittest：`Ran 187 tests in 96.024s OK`。
- `py_compile`：pass。
- required `rg`：pass。
- scoped diff check：pass。

Task C：

```text
rg -n "mobile-pwa-install-prompt-event-capture|mobile_pwa_install_prompt_event_capture|software_proof_docker_mobile_pwa_install_prompt_event_capture_gate|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|full-stack-software-engineer|robot-software-engineer" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture
pass: OKR.md、docs/process/okr_progress_log.md 和本 sprint 文档均命中新 sprint、证据边界、Objective 4/5、owner 和安全口径。

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture
pass: no output
```

## 剩余风险

- `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy、Start/Confirm/Cancel fail closed 必须持续保留。
- 真实 PWA prompt/user choice 仍需要真实设备或 production app 现场材料证明；本轮只证明软件监听与包装能力。
- O5 仍缺真实外部证据，不能因本轮手机端事件捕获上调。

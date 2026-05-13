# Sprint 2026.05.14_01-02 Mobile PWA Install Prompt Evidence Gate - Tech Done

## Sprint 声明

- sprint_type: epic
- 收口时间：2026-05-14 01:15 Asia/Shanghai
- 目标 Objective：Objective 4 手机用户体验与低成本量产边界
- 统一证据边界：`software_proof_docker_mobile_pwa_install_prompt_evidence_gate`
- 本轮功能名：`mobile-pwa-install-prompt-evidence`

## A/B 证据核对结论

Task A Full-stack 已按计划完成 `mobile/web/` PWA 安装提示证据面板和 phone-safe copy package。实际改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

Task A 交付内容核对：

- PWA 安装提示证据 panel 已覆盖 install prompt capture status、user outcome、display-mode/installability/offline shell、manifest/service worker、production app readiness、safe-to-control、ACK 语义和 `not_proven`。
- copyable phone-safe package 已按 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate` 保持支持/交接 metadata 口径。
- fixture coverage 和 targeted unittest assertions 已覆盖该面板与复制边界。
- `docs/product/mobile_user_flow.md` 与 `mobile/README.md` 已同步说明 PWA install prompt evidence 的字段、步骤、边界和剩余缺口。
- 缺真实手机/browser、production app、真实 PWA install prompt 时，Start Delivery、Confirm Dropoff、Cancel 继续 fail closed。

Task A 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 22 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
pass
```

Task B Robot 已按计划完成 remote bridge/protocol metadata-only 围栏。实际改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task B 交付内容核对：

- `mobile_pwa_install_prompt_evidence`、summary、package metadata-only tests 已覆盖。
- metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success claim。
- metadata 与 valid command envelope 混合时，只执行 command envelope；install prompt evidence metadata 不进入 ACK/status。
- `docs/interfaces/ros_contracts.md` 已写清这些字段是 phone/support metadata，不是 command、ACK、cursor、delivery result、production readiness、HIL、真实 device proof、真实 PWA install prompt proof 或 Start/Confirm/Cancel 放行依据。

Task B 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 125 tests in 63.139s OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

## Product Closeout 实际改动

Task C Product closeout 更新以下文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-done.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/side2side_check.md`
- `sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md`

## OKR 调整

Objective 4 从约 77% 谨慎上调到约 78%。理由是本轮把 PWA install prompt evidence 从风险提示推进为 `mobile/web/` 首屏可见、可复制、可交接的 phone-safe software proof，并用 targeted unittest 与 robot metadata-only fence 证明该 metadata 不污染 command/ACK/status/cursor，也不放行 Start/Confirm/Cancel。

Objective 5 保持约 68%，不调整。理由是本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。PWA install prompt evidence 是 Objective 4 的手机/PWA support metadata，不是 O5 completion。

Objective 1/2/3 不调整。本轮未改硬件协议、WAVE ROVER、UART、Nav2/fixed-route、task_orchestrator、真实 dropoff/cancel 或真实 delivery 链路。

## 证据边界

本轮唯一可声明证据边界是 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`。

明确未证明：

- 真实手机设备。
- 真实 iPhone/Android device behavior。
- production app。
- 真实 PWA install prompt 或真实 user choice。
- 真实 public HTTPS/TLS。
- 4G/SIM。
- OSS/CDN live traffic。
- production DB/queue。
- Nav2/fixed-route。
- WAVE ROVER。
- HIL。
- 真实 dropoff/cancel completion。
- 真实 delivery。

ACK、HTTP accepted、receipt、evidence package、handoff、install prompt evidence 仍是 accepted/processing/support metadata only，不是 delivery success。

## Product 验收结果

```text
test -f sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-done.md && test -f sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/side2side_check.md && test -f sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md
pass

rg -n "software_proof_docker_mobile_pwa_install_prompt_evidence_gate|mobile-pwa-install-prompt-evidence|Objective 4|Objective 5|真实手机设备|真实 iPhone/Android|production app|真实 PWA install prompt|ACK|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-done.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/side2side_check.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md
pass
```

## 剩余风险

- 需要真实 iPhone/Android 设备或真实手机浏览器执行 PWA install prompt/user choice 验收，才能把 `not_proven` 迁出。
- 需要 production app 或真实部署入口证明，才能关闭 production app 缺口。
- 需要真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 worker/migration 材料，Objective 5 才能继续上调。
- 需要 Nav2/fixed-route、WAVE ROVER、HIL 与真实投放/取消/送达证据，才能推进真实交付闭环。

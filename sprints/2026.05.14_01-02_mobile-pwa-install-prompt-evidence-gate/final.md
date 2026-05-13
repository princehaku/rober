# Sprint 2026.05.14_01-02 Mobile PWA Install Prompt Evidence Gate - Final

## 结论

本 sprint 完成 `mobile-pwa-install-prompt-evidence`，证据边界为 `software_proof_docker_mobile_pwa_install_prompt_evidence_gate`。Task A/B 已完成，Product Closeout 已更新 `tech-done.md`、`side2side_check.md`、`final.md`、`OKR.md` 和 `docs/process/okr_progress_log.md`。

用户价值：PWA install prompt evidence 已从风险项推进为 `mobile/web/` 里可见、可复制、可交接的 phone-safe 软件证据面板。测试/支持人员可以围绕 install prompt capture status、user outcome、display-mode/installability/offline shell、manifest/service worker、production app readiness、safe-to-control、ACK 语义和 `not_proven` 判断下一步缺口。

## A/B 实际交付

Task A Full-stack 改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 22 tests ... OK
py_compile pass
node --check mobile/web/app.js pass
scoped git diff --check pass
```

Task B Robot 改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task B 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
Ran 125 tests in 63.139s OK
py_compile pass
scoped git diff --check pass
```

Task B 证明 `mobile_pwa_install_prompt_evidence`、summary、package 是 metadata-only；它们不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success claim。metadata 与 valid command 混合时，只执行 command envelope，不把 install prompt evidence metadata 编入 ACK/status。

## OKR 更新

Objective 4 从约 77% 谨慎上调到约 78%。理由是本轮把 PWA install prompt evidence 做成首屏可见的软件护栏、phone-safe package 和 robot metadata-only fence，直接推进 Objective 4 KR5/KR7 的手机验收解释能力。

Objective 5 保持约 68%。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料。PWA install prompt evidence 属于 Objective 4 的 phone/support metadata，不是 O5 云中转或 OSS/CDN productization proof。

Objective 1/2/3 不调整。本轮未改硬件协议、WAVE ROVER、UART、Nav2/fixed-route、task_orchestrator、真实 dropoff/cancel 或真实 delivery。

## 明确未证明

本轮未证明：

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

ACK、HTTP accepted、receipt、evidence package、handoff、install prompt evidence 和 terminal confirmation 都仍是 accepted/processing/support metadata only，不是 delivery success。

## Product 验收命令

```text
test -f sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-done.md && test -f sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/side2side_check.md && test -f sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md
pass

rg -n "software_proof_docker_mobile_pwa_install_prompt_evidence_gate|mobile-pwa-install-prompt-evidence|Objective 4|Objective 5|真实手机设备|真实 iPhone/Android|production app|真实 PWA install prompt|ACK|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate
pass

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/tech-done.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/side2side_check.md sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md
pass
```

## 剩余风险与下一步

- 若可获得真实外部材料，下一轮优先推进 Objective 5：真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。
- 若仍没有外部 O5 材料，下一轮应继续 Objective 4，把本轮 phone-safe PWA install prompt evidence package 带到真实 iPhone/Android 设备、production app 或真实 PWA install prompt/user choice 验收。
- HIL、WAVE ROVER、Nav2/fixed-route、真实 dropoff/cancel completion 和真实 delivery 仍需后续独立证据链。

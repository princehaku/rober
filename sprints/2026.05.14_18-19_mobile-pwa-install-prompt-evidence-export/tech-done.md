# Sprint 2026.05.14_18-19 Mobile PWA Install Prompt Evidence Export - Tech Done

sprint_type: epic

## 实际改动

Task A `full-stack-software-engineer` 已完成手机端 export 能力：

- `mobile/web/app.js`
- `mobile/web/index.html`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/evidence/task_a_mobile_pwa_install_prompt_evidence_export.md`

Task A 交付内容：

- 新增 `mobile_pwa_install_prompt_evidence_export*` 为 support/acceptance metadata。
- export input priority 为 explicit export -> event capture -> previous install-prompt evidence -> handoff/device/browser support metadata -> blocked-by-design fallback。
- copy/download 共用 whitelist-only JSON，固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`evidence_boundary=software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate` 和 `not_proven`。
- Start Delivery、Confirm Dropoff、Cancel 继续 fail closed；export/copy/download 不新增控制授权。

Task B `robot-software-engineer` 已完成 Robot metadata-only compatibility fence：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Task B 交付内容：

- 新增 `mobile_pwa_install_prompt_evidence_export*` metadata-only fence。
- 证明 metadata-only response 不触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed valid-command 场景仍只由合法 `trashbot.remote.v1` command envelope 决定 action/ACK/cursor；export metadata 不参与授权。

Task C `product-okr-owner` 收口改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/tech-done.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/side2side_check.md`
- `sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export/final.md`

`docs/product/mobile_user_flow.md` 已由 Task A 覆盖本轮用户可见 export 行为、schema、whitelist-only copy/download 和非控制授权边界；Task C 未重复扩写。

## 验证结果

Task A 验证：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 35 tests OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
OK

node --check mobile/web/app.js
OK

required rg
matched updated app, fixture, test, README, product flow docs

scoped git diff --check
OK
```

Task B 验证：

```text
targeted remote bridge/protocol unittest
Ran 191 tests OK

py_compile
OK

required rg
OK

scoped git diff --check
OK
```

Task C 收口验证：

```text
rg -n "mobile-pwa-install-prompt-evidence-export|mobile_pwa_install_prompt_evidence_export|software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|full-stack-software-engineer|robot-software-engineer" OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export

git diff --check -- OKR.md docs/process/okr_progress_log.md docs/product/mobile_user_flow.md sprints/2026.05.14_18-19_mobile-pwa-install-prompt-evidence-export
```

Task C 命令输出以最终聊天汇总为准。

## 偏差与边界

- 本轮证据边界统一为 `software_proof_docker_mobile_pwa_install_prompt_evidence_export_gate`。
- 本轮只证明 Docker/local mobile software proof 和 Robot metadata-only compatibility proof。
- 本轮不是真实 iPhone/Android device behavior、production app、真实 PWA prompt/user choice、Objective 5 external proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。
- Objective 4 可从约 94% 谨慎上调到约 95%；Objective 5 因没有真实外部证据，保持约 68%。

## 剩余风险

- 真实手机设备、production app、真实 PWA prompt/userChoice 现场验收仍未完成。
- Objective 5 仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration。
- 真实 Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery 仍未完成。

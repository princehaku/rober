# Sprint 2026.05.14_02-03 Mobile Current PWA Browser Proof Refresh - Tech Plan

## 总体方案

本 sprint 是 Epic，采用 A/B 并行、C 收口：

- Task A Full-stack：更新 current `mobile/web/` local browser proof gate，覆盖最新首屏面板并生成 evidence。
- Task B Robot：核对或补充 browser proof refresh metadata-only compatibility fence。
- Task C Product：A/B 返回后更新 `OKR.md`、`docs/process/okr_progress_log.md`、`tech-done.md`、`side2side_check.md`、`final.md`。

统一证据边界：`software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`。本边界只证明当前 `mobile/web/` PWA 的本地 Chromium-family browser software proof，不证明真实手机设备、production app、真实 PWA install prompt、O5 外部材料或真实 delivery。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5，而是针对 Objective 4：手机用户体验与低成本量产边界。
3. 不针对 Objective 5 的具体理由：`OKR.md` 第 6 节明确，Objective 5 completion 需要至少一种真实外部材料，包括真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration。当前本机只有 Docker，无真实硬件，也没有这些外部 O5 材料；继续推进本地 O5 metadata depth 会重复消费同一 blocker。
4. 转向 Objective 4 的证据依据：`sprints/2026.05.14_01-02_mobile-pwa-install-prompt-evidence-gate/final.md` 指出下一步应把 PWA/install prompt support evidence 带向真实设备或 production app 验收；在 Docker-only 主机上，当前可执行的前置步骤是刷新本地 Chromium browser proof，使其覆盖最新 PWA 首屏。

## Task A - Full-stack Current Browser Proof

Owner：`full-stack-software-engineer`

允许改动文件：

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/evidence/*`

实现要求：

1. 在 browser gate 中新增 current PWA refresh boundary：`software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate`，同时保留旧 `software_proof_docker_mobile_web_browser_proof_gate` 兼容说明。
2. Gate 必须验证当前首屏关键元素和文案，包括 primary journey、recovery decision、terminal action confirmation、device evidence capture、handoff session、PWA install prompt evidence、browser acceptance bundle、Diagnostics、Support Handoff 和 ACK copy。
3. Gate 必须继续检查 390x844 与 768x900 两个 viewport：无水平 overflow、无关键元素不合理 overlap、主操作 fail closed、phone-safe text 不泄漏敏感/硬件/机器人内部字段、44px hit area。
4. 成功输出 `mobile_web_browser_390x844.json/png`、`mobile_web_browser_768x900.json/png`、`mobile_web_browser_acceptance_summary.json` 到本 sprint `evidence/` 目录。
5. 更新 `mobile/test_mobile_web_entrypoint.py`，用静态断言保护 gate 覆盖最新 current PWA panels 和 refresh boundary。
6. 更新 `mobile/README.md` 与 `docs/product/mobile_user_flow.md`，写清 current proof refresh 只是 local Chromium proof，不是真实手机、production app 或真实 PWA prompt。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 pc-tools/evidence/phone_browser_acceptance_gate.py --output-dir sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/evidence
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py
git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh
```

输出要求：

- 实际改动文件列表。
- 上述命令关键输出。
- Browser gate 的 summary 状态、browser path、两个 viewport 结果和 evidence 文件列表。
- 失败定位与修复状态。
- 剩余风险，尤其是真实 iPhone/Android、production app、真实 PWA install prompt、O5 外部材料、真实 robot/delivery 未证明范围。

## Task B - Robot Compatibility Fence

Owner：`robot-software-engineer`

允许改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

生产 `remote_bridge` 代码默认禁止改，除非 targeted tests 证明必须最小修复。若不需要改代码，也必须在输出中说明现有 fence 是否覆盖 `mobile_current_pwa_browser_proof_refresh` metadata。

实现要求：

1. 检查现有 `mobile_web_browser_proof` / `phone_browser_proof` / `mobile_browser_proof_summary` metadata-only fence 是否足以覆盖 refresh boundary。
2. 如不足，新增 `mobile_current_pwa_browser_proof_refresh` / summary metadata-only tests。
3. 证明 metadata-only response 不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence 或 delivery success claim。
4. 证明 metadata 与 valid command envelope 混合时，只执行 command envelope，不把 browser proof refresh metadata 编入 ACK/status。
5. `docs/interfaces/ros_contracts.md` 必须写清 refresh metadata 是 phone/support proof metadata，不是 command、ACK、cursor、delivery result、production readiness、HIL、真实 device/browser proof 或 Start/Confirm/Cancel 放行依据。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

输出要求：

- 实际改动文件列表，或无代码改动时的明确核对结论。
- 上述命令关键输出。
- 若失败，给出失败定位和是否需要扩大生产代码范围。
- 剩余风险，尤其是本地 metadata fence 不证明真实 robot execution、Nav2/fixed-route、WAVE ROVER、HIL 或 delivery。

## Task C - Product Closeout

Owner：`product-okr-owner`

允许改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/tech-done.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/side2side_check.md`
- `sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/final.md`

执行条件：

Task C 只能在 Task A 和 Task B 都返回后执行。Product 必须核对 A/B 文件范围、验证输出、证据边界、evidence 目录和 `not_proven` 文案，再决定 Objective 4 是否谨慎上调。没有真实外部 O5 材料时，Objective 5 不上调。

验收命令：

```bash
test -f sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/tech-done.md && test -f sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/side2side_check.md && test -f sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh/final.md
rg -n "software_proof_docker_mobile_current_pwa_browser_proof_refresh_gate|mobile-current-pwa-browser-proof-refresh|Objective 4|Objective 5|真实 iPhone/Android|production app|真实 PWA install prompt|ACK|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_02-03_mobile-current-pwa-browser-proof-refresh
```

输出要求：

- A/B 证据核对结论。
- 实际改动文件列表。
- Product 验收命令关键输出。
- OKR 调整或不调整理由。
- 剩余风险和下一步建议。

## 并行启动要求

Task A 和 Task B 文件范围互不重叠，必须并行启动两个 `spawn_agent(agent_type=worker)`。Task C 不得与 A/B 并行；必须等 A/B 返回后再执行。

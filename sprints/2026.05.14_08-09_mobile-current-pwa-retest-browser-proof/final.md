# Sprint 2026.05.14_08-09 Mobile Current PWA Retest Browser Proof - Final

## 收口结论

- sprint_type: epic
- 本轮完成：`software_proof_docker_mobile_current_pwa_retest_browser_proof_gate`
- OKR 调整：Objective 4 从约 84% 保守上调到约 85%；Objective 5 保持约 68%；Objective 1/2/3 不调整。

## 用户价值和产品北极星

手机仍是普通用户唯一入口。本轮把“真实设备复测请求”从上一轮静态/单测层面的材料请求，推进到当前 `mobile/web` PWA 的本地 Chromium-family browser proof：支持/验收人员可以用截图与 JSON evidence 复查首屏关键面板、copy 行为、phone-safe 文案、ACK 非 delivery success 和 fail-closed 主操作。

这不是愿景交付，也不是 happy path 完成；它只补齐当前 PWA 变更后的浏览器可见证据，为后续真实 iPhone/Android、production app 和真实 PWA install prompt/user choice 验收准备对照材料。

## Task A/B 结果

- Task A Full-stack：更新 `pc-tools/evidence/phone_browser_acceptance_gate.py`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md` 和 sprint evidence；生成 `mobile_web_browser_390x844.json/png`、`mobile_web_browser_768x900.json/png`、`mobile_web_browser_acceptance_summary.json`。browser gate 输出 390x844 `passed=true`、768x900 `passed=true`、summary `ok=true`；`mobile.test_mobile_web_entrypoint` 28 tests OK；`py_compile` 与 scoped diff check pass。
- Task B Robot：更新 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`；新增 `mobile_current_pwa_retest_browser_proof*` protocol/worker 围栏和 mixed valid-command 场景。验证 `Ran 153 tests in 78.872s OK`；`py_compile` 与 scoped diff check pass。

## 首次失败和修复

- Task A 首次 browser gate 直接调用 `renderTerminalActionPanel()`，触发 out-of-scope `mobile/web/app.js` 内部路径 `ReferenceError: nextEvidence is not defined`。修复为 browser gate 只展开既有 DOM，不调用内部控制或提交路径，并复验通过。
- Task B 本轮 closeout 未报告未修复失败；Robot fence 验证已通过。

## OKR 最低优先级回顾

Objective 5 仍是当前最低 Objective（约 68%）。本轮没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或其他真实外部 O5 材料，因此继续 O5 本地 metadata depth 不能提升 completion。按 stop rule，本轮转向 Objective 4 的当前 PWA browser proof 缺口，并保持 O5 不调整。

## 证据边界和剩余风险

- `software_proof_docker_mobile_current_pwa_retest_browser_proof_gate` 只证明 Docker/local current PWA browser proof 和 robot metadata-only fence。
- `not_proven` 仍包括真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。
- 真实设备复测请求、browser proof、ACK、HTTP accepted、receipt、intake package、acceptance decision package、review handoff package、review execution package、retest request package、handoff session 和 install prompt evidence 仍只是 accepted/processing/support metadata，不是 delivery success。

## 下一步

下一轮优先按 `OKR.md` 4.1 重新排序。若仍拿不到 Objective 5 的真实外部材料，优先推进 Objective 4 的真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice 或主路径真实移动设备验收；若拿到 O5 外部材料，再回到公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration evidence。

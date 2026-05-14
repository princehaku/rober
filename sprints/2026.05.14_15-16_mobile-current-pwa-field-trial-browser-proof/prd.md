# Sprint 2026.05.14_15-16 Mobile Current PWA Field Trial Browser Proof - PRD

sprint_type: epic

## 用户价值和产品北极星

手机端是普通用户唯一入口。当前问题不是又缺一个新面板，而是当前 `mobile/web` PWA 首屏已经包含 field-trial package、review、runbook execution、evidence record、evidence verdict、retest execution 等完整材料链，但最近一次 current PWA browser proof 只到真实设备复测请求。没有更新的浏览器证据，Product、Support 和后续真实设备验收会缺少可对照的首屏截图、可见元素和 JSON summary。

本轮 PRD 的北极星是：用本地 Chromium-family browser proof 证明“当前 PWA 首屏组合可见、phone-safe、fail closed、copy/summary 边界正确”，同时明确它不是真实手机、production app、O5 外部云、HIL 或 delivery success。

## OKR 映射

- Objective 4：直接推进。KR1/KR5/KR7 对应手机最小流程、用户验收标准、主流尺寸适配和首屏可用性；本轮通过 390x844 与 768x900 browser proof 补证当前 PWA 可见体验。
- Objective 5：不推进 completion。当前仍缺真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 和 production worker/migration；本轮只记录 stop rule，避免继续堆本地 O5 metadata。
- Objective 1/2/3：不推进 completion。Robot 侧只围栏 metadata，不证明底盘、导航、任务闭环或真实投放。

## KR 拆解

1. KR-A：current PWA browser proof 覆盖完整 field-trial 首屏组合。
   - 必须覆盖 `mobile_real_device_field_trial_package*`。
   - 必须覆盖 `mobile_real_device_field_trial_review*`。
   - 必须覆盖 `mobile_real_device_field_trial_runbook_execution*`。
   - 必须覆盖 `mobile_real_device_field_trial_evidence_record*` 和 archive/copy 可见边界。
   - 必须覆盖 `mobile_real_device_field_trial_evidence_verdict*`。
   - 必须覆盖 `mobile_real_device_field_trial_retest_execution*`。
2. KR-B：browser proof 输出本 sprint `evidence/` 下两套 viewport artifact。
   - 390x844 JSON/PNG。
   - 768x900 JSON/PNG。
   - summary JSON 使用新边界 `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`。
3. KR-C：Robot metadata-only fence 覆盖 `mobile_current_pwa_field_trial_browser_proof*` family。
   - 证明 metadata 不触发 collect/dropoff/cancel。
   - 证明 metadata 不触发 ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
4. KR-D：产品和接口文档同步，且不扩大证据声明。
   - `mobile/README.md`、`docs/product/mobile_user_flow.md` 写清 local Chromium-family proof。
   - `docs/interfaces/ros_contracts.md` 写清 Robot metadata-only family 和 forbidden side effects。

## 范围边界

本轮要做：

- 更新 `pc-tools/evidence/phone_browser_acceptance_gate.py` 的 current evidence boundary 与 element expectations。
- 生成 sprint evidence artifact 到 `sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/evidence/`。
- 必要时更新 `mobile/test_mobile_web_entrypoint.py` 的现有边界/脚本断言，但不新增一堆测试。
- 更新 `mobile/README.md`、`docs/product/mobile_user_flow.md`。
- 新增或更新 robot metadata-only fence，并同步 `docs/interfaces/ros_contracts.md`。

本轮不做：

- 不新增一个新的 O4 metadata panel。
- 不继续增加 O5 本地 metadata rung。
- 不修改真实控制语义、ACK POST 语义、cursor persistence、terminal ACK 或 production readiness。
- 不声明真实手机设备、production app、真实 PWA install prompt/user choice、O5 外部 proof、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success。

## 优先级和验收口径

P0：Task A browser proof gate 必须通过，且 summary 明确 `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`。

P0：Task B robot metadata-only fence 必须通过，且 mixed valid-command 场景只能执行合法 `trashbot.remote.v1` command envelope，browser proof metadata 不改变 action、target、idempotency、ACK 或 cursor。

P1：产品文档必须同步，确保 Product/Support 不把 browser proof 或 retest execution package 误读为真实设备验收或 delivery success。

P2：如果现有 `mobile.test_mobile_web_entrypoint` 断言已覆盖主要边界，只允许做最小断言补齐；不要扩成大规模测试建设。

## 对应责任 Engineer

- `full-stack-software-engineer`：Task A，负责 mobile/web browser proof、evidence artifact、mobile 文档和必要的现有 mobile unittest 围栏。
- `robot-software-engineer`：Task B，负责 robot metadata-only fence、remote bridge/protocol 侧语义围栏和 ROS contract 文档。
- Product Owner：只负责本 planning、后续验收口径、sprint 留档和 OKR 边界复核，不写产品代码或测试代码。

## 风险、阻塞和证据链

- 证据链必须从 `OKR.md` 14:15 snapshot、14-15 final、08-09 browser proof final、current `docs/product/mobile_user_flow.md` 出发。
- 浏览器 proof artifact 是 local Chromium-family proof，不是手机真机 proof。
- Robot fence 是 software proof，不是 HIL 或真实控制 proof。
- Objective 5 的真实缺口仍等待外部材料；本轮 final 不应上调 O5。

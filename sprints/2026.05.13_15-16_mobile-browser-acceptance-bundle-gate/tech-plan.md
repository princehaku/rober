# Sprint 2026.05.13_15-16 Mobile Browser Acceptance Bundle Gate - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective：Objective 4，约 66%。Objective 5 在 `2026.05.13_14-15_oss-cdn-live-probe-gate` 后约 67%。
2. 本 sprint 是否针对该最低 Objective：是，主目标是 Objective 4 手机用户体验与低成本量产边界。
3. 具体理由：Objective 4 当前主要缺口是真实手机设备/browser、production app、真实 PWA install prompt 和普通用户验收证据。当前主机没有真实设备，因此本轮先把手机浏览器验收材料做成可复制、可脱敏、可 fence 的 Docker/local software gate；不声明真实手机或真实 PWA install prompt 完成。

## Team 分工

### Task A - Full-stack Mobile Browser Acceptance Bundle Gate

Owner：`full-stack-software-engineer`

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

目标：

- 在 mobile web 首屏增加“浏览器验收包/验收证据”能力。
- 能生成、显示或复制 phone-safe acceptance bundle，覆盖 viewport、touch、PWA/offline、diagnostics、cloud gate、action fail-closed、ACK 语义、client timestamp、evidence boundary 和 not-proven 摘要。
- 没有真实设备/browser、production app 或真实 PWA install prompt 时，bundle 必须 blocked-by-design；Start/Confirm/Cancel fail closed，Diagnostics/Support Handoff 可用。
- Bundle 不得包含 tokens、Authorization、OSS AK/SK、root password、DB/queue URL、ROS topics、serial、`/cmd_vel`、WAVE ROVER 参数、本地路径、traceback、checksum 或完整 artifact。

实现要求：

- 优先消费 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle`；缺失时从现有 phone-safe fields 派生 blocked 默认摘要。
- 建议 schema 使用 `trashbot.mobile_browser_acceptance_bundle.v1`，`schema_version=1`，`evidence_boundary=software_proof_docker_mobile_browser_acceptance_bundle_gate`。
- Bundle 至少包含：`overall_status`、`production_app_ready`、`safe_to_control`、`viewport`、`touch_target`、`pwa_install_prompt`、`offline_shell`、`diagnostics`、`cloud_gate`、`action_gate`、`ack_semantics`、`client_timestamp`、`safe_phone_copy`、`recovery_hint`、`not_proven`。
- UI 文案中文优先，明确 ACK 是 accepted/processing evidence，不是 delivery success。
- 不改变现有 command request schema；Start/Confirm/Cancel 的最终 gate 仍由 `command_safety` 和已有 permission 控制，并在 bundle blocked 时 fail closed。
- 更新 `mobile/README.md` 和 `docs/product/mobile_user_flow.md`，说明 bundle 是 phone/support metadata 和 Docker/local software proof。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

### Task B - Robot Metadata Compatibility Fence

Owner：`robot-software-engineer`

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

目标：

- 加入 `mobile_browser_acceptance_bundle`、`phone_browser_acceptance_bundle`、`mobile_acceptance_evidence_bundle` metadata-only fence。
- 证明这些字段不触发 collect/dropoff/cancel、不 POST ACK、不推进内存 cursor、不持久化 `last_terminal_ack_id`。
- 证明 protocol normalization 不把这些字段放进 command envelope。

实现要求：

- 增加 metadata-only remote response fixtures，字段可包含 realistic safe bundle 摘要，但不得构造 valid `trashbot.remote.v1` command。
- remote bridge 测试断言 backend action mock 未调用、ACK client 未 POST、cursor 不变、持久化状态不变。
- protocol normalization 测试断言这些字段不进入 command/status/ACK envelope，不生成 command id 或 terminal ACK。
- `docs/interfaces/ros_contracts.md` 增加接口说明：这些字段只属于 phone/support metadata，可被 mobile UI/diagnostics 消费，robot control loop 必须忽略。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C - Product Closeout

Owner：`product-okr-owner`

允许改动：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/tech-done.md`
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/side2side_check.md`
- `sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate/final.md`

目标：

- 等 Task A/B 返回后收口，只有 A+B 都完成且验证通过时才保守更新 Objective 4。
- 明确证据边界为 `software_proof_docker_mobile_browser_acceptance_bundle_gate`。
- 不声明真实手机/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

实现要求：

- `tech-done.md` 记录 Task A/B 实际改动、验证输出、偏差和剩余风险。
- `side2side_check.md` 对照 PRD 验收口径，逐项确认 bundle、fail-closed、metadata-only fence 和证据边界。
- `final.md` 回顾 OKR 最低优先级核对，说明 Objective 4 是否上调；如上调，必须说明只因 A/B Docker/local software proof 完成。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 只能根据实际完成结果更新，且必须保留真实手机设备/browser、production app、真实 PWA install prompt 等缺口。

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_15-16_mobile-browser-acceptance-bundle-gate
```

## 接口影响

- 新增或消费 phone/support metadata，不改变 `trashbot.remote.v1` command/status/ACK 主 envelope。
- Mobile UI 可展示/复制 acceptance bundle；robot control loop 必须忽略该 metadata。
- ACK 语义不变：只表示 command accepted/processing evidence，不表示 delivery success、dropoff success、cancel completed、Nav2/fixed-route 成功、WAVE ROVER 运动、HIL 或真实送达。

## 并行执行策略

- Task A 与 Task B 文件范围互不重叠，后续实现阶段必须并行派发给 `full-stack-software-engineer` 和 `robot-software-engineer`。
- Task C 依赖 Task A/B 的实际验证结果，不能提前更新 OKR 或 closeout。
- 主节点只做结果验收、证据核对和 sprint 留档，不直接修改 Task A/B 产品代码或测试代码。

## 风险边界

- Docker/local browser software proof 不能证明真实 iPhone/Android、真实 production app 或真实 PWA install prompt。
- 当前没有真实云/4G、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。
- Acceptance bundle 可能被误解为“验收完成”；所有 UI、fixture、README 和 closeout 必须保留 blocked-by-design、not-proven 和 ACK 边界。
- 敏感字段过滤是 P0；任何 token、credential、raw ROS topic、serial、`/cmd_vel` 或完整 artifact 泄露都必须阻断收口。

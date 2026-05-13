# Sprint 2026.05.13_21-22 Mobile Recovery Decision Gate - Tech Plan

## 目标

建立 `software_proof_docker_mobile_recovery_decision_gate`。在既有三步主路径之后，补齐普通用户在 blocked、offline、pending ACK、manual takeover、本地提交失败或缺少真实验收摘要时的首屏恢复决策。

恢复决策只消费 phone-safe 字段：

- `mobile_recovery_decision_gate` / `mobile_recovery_decision_summary`
- `phone_offline_resume_readiness`
- `command_safety`
- `operation_log` / `phone_operation_log`
- `mobile_action_receipt` / `phone_action_feedback`
- `phone_support_bundle`
- `mobile_primary_journey_gate` / `mobile_primary_journey_summary`

## 架构和接口边界

- Full-stack 只改 `mobile/` 与 `docs/product/mobile_user_flow.md`，不新增 robot state，不发明真实完成语义。
- Robot 只改 remote bridge/protocol 测试和接口文档，证明恢复决策 summary 是 metadata-only。
- Product 在 A/B 返回后收口 sprint、`OKR.md` 和 `docs/process/okr_progress_log.md`。

Evidence boundary 必须统一写成 `software_proof_docker_mobile_recovery_decision_gate`。Closeout 必须写明它不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实 cancel completion、真实 dropoff completion 或真实送达。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
- 本 sprint 是否针对该最低 Objective：否，本 sprint 针对 Objective 4。
- 不针对 Objective 5 的理由：`OKR.md` 第 6 节明确要求 Objective 5 只有拿到真实外部材料时才继续推进 completion。当前本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据；继续堆本地 O5 metadata depth 会重复消费同一 blocker。Objective 4 当前约 73%，是 Docker-only 下最低可推进目标。
- final.md 收口时需复核：若 A/B 期间拿到真实外部 O5 材料，Product closeout 重新评估 Objective 5；否则 Objective 5 不上调。

## Task A：Full-stack mobile recovery decision gate

责任 Engineer：`full-stack-software-engineer`

允许改动文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

禁止改动：

- `onboard/` robot remote bridge 生产代码和测试。
- `cloud-relay/` runtime。
- WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数。
- `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 文件。

实现要求：

- 首屏新增“恢复决策” panel，展示恢复状态、建议下一步、阻塞原因、支持入口、ACK 语义、证据边界和 not_proven 摘要。
- 优先消费 `mobile_recovery_decision_gate` / `mobile_recovery_decision_summary`；缺失时只从现有 phone-safe 字段派生 blocked-by-design 摘要。
- 对 pending ACK、offline/status stale、manual takeover/human help、local submit failed、missing primary journey readiness、missing support handoff 给出中文优先恢复建议。
- 恢复决策 panel 必须 read-only，不直接调用 Start/Confirm/Cancel，不把 ACK/receipt 写成 delivery success、dropoff success 或 cancel completed。
- Fixture 增加 `trashbot.mobile_recovery_decision_gate.v1` 样本。
- `mobile/test_mobile_web_entrypoint.py` 只做围栏：panel 可见、字段消费、缺字段 fail closed、安全词过滤、ACK 非成功语义。
- `mobile/README.md` 与 `docs/product/mobile_user_flow.md` 同步边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

预期输出：

- targeted mobile unittest `OK`。
- `py_compile` exit 0。
- scoped diff check exit 0。
- 文档和 fixture 出现 `software_proof_docker_mobile_recovery_decision_gate`。

## Task B：Robot metadata-only compatibility fence

责任 Engineer：`robot-software-engineer`

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

禁止改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，除非现有测试证明生产实现错误且必须最小修复；如需修复，返回中单独标记原因。
- `cloud-relay/` runtime。
- `mobile/web/`。
- 硬件、launch、Nav2/fixed-route 配置。
- `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 文件。

实现要求：

- 增加 metadata-only 样本：`mobile_recovery_decision_gate`、`mobile_recovery_decision_summary`。
- 样本可包含恢复状态、next_action、blocking_reason、support_entry、ack_semantics、evidence_boundary、not_proven，但不得包含 command envelope。
- 验证 metadata-only response 不触发 collect、confirm_dropoff、cancel，不 POST ACK，不推进 `last_ack_id`，不持久化 terminal cursor，不写 cursor override。
- 验证 valid collect command mixed recovery metadata 只按 command envelope 执行动作，metadata 不改变 ACK/cursor 语义。
- 文档说明 recovery decision metadata 是手机/支持 summary，不是 robot command、ACK、cursor、delivery success、dropoff success、cancel completion、production readiness 或 HIL。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

预期输出：

- remote bridge/protocol targeted tests `OK`。
- py_compile exit 0。
- scoped diff check exit 0。

## Task C：Product closeout

责任 Engineer：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/tech-done.md`
- `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/side2side_check.md`
- `sprints/2026.05.13_21-22_mobile-recovery-decision-gate/final.md`

触发条件：

- Task A 和 Task B 都返回后执行。
- 若任一任务失败，先要求对应 Engineer 定位并重试；Product 不用失败验证直接收口。

验收命令：

```bash
test -f sprints/2026.05.13_21-22_mobile-recovery-decision-gate/tech-done.md && test -f sprints/2026.05.13_21-22_mobile-recovery-decision-gate/side2side_check.md && test -f sprints/2026.05.13_21-22_mobile-recovery-decision-gate/final.md
rg -n "software_proof_docker_mobile_recovery_decision_gate|Objective 4|Objective 5|ACK|cancel completed|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_21-22_mobile-recovery-decision-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_21-22_mobile-recovery-decision-gate
```

## 并行启动要求

Task A 与 Task B 文件范围互不重叠，必须并行启动。Task C 等 A/B 完成后再执行。

## 验证围栏

本 sprint 只做 targeted mobile unittest、targeted robot metadata-only unittest、targeted py_compile 和 scoped `git diff --check`。不做 broad regression、不跑真实硬件、不跑 HIL、不声称真实手机设备、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue 或真实送达。

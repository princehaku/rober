# Sprint 2026.05.13_22-23 Mobile Terminal Action Confirmation Gate - Tech Plan

## 目标

建立 `software_proof_docker_mobile_terminal_action_confirmation_gate`。在既有 `mobile/web/` Start gate、operation log、action feedback 和 recovery decision 之后，给 Confirm Dropoff / Cancel 增加终端动作二次确认 gate。

本 sprint 只证明 Docker/local mobile software proof：

- 用户首次点击 Confirm Dropoff / Cancel 后进入只读确认 panel。
- panel 展示 action、风险、ACK 语义、not_proven、client_reference 和取消/返回入口。
- 用户显式确认后才调用现有 endpoint。
- Robot 侧只接受 valid command envelope；`mobile_terminal_action_confirmation_gate` / summary metadata 不触发 collect、confirm_dropoff、cancel、ACK 或 cursor。

## 架构和接口边界

- Full-stack 只改 `mobile/` 与 `docs/product/mobile_user_flow.md`，不新增 robot state，不改变 endpoint path，不改变 Start Delivery 的更强 start-confirmation gate。
- Confirm Dropoff / Cancel 继续使用既有 `trashbot.mobile_action_confirmation.v1` payload 语义，但在提交前增加 UI 二次确认状态。
- Robot 只改 remote bridge/protocol targeted tests 和接口文档，证明 `mobile_terminal_action_confirmation_gate` / `mobile_terminal_action_confirmation_summary` 是 metadata-only。
- Product 在 A/B 返回后收口 sprint、`OKR.md` 和 `docs/process/okr_progress_log.md`。
- Evidence boundary 必须统一写成 `software_proof_docker_mobile_terminal_action_confirmation_gate`。

Closeout 必须写明：该证据不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff completion、真实 cancel completion 或真实 delivery。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
- 本 sprint 是否针对该最低 Objective：否，本 sprint 针对 Objective 4。
- 不针对 Objective 5 的理由：`OKR.md` 第 6 节明确要求 Objective 5 只有拿到真实外部材料时才继续推进 completion。当前本机只有 Docker，没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据；继续堆本地 O5 metadata depth 会重复消费同一 blocker。Objective 4 当前约 74%，是 Docker-only 下最低可推进目标。
- final.md 收口时需复核：若 A/B/C 期间拿到真实外部 O5 材料，Product closeout 重新评估 Objective 5；否则 Objective 5 不上调。

## Task A：Full-stack mobile terminal action confirmation gate

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

- Confirm Dropoff / Cancel 首次点击只进入终端动作二次确认 panel，不调用 endpoint。
- panel 必须显示 action、用户风险、ACK 语义、not_proven、evidence boundary、client_reference 预览或确认后引用、取消/返回入口。
- 用户显式确认后才调用现有 Confirm Dropoff / Cancel endpoint，并沿用 `trashbot.mobile_action_confirmation.v1` 兼容 payload。
- `safe_phone_copy` 必须中文优先，并说明 accepted/processing only，不是 delivery success、dropoff success 或 cancel completed。
- 缺少 `command_safety`、action disabled、pending ACK、offline/stale、manual takeover、blocked state 时，确认入口 fail closed。
- Fixture 增加 `mobile_terminal_action_confirmation_gate` / `mobile_terminal_action_confirmation_summary` 样本，包含 `software_proof_docker_mobile_terminal_action_confirmation_gate`。
- `mobile/test_mobile_web_entrypoint.py` 只做围栏：首次点击不提交、确认后提交、取消返回不提交、字段可见、安全词过滤、ACK 非成功语义、blocked 状态 fail closed。
- `mobile/README.md` 与 `docs/product/mobile_user_flow.md` 同步边界。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

预期输出：

- targeted mobile unittest `OK`。
- `py_compile` exit 0。
- `node --check mobile/web/app.js` exit 0。
- scoped diff check exit 0。
- 文档和 fixture 出现 `software_proof_docker_mobile_terminal_action_confirmation_gate`。

## Task B：Robot metadata-only compatibility fence

责任 Engineer：`robot-software-engineer`

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

禁止改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，除非现有 targeted tests 证明生产实现错误且必须最小修复；如需修复，返回中单独标记原因。
- `cloud-relay/` runtime。
- `mobile/web/`。
- 硬件、launch、Nav2/fixed-route 配置。
- `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 文件。

实现要求：

- 增加 metadata-only 样本：`mobile_terminal_action_confirmation_gate`、`mobile_terminal_action_confirmation_summary`。
- 样本可包含 action、risk_copy、ack_semantics、client_reference、evidence_boundary、not_proven 和 safe_phone_copy，但不得包含 command envelope。
- 验证 metadata-only response 不触发 collect、confirm_dropoff、cancel。
- 验证 metadata-only response 不 POST ACK、不推进 `last_ack_id`、不持久化 terminal cursor、不写 cursor override。
- 验证 valid command envelope mixed terminal-action metadata 只按 command envelope 执行动作，metadata 不改变 ACK/cursor 语义。
- 文档说明 terminal action confirmation metadata 是手机/支持 summary，不是 robot command、ACK、cursor、delivery success、dropoff success、cancel completion、production readiness 或 HIL。

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
- 接口文档出现 `mobile_terminal_action_confirmation_gate` 和 `software_proof_docker_mobile_terminal_action_confirmation_gate`。

## Task C：Product closeout

责任 Engineer：`product-okr-owner`

允许改动文件范围：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-done.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/side2side_check.md`
- `sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/final.md`

触发条件：

- Task A 和 Task B 都返回后执行。
- 若任一任务失败，先要求对应 Engineer 定位并重试；Product 不用失败验证直接收口为完成。

实现要求：

- 汇总 A/B 实际改动和验证输出。
- 更新 `OKR.md` 4.1：Objective 4 可按证据谨慎调整；Objective 5 没有真实外部材料则保持约 68%。
- 更新 `docs/process/okr_progress_log.md`，记录 `software_proof_docker_mobile_terminal_action_confirmation_gate` 的证据边界。
- 创建/更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- final 必须复盘 OKR 最低优先级核对，并明确本轮不证明真实 dropoff completion、真实 cancel completion 或 delivery success。

验收命令：

```bash
test -f sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-done.md && test -f sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/side2side_check.md && test -f sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/final.md
rg -n "software_proof_docker_mobile_terminal_action_confirmation_gate|Objective 4|Objective 5|ACK|cancel completed|dropoff completion|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate
```

## 并行启动要求

Task A 与 Task B 文件范围互不重叠，必须并行启动。Task C 等 A/B 完成后再执行。

如果后续实现阶段由主节点派发 Codex worker，prompt 必须包含对应 role 的完整 `.codex/agents/<role>.toml` `prompt` 字段、本轮任务、文件范围、验收命令和输出要求。主节点不得自己写产品代码、测试代码或硬件配置。

## 验证围栏

本 sprint 只做 targeted mobile unittest、targeted robot metadata-only unittest、targeted `py_compile`、`node --check` 和 scoped `git diff --check`。不做 broad regression、不跑真实硬件、不跑 HIL、不声称真实手机设备、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue 或真实送达。

本计划文档自身验收命令：

```bash
test -f sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/pre_start.md && test -f sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/prd.md && test -f sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|Task A|Task B|Task C|mobile_terminal_action_confirmation|software_proof_docker_mobile_terminal_action_confirmation_gate" sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate
git diff --check -- sprints/2026.05.13_22-23_mobile-terminal-action-confirmation-gate
```


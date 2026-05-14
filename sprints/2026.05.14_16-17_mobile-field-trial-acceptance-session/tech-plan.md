# Sprint 2026.05.14_16-17 Mobile Field Trial Acceptance Session - Tech Plan

sprint_type: epic

## 目标

新增 `mobile_real_device_field_trial_acceptance_session*` phone-safe 会话包，把上一轮 field-trial browser proof、retest execution 和 evidence verdict 转成手机端可执行的现场验收会话，同时新增 Robot metadata-only fence，确保该 family 不触发任何机器人控制、副作用或成功语义。

本轮统一 evidence boundary：`software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 4 约 92%，Objective 1 约 75%，Objective 2/3 约 77%。
2. 本 sprint 不直接针对 Objective 5 completion，而是针对 Objective 4 的 `mobile_real_device_field_trial_acceptance_session*` 手机现场验收会话缺口。
3. 不针对 Objective 5 的理由：当前用户明确本机没有真实硬件，只有 Docker；当前环境也缺少真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料。继续新增本地 O5 metadata 不能产生真实 O5 进展；按 stop rule，本轮转向下一项可推进的 Objective 4 手机验收会话能力。
4. 本 sprint 仍需在 `final.md` 回顾该理由是否成立；若工程执行期间拿到真实 O5 外部材料，应在后续 sprint 切回 O5，而不是把本轮 acceptance session 冒充 O5 external proof。

## 并行任务拆分

本轮默认并行启动 2 个 worker，文件范围互不重叠。

### Task A - `full-stack-software-engineer`

**目标**：在 `mobile/web` 新增现场验收会话面板和 whitelist-only copy package，让手机端可执行 `mobile_real_device_field_trial_acceptance_session*`。

**允许改动文件**

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/evidence/`

**禁止改动**

- `onboard/`
- `docs/interfaces/ros_contracts.md`
- `OKR.md`
- 任何硬件配置、launch 参数、ROS2 行为实现或 remote bridge 代码。

**实现要求**

- 新增/消费字段：
  - `mobile_real_device_field_trial_acceptance_session`
  - `mobile_real_device_field_trial_acceptance_session_summary`
  - `mobile_real_device_field_trial_acceptance_session_copy`
- schema 使用 `trashbot.mobile_real_device_field_trial_acceptance_session.v1`，本地 evidence boundary 使用 `software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`。
- 输入优先级：
  1. 显式 `mobile_real_device_field_trial_acceptance_session*`。
  2. `mobile_real_device_field_trial_retest_execution*`。
  3. `mobile_real_device_field_trial_evidence_verdict*`。
  4. `mobile_current_pwa_field_trial_browser_proof*`。
  5. 缺失时派生 blocked-by-design session。
- 会话 checklist 至少覆盖：
  - real device observed。
  - production app observed。
  - PWA install prompt observed。
  - install/user choice observed。
  - offline reload observed。
  - touch target issue。
  - visual issue。
  - material redaction status。
  - operator/support note。
- UI/copy 必须保持：
  - `safe_to_control=false`。
  - `ack_semantics=accepted_processing_only_not_delivery_success`。
  - `not_proven`。
  - whitelist-only copy。
  - Start/Confirm/Cancel fail closed。
- copy package 禁止包含 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw robot responses、raw intake JSON 或 robot/internal 技术字段。
- 不新增控制 grant，不改 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 语义，不调用 ACK/cursor/terminal ACK 路径。
- `mobile/README.md` 与 `docs/product/mobile_user_flow.md` 必须写清：该 session 是 Docker/local mobile software proof，不是真实手机验收、production app、真实 PWA prompt、O5 external proof、HIL 或 delivery success。

**验收命令**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py

node --check mobile/web/app.js

rg -n "mobile_real_device_field_trial_acceptance_session|software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|whitelist-only" mobile/web mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md

git diff --check -- mobile/web mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/evidence
```

### Task B - `robot-software-engineer`

**目标**：新增/更新 Robot metadata-only fence，覆盖 `mobile_real_device_field_trial_acceptance_session*`，证明它不会触发机器人控制或成功语义。

**允许改动文件**

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

**禁止改动**

- `mobile/`
- `docs/product/mobile_user_flow.md`
- `mobile/README.md`
- `OKR.md`
- 任何硬件配置、launch 参数或导航代码。

**实现要求**

- 新增/更新 metadata family：
  - `mobile_real_device_field_trial_acceptance_session`
  - `mobile_real_device_field_trial_acceptance_session_summary`
  - `mobile_real_device_field_trial_acceptance_session_copy`
- fence 必须证明 metadata-only payload 不触发：
  - collect/dropoff/cancel command。
  - ACK POST。
  - cursor advance 或 persistence。
  - terminal ACK。
  - production readiness。
  - HIL。
  - dropoff/cancel completion。
  - delivery success。
- mixed valid-command 场景仍只执行合法 `trashbot.remote.v1` envelope；acceptance session metadata 不改变 action、target、idempotency、ACK 或 cursor。
- `docs/interfaces/ros_contracts.md` 必须写清该 family 是 `software_proof` metadata-only，不是真实手机、O5 external proof、HIL、dropoff/cancel completion 或 delivery success。

**验收命令**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py

rg -n "mobile_real_device_field_trial_acceptance_session|software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate|ACK POST|cursor|terminal ACK|delivery success|HIL" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

## Worker 启动要求

后续实现阶段必须按 AGENTS.md 使用 `spawn_agent(agent_type=worker)` 并行启动 Task A 和 Task B。每个 worker prompt 必须包含：

- `[角色 System Prompt]`：完整复制 `.codex/agents/<role>.toml` 的 `prompt` 字段。
- `[本轮任务]`：复制对应 Task 目标、实现要求和证据边界。
- `[文件范围]`：复制对应 Task 的允许/禁止改动文件。
- `[验收命令]`：复制对应 Task 的验收命令。
- `[输出要求]`：必须返回实际改动文件列表、验证命令输出结果、失败定位和剩余风险。

## 集成验收

工程完成后，Product Owner 只做证据核对和 sprint 留档，不补写产品代码或测试代码。

必须补齐：

- `tech-done.md`：记录 Task A/B 实际改动、验证结果、失败定位和剩余风险。
- `side2side_check.md`：核对 PRD/tech-plan 与 UI session、copy package、Robot fence 是否一致。
- `final.md`：给出 OKR 进度边界。若只完成 Docker/local mobile software proof，Objective 4 可谨慎评估是否上调；Objective 5 不应上调。

Product 验收命令：

```bash
rg -n "mobile-field-trial-acceptance-session|mobile_real_device_field_trial_acceptance_session|OKR 最低优先级核对|Objective 5|Objective 4|full-stack-software-engineer|robot-software-engineer" sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session

git diff --check -- sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session
```

## 剩余风险

- 没有真实 iPhone/Android、production app、真实 PWA install prompt/user choice，本轮 acceptance session 只能是 Docker/local mobile software proof。
- 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration，本轮不能替代 Objective 5 外部证据。
- 没有真实 WAVE ROVER、Nav2/fixed-route、dropoff/cancel completion、delivery success 或 HIL，本轮 Robot fence 只证明 metadata 无副作用。
- 若后续现场材料进入仓库或 artifact，需要继续坚持 whitelist-only copy，避免把凭证、URL 密钥、raw robot response、local path 或完整 artifact 泄漏进手机复制包。

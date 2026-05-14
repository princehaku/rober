# Sprint 2026.05.14_17-18 Mobile PWA Install Prompt Event Capture - Tech Plan

sprint_type: epic

## 目标

新增 `mobile_pwa_install_prompt_event_capture*` phone-safe 事件证据包，让 `mobile/web` 静态 PWA 入口监听真实浏览器 `beforeinstallprompt`、`appinstalled` 和 `userChoice` 事件，并把事件状态收敛为 whitelist-only copy package。同时新增 Robot metadata-only fence，确保该 family 不触发任何机器人控制、副作用或成功语义。

本轮统一 evidence boundary：`software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 4 约 93%，Objective 1 约 75%，Objective 2/3 约 77%。
2. 本 sprint 不直接针对 Objective 5 completion，而是针对 Objective 4 的 `mobile_pwa_install_prompt_event_capture*` PWA 安装提示事件捕获缺口。
3. 不针对 Objective 5 的理由：当前本机只有 Docker，缺少真实硬件、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料。继续新增本地 O5 metadata 不能产生真实 O5 进展；按 stop rule，本轮转向下一项可推进的 Objective 4 真实 PWA prompt/user choice 事件捕获能力。
4. 本 sprint 仍需在 `final.md` 回顾该理由是否成立；若工程执行期间拿到真实 O5 外部材料，应在后续 sprint 切回 O5，而不是把本轮 install prompt event capture 冒充 O5 external proof。

## 并行任务拆分

本轮默认并行启动 2 个 worker，文件范围互不重叠；Product closeout 在工程完成后收口，不与实现文件并行写。

### Task A - `full-stack-software-engineer`

**目标**：在 `mobile/web` 新增 PWA install prompt 浏览器事件监听、状态面板和 whitelist-only copy package，让手机端可生成 `mobile_pwa_install_prompt_event_capture*`。

**允许改动文件**

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/evidence/`

**禁止改动**

- `onboard/`
- `docs/interfaces/ros_contracts.md`
- `OKR.md`
- 任何硬件配置、launch 参数、ROS2 行为实现或 remote bridge 代码。

**实现要求**

- 新增/消费字段：
  - `mobile_pwa_install_prompt_event_capture`
  - `mobile_pwa_install_prompt_event_capture_summary`
  - `mobile_pwa_install_prompt_event_capture_copy`
- schema 使用 `trashbot.mobile_pwa_install_prompt_event_capture.v1`，本地 evidence boundary 使用 `software_proof_docker_mobile_pwa_install_prompt_event_capture_gate`。
- 必须在 `mobile/web` 静态入口监听：
  - `beforeinstallprompt`
  - `appinstalled`
  - `userChoice`
- `beforeinstallprompt` 处理要求：
  - 记录事件 observed/missing/blocked 状态、client timestamp、display mode、platform/browser summary 和 prompt availability。
  - 如保存 deferred prompt，只能保存在前端 runtime，用于用户手势后的 prompt 调用；copy package 禁止包含 raw event。
  - 不得因为事件出现而启用 Start、Confirm 或 Cancel。
- `userChoice` 处理要求：
  - 记录 allowlisted outcome，例如 accepted、dismissed、unknown/not_proven。
  - 捕获 choice timestamp 和 platform/browser summary。
  - 不保存 raw Promise、raw event、完整 UA 或敏感浏览器对象。
- `appinstalled` 处理要求：
  - 记录 installed event observed、timestamp、display mode。
  - 不得写成 production app readiness、真实设备验收通过或 delivery success。
- 缺少事件时必须派生 blocked-by-design package，并显示 `not_proven`，不能静默成功。
- UI/copy 必须保持：
  - `safe_to_control=false`。
  - `ack_semantics=accepted_processing_only_not_delivery_success`。
  - `not_proven`。
  - whitelist-only copy。
  - Start/Confirm/Cancel fail closed。
- copy package 禁止包含 token、Authorization、OSS AK/SK、DB/queue URL、credential-bearing URL、raw ROS topic、`/cmd_vel`、serial/UART、baudrate、WAVE ROVER 参数、本地路径、traceback、checksum、完整 artifacts、raw browser event、raw robot responses、raw intake JSON 或 robot/internal 技术字段。
- 不新增控制 grant，不改 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 语义，不调用 ACK/cursor/terminal ACK 路径。
- `mobile/README.md` 与 `docs/product/mobile_user_flow.md` 必须写清：该 event capture 是 Docker/local mobile software proof 和真实浏览器事件捕获准备，不是真实手机验收、production app、O5 external proof、HIL 或 delivery success。

**验收命令**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py

node --check mobile/web/app.js

rg -n "mobile_pwa_install_prompt_event_capture|software_proof_docker_mobile_pwa_install_prompt_event_capture_gate|beforeinstallprompt|appinstalled|userChoice|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|whitelist-only" mobile/web mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md

git diff --check -- mobile/web mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/evidence
```

### Task B - `robot-software-engineer`

**目标**：新增/更新 Robot metadata-only fence，覆盖 `mobile_pwa_install_prompt_event_capture*`，证明它不会触发机器人控制或成功语义。

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
  - `mobile_pwa_install_prompt_event_capture`
  - `mobile_pwa_install_prompt_event_capture_summary`
  - `mobile_pwa_install_prompt_event_capture_copy`
- fence 必须证明 metadata-only payload 不触发：
  - collect/dropoff/cancel command。
  - ACK POST。
  - cursor advance 或 persistence。
  - terminal ACK。
  - production readiness。
  - HIL。
  - dropoff/cancel completion。
  - delivery success。
- mixed valid-command 场景仍只执行合法 `trashbot.remote.v1` envelope；install prompt event capture metadata 不改变 action、target、idempotency、ACK 或 cursor。
- `docs/interfaces/ros_contracts.md` 必须写清该 family 是 `software_proof` metadata-only，不是真实手机、production app、O5 external proof、HIL、dropoff/cancel completion 或 delivery success。

**验收命令**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py

rg -n "mobile_pwa_install_prompt_event_capture|software_proof_docker_mobile_pwa_install_prompt_event_capture_gate|ACK POST|cursor|terminal ACK|delivery success|HIL" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Task C - `product-okr-owner`

**目标**：工程完成后执行 closeout，更新 sprint 收口、OKR 边界和 process log。

**允许改动文件**

- `sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/tech-done.md`
- `sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/side2side_check.md`
- `sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

**实现要求**

- 只在 Task A/B 返回并完成验收后收口。
- 明确 Objective 5 不因本轮上调，除非出现真实外部 O5 材料。
- Objective 4 是否上调必须基于事件监听、事件证据包、Robot metadata-only fence 和验证结果；若只有 local browser readiness，不得写成真实手机验收通过。
- `final.md` 必须回顾 `OKR 最低优先级核对` 中的 O5 stop rule 是否仍成立。

**验收命令**

```bash
rg -n "mobile-pwa-install-prompt-event-capture|mobile_pwa_install_prompt_event_capture|software_proof_docker_mobile_pwa_install_prompt_event_capture_gate|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|full-stack-software-engineer|robot-software-engineer" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture
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
- `side2side_check.md`：核对 PRD/tech-plan 与 UI event capture、copy package、Robot fence 是否一致。
- `final.md`：给出 OKR 进度边界。若只完成 Docker/local mobile software proof，Objective 4 可谨慎评估是否上调；Objective 5 不应上调。

Product planning 验收命令：

```bash
test -f sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/pre_start.md && test -f sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/prd.md && test -f sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture/tech-plan.md

rg -n "sprint_type: epic|OKR 最低优先级核对|beforeinstallprompt|appinstalled|userChoice|Objective 5|Objective 4|full-stack-software-engineer|robot-software-engineer" sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture

git diff --check -- sprints/2026.05.14_17-18_mobile-pwa-install-prompt-event-capture
```

## 剩余风险

- 没有真实 iPhone/Android、production app、真实 PWA install prompt/user choice，本轮 event capture 只能证明 `mobile/web` 具备监听和 phone-safe 包装能力；真实验收仍需现场设备材料。
- 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration，本轮不能替代 Objective 5 外部证据。
- 没有真实 WAVE ROVER、Nav2/fixed-route、dropoff/cancel completion、delivery success 或 HIL，本轮 Robot fence 只证明 metadata 无副作用。
- 浏览器安装提示事件具有平台差异；未触发时必须保持 `not_proven`，不能用手工记录或旧面板冒充真实事件捕获。

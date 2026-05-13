# Sprint 2026.05.13_20-21 Mobile Primary Journey Gate - Tech Plan

## 目标

建立 `software_proof_docker_mobile_primary_journey_gate`：把 `mobile/web/` 首屏从 proof 面板堆叠推进成普通用户可理解的“三步主路径” summary/gate，并用 robot compatibility fence 证明该手机 summary metadata 不会污染 command、ACK 或 cursor。

三步主路径固定为：

1. 目标垃圾站：从已有 phone-safe destination/target 字段读取。
2. 已放入垃圾确认：用户手动确认，不做自动载荷检测声明。
3. 发车安全 gate：由 `command_safety`、legacy `can_collect`、browser/device/cloud gates 和本地状态共同决定，默认 fail closed。

## 架构和接口边界

- Full-stack 负责 `mobile/web/` 首屏、fixture、移动端 entrypoint test 和产品流程文档。它只能消费已有 phone-safe 字段，不新增 robot state，不绕过 `command_safety`。
- Robot 负责 metadata-only compatibility fence 和接口文档。它不修改生产 command contract，不让 summary metadata 触发 collect、confirm_dropoff、cancel、ACK 或 cursor。
- Product 负责 closeout。它在 A/B 返回后更新 sprint 收口、`OKR.md` 和 `docs/process/okr_progress_log.md`；本计划阶段不改这些文件。

Evidence boundary 必须统一写成 `software_proof_docker_mobile_primary_journey_gate`。任何 closeout 都必须写明它不是真实 iPhone/Android device behavior、production app、真实 PWA install prompt、真实 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5 云中转 + OSS/CDN 数据通路产品化，约 68%。
- 本 sprint 是否针对该最低 Objective：否，本 sprint 主目标转向 Objective 4，Objective 5 只作为既有 phone-safe cloud/browser/device readiness metadata 的输入背景。
- 不针对 Objective 5 的理由：`OKR.md` 第 6 节要求 Objective 5 只有拿到真实外部材料时才继续推进 completion。当前没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 证据。最近 `2026.05.13_17-18_o5_external-evidence-intake-gate/final.md`、`2026.05.13_18-19_cloud-hosted-mobile-web-gate/final.md`、`2026.05.13_19-20_mobile-pwa-installability-gate/final.md` 都把无真实外部材料作为 O5 不上调或下一步转 O4 的依据。继续本地 O5 metadata depth 会重复消费同一 blocker；Objective 4 仍缺真实手机/production app/真实 PWA install prompt，在 Docker-only 下可先推进主路径可理解性和 fail-closed software proof。
- final.md 收口时需复核：若 A/B 期间拿到真实外部 O5 材料，Product closeout 需要重新评估 Objective 5；否则本轮只考虑 Objective 4 的软件证明口径。

## Task A：Full-stack mobile primary journey summary/gate

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

- Robot remote bridge 生产代码和测试。
- `cloud-relay/` runtime。
- WAVE ROVER、ESP32、Orange Pi、UART、launch 硬件参数。
- `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 文件。

实现要求：

- 首屏新增或重排三步主路径 summary：目标垃圾站 -> 已放入垃圾确认 -> 发车安全 gate。
- 目标垃圾站只能来自已有 phone-safe 字段，例如 `phone_task_flow_readiness.destination_summary`、destination-confirmed step、`phone_readiness.destination`、`status.destination` 或 `/api/collect` 兼容所需 `target`。
- 已放入垃圾确认必须仍是用户手动确认，不新增自动载荷检测声明。
- 发车安全 gate 必须消费现有 `phone_task_flow_readiness`、`command_safety`、browser/device/cloud readiness、operation log 和 action feedback；缺字段、blocked、offline、pending ACK、manual takeover、missing destination、unchecked load confirmation 都 fail closed。
- `POST /api/collect` payload 兼容现有 `target`，但 evidence boundary 更新为 `software_proof_docker_mobile_primary_journey_gate`；ACK 文案仍是 accepted/processing only。
- UI 不得暴露 token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、local path、traceback、checksum 或完整 artifact。
- `mobile/test_mobile_web_entrypoint.py` 只做围栏：三步主路径可渲染、Start fail closed、危险字段不泄漏、ACK 不含 delivery success 文案。
- `mobile/README.md` 和 `docs/product/mobile_user_flow.md` 必须写清这是 Docker/local mobile primary journey software proof，不是真实手机、production app、真实 PWA install prompt 或真实送达。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

预期输出：

- `mobile.test_mobile_web_entrypoint` targeted unittest `OK`。
- `py_compile` exit 0。
- scoped diff check exit 0。
- 文档和 fixture 出现 `software_proof_docker_mobile_primary_journey_gate`、`mobile_primary_journey_gate` 或 `mobile_primary_journey_summary`。

## Task B：Robot metadata-only compatibility fence

责任 Engineer：`robot-software-engineer`

允许改动文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

禁止改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_bridge.py`，除非现有测试证明生产实现错误且必须最小修复；如需修复，必须在返回中单独标记并说明原因。
- `cloud-relay/` runtime。
- `mobile/web/`。
- 硬件、launch、Nav2/fixed-route 配置。
- `OKR.md`、`docs/process/okr_progress_log.md`、本 sprint closeout 文件。

实现要求：

- 增加 metadata-only 样本：`mobile_primary_journey_gate`、`mobile_primary_journey_summary`。
- 样本可包含目标垃圾站、load confirmation requirement、command safety summary、browser/device/cloud gates、operation log/action feedback 摘要和 not_proven 列表，但不得包含 command envelope。
- 验证 metadata-only response 不触发 collect、confirm_dropoff、cancel，不 POST ACK，不推进 `last_ack_id`，不持久化 terminal cursor，不写 cursor override。
- 验证 valid collect command mixed metadata 只按 command envelope 执行动作，metadata 不改变 ACK/cursor 语义。
- 文档必须说明 primary journey metadata 是手机/支持 summary，不是 robot command、ACK、cursor、delivery success、dropoff success、cancel completion、production readiness 或 HIL。

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
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/tech-done.md`
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/side2side_check.md`
- `sprints/2026.05.13_20-21_mobile-primary-journey-gate/final.md`

触发条件：

- Task A 和 Task B 都返回后执行。
- 若任一任务失败，先要求对应 Engineer 定位并重试；Product 不用失败验证直接收口。

实现要求：

- 汇总 A/B 实际改动、验证命令、失败定位和剩余风险。
- `final.md` 必须回顾 `OKR 最低优先级核对` 的理由是否仍成立。
- `OKR.md` 和 `docs/process/okr_progress_log.md` 只能基于已返回证据更新；若没有真实外部 O5 材料，Objective 5 不上调。
- 证据边界写成 `software_proof_docker_mobile_primary_journey_gate`，并明确 ACK 不是 delivery success。

验收命令：

```bash
test -f sprints/2026.05.13_20-21_mobile-primary-journey-gate/tech-done.md && test -f sprints/2026.05.13_20-21_mobile-primary-journey-gate/side2side_check.md && test -f sprints/2026.05.13_20-21_mobile-primary-journey-gate/final.md
rg -n "software_proof_docker_mobile_primary_journey_gate|Objective 4|Objective 5|ACK|真实 iPhone|production app|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_20-21_mobile-primary-journey-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_20-21_mobile-primary-journey-gate
```

## 并行启动要求

Task A 与 Task B 文件范围互不重叠，必须并行启动。Task C 等 A/B 完成后再执行，不与 A/B 并行改同一 sprint 收口文件。

每个 worker prompt 必须包含：

- 对应 `.codex/agents/<role>.toml` 的完整 prompt。
- 本轮任务。
- 文件范围。
- 本 tech-plan 中的验收命令。
- 输出要求：实际改动文件列表、验证命令输出、失败定位、剩余风险。

## 验证围栏

本 sprint 的验证只做围栏：

- targeted mobile unittest。
- targeted robot metadata-only unittest。
- targeted py_compile。
- scoped `git diff --check`。

不做 broad regression、不跑真实硬件、不跑 HIL、不声称真实手机设备、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、production DB/queue 或真实送达。

## 风险边界

- 本机没有真实硬件，不能提升 Objective 1 HIL 口径。
- 本机没有真实公网/4G/OSS/CDN/production DB queue，不能提升 Objective 5 真实外部材料口径。
- Docker/local mobile primary journey gate 不等于真实 iPhone/Android device behavior，也不等于 production app 或真实 PWA install prompt。
- ACK、HTTP accepted 或 action receipt 仍只是 accepted/processing evidence，不是 delivery success、dropoff success、cancel completed 或 true task completion。

## 规划阶段验收命令

```bash
test -f sprints/2026.05.13_20-21_mobile-primary-journey-gate/pre_start.md && test -f sprints/2026.05.13_20-21_mobile-primary-journey-gate/prd.md && test -f sprints/2026.05.13_20-21_mobile-primary-journey-gate/tech-plan.md
rg -n "software_proof_docker_mobile_primary_journey_gate|OKR 最低优先级核对|Objective 5|Objective 4|full-stack-software-engineer|robot-software-engineer" sprints/2026.05.13_20-21_mobile-primary-journey-gate
git diff --check -- sprints/2026.05.13_20-21_mobile-primary-journey-gate
```

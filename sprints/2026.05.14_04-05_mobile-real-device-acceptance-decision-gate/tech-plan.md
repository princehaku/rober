# Sprint 2026.05.14_04-05 Mobile Real Device Acceptance Decision Gate - Tech Plan

## 目标

实现 `software_proof_docker_mobile_real_device_acceptance_decision_gate`：把上一轮 intake gate 收到或派生的真实设备/PWA/production app 材料，转换成 phone-safe acceptance decision、blocker list、next required evidence 和 redacted package，同时用 Robot metadata-only fence 证明该 metadata 不会污染 command、ACK、cursor 或 delivery success。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5，转向 Objective 4。
3. 理由：`OKR.md` 第 6 节明确没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration 证据时，不应继续堆 O5 metadata；当前主机只有 Docker/local，也没有真实硬件或真实外部云材料。上一 sprint 已完成 Objective 4 real-device evidence intake gate，因此本轮最可推进的弱项是把 O4 intake 材料转成 acceptance decision / blocker list / next required evidence，并保持 `not_proven`。

## 任务拆分

### Task A - Full-stack：手机/PWA acceptance decision gate

责任角色：`full-stack-software-engineer`

允许改动文件：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md`

实现要求：

- 新增或派生 `mobile_real_device_acceptance_decision`、`mobile_real_device_acceptance_decision_summary`、`mobile_real_device_acceptance_decision_package`。
- 支持从上一轮 `mobile_real_device_evidence_intake` / summary / package 派生 decision。
- 决策状态必须覆盖 `accepted_for_review`、`blocked_missing_evidence`、`rejected_unsafe_or_unredacted`、`not_proven`。
- UI 必须显示 blocker list、next required evidence、safe phone copy、ACK semantics、evidence boundary、redaction status 和 `not_proven`。
- copied package 必须过滤敏感字段：token、Authorization、OSS AK/SK、root password、DB/queue URL、raw ROS topic、`/cmd_vel`、serial、baudrate、WAVE ROVER、本地路径、traceback、checksum、complete artifact、raw robot response。
- 缺真实设备/PWA/production app 外部证据时，Start Delivery、Confirm Dropoff、Cancel 必须继续 fail closed。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "software_proof_docker_mobile_real_device_acceptance_decision_gate|mobile_real_device_acceptance_decision|accepted_for_review|blocked_missing_evidence|rejected_unsafe_or_unredacted|not_proven|PWA install prompt|production app" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/fixtures/mobile_web_status.fixture.json mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md
```

### Task B - Robot：metadata-only compatibility fence

责任角色：`robot-software-engineer`

允许改动文件：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md`

实现要求：

- 为 `mobile_real_device_acceptance_decision`、`mobile_real_device_acceptance_decision_summary`、`mobile_real_device_acceptance_decision_package` 增加 metadata-only response fence。
- 证明无 command envelope 时不触发 collect、confirm_dropoff、cancel、ACK POST、cursor advance、cursor persistence、terminal ACK、production readiness、HIL、dropoff success、cancel completed 或 delivery success。
- 证明 valid command mixed metadata 时只执行 command envelope，acceptance decision metadata 不进入 normalized command、ACK、status、cursor 或 terminal result。
- 文档明确该 metadata 只服务 phone/support/product acceptance，不能写入 robot control semantics。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_acceptance_decision|software_proof_docker_mobile_real_device_acceptance_decision_gate|metadata-only|delivery success|cursor|terminal ACK|production readiness|HIL" onboard/src/ros2_trashbot_behavior/test docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md
```

### Task C - Product：验收、OKR 和文档收口

责任角色：`product-okr-owner`

允许改动文件：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/side2side_check.md`
- `sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/final.md`

实现要求：

- 核对 Task A/B 验证证据，确认 `software_proof_docker_mobile_real_device_acceptance_decision_gate` 是否成立。
- 若没有真实外部设备材料，不得声明真实 iPhone/Android、production app、PWA prompt/user choice、真实 delivery 或 O5 外部证据通过。
- `OKR.md` 只允许在证据充分时谨慎更新 Objective 4；Objective 5 没有真实外部材料时保持约 68%。
- `side2side_check.md` 和 `final.md` 必须回顾 Objective 5 最低但不选的理由是否仍成立。

验收命令：

```bash
test -f sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-done.md && test -f sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/side2side_check.md && test -f sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/final.md
rg -n "software_proof_docker_mobile_real_device_acceptance_decision_gate|mobile_real_device_acceptance_decision|Objective 5|Objective 4|not_proven|metadata-only|delivery success" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate
```

## 并行执行规则

Task A 与 Task B 文件范围互不重叠，应并行启动 `full-stack-software-engineer` 与 `robot-software-engineer`。Task C 在 A/B 返回后执行验收和 OKR closeout。Hardware 与 Autonomy 本轮无实现任务；若执行中发现需要硬件、Nav2 或 route 事实，只做只读事实补充，不扩大改动范围。

## 接口影响

- 新增 acceptance decision metadata 字段，不新增 robot command。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 的控制语义。
- 不改变 ACK、cursor、delivery result、terminal result、production readiness、HIL 或 robot status 成功语义。
- 不引入云端生产依赖，不要求真实设备自动化测试环境。

## 风险边界

- 本轮最高证据等级是 Docker/local software proof + robot metadata-only fence。
- `accepted_for_review` 只表示材料可进入产品/工程评审，不等于真实设备通过。
- `not_proven` 必须保留真实手机设备、production app、真实 PWA install prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel/delivery。
- 若导入材料未脱敏或包含敏感字段，必须输出 `rejected_unsafe_or_unredacted` 或等价 blocker，而不是复制原文。

## 本规划验收命令

```bash
test -f sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/pre_start.md && test -f sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/prd.md && test -f sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 4|software_proof_docker_mobile_real_device_acceptance_decision_gate|mobile_real_device_acceptance_decision|metadata-only|not_proven" sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate
git diff --check -- sprints/2026.05.14_04-05_mobile-real-device-acceptance-decision-gate
```

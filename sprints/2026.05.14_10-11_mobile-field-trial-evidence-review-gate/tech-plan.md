# Sprint 2026.05.14_10-11 Mobile Field Trial Evidence Review Gate - Tech Plan

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的是 Objective 5：云中转 + OSS/CDN 数据通路产品化，约 68%。
2. 本 sprint 不直接针对 Objective 5；本 sprint 针对 Objective 4 的真实设备现场试跑材料复核链路。
3. 不针对 Objective 5 的理由：最新 `2026.05.14_09-10_mobile-real-device-field-trial-package/final.md` 明确 Objective 5 需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 等外部材料。本机只有 Docker/local proof，继续堆本地 O5 metadata 不能提升 Objective 5。按 stop rule，本轮转向 Objective 4。

## 方案概览

在上一轮 `mobile_real_device_field_trial_package*` 基础上新增 evidence review gate：

- 新 family：`mobile_real_device_field_trial_review*`
- 新 schema：`trashbot.mobile_real_device_field_trial_review.v1`
- 新 boundary：`software_proof_docker_mobile_real_device_field_trial_review_gate`
- 控制状态：`safe_to_control=false`
- ACK 语义：`accepted_processing_only_not_delivery_success`
- 缺口状态：完整保留 `not_proven`

该 gate 只复核现场材料 shape、缺失项、脱敏状态和 phone-safe copy，不证明真实设备、production app、真实 PWA install prompt/user choice、Objective 5 外部 proof、HIL 或 delivery success。

## Task A - Full-stack evidence review gate

### Owner

User Touchpoint Full-Stack Engineer

### 文件范围

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

### 实现要求

- 在手机入口新增“现场试跑证据复核”panel。
- 消费上一轮 field trial package 的 observation/runtime metadata，或从当前页面 observation fields 派生 review summary。
- 生成 `mobile_real_device_field_trial_review`、`mobile_real_device_field_trial_review_summary`、`mobile_real_device_field_trial_review_copy`。
- Review status 必须覆盖 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction。
- Copy package 必须 whitelist-only，不包含 token、Authorization、credential-bearing URL、raw local path、串口、WAVE ROVER 参数、ROS topic 或 `/cmd_vel`。
- Copy/package 必须固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven`。
- UI 文案必须避免 delivery success、真实送达、真实通过等完成暗示。
- 代码新增技术注释使用中文，并确保新增复杂逻辑有中文“为什么”注释。

### 验收命令

```bash
python3 -m unittest mobile.test_mobile_web_entrypoint
python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "software_proof_docker_mobile_real_device_field_trial_review_gate|mobile_real_device_field_trial_review|accepted_processing_only_not_delivery_success|not_proven|safe_to_control=false|现场试跑证据复核" mobile/web/index.html mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

## Task B - Robot metadata-only compatibility fence

### Owner

Robot Platform Engineer

### 文件范围

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

### 实现要求

- 将 `mobile_real_device_field_trial_review*` 纳入 remote bridge metadata-only family。
- 增加 protocol normalization fence，证明 review package 不被解析成 control command。
- 增加 worker metadata-only fence，证明 review package 不触发 ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- 增加 mixed valid-command coverage：review metadata 与有效 `trashbot.remote.v1` command 共存时，只允许 command envelope 走既有控制语义，review metadata 仍是支持材料。
- `docs/interfaces/ros_contracts.md` 同步说明 `mobile_real_device_field_trial_review*` 是 support metadata，不是 command、ACK 或 delivery proof。
- 代码新增技术注释使用中文，并确保新增复杂逻辑有中文“为什么”注释。

### 验收命令

```bash
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_field_trial_review|metadata-only|delivery success|HIL|production readiness|cursor|ACK" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

## Task C - Product closeout and OKR sync

### Owner

Product Manager / OKR Owner

### 文件范围

- `sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/tech-done.md`
- `sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/side2side_check.md`
- `sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

### 实现完成后的收口要求

- 核对 Task A/B 验证日志后再更新 closeout。
- `OKR.md` 只能在 Task A/B 均通过且 docs 同步后更新；若证据仍只是 software proof，Objective 4 只允许保守调整或不调整，Objective 5 不因本轮上调。
- 明确写入 `software_proof_docker_mobile_real_device_field_trial_review_gate`、`safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`。
- 明确未完成事项：真实手机设备、production app、真实 PWA install prompt/user choice、Objective 5 外部材料、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 和真实 delivery。

### 验收命令

```bash
rg -n "software_proof_docker_mobile_real_device_field_trial_review_gate|Objective 5|Objective 4|not_proven|metadata-only|delivery success|safe_to_control=false|accepted_processing_only_not_delivery_success|现场试跑证据复核" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate
```

## 并行启动计划

本轮为 epic sprint，默认并行启动 2 个 Engineer 子 agent：

- Task A Full-stack 负责手机端 review gate、tests 和产品文档。
- Task B Robot 负责 metadata-only / mixed valid-command 围栏和接口文档。

Task C Product closeout 在 Task A/B 返回后执行。Product 不抢 Engineer 实现，不把 PRD 或计划当交付。

## 接口影响

- 新增 support metadata family：`mobile_real_device_field_trial_review*`。
- 新增 schema：`trashbot.mobile_real_device_field_trial_review.v1`。
- 新增 evidence boundary：`software_proof_docker_mobile_real_device_field_trial_review_gate`。
- 不新增控制命令，不改变 `trashbot.remote.v1` command envelope。
- 不改变 ACK/delivery semantics；继续 `accepted_processing_only_not_delivery_success`。
- 不改变 production readiness；继续不证明 Objective 5 外部 proof。

## 风险边界

- 本轮无法产生真实外部材料：真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration。
- 本轮无法产生真实硬件/机器人材料：Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion、真实 delivery。
- 本轮 review package 不等于人工验收通过；它只让材料状态更可审计。
- 若现场材料缺失或脱敏不合规，review gate 必须输出 missing、blocked 或 `not_proven`，不得输出通过。

## 本轮计划文件验收

```bash
test -f sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/pre_start.md && test -f sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/prd.md && test -f sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate/tech-plan.md
rg -n "sprint_type: epic|Objective 5|Objective 4|OKR 最低优先级核对|software_proof_docker_mobile_real_device_field_trial_review_gate|mobile_real_device_field_trial_review|not_proven|safe_to_control=false|accepted_processing_only_not_delivery_success" sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate
git diff --check -- sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate
```

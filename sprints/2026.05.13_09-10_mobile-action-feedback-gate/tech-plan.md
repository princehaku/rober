# Sprint 2026.05.13_09-10 Mobile Action Feedback Gate - Tech Plan

## 目标

建立 `software_proof_docker_mobile_action_feedback_gate`：让 Start/Confirm/Cancel 提交后在手机首屏显示 phone-safe 动作回执、失败提示、恢复建议和 ACK 语义；Confirm/Cancel 也带 generic mobile action confirmation payload；robot-side compatibility fence 证明相关 metadata-only 响应不触发机器人动作、不 POST ACK、不推进或持久化 cursor。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 最低且 Docker-only 可行动 Objective 是 Objective 4：手机用户体验与低成本量产边界，约 60%。
2. Objective 5 约 61%，最新 sprint `sprints/2026.05.13_08-09_cloud-public-ingress-tls-gate/final.md` 只提升 O5，不调整 O4。
3. Objective 1/2/3 约 75%/77%/77%，主要缺真实 WAVE ROVER、真实串口、真实 Nav2/fixed-route、同一 `evidence_ref` 任务复盘、HIL 和真实送达；当前主机没有真实硬件，只有 Docker。
4. 本 sprint 直接针对 Objective 4。理由是 O4 当前低于 O5，且可以在 Docker-only 条件下通过 local/static mobile action feedback gate 推进手机用户体验。
5. 不选择 Objective 1：真实 `hil_pass`、真实串口日志、`T=1001` feedback、`/odom`、`/imu/data`、`/battery` 实机样本仍不可得。
6. 不选择 Objective 2：真实 Nav2/fixed-route 运行、任务复盘、真实送达和失败恢复实测仍不可得。
7. 不选择 Objective 3：真实路线采集、Nav2 waypoint/fixed-route 实跑、关键帧实景证据与上车复账仍不可得。
8. 不选择 Objective 5：上一轮刚完成 `software_proof_docker_cloud_public_ingress_tls_gate` 并上调到约 61%，当前低于它的是 O4。
9. Docker-only 边界：本 sprint 只能声明 local/static software proof。不得声明真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

## 技术方案

### Mobile/web action feedback 方案

- 在 `mobile/web/` 首屏新增或扩展动作反馈面板，展示最近一次用户动作、提交状态、失败原因、恢复建议、client reference 和 ACK 语义。
- 面板消费 fixture/status 中的 `mobile_action_receipt`、`phone_action_feedback` 或等价 phone-safe 字段；若本地提交失败，也显示本地 failed/blocked copy。
- Start 继续使用既有 `trashbot.mobile_task_start_confirmation.v1` body，保持 destination 和 trash-loaded confirmation gate。
- Confirm Dropoff 和 Cancel 改为携带 generic mobile action confirmation payload，例如 `trashbot.mobile_action_confirmation.v1`。
- payload 必须包含 phone-safe 字段：`schema`、`schema_version`、`source=mobile_web`、`action`、`user_confirmed`、`client_reference`、`client_timestamp`、`safe_phone_copy`、`ack_semantics`、`evidence_boundary=software_proof_docker_mobile_action_feedback_gate`。
- payload 不得包含 raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数、token、Authorization header、OSS AK/SK、DB/queue URL、本地路径、完整 artifact 或 checksum。
- 所有提交成功、HTTP success、receipt 或 ACK 文案都必须写成 accepted/processing evidence，不得写成 delivery success、dropoff success 或 cancel completed。
- 更新 fixture/static smoke，覆盖动作回执面板、失败提示、ACK 文案和 Confirm/Cancel payload。
- 更新 `mobile/README.md` 与 `docs/product/mobile_user_flow.md`，明确本 gate 是 local/static software proof。

### Robot compatibility 方案

- 在 remote bridge / protocol 测试中增加 metadata-only 响应字段：`mobile_action_confirmation`、`mobile_action_receipt`、`phone_action_feedback` 或等价命名。
- 验证这些 metadata-only response 不触发 backend action。
- 验证不 POST ACK。
- 验证不推进或持久化 cursor。
- 验证 protocol normalization 剥离 command envelope 外 metadata。
- 文档中明确 action feedback metadata 属于 phone-safe support/status summary，不属于 `trashbot.remote.v1` action command envelope。

## 并行 owner 拆分

### Task A：full-stack-software-engineer

文件范围：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`（如需要）
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

实现要求：

- 实现 mobile/web 动作回执面板。
- Confirm Dropoff 和 Cancel 提交时带 generic mobile action confirmation payload。
- Start 保持既有 task-start confirmation gate，不能降低 destination/load confirmation 门槛。
- 动作回执、失败提示和 ACK copy 必须 phone-safe、中文优先、fail closed。
- fixture 和 static smoke 覆盖 Start/Confirm/Cancel 的反馈展示与安全 payload。
- 文档同步写清 evidence boundary 和非声明边界。
- 代码技术注释必须使用中文；复杂逻辑注释解释为什么 fail closed 或为什么不能把 ACK 写成成功。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/README.md docs/product/mobile_user_flow.md
```

预期结果：

- targeted unittest 输出 `OK`。
- `py_compile` 无输出。
- scoped `git diff --check` 无输出。
- fixture/static smoke 能证明 `software_proof_docker_mobile_action_feedback_gate`，但不声明真实手机设备/browser 或真实送达。

### Task B：robot-software-engineer

文件范围：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

实现要求：

- 增加 `mobile_action_confirmation` / `mobile_action_receipt` / `phone_action_feedback` metadata-only compatibility fence。
- 覆盖 metadata-only response 不触发 backend action。
- 覆盖不 POST ACK。
- 覆盖不推进或持久化 cursor。
- 覆盖 protocol normalization 剥离 command envelope 外 metadata。
- 更新接口文档，明确该 metadata 不改变 command/status/ack envelope。
- 保持 ACK 只是 accepted/processing evidence，不是 delivery success。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

预期结果：

- targeted unittest 输出 `OK`。
- `py_compile` 无输出。
- scoped `git diff --check` 无输出。
- compatibility fence 证明 mobile action feedback metadata 不产生 robot side effect。

### Task C：product-okr-owner closeout

文件范围：

- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/tech-done.md`
- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/side2side_check.md`
- `sprints/2026.05.13_09-10_mobile-action-feedback-gate/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

收口要求：

- 汇总 Task A 和 Task B 实际改动与验证输出。
- 检查引用文档路径真实存在。
- 保守更新 Objective 4 进度；Objective 1/2/3/5 除非有新证据不调整。
- 明确 evidence boundary：`software_proof_docker_mobile_action_feedback_gate`。
- 明确不声明真实手机设备/browser、production app、真实 PWA install prompt、真实云/4G、OSS/CDN live traffic、Nav2/fixed-route、WAVE ROVER、HIL 或真实送达。

验收命令：

```bash
test -f OKR.md && test -f docs/process/okr_progress_log.md && test -f docs/product/mobile_user_flow.md && test -f docs/interfaces/ros_contracts.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.13_09-10_mobile-action-feedback-gate
```

## 接口影响

- Mobile/web 可新增 `trashbot.mobile_action_confirmation.v1` request body for Confirm Dropoff and Cancel。
- Mobile/web 可消费 `mobile_action_receipt`、`phone_action_feedback` 或等价 phone-safe status/fixture 字段。
- 不改变 `trashbot.remote.v1` command/status/ack envelope。
- 不改变 ROS2 topic、`/cmd_vel`、hardware launch 参数、WAVE ROVER 串口协议或 robot action 语义。
- ACK copy 与 receipt copy 必须保持 accepted/processing only。

## 安全与隐私边界

Action feedback payload、receipt、fixture、文档和 phone-safe summary 不得包含：

- bearer token、Authorization header、OSS AK/SK、root password。
- DB URL、queue URL、credential-bearing URL、production secret。
- raw ROS topic、`/cmd_vel`、serial device、baudrate、WAVE ROVER 参数。
- local filesystem path、traceback、checksum、完整 artifact。
- 任何能把 accepted/processing 误读为 delivery success、dropoff success、cancel completed、real cloud ready、HIL pass 或真实送达的文案。

## 验证计划

后续执行阶段必须至少运行围栏验证：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/README.md docs/product/mobile_user_flow.md onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

本 planning 阶段验收命令：

```bash
test -f sprints/2026.05.13_09-10_mobile-action-feedback-gate/pre_start.md && test -f sprints/2026.05.13_09-10_mobile-action-feedback-gate/prd.md && test -f sprints/2026.05.13_09-10_mobile-action-feedback-gate/tech-plan.md
git diff --check -- sprints/2026.05.13_09-10_mobile-action-feedback-gate
```

## 风险与回滚

- 如果 action feedback 文案把 HTTP success 或 ACK 写成 delivery success，Task A 必须先修文案和测试，再允许收口。
- 如果 Confirm/Cancel payload 暴露 raw/hardware/secret 字段，Task A 必须收紧 builder 与 fixture。
- 如果 robot fence 发现 metadata-only 字段进入 action path，Task B 必须补 normalization 或负例，不能用文档绕过。
- 如果只完成 mobile/static proof，Objective 4 只能保守小幅推进；真实手机、真实云、真实硬件与真实送达仍留作后续。
- 回滚方式是移除本 sprint 的 mobile action feedback 增量和对应文档增量；不得回滚无关 sprint 或其他 worker 改动。

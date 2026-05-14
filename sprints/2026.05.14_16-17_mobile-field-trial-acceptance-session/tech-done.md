# Tech Done

## Sprint 声明

- sprint_type: epic
- sprint：`sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/`
- evidence boundary：`software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`
- closeout owner：`product-okr-owner`

## 用户价值和产品北极星

本轮把手机端真实设备现场材料链从“证据 verdict / 复测 execution / 当前 PWA browser proof”推进到“现场验收会话”：普通用户、支持同学或验收人可以在手机首屏看到一次现场验收应该执行、复测、判定和复用的材料包，同时不会误以为机器人已经可真实控制或已经送达成功。

产品北极星保持不变：让不会电脑和 ROS2 的普通手机用户，以低成本、可诊断、可复盘的方式完成送垃圾任务。本轮只推进 Objective 4 的手机验收会话能力，不把软件 proof 写成真实手机验收或真实送达。

## OKR 映射

- Objective 4：主目标。覆盖 KR1、KR5、KR7，把手机端核心流程和用户验收标准继续产品化，增强主流手机首屏验收材料链。
- Objective 5：不提升。本轮没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration 或真实外部材料。
- Objective 1/2/3：不提升。本轮 Robot fence 是 metadata-only 兼容性证明，不是硬件、Nav2/fixed-route 或真实送达闭环。

## KR 拆解或更新

- KR-A：手机端新增 `mobile_real_device_field_trial_acceptance_session*` 会话面板，支持显式 session、retest execution、evidence verdict、current PWA field-trial browser proof 派生 whitelist-only package。
- KR-B：Robot 侧新增同 family metadata-only fence，确保该类现场验收材料不会触发 collect/dropoff/cancel、ACK POST、cursor advance/persistence、terminal ACK、success/readiness/HIL 或 delivery success。
- KR-C：产品口径收口为 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven` 和 Start/Confirm/Cancel fail closed。

## 实际改动

Task A `full-stack-software-engineer` 已完成：

- `mobile/web/app.js`
- `mobile/web/index.html`
- `mobile/web/styles.css`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/evidence/task_a_mobile_field_trial_acceptance_session.json`

Task B `robot-software-engineer` 已完成：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

Product closeout 已完成：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/tech-done.md`
- `sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/side2side_check.md`
- `sprints/2026.05.14_16-17_mobile-field-trial-acceptance-session/final.md`

## 验证结果

Task A 已回报验证：

```text
mobile.test_mobile_web_entrypoint: Ran 35 tests OK
py_compile: pass
node --check mobile/web/app.js: pass
required rg: pass
scoped diff check: pass
```

Task B 已回报验证：

```text
remote bridge targeted unittest: Ran 184 tests in 94.243s OK
py_compile: pass
required rg: pass
scoped diff check: pass
```

Product closeout 围栏验证见本 sprint `final.md`；执行范围只覆盖允许的 OKR / process log / sprint closeout 文档。

## 偏差和边界

- 本轮证据边界是 `software_proof_docker_mobile_real_device_field_trial_acceptance_session_gate`。
- 本轮不是：真实手机验收、production app、真实 PWA prompt/user choice、O5 external proof、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、HIL、WAVE ROVER、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。
- `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`、Start/Confirm/Cancel fail closed 必须继续保留。

## 剩余风险

- Objective 5 仍约 68%，是当前最低完成度；但没有真实外部云/4G/OSS/CDN/DB/queue 材料时，不应继续用本地 metadata depth 抬 O5。
- Objective 4 下一步若继续上调，应优先取得真实 iPhone/Android device behavior、production app 或真实 PWA prompt/user choice 证据。
- 本轮没有真实 HIL、WAVE ROVER、Nav2/fixed-route 或真实送达证据，因此 Objective 1/2/3 不因本轮提升。

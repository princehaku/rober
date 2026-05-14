# Sprint 2026.05.14_14-15 Mobile Field Trial Retest Execution Gate - Tech Done

sprint_type: epic

## 实际改动

本轮完成 `software_proof_docker_mobile_real_device_field_trial_retest_execution_gate`，把 13-14 轮的现场证据 verdict / retest / material request 推进到可执行记录的复测执行 package。

Task A - full-stack-software-engineer：

- 新增 `mobile_real_device_field_trial_retest_execution*` 首屏 panel、summary 和 whitelist-only copy package。
- Retest execution package 从 `mobile_real_device_field_trial_evidence_verdict*` 的 `retest_request` / `material_request` 派生或消费后端同名字段，输出复测执行状态、材料请求、缺口摘要和 execution checklist。
- Copy package 固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、完整 `not_proven` 和 `software_proof_docker_mobile_real_device_field_trial_retest_execution_gate`，不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义。

Task B - robot-software-engineer：

- 新增 retest execution family metadata-only tests/docs，覆盖 `mobile_real_device_field_trial_retest_execution`、`mobile_real_device_field_trial_retest_execution_summary`、`mobile_real_device_field_trial_retest_execution_copy`。
- Robot fence 证明 retest execution metadata 不触发 command、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- Mixed valid-command 场景仍只执行 `trashbot.remote.v1` command envelope，retest execution metadata 不改变 action、target、idempotency、ACK 或 cursor。

Product closeout：

- 更新本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 当前进度快照和第 6/7 节口径。
- 追加 `docs/process/okr_progress_log.md` 顶部 2026-05-14 14-15 记录。

## 验证结果

Full-stack worker 已报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 34 tests in 0.044s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
pass
```

Robot worker 已报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
Ran 176 tests in 90.862s
OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

Robot unittest 过程中有一条 Python `ResourceWarning`，命令退出码为 0，测试结果为 `OK`。

Product closeout 本地验收命令记录在 `final.md`。

## 偏差

- 本轮按计划完成 retest execution package 和 Robot metadata-only fence；未改动硬件、Nav2/fixed-route、cloud production runtime、DB/queue、OSS/CDN 或真实手机设备。
- 本轮没有真实 iPhone/Android、production app、真实 PWA prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success 证据。

## 剩余风险

- Objective 5 仍最低约 68%，但缺真实外部材料；没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 前不调整。
- Objective 4 可从约 90% 谨慎上调到约 91%，但证据边界只到 Docker/local mobile software proof + Robot metadata-only fence。
- `mobile_real_device_field_trial_retest_execution*` 是复测执行材料链路，不是真实手机验收、production app readiness、真实 PWA install prompt success、真实交付或 HIL。

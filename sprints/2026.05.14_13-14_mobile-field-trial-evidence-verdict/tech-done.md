# Sprint 2026.05.14_13-14 Mobile Field Trial Evidence Verdict - Tech Done

sprint_type: epic

## 实际改动

本轮完成 `software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate`，把 12-13 轮的现场证据记录推进到可复核的 verdict / retest / material request package。

Task A - full-stack-software-engineer：

- 新增 `mobile_real_device_field_trial_evidence_verdict*` 首屏 panel、summary 和 phone-safe copy package。
- Verdict package 继续固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven` 和 `software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate`。
- Copy package 只表达材料复核、缺口、下一步 retest/material request，不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义。

Task B - robot-software-engineer：

- 新增 verdict family metadata-only tests/docs，覆盖 `mobile_real_device_field_trial_evidence_verdict`、`mobile_real_device_field_trial_evidence_verdict_summary`、`mobile_real_device_field_trial_evidence_verdict_copy`。
- Robot fence 证明 verdict metadata 不触发 command、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- Mixed valid-command 场景仍只执行 `trashbot.remote.v1` command envelope，verdict metadata 不改变 action、target、idempotency、ACK 或 cursor。

Product closeout：

- 更新本文件、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 4.1 当前进度快照和第 6/7 节口径。
- 追加 `docs/process/okr_progress_log.md` 顶部 2026-05-14 13-14 记录。

## 验证结果

Full-stack worker 已报告：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 33 tests ... OK

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
Ran 173 tests ... OK

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

Product closeout 本地验收命令记录在 `final.md`。

## 偏差

- 本轮按计划完成 verdict package 和 Robot metadata-only fence；未改动硬件、Nav2/fixed-route、cloud production runtime、DB/queue、OSS/CDN 或真实手机设备。
- 本轮没有真实 iPhone/Android、production app、真实 PWA prompt/user choice、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、Nav2/fixed-route、WAVE ROVER、HIL、dropoff/cancel completion 或 delivery success 证据。

## 剩余风险

- Objective 5 仍最低约 68%，但缺真实外部材料；没有公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 前不调整。
- Objective 4 可从约 89% 谨慎上调到约 90%，但证据边界只到 Docker/local mobile software proof + Robot metadata-only fence。
- `mobile_real_device_field_trial_evidence_verdict*` 是材料复核与下一步请求，不是真实手机验收、production app readiness、真实 PWA install prompt success、真实交付或 HIL。

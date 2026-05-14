# Sprint 2026.05.14_12-13 Mobile Field Trial Evidence Recorder - Tech Done

sprint_type: epic

## 实际改动

Task A Full-stack 已完成：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

交付内容：新增首屏“现场证据记录”入口，生成、展示、复制、归档 `mobile_real_device_field_trial_evidence_record*`。字段覆盖 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction、operator note、support note。copy/archive 采用 whitelist-only，固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`、`not_proven` 和 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。没有改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义。

Task B Robot 已完成：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

交付内容：新增 `_record`、`_summary`、`_copy`、`_archive` metadata-only 围栏，证明该 family 不触发 command、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。mixed valid-command 场景只执行 `trashbot.remote.v1` envelope，metadata 不改变 action、target、idempotency、ACK 或 cursor。

Product closeout 已同步：

- 本 sprint `tech-done.md`、`side2side_check.md`、`final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## 验证结果

Task A Full-stack 围栏验证：

```text
python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 32 tests in 0.042s
OK

python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg
pass

git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
pass
```

Task B Robot 围栏验证：

```text
python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
Ran 169 tests in 86.466s
OK
注：有一个既有 ResourceWarning，未影响 exit code。

python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
pass

required rg
pass

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
pass
```

Product closeout 本地验收：

```text
rg -n "software_proof_docker_mobile_real_device_field_trial_evidence_record_gate|mobile_real_device_field_trial_evidence_record|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven|现场证据记录" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder
exit 0，命中 OKR.md、docs/process/okr_progress_log.md 和本 sprint 文档中的 evidence boundary、package family、Objective 4/5、safe_to_control=false、accepted_processing_only_not_delivery_success、not_proven、现场证据记录。

test -f sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/tech-done.md && test -f sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/side2side_check.md && test -f sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder/final.md
exit 0。

git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_12-13_mobile-field-trial-evidence-recorder
exit 0。
```

## 偏差和失败定位

- 计划要求 A/B worker 并行推进，实际 A/B 均已完成并给出围栏验证结果。
- Product closeout 开始时发现本 sprint 缺 `tech-done.md`、`side2side_check.md`、`final.md`，本次按 closeout 范围补齐。
- Robot 验证中出现一个既有 ResourceWarning；当前记录为既有噪声，不作为本轮失败。
- 未发现需要回退 Full-stack 或 Robot worker 改动的证据；Product closeout 只编辑指定收口文件。

## 剩余风险

- 本轮证据只属于 `software_proof_docker_mobile_real_device_field_trial_evidence_record_gate`。
- 仍未证明真实手机验收、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。
- Objective 5 仍是最低约 68%，但没有真实外部材料，本轮不调整。
- Objective 4 可从约 88% 谨慎上调到约 89%，理由是 `mobile/web` 已从“现场试跑执行清单”推进到可填写、展示、复制、归档的现场证据记录入口，并有 Robot metadata-only fence。

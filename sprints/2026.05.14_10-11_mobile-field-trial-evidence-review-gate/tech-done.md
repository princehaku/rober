# Sprint 2026.05.14_10-11 Mobile Field Trial Evidence Review Gate - Tech Done

## Sprint 类型

- sprint_type: epic
- evidence_boundary: `software_proof_docker_mobile_real_device_field_trial_review_gate`
- 收口时间：2026-05-14 10:14 Asia/Shanghai

## 实际改动

Task A Full-stack 已完成：

- 修改 `mobile/web/index.html`、`mobile/web/app.js`、`mobile/web/styles.css`、`mobile/test_mobile_web_entrypoint.py`、`mobile/README.md`、`docs/product/mobile_user_flow.md`。
- 新增首屏“现场试跑证据复核”panel，生成、展示、复制 `mobile_real_device_field_trial_review`、`mobile_real_device_field_trial_review_summary`、`mobile_real_device_field_trial_review_copy`。
- Review status 覆盖 real device、production app、PWA install prompt、user choice、offline、touch、visual、material redaction。
- Copy package 固定 `safe_to_control=false`、`ack_semantics=accepted_processing_only_not_delivery_success`，完整保留 `not_proven`，并保持 whitelist-only phone-safe copy。

Task B Robot 已完成：

- 修改 `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`、`onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`、`docs/interfaces/ros_contracts.md`。
- 新增 `mobile_real_device_field_trial_review*` protocol normalization、worker metadata-only、mixed valid-command coverage。
- 证明 review metadata 不污染 command、ACK、status、cursor、terminal result；与有效 `trashbot.remote.v1` command 共存时，只执行 command envelope。

Task C Product closeout 已完成：

- 更新本 sprint `tech-done.md`、`side2side_check.md`、`final.md`。
- 更新 `OKR.md` 当前快照和 `docs/process/okr_progress_log.md`。
- Objective 4 从约 86% 保守上调到约 87%；Objective 5 保持约 68%；Objective 1/2/3 不调整。

## 验证结果

Task A Full-stack 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
Ran 30 tests ... OK

python3 -m py_compile mobile/test_mobile_web_entrypoint.py
pass

node --check mobile/web/app.js
pass

required rg pass
scoped git diff --check pass
```

Task B Robot 验证结果：

```text
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
Ran 161 tests in 82.342s OK
one existing ResourceWarning

py_compile pass
required rg pass
scoped git diff --check pass
```

Task C Product 验收命令在收口后执行：

```bash
rg -n "software_proof_docker_mobile_real_device_field_trial_review_gate|Objective 5|Objective 4|not_proven|metadata-only|delivery success|safe_to_control=false|accepted_processing_only_not_delivery_success|现场试跑证据复核" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_10-11_mobile-field-trial-evidence-review-gate
```

## 证据边界

本轮只形成 `software_proof_docker_mobile_real_device_field_trial_review_gate`。它证明 Docker/local `mobile/web` 能生成现场试跑证据复核 package，且 Robot remote bridge 将 `mobile_real_device_field_trial_review*` 视为 metadata-only support material。

本轮不证明真实手机设备、真实 iPhone/Android device behavior、production app、真实 PWA install prompt/user choice、Objective 5 外部 proof、真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、production worker/migration、Nav2/fixed-route、WAVE ROVER、HIL、真实 dropoff/cancel completion 或 delivery success。

## 剩余风险

- Objective 5 仍缺真实外部材料，保持约 68%。
- 真实设备现场试跑材料还需要真实手机设备、production app、真实 PWA install prompt/user choice 和现场截图/录屏/人工记录补齐。
- ACK、HTTP accepted、copy package、review package、browser proof、metadata-only response 均只能作为 accepted/processing/support metadata，不是 delivery success。

# Sprint 2026.05.14_13-14 Mobile Field Trial Evidence Verdict - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。
2. 本 sprint 不直接针对 Objective 5。
3. 原因：Objective 5 当前需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 worker/migration 等外部材料；本机只有 Docker，继续本地 metadata 不应上调 O5。Objective 1 真实 HIL 同样被真实硬件缺失锁死。本轮选择 Objective 4 的真实手机验收材料 verdict，是当前 Docker-only 环境下仍能推进的最低有效产品链路。

## 方案

新增 `mobile_real_device_field_trial_evidence_verdict*` family：

- `mobile_real_device_field_trial_evidence_verdict`
- `mobile_real_device_field_trial_evidence_verdict_summary`
- `mobile_real_device_field_trial_evidence_verdict_copy`

该 family 从上轮 `mobile_real_device_field_trial_evidence_record*` 派生，只做材料复核和下一步请求，不做控制放行。

## 分工和文件范围

### Task A - full-stack-software-engineer

允许改动：

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

任务：

- 新增现场证据 verdict panel 和复制入口。
- 从 record/archive/status 派生 verdict summary、missing evidence、retest request。
- 保持 `safe_to_control=false`、ACK 非 delivery success、`not_proven`、whitelist-only copy。
- 更新 targeted mobile static smoke 和产品流程文档。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_real_device_field_trial_evidence_verdict|software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven" mobile/web/index.html mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

### Task B - robot-software-engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 增加 verdict family metadata-only 围栏。
- 证明 `_verdict`、`_summary`、`_copy` 不触发 command、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed valid-command 场景仍只执行 `trashbot.remote.v1` envelope，verdict metadata 不改变 action、target、idempotency、ACK 或 cursor。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_field_trial_evidence_verdict|software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate|metadata-only|delivery success|HIL" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

### Product closeout

允许改动：

- `sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict/tech-done.md`
- `sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict/side2side_check.md`
- `sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

验收命令：

```bash
rg -n "software_proof_docker_mobile_real_device_field_trial_evidence_verdict_gate|mobile_real_device_field_trial_evidence_verdict|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict
test -f sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict/tech-done.md && test -f sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict/side2side_check.md && test -f sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict/final.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_13-14_mobile-field-trial-evidence-verdict
```

## 风险边界

- Verdict 是材料复核 metadata，不是验收通过。
- 本轮不生成真实手机、生产 app、真实 PWA prompt/user choice 或真实云证据。
- 主操作继续由既有 command safety、cloud/device/browser readiness、operation log、action feedback 和 review gates fail closed。

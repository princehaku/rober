# Sprint 2026.05.14_14-15 Mobile Field Trial Retest Execution Gate - Tech Plan

sprint_type: epic

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低 Objective：Objective 5，约 68%。
2. 本 sprint 不直接推进 Objective 5 completion。
3. 原因：Objective 5 的下一步真实进展需要真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity 或 production worker/migration 等外部材料；当前主机只有 Docker。按既有 stop rule，不能继续堆本地 O5 metadata，本轮转向 Objective 4 的真实手机验收材料链路。Objective 1 HIL 也因缺真实硬件不可推进。

## 技术方案

新增 `mobile_real_device_field_trial_retest_execution*` family：

- `mobile_real_device_field_trial_retest_execution`
- `mobile_real_device_field_trial_retest_execution_summary`
- `mobile_real_device_field_trial_retest_execution_copy`

该 family 从上轮 `mobile_real_device_field_trial_evidence_verdict*` 的 `retest_request` / `material_request` 派生，只记录复测执行结果和下一步缺口，不做控制放行。

## Task A - full-stack-software-engineer

### 文件范围

- `mobile/web/index.html`
- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/test_mobile_web_entrypoint.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`

### 实现要点

- 新增“现场复测执行结果”首屏 panel 和复制入口。
- 从 status/readiness/diagnostics/verdict package 派生 retest execution summary。
- 保持 `safe_to_control=false`、ACK 非 delivery success、`not_proven`、whitelist-only copy。
- 不改变 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` endpoint 语义。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
rg -n "mobile_real_device_field_trial_retest_execution|software_proof_docker_mobile_real_device_field_trial_retest_execution_gate|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven" mobile/web/index.html mobile/web/app.js mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
git diff --check -- mobile/web/index.html mobile/web/app.js mobile/web/styles.css mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md
```

## Task B - robot-software-engineer

### 文件范围

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`

### 实现要点

- 增加 retest execution family metadata-only 围栏。
- 证明 `_retest_execution`、`_summary`、`_copy` 不触发 command、ACK POST、cursor advance/persistence、terminal ACK、production readiness、HIL、dropoff/cancel completion 或 delivery success。
- mixed valid-command 场景仍只执行 `trashbot.remote.v1` envelope，retest execution metadata 不改变 action、target、idempotency、ACK 或 cursor。

### 验收命令

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest onboard.src.ros2_trashbot_behavior.test.test_remote_bridge onboard.src.ros2_trashbot_behavior.test.test_remote_bridge_protocol
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py
rg -n "mobile_real_device_field_trial_retest_execution|software_proof_docker_mobile_real_device_field_trial_retest_execution_gate|metadata-only|delivery success|HIL" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md
```

## Product Closeout

### 文件范围

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate/tech-done.md`
- `sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate/side2side_check.md`
- `sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate/final.md`

### 验收命令

```bash
rg -n "software_proof_docker_mobile_real_device_field_trial_retest_execution_gate|mobile_real_device_field_trial_retest_execution|Objective 5|Objective 4|safe_to_control=false|accepted_processing_only_not_delivery_success|not_proven" OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate
test -f sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate/tech-done.md && test -f sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate/side2side_check.md && test -f sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate/final.md
git diff --check -- OKR.md docs/process/okr_progress_log.md sprints/2026.05.14_14-15_mobile-field-trial-retest-execution-gate
```

## 风险边界

- 本轮仍是 Docker/local mobile software proof，不是真实 iPhone/Android、production app、真实 PWA install prompt/user choice 或真实交付。
- Robot fence 只证明 metadata 不触发控制语义，不证明真实机器人动作。
- Objective 5 不上调；缺真实外部材料前不继续本地 O5 depth。

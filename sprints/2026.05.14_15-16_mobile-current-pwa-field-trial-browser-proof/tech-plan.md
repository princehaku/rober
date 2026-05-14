# Sprint 2026.05.14_15-16 Mobile Current PWA Field Trial Browser Proof - Tech Plan

sprint_type: epic

## 目标

刷新当前 `mobile/web` PWA 的本地 Chromium-family browser proof，覆盖 14-15 之后完整 field-trial 首屏组合，并新增 Robot metadata-only fence，确保新的 browser proof metadata family 不触发任何机器人控制或成功语义。

本轮统一 evidence boundary：`software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`。

## OKR 最低优先级核对

1. 当前 `OKR.md` 4.1 完成度最低的 Objective 是 Objective 5，约 68%。Objective 4 约 91%，Objective 1 约 75%，Objective 2/3 约 77%。
2. 本 sprint 不直接针对 Objective 5 completion，而是针对 Objective 4 的 current PWA browser proof 缺口。
3. 不针对 Objective 5 的理由：当前主机只有 Docker，缺少真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue connectivity、production worker/migration 或真实外部材料。继续新增本地 O5 metadata 不能产生真实 O5 进展；按 stop rule，本轮转向下一项可推进的 Objective 4 浏览器证明缺口。
4. 本 sprint 仍需在 closeout 回顾该理由是否成立；若工程执行期间拿到真实 O5 外部材料，应在 final 中明确是否需要切回 O5 后续 sprint，而不是把本轮 browser proof 冒充 O5。

## 并行任务拆分

### Task A - `full-stack-software-engineer`

**目标**：更新 current PWA browser proof gate，覆盖完整 field-trial 首屏组合，并产出本 sprint evidence artifact。

**允许改动文件**

- `pc-tools/evidence/phone_browser_acceptance_gate.py`
- `mobile/README.md`
- `docs/product/mobile_user_flow.md`
- `mobile/test_mobile_web_entrypoint.py`（仅当现有边界/脚本断言需要最小补齐）
- `sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/evidence/`
- `sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/tech-done.md`（追加 Task A 结果）

**实现要求**

- 将 current evidence boundary 更新为 `software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate`。
- browser proof 必须检查可见/summary/copy 边界，至少覆盖：
  - `mobile_real_device_field_trial_package*`
  - `mobile_real_device_field_trial_review*`
  - `mobile_real_device_field_trial_runbook_execution*`
  - `mobile_real_device_field_trial_evidence_record*`
  - `mobile_real_device_field_trial_evidence_verdict*`
  - `mobile_real_device_field_trial_retest_execution*`
- 生成并提交本 sprint evidence：
  - `evidence/mobile_current_pwa_field_trial_browser_390x844.json`
  - `evidence/mobile_current_pwa_field_trial_browser_390x844.png`
  - `evidence/mobile_current_pwa_field_trial_browser_768x900.json`
  - `evidence/mobile_current_pwa_field_trial_browser_768x900.png`
  - `evidence/mobile_current_pwa_field_trial_browser_acceptance_summary.json`
- 保持 `safe_to_control=false`、`accepted_processing_only_not_delivery_success`、`not_proven`、whitelist-only copy、Start/Confirm/Cancel fail closed。
- 不新增 O4 metadata panel，不改 `/api/collect`、`/api/dropoff/confirm`、`/api/cancel` 控制语义。
- 不直接调用会触发控制提交、ACK、cursor 或内部 action 路径的 app 函数；browser proof 应验证当前 DOM 和 phone-safe artifact。

**验收命令**

```bash
python3 pc-tools/evidence/phone_browser_acceptance_gate.py \
  --output-dir sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/evidence

PYTHONDONTWRITEBYTECODE=1 python3 -m unittest mobile.test_mobile_web_entrypoint

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py

rg -n "software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate|mobile_real_device_field_trial_package|mobile_real_device_field_trial_review|mobile_real_device_field_trial_runbook_execution|mobile_real_device_field_trial_evidence_record|mobile_real_device_field_trial_evidence_verdict|mobile_real_device_field_trial_retest_execution" pc-tools/evidence/phone_browser_acceptance_gate.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/evidence

git diff --check -- pc-tools/evidence/phone_browser_acceptance_gate.py mobile/test_mobile_web_entrypoint.py mobile/README.md docs/product/mobile_user_flow.md sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof
```

### Task B - `robot-software-engineer`

**目标**：新增/更新 robot metadata-only fence，覆盖新的 browser proof metadata family，证明它不会触发机器人控制或成功语义。

**允许改动文件**

- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py`
- `docs/interfaces/ros_contracts.md`
- `sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof/tech-done.md`（追加 Task B 结果）

**实现要求**

- 新增或更新 metadata family，建议命名：
  - `mobile_current_pwa_field_trial_browser_proof`
  - `mobile_current_pwa_field_trial_browser_proof_summary`
  - `mobile_current_pwa_field_trial_browser_proof_copy`
- fence 必须证明 metadata-only payload 不触发：
  - collect/dropoff/cancel command。
  - ACK POST。
  - cursor advance 或 persistence。
  - terminal ACK。
  - production readiness。
  - HIL。
  - dropoff/cancel completion。
  - delivery success。
- mixed valid-command 场景仍只执行合法 `trashbot.remote.v1` envelope；browser proof metadata 不改变 action、target、idempotency、ACK 或 cursor。
- `docs/interfaces/ros_contracts.md` 必须写清该 family 是 `software_proof` metadata-only，不是真实手机、O5 external proof、HIL 或 delivery success。

**验收命令**

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m unittest \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py

PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py \
  onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py

rg -n "mobile_current_pwa_field_trial_browser_proof|software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate|ACK POST|cursor|terminal ACK|delivery success|HIL" onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md

git diff --check -- onboard/src/ros2_trashbot_behavior/test/test_remote_bridge.py onboard/src/ros2_trashbot_behavior/test/test_remote_bridge_protocol.py docs/interfaces/ros_contracts.md sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof
```

## 集成验收

工程完成后，Product Owner 只做证据核对和 sprint 留档，不补写产品代码或测试代码。

必须补齐：

- `tech-done.md`：记录 Task A/B 实际改动、验证结果、失败定位和剩余风险。
- `side2side_check.md`：核对 PRD/tech-plan 与 artifact/robot fence 是否一致。
- `final.md`：给出 OKR 进度边界。若只完成 local Chromium-family proof，Objective 4 可谨慎评估是否上调；Objective 5 不应上调。

Product 验收命令：

```bash
rg -n "mobile-current-pwa-field-trial-browser-proof|software_proof_docker_mobile_current_pwa_field_trial_browser_proof_gate|Objective 5|Objective 4|OKR 最低优先级核对|full-stack-software-engineer|robot-software-engineer" sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof

git diff --check -- sprints/2026.05.14_15-16_mobile-current-pwa-field-trial-browser-proof
```

## 剩余风险

- 没有真实 iPhone/Android、production app、真实 PWA install prompt/user choice，本轮 artifact 只能是 local Chromium-family browser proof。
- 没有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 production worker/migration，本轮不能替代 Objective 5 外部证据。
- 没有真实 WAVE ROVER、Nav2/fixed-route、dropoff/cancel completion、delivery success 或 HIL，本轮 Robot fence 只证明 metadata 无副作用。

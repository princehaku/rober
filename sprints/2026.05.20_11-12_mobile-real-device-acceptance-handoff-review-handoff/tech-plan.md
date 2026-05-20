# Sprint 2026.05.20_11-12 Mobile Real Device Acceptance Handoff Review Handoff - Tech Plan

## 1. 技术目标

实现 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff` 的 Robot diagnostics safe summary 与 mobile/web 只读展示。它承接上一轮 `mobile_real_device_field_trial_acceptance_execution_handoff_review_decision`，把 accepted / missing / rejected / blocked 复核结果转成下一步现场 owner handoff package。

本轮计划的 evidence boundary：

- `software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate`
- `software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

## 2. OKR 最低优先级核对

- 当前 `OKR.md` 4.1 节完成度最低的 Objective：Objective 5，约 68%。
- 本 sprint 是否针对该 Objective：否。
- 不针对理由：Objective 5 只有真实公网 HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover 或真实手机/browser 才能提升；当前主机只有 Docker，近期已完成 `cloud_ack_outage_replay_guard`、`cloud_pending_ack_status_guard`、`cloud_command_expiry_safety_guard`、`cloud_command_idempotency_visibility_guard`、`cloud_command_id_conflict_visibility_guard` 等本地 fail-closed metadata proof，继续堆 O5 metadata depth 不应计入进展。
- 下一低项 Objective 1 约 81%，但 PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending，缺真实 2D LiDAR / ToF SKU/source/receipt/procurement/install/wiring/power/calibration/HIL-entry，也缺真实 WAVE ROVER/UART/HIL；本轮不得写成 O1 hardware/HIL 进展。
- 本 sprint 选择 Objective 4 的理由：最新 sprint 已完成 handoff review decision，本轮把复核结果转成现场 owner handoff package，属于不依赖 O5 external material 或 O1 hardware material 的可执行 O4 软件证明链路。
- final.md 收口时需复核：O5/O1 blocker 是否仍成立；若真实 external/hardware material 到位，下一轮必须重新排序。

## 3. 并行 owner 与文件范围

本轮必须并行启动 2 个 engineering owner，文件范围互不重叠。

### Robot Platform Engineer

允许改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/ros_contracts.md`

任务：

- 在 diagnostics safe summary 中新增/兼容 `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff`。
- 输出字段包括 current decision、handoff owner、handoff reason、accepted / missing / rejected / blocked summaries、next required evidence、rerun guidance、same safe `evidence_ref`、evidence boundary。
- 保持 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false`。
- 测试 missing/unsafe/raw fields fail closed，不产生真实手机/browser、O5 external proof、O1 hardware/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success claim。
- 同步 `docs/interfaces/ros_contracts.md`。

验收命令：

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md
```

### User Touchpoint Full-Stack Engineer

允许改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

任务：

- 在 mobile/web 中新增或延续只读“现场验收交接复核交接”展示。
- 消费 Robot/status/diagnostics 中的 handoff review handoff safe summary；缺字段、unsafe 字段或 boundary 不匹配时 fail closed 到 `not_proven`。
- 展示 current decision、handoff owner、handoff reason、accepted / missing / rejected / blocked summaries、next required evidence、rerun guidance、same safe `evidence_ref` 和 evidence boundary。
- 不新增控制 endpoint，不请求 ACK/cursor，不 fetch raw artifacts，不改变 Start Delivery / Confirm Dropoff / Cancel gating。
- 更新 fixtures 和 mobile entrypoint test，确认 `safe_to_control=false`、`delivery_success=false`、`primary_actions_enabled=false` 时三类主操作保持禁用。
- 同步 `docs/product/mobile_user_flow.md`。

验收命令：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/tmp/mobile_web_status.fixture.json.checked
python3 -m json.tool mobile/web/fixtures/status.json >/tmp/mobile_web_status.json.checked
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md
```

## 4. 接口契约

Robot diagnostics safe summary 至少需要包含以下 phone-safe 字段：

- `schema`: `trashbot.mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_summary.v1`
- `kind`: `mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff`
- `current_decision`
- `handoff_owner`
- `handoff_reason`
- `accepted_summary`
- `missing_summary`
- `rejected_summary`
- `blocked_summary`
- `next_required_evidence`
- `rerun_guidance`
- `safe_evidence_ref`
- `same_evidence_ref_required=true`
- `evidence_boundary=software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate`
- `software_proof`
- `not_proven`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`

Forbidden in Robot/mobile output:

- raw ROS topics
- `/cmd_vel`
- raw JSON artifacts
- serial/UART paths
- baudrate values
- WAVE ROVER parameters
- credentials
- DB/queue URLs
- OSS AK/SK
- local paths
- tracebacks
- checksums
- complete artifacts
- raw field materials
- delivery success wording
- HIL/pass wording

## 5. Product closeout 文件范围

后续实现完成后，Product closeout 允许改动：

- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/tech-done.md`
- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/side2side_check.md`
- `sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

closeout 规则：

- 只记录 worker 实际改动和验证证据。
- 若仍只有 Docker/local software proof，OKR 百分比不提高。
- 必须明确 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / material pending，除非 live GitHub thread 已被 reviewer resolve。
- 必须同步说明不是真实手机/browser、O5 external proof、O1 hardware/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。

## 6. 子 Agent Prompt 固定结构

主节点实现阶段必须按 AGENTS.md 固定结构并行派发以下 2 个 Codex worker。

### Prompt: Robot Platform Engineer

```text
[角色 System Prompt]
从 .codex/agents/robot-software-engineer.toml 的 prompt 字段完整复制，不裁剪。

[本轮任务]
实现 mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff 的 Robot diagnostics safe summary。承接上一轮 handoff review decision，把 accepted/missing/rejected/blocked 复核结果转成现场 owner handoff package。必须保持 software_proof、not_proven、safe_to_control=false、delivery_success=false、primary_actions_enabled=false，并使用 evidence_boundary=software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate。不得写成真实手机/browser、O5 external proof、O1 hardware/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。

[文件范围]
仅允许改动：
- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
- onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
- docs/interfaces/ros_contracts.md

[验收命令]
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=onboard/src/ros2_trashbot_behavior python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" onboard/src/ros2_trashbot_behavior docs/interfaces/ros_contracts.md
git diff --check -- onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py docs/interfaces/ros_contracts.md

[输出要求]
必须返回：
1. 实际改动的文件列表
2. 验证命令输出结果（截图或日志片段）
3. 失败定位（如有）
4. 剩余风险
```

### Prompt: User Touchpoint Full-Stack Engineer

```text
[角色 System Prompt]
从 .codex/agents/full-stack-software-engineer.toml 的 prompt 字段完整复制，不裁剪。

[本轮任务]
实现 mobile/web 只读“现场验收交接复核交接”展示，消费 mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff safe summary。展示 current decision、handoff owner、handoff reason、accepted/missing/rejected/blocked summaries、next required evidence、rerun guidance、same safe evidence_ref 和 evidence boundary。必须保持 software_proof、not_proven、safe_to_control=false、delivery_success=false、primary_actions_enabled=false；不得打开 Start Delivery、Confirm Dropoff、Cancel；不得写成真实手机/browser、O5 external proof、O1 hardware/HIL、route/elevator field pass、dropoff/cancel completion 或 delivery success。

[文件范围]
仅允许改动：
- mobile/web/app.js
- mobile/web/styles.css
- mobile/web/test_mobile_web_entrypoint.py
- mobile/fixtures/mobile_web_status.fixture.json
- mobile/web/fixtures/status.json
- docs/product/mobile_user_flow.md

[验收命令]
python3 mobile/web/test_mobile_web_entrypoint.py
PYTHONDONTWRITEBYTECODE=1 python3 -m py_compile mobile/web/test_mobile_web_entrypoint.py
node --check mobile/web/app.js
python3 -m json.tool mobile/fixtures/mobile_web_status.fixture.json >/tmp/mobile_web_status.fixture.json.checked
python3 -m json.tool mobile/web/fixtures/status.json >/tmp/mobile_web_status.json.checked
rg -n "mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false|not_proven" mobile docs/product/mobile_user_flow.md
git diff --check -- mobile/web/app.js mobile/web/styles.css mobile/web/test_mobile_web_entrypoint.py mobile/fixtures/mobile_web_status.fixture.json mobile/web/fixtures/status.json docs/product/mobile_user_flow.md

[输出要求]
必须返回：
1. 实际改动的文件列表
2. 验证命令输出结果（截图或日志片段）
3. 失败定位（如有）
4. 剩余风险
```

## 7. Planning 阶段验收命令

本轮 Product planning docs 必须通过：

```bash
test -f sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/pre_start.md && test -f sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/prd.md && test -f sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff/tech-plan.md
rg -n "sprint_type: epic|OKR 最低优先级核对|Objective 5|Objective 1|Objective 4|PRRT_kwDOSWB9286CJ3tX|mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff|software_proof_docker_mobile_real_device_field_trial_acceptance_execution_handoff_review_handoff_gate|safe_to_control=false|delivery_success=false|primary_actions_enabled=false" sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff
git diff --check -- sprints/2026.05.20_11-12_mobile-real-device-acceptance-handoff-review-handoff
```

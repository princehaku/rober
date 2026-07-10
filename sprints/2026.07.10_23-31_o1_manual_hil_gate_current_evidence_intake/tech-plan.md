# O1 Manual HIL Gate Current Evidence Intake Tech Plan

## 方案

扩展现有 `trashbot.wave_rover_motion_map_hil_material_bundle.v1`，新增 additive section `manual_hil_gate_current_evidence_material`。该 section 只读消费已有 PC proxy / real-board readback artifacts，输出安全摘要并保持 fail-closed。

优先复用现有 bundle 的安全投影、CLI、测试风格和文档结构，避免新增一套并行合同。

## 文件范围

Hardware owner 可修改：

- `onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py`
- `onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py`
- `docs/hardware/wave_rover_motion_map_hil_material_bundle.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/tech-done.md`
- 必要时新增本 sprint `artifacts/hardware_worker_report.md`

Product owner 后续可修改：

- `OKR.md`
- `docs/process/okr_progress_log.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/side2side_check.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/final.md`
- `sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake/artifacts/product_worker_report.md`

## 输入 artifacts

默认正向输入：

- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/gate_decision_before.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/stop_safety_smoke.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/manual_forward_expected_reject.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/pc_proxy/proxy_smoke_result.json`
- `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/remote_readback/after_api_base_feedback-samples_latest.json`
- `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts/real_board_operator_report_direct_192_168_1_11_8787.json`
- `sprints/2026.06.11_06-05_pc_structured_hil_report_readback/artifacts/real_board_robot_control_summary_192_168_1_11_8787.json`

## Contract 字段

建议字段：

- `manual_hil_gate_current_evidence_material_present`
- `manual_hil_gate_status`
- `manual_hil_gate_missing_fields`
- `visible_content_proven_blocks_motion`
- `manual_nonzero_policy`
- `stop_safety_smoke_forwarded`
- `stop_remote_http_status`
- `manual_nonstop_local_reject_present`
- `manual_nonstop_remote_base_manual_called`
- `manual_nonstop_failure_reason`
- `proxy_remote_base_manual_not_called_by_local_reject`
- `manual_gate_t1001_observed_count`
- `manual_gate_all_samples_observed_t1001`
- `manual_gate_feedback_request_t130_observed`
- `operator_structured_report_material_only`
- `operator_structured_report_status`
- `operator_structured_delivery_claim_material_only`
- `manual_hil_gate_ready_not_hil_pass`

固定 false 字段继续保留：

- `hil_pass=false`
- `safe_to_control=false`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `robot_control_executed=false`
- `nav2_route_execution_success=false`

## Fail-closed 规则

- 任一核心 artifact 缺失或 schema 不匹配时 blocked。
- `operator_gate.status` 不是 `blocked` 时 blocked，除非 future artifact 明确由真实 HIL pass 合同替代；本轮不实现替代。
- missing fields 不包含 external video、visible content、wheel feedback L/R nonzero、LiDAR motion delta 时 blocked。
- stop safety smoke 未通过 PC proxy 转发到固定 `/api/base/stop` 时 blocked。
- non-stop manual request 未被本地拒绝、或远端 `/api/base/manual` 被调用时 blocked。
- T1001 feedback request 未证明 `T=130` context、`all_samples_observed_t1001=true`、`t1001_observed_count=2` 时 blocked。
- operator structured report 只能 material-only；nested `delivery_success=true` 不得提升顶层 `delivery_success`。
- 任意 allowlisted 输出中出现 URL、`/root/`、`/Users/`、`/dev/tty`、token、secret、password、traceback、baudrate 或长 raw/base64 时 blocked 或不输出。

## 验收命令

Hardware owner 必须运行：

```bash
python3 -m py_compile onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/*.py
```

```bash
python3 -m unittest discover -s onboard/src/ros2_trashbot_hardware/test -p '*motion*map*hil*.py'
```

```bash
PYTHONPATH=onboard/src/ros2_trashbot_hardware python3 -m ros2_trashbot_hardware.wave_rover_motion_map_hil_material_bundle
```

```bash
rg -n "manual_hil_gate_current_evidence|manual_hil_gate_ready_not_hil_pass|remote_base_manual_not_called|operator_structured_report" onboard/src/ros2_trashbot_hardware docs/hardware sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake
```

```bash
git diff --check -- onboard/src/ros2_trashbot_hardware/ros2_trashbot_hardware/wave_rover_motion_map_hil_material_bundle.py onboard/src/ros2_trashbot_hardware/test/test_wave_rover_motion_map_hil_material_bundle.py docs/hardware/wave_rover_motion_map_hil_material_bundle.md sprints/2026.07.10_23-31_o1_manual_hil_gate_current_evidence_intake
```

## OKR 最低优先级核对

当前 `OKR.md` 4.1 节最低 Objective 是 O5：云中转控制面，约 `~85%`。

本 sprint 不针对 O5。原因：最近 O5 sprint 已把 production cutover readiness packet 固定为 `okr_credit_allowed=false` / `support_only_reason=no_real_production_external_evidence`，当前仍缺真实公网 HTTPS/TLS、4G/SIM、production DB/queue、production worker/cutover、OSS/CDN live traffic 与真实 phone/browser 材料。继续 O5 会重复消费同一外部证据 blocker。

本 sprint 转向 O1。O1 是下一个较低且当前可推进的 Objective，本轮消费不同于上一轮 bounded-motion 的 manual HIL gate current evidence artifacts，且交付可由本地测试和 CLI 复验。

## 风险

- 本轮可能只能把 O1 从材料可读性向前推进，不能归档 KR。
- 如果 worker 发现这些材料已被现有 bundle 完整消费，应停止实现并在 `tech-done.md` 中记录原因，而不是重复包装。
- 因工作区已有大量未提交变更，worker 必须避免回滚他人改动，并只编辑文件范围内内容。

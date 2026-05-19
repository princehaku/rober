# Sprint 2026.05.19_23-24 Real Material Followup Escalation Status - Tech Done

## 1. Sprint 类型和交付结论

- sprint_type: epic
- closeout 时间：2026-05-19 23:23 Asia/Shanghai。
- 本轮已从 planning commit `93dd965` 进入实现收口，完成 `real_material_followup_escalation_status` PC gate、Robot safe alias、mobile/web 只读 panel、接口文档、产品文档和 evidence artifacts。
- 证据边界保持 `software_proof_docker_real_material_followup_escalation_status_gate`、`source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。
- 本轮不证明真实 O5 external proof、Objective 1 HIL、PR #5 hardware material、PR #4 route/elevator field pass、真实手机/browser、Nav2/fixed-route、dropoff/cancel completion 或 delivery success。

## 2. Hardware Infra Owner

实际改动：

- `pc-tools/evidence/real_material_followup_escalation_status.py`
- `tests/test_real_material_followup_escalation_status.py`
- `docs/interfaces/real_material_followup_escalation_status.md`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status.json`
- `sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status_summary.json`

完成内容：

- 新增 `trashbot.real_material_followup_escalation_status.v1` artifact 和 `trashbot.real_material_followup_escalation_status_summary.v1` summary。
- 覆盖 `o5_external`、`o1_pr5_hardware`、`pr4_route_elevator`、`o4_real_phone` 四类 material group。
- 每组输出 `field_owner`、`due_status`、`blocked_reason`、`next_required_evidence`、`escalation_level`、`rerun_command`、`rerun_status_summary`、source template/intake status 和 review route。
- O1 / PR #5 保持 `PRRT_kwDOSWB9286CJ3tX` 为 `blocked_pending_real_materials`，并要求 mandatory sensor baseline cite `docs/vendor/VENDOR_INDEX.md` 及其指向本地 vendor sources。

验证结果：

```bash
test -f docs/vendor/VENDOR_INDEX.md
# passed

python3 -m unittest tests/test_real_material_followup_escalation_status.py
# Ran 6 tests ... OK

python3 pc-tools/evidence/real_material_followup_escalation_status.py --help
# passed

python3 pc-tools/evidence/real_material_followup_escalation_status.py --output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status.json --summary-output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status_summary.json
# generated artifact and summary
```

剩余风险：

- 这只是现场材料 follow-up/escalation software proof。真实 WAVE ROVER/UART/HIL、真实 2D LiDAR / ToF source/procurement/installation/wiring/power/calibration/HIL-entry、真实 external proof 和 PR #5 `PRRT_kwDOSWB9286CJ3tX` closure 仍未发生。

## 3. Autonomy Algorithm Owner 只读咨询

咨询结论：

- `pr4_route_elevator` required materials 必须继续沿用 `nav2_fixed_route_runtime_log`、`route_completion_signal`、`field_task_record`、`elevator_door_state`、`target_floor_confirmation`、`human_assistance_record`、`dropoff_cancel_material`、`delivery_result`。
- `due_status` / status 必须保持 `not_proven` 或 pending real materials 语义，避免 `pass`、`complete`、`success`、`delivery_success=true` 或 field-pass wording。

剩余风险：

- 本轮未新增真实 route/elevator execution、Nav2/fixed-route runtime、route completion signal、现场 task record、电梯门状态、楼层确认、人工协助记录、dropoff/cancel material 或 delivery result。

## 4. Robot Platform Owner

实际改动：

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `docs/interfaces/operator_gateway_diagnostics.md`
- `docs/interfaces/ros_contracts.md`

完成内容：

- 新增 `robot_diagnostics_real_material_followup_escalation_status_summary` safe alias。
- 支持 summary-only consumption for `real_material_followup_escalation_status`、`real_material_followup_escalation_status_summary`、nested diagnostics summaries、explicit refs 和 `TRASHBOT_REAL_MATERIAL_FOLLOWUP_ESCALATION_STATUS(_SUMMARY)`。
- 缺 summary、schema/boundary mismatch、unsafe `evidence_ref`、raw manifest/materials、credentials、checksums、success/control fields 或 unsafe copy 时 fail closed。
- Robot command path 未改变；没有新增 Start/Confirm/Cancel、ACK、Nav2、WAVE ROVER、HIL、material collection 或 movement authorization。

验证结果：

```bash
python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
# Ran 217 tests ... OK

python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
# passed
```

剩余风险：

- 这是 Robot diagnostics `software_proof` / `not_proven` 只读展示，不证明真实材料、真实硬件、真实手机/browser、O5 public-cloud evidence、PR #4 route/elevator field pass、PR #5 hardware closure 或 HIL。

## 5. User Touchpoint Full-Stack Owner

实际改动：

- `mobile/web/app.js`
- `mobile/web/styles.css`
- `mobile/web/test_mobile_web_entrypoint.py`
- `mobile/fixtures/mobile_web_status.fixture.json`
- `mobile/web/fixtures/status.json`
- `docs/product/mobile_user_flow.md`

完成内容：

- mobile/web 新增只读 “真实材料升级状态” panel。
- 优先消费 `robot_diagnostics_real_material_followup_escalation_status_summary`，并兼容 `real_material_followup_escalation_status_summary` 或 `phone_safe_real_material_followup_escalation_status_summary`。
- 展示四类固定 material group、safe `evidence_ref`、field owner、due_status、blocked_reason、next_required_evidence、escalation_level、rerun command/status summary 和 fail-closed boundary。
- 不新增控制按钮，不改变 Start Delivery、Confirm Dropoff、Cancel gating。

验证结果：

```bash
python3 mobile/web/test_mobile_web_entrypoint.py
# Ran 141 tests ... OK

node --check mobile/web/app.js
# passed
```

剩余风险：

- 本地 mobile/web panel 不是真实 iPhone/Android、production app、PWA prompt/user choice、true phone/browser acceptance 或现场手机验收材料。

## 6. Product Closeout 集成验收

本轮 Product closeout 复跑并通过：

```bash
python3 -m unittest tests/test_real_material_followup_escalation_status.py
# Ran 6 tests ... OK

python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py
# Ran 217 tests ... OK

python3 mobile/web/test_mobile_web_entrypoint.py
# Ran 141 tests ... OK

node --check mobile/web/app.js
# passed

python3 -m py_compile pc-tools/evidence/real_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py
# passed

python3 pc-tools/evidence/real_material_followup_escalation_status.py --output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status.json --summary-output sprints/2026.05.19_23-24_real-material-followup-escalation-status/evidence/real_material_followup_escalation_status_summary.json
# regenerated artifact and summary

rg -n "real_material_followup_escalation_status|robot_diagnostics_real_material_followup_escalation_status_summary|Objective 5|Objective 1|PRRT_kwDOSWB9286CJ3tX|blocked_pending_real_materials|due_status|blocked_reason|next_required_evidence|escalation_level|software_proof_docker_real_material_followup_escalation_status_gate|not_proven|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" ...
# matched required contract strings

git diff --check -- ...
# passed
```

## 7. 偏差和剩余风险

- 偏差：并行实现期间 `tech-done.md` 一度只保留 Robot 段落，Product closeout 已重新合并 Hardware、Autonomy consult、Robot、Full-Stack 和集成验收结果。
- 无代码级失败残留。
- 剩余风险仍是外部事实未到位：真实 O5 external proof、真实 Objective 1 WAVE ROVER/UART/HIL、PR #5 hardware materials、PR #4 route/elevator field materials、真实手机/browser、Nav2/fixed-route、dropoff/cancel completion 和 delivery success 均未证明。

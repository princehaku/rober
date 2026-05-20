# pc-tools/ — PC 工作站开发工具集

本目录是 `ros_rbs` 的 **PC 端 dev tool 集合**：路径学习、视觉样本标注/复核、证据交叉检查、模型训练等工作流，统一收口在这里。

> 当前状态：sprint `2026.05.13_01-02_codebase-restructure-four-tier` 的 Phase 1 已建立脚手架；真正的工具脚本会在 Phase 4 由 `autonomy-engineer` 从 `onboard/src/ros2_trashbot_nav/` 和 `scripts/` 搬到这里。

## 用途（What lives here）

- 给 **开发者 / 操作员 PC** 用的离线工具集合，不上车、不进云。
- 消费 onboard 产出的产物（route CSV、phone API JSON、vision sample manifest 等），生成可视化、标注、训练数据集等下游产物。

## 子目录

| 目录 | 用途 | 主要文件（P4 完成后） |
| --- | --- | --- |
| `pc-tools/route/` | 路径学习 + debug Web | `route_debug_web.py`（标准库 HTML/JSON API 路径复盘）、`route_csv_to_yaml.py`（CSV → YAML 转换，仍在 onboard） |
| `pc-tools/labeling/` | 视觉样本标注 / 复核 GUI 占位 | 见 `CONTRACT.md`；本 sprint 不实现真实 GUI，留给 autonomy 后续 sprint |
| `pc-tools/evidence/` | 证据交叉检查、phone browser gate | `evidence_crosscheck.py`、`phone_browser_acceptance_gate.py` |
| `pc-tools/training/` | YOLO / RT-DETR 训练入口、数据集组织规范 | 占位，留给 autonomy 后续 sprint |

## 部署目标（Deployment target）

- **环境**：PC 工作站（macOS / Linux / Windows + WSL），Python **3.10+**。
- **可选**：ROS2 dev container（如需在 PC 上本地 simulate `rclpy` 行为时）。
- **网络**：可访问 onboard 产出的数据目录（NAS / 本地拷贝 / scp），可选连云端 OSS / S3 拉样本。
- **不上车**：本目录的工具运行在 PC 上，不会被 Orange Pi 调度；不要把 `pc-tools/*` 误打入 `onboard/docker/humble` 镜像。

## 运行时契约（Runtime contracts）

- **与 `onboard/` 的契约**：消费 onboard 产生的 route CSV、phone-safe JSON、vision sample manifest（`trashbot.vision_samples.v1`）；异步、离线、单向。
- **与 `cloud-relay/` 的契约**：可选消费 cloud-relay 暴露的 phone-safe JSON 做证据交叉检查；不写回。
- **与 `mobile/` 没有直接契约**：mobile 是手机用户视角，pc-tools 是开发者视角，两者独立演进。

## 当前状态（本轮）

- `pc-tools/evidence/evidence_crosscheck.py`、`pc-tools/evidence/phone_browser_acceptance_gate.py` 已从仓库根 `scripts/` 迁入。
- `pc-tools/route/route_debug_web.py` 已落地为 PC 工作站独立工具：只读消费 fixed-route status JSON、可选 task/task_record JSON 或 task_record dir，以及可选 elevator-route reconciliation artifact/summary，输出 `schema=trashbot.pc_route_debug_console.v1`、父级 `evidence_boundary=software_proof_docker_pc_route_debug_console_gate`、`route_progress`、`keyframe_preflight`、recent task summary、嵌套 `route_elevator_reconciliation.evidence_boundary=software_proof_docker_pc_route_elevator_console_integration_gate`、`not_proven` 和 `delivery_success=false`。
- `route_csv_to_yaml.py` 仍位于 `onboard/src/ros2_trashbot_nav/`（可选后续再抽到 `pc-tools/route/` 以降低与 colcon 的耦合）。
- `labeling/`、`training/` 仍为占位与契约说明。

## real material manifest template

`pc-tools/evidence/real_material_evidence_intake.py` 可以生成 field owner
交付用的真实材料 manifest template / submission pack：

```bash
python3 pc-tools/evidence/real_material_evidence_intake.py \
  --template-output sprints/2026.05.19_22-23_real-material-manifest-template/evidence/real_material_manifest_template.json \
  --template-evidence-ref field-material-template-2026-05-19T22-23Z \
  --output /tmp/real_material_evidence_intake.json \
  --summary-output /tmp/real_material_evidence_intake_summary.json
```

模板输出 `schema=trashbot.real_material_manifest_template.v1`，覆盖
`o5_external`、`o1_pr5_hardware`、`pr4_route_elevator` 和 `o4_real_phone` 四类
material group。每个 required item 都带 `summary_hint`、`material_ref_hint`、
`owner_handoff`、`objective_ref` 和 `next_action`，并固定
`source=software_proof`、`status=not_proven`、`delivery_success=false`、
`primary_actions_enabled=false`、`safe_to_control=false`。PR #5 review thread
继续记录为 `PRRT_kwDOSWB9286CJ3tX`，状态为
`blocked_pending_real_materials_not_closed`。

生成 template 不会改变原 intake artifact/summary 的 exit code。这个模板只帮助现场
owner 收集真实材料，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、
真实手机、外部云、OSS/CDN、DB/queue 或 4G，也不证明 HIL、delivery success、
PR #5 closure、PR #4 route/elevator completion、O4 phone acceptance 或 O5 external proof。

## hardware sensor HIL-entry callback intake

`pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py` 是
`hardware_sensor_hil_entry_execution_pack` 之后的 PC-only callback material
入口：

```bash
python3 pc-tools/evidence/hardware_sensor_hil_entry_callback_intake_gate.py \
  --execution-pack-json /tmp/hardware_sensor_hil_entry_execution_pack.json \
  --callback-json /tmp/hardware_sensor_hil_entry_callback_materials.json \
  --output /tmp/hardware_sensor_hil_entry_callback_intake.json \
  --summary-output /tmp/hardware_sensor_hil_entry_callback_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.hardware_sensor_hil_entry_callback_intake.v1`，
summary 使用
`schema=trashbot.hardware_sensor_hil_entry_callback_intake_summary.v1`，证据边界固定为
`software_proof_docker_hardware_sensor_hil_entry_callback_intake_gate`。该 gate
只接受 execution pack artifact、summary 或 nested wrapper summary，以及脱敏的
2D LiDAR SKU/source/receipt、ToF SKU/source/receipt、mounting、wiring、power、
calibration 和 HIL-entry operator result callback summary/ref。

所有输出都固定保持 `source=software_proof`、`hardware_material_pending`、
`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。
缺 execution pack、缺 callback materials、unsupported schema/boundary、
`evidence_ref` mismatch、弱 bool/source 合同、raw credentials、raw serial/UART、
完整本机路径、complete artifacts、checksums、HIL pass / field pass /
delivery success copy、`delivery_success=true` 或 `primary_actions_enabled=true`
都会 fail closed。

vendor/source boundary 只引用 `docs/vendor/VENDOR_INDEX.md` 及其列出的本地
WAVE ROVER / UART JSON / firmware/vendor-app 资料。该 gate 不访问 ROS graph、
Nav2 runtime、serial/UART、WAVE ROVER、真实 2D LiDAR / ToF、HIL rig、真实手机、
外部云、OSS/CDN、DB/queue 或 4G；ready 状态只表示脱敏 callback 材料可进入
下一轮人工 review，不是 HIL pass、PRRT_kwDOSWB9286CJ3tX 关闭、field pass、
Objective 5 external proof 或 delivery success。

## PC route debug console

`pc-tools/route/route_debug_web.py` 是本地 PC console，不依赖 ROS2，不 import `ros2_trashbot_*`，不访问硬件、serial/UART、Nav2 runtime、ROS graph 或网络外部服务：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --elevator-route-reconciliation /tmp/elevator_route_evidence_reconciliation.json \
  --once-json
```

启动 HTML/API：

```bash
python3 pc-tools/route/route_debug_web.py \
  --status-json /tmp/trashbot_fixed_route_status.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --elevator-route-reconciliation /tmp/elevator_route_evidence_reconciliation_summary.json \
  --host 127.0.0.1 \
  --port 8766
```

API `/api/status` 与 `/api/summary` 返回同一份只读 summary：`pc_route_debug_console`、父级 `software_proof_docker_pc_route_debug_console_gate`、`route_progress`、`keyframe_preflight`、当前位置/当前 checkpoint、目标点、匹配状态、失败原因、recent task/task_record summary、嵌套 `route_elevator_reconciliation`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。该结果只证明 PC/local/Docker 软件复盘材料可读，不是真实 fixed-route/Nav2 实跑、真实电梯、HIL、dropoff/cancel completion 或 delivery success。

`route_elevator_reconciliation` 只接受 `trashbot.elevator_route_evidence_reconciliation.v1` 或 `trashbot.elevator_route_evidence_reconciliation_summary.v1`，输入边界必须是 `software_proof_docker_elevator_route_evidence_reconciliation_gate`。HTML/API 中该嵌套字段的 `evidence_boundary` 是 `software_proof_docker_pc_route_elevator_console_integration_gate`，并用 `source_evidence_boundary` 保留输入复账边界；只展示 safe evidence ref、status/verdict、same-evidence-ref 状态、source states、missing/mismatch 摘要、operator next steps、boundary、`not_proven` 和 `safe_copy`；缺失、坏 JSON、unsupported schema/boundary、unsafe copy、success claim 或 control claim 都会 blocked/not_proven。

## route/elevator field-session handoff

`pc-tools/evidence/route_elevator_field_session_handoff.py` 把 PC route debug console、route completion signal 和 elevator-route reconciliation 的 artifact 或 summary 整理成下一次真实现场 session 的交接材料：

```bash
python3 pc-tools/evidence/route_elevator_field_session_handoff.py \
  --pc-route-debug-json /tmp/pc_route_debug_console.json \
  --route-completion-json /tmp/route_task_completion_signal.json \
  --elevator-route-reconciliation-json /tmp/elevator_route_evidence_reconciliation.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_elevator_field_session_handoff.json \
  --summary-output /tmp/route_elevator_field_session_handoff_summary.json
```

输出 artifact 使用 `schema=trashbot.route_elevator_field_session_handoff.v1`，summary 使用 `schema=trashbot.route_elevator_field_session_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_elevator_field_session_handoff_gate`。核心字段包括 `source_summaries`、`field_session_manifest`、`required_materials`、`operator_handoff`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

`required_materials` 只是现场回填清单，覆盖 `nav2_fixed_route_runtime_log.json`、`route_completion_signal.json`、`task_record.json`、`door_state.json`、`target_floor_confirmation.json`、`human_assistance_operator_note.md`、`dropoff_or_cancel_completion.json`、`delivery_result.json` 和 `diagnostics_mobile_safe_summary.json`。这些材料后续必须使用同一 safe `evidence_ref`；本 gate 不读取 Nav2 runtime、ROS graph、serial/UART、WAVE ROVER、真实电梯、手机设备、外部云、OSS/CDN、DB/queue 或 4G。

缺输入、坏 JSON、unsupported schema/boundary/source、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或成功文案都会 fail closed。`robot_diagnostics_summary` 和 `mobile_readonly_summary` 只输出白名单摘要，不包含 raw artifact、本机完整路径、checksum、traceback、凭证、DB/queue URL、OSS AK/SK、ROS topic、`/cmd_vel`、serial/UART 或 WAVE ROVER 参数。该 gate 是现场 session handoff，不是 delivery_success=false 之外的送达证明，也不是 Objective 5 external proof；`not_proven` 必须继续展示。

## route/task terminal completion rehearsal

`pc-tools/evidence/route_task_terminal_completion_rehearsal.py` 只读 route status、task record、既有 `route_task_completion_signal` artifact/summary，以及可选 dropoff/cancel material summary，生成终态复账 rehearsal：

```bash
python3 pc-tools/evidence/route_task_terminal_completion_rehearsal.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_task_completion_signal.json \
  --dropoff-material-json /tmp/dropoff_completion.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_terminal_completion_rehearsal.json \
  --summary-output /tmp/route_task_terminal_completion_rehearsal_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_terminal_completion_rehearsal.v1`，summary 使用 `schema=trashbot.route_task_terminal_completion_rehearsal_summary.v1`，证据边界固定为 `software_proof_docker_route_task_terminal_completion_rehearsal_gate`。核心字段包括 `terminal_verdict`、safe `evidence_ref`、`dropoff` / `cancel` material status、`failure_reason`、`recovery_reason`、`operator_next_steps`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 gate 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、真实手机、外部云、OSS/CDN、DB/queue 或 4G。缺 required source、坏 JSON、unsupported schema/boundary、same `evidence_ref` mismatch、unsafe copy、raw path/credential/ROS topic/serial/WAVE ROVER/HIL/success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_terminal_completion_rehearsal_not_proven` 只表示 Docker/local 终态复账材料可读，不是真实 dropoff/cancel completion、delivery success、HIL 或 Objective 5 external proof。

## route/task terminal review decision

`pc-tools/evidence/route_task_terminal_review_decision.py` 只读上一轮 `route_task_terminal_completion_rehearsal` artifact 或 summary，把终态复账材料转成 operator review decision、`owner_handoff`、`next_required_evidence` 和 field retest request guidance：

```bash
python3 pc-tools/evidence/route_task_terminal_review_decision.py \
  --terminal-rehearsal-json /tmp/route_task_terminal_completion_rehearsal.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_terminal_review_decision.json \
  --summary-output /tmp/route_task_terminal_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_terminal_review_decision.v1`，summary 使用 `schema=trashbot.route_task_terminal_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_route_task_terminal_review_decision_gate`。核心字段包括 `review_decision`、`decision_reason`、safe `evidence_ref`、`owner_handoff`、`next_required_evidence`、`field_retest_request_guidance`、`software_proof`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 gate 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、真实手机、外部云、OSS/CDN、DB/queue 或 4G。缺输入、坏 JSON、unsupported schema/boundary、same `evidence_ref` mismatch、unsafe copy、raw path/credential/ROS topic/serial/WAVE ROVER/HIL/success wording、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_operator_terminal_review_not_proven` 只表示 Docker/local 终态复账材料足够进入 operator review 或 field retest 请求准备，不是真实 dropoff/cancel completion、delivery success、HIL、真实手机设备或 Objective 5 external proof。

## task_terminal_field_material_review_decision

`pc-tools/evidence/task_terminal_field_material_review_decision.py` 只读上一轮 `task_terminal_field_material_intake` artifact、summary 或 Robot safe alias，把 returned/missing materials 转成 metadata-only 复核决策：

```bash
python3 pc-tools/evidence/task_terminal_field_material_review_decision.py \
  --intake-json /tmp/task_terminal_field_material_intake_summary.json \
  --evidence-ref terminal-field-material-review-001 \
  --output /tmp/task_terminal_field_material_review_decision.json \
  --summary-output /tmp/task_terminal_field_material_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.task_terminal_field_material_review_decision.v1`，summary 使用 `schema=trashbot.task_terminal_field_material_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_task_terminal_field_material_review_decision_gate`。核心字段包括 `review_decision`、`accepted_materials`、`missing_materials`、`rejected_materials`、`blocked_materials`、`owner_handoff`、`next_required_evidence`、`rerun_guidance`、`same_evidence_ref_required=true`、`software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false` 和 `safe_to_control=false`。

Decision mapping 固定覆盖 `ready_for_owner_handoff_not_proven`、`needs_required_material_backfill_not_proven`、`blocked_rejected_or_unsafe_materials_not_proven`、`blocked_evidence_ref_mismatch_not_proven` 和 `blocked_missing_or_unsupported_intake_not_proven`。该 gate 服务 Objective 3 / PR #4 的现场材料复核链路，也保留 PR #5 真实材料 blocker 边界；它不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。ready 只表示 owner handoff 可复核，不是真实 route/elevator field pass、真实 dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest execution pack

`pc-tools/evidence/route_task_field_retest_execution_pack.py` 只读上一轮 `route_task_terminal_review_decision` artifact、summary 或 wrapper/nested JSON，把 review decision、owner handoff、next required evidence 和 field retest guidance 整理成下一次真实现场复测可用的 execution pack：

```bash
python3 pc-tools/evidence/route_task_field_retest_execution_pack.py \
  --review-decision-json /tmp/route_task_terminal_review_decision.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_execution_pack.json \
  --summary-output /tmp/route_task_field_retest_execution_pack_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_execution_pack.v1`，summary 使用 `schema=trashbot.route_task_field_retest_execution_pack_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_execution_pack_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`required_field_materials`、`rerun_commands`、`operator_handoff`、`field_retest_checklist`、`boundary`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

`required_field_materials` 默认列出下一次复测必须回填的真实 Nav2/fixed-route runtime log、route completion signal、task record、operator field note 和 mobile/diagnostics safe summary；如果 source review decision 提到 elevator，还会追加 door state、target floor confirmation 和 human assistance note。该 pack 服务 Objective 2 / Objective 3 的路线-任务现场复测准备，不推进 Objective 5 external proof。

该 gate 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue 或 4G。缺输入、坏 JSON、unsupported schema/boundary、unsafe copy、missing `evidence_ref`、`same_evidence_ref_required=false`、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_execution_pack_not_proven` 只表示 Docker/local software proof 足以生成复测材料清单，不是真实 field pass、HIL、真实手机/browser、delivery success 或 Objective 5 external proof。

## route/task field retest session handoff

`pc-tools/evidence/route_task_field_retest_session_handoff.py` 只读上一轮 `route_task_field_retest_execution_pack` artifact、summary 或 wrapper/nested JSON，把复测执行包转换成下一次现场复测 session 的交接 artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_session_handoff.py \
  --execution-pack-json /tmp/route_task_field_retest_execution_pack.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --session-owner "Autonomy Algorithm Engineer" \
  --output /tmp/route_task_field_retest_session_handoff.json \
  --summary-output /tmp/route_task_field_retest_session_handoff_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_session_handoff.v1`，summary 使用 `schema=trashbot.route_task_field_retest_session_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_session_handoff_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`session_handoff`、`operator_handoff`、`material_placeholders`、`material_paths`、`rerun_commands`、`field_callback_checklist`、`safe_copy`、`fail_closed_summary`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 handoff 要求 source execution pack 已列出下一次真实现场回填材料：Nav2/fixed-route runtime log、route completion signal、task record、door state、target floor confirmation、human assistance note、dropoff/cancel completion 和 delivery result。`material_placeholders` 只给出相对 placeholder path 和 required fields，便于现场回填；本 gate 不读取这些真实材料，也不访问 ROS graph、Nav2 runtime、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue 或 4G。

缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、缺 required materials、placeholder-only materials、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_session_handoff_not_proven` 只表示 Docker/local software proof 足以生成现场 session 交接材料，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest material pack

`pc-tools/evidence/route_task_field_retest_material_pack.py` 读取现场复测回填目录 `--material-dir`，把八类材料打包并校验成 sanitized artifact / summary，供现有 `route_task_field_retest_result_intake.py` 和 `route_task_field_retest_result_reconciliation.py` 消费：

```bash
python3 pc-tools/evidence/route_task_field_retest_material_pack.py \
  --material-dir /tmp/route_task_field_retest_materials \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_material_pack.json \
  --summary-output /tmp/route_task_field_retest_material_pack_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_material_pack.v1`，summary 使用 `schema=trashbot.route_task_field_retest_material_pack_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_material_pack_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`material_manifest`、`material_completeness`、`missing_materials`、`rejected_materials`、`operator_next_steps`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

material pack 固定校验八类材料：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion` 和 `delivery_result`。每类材料必须使用同一 safe `evidence_ref`；缺失材料、placeholder/TBD/sample、evidence ref mismatch、raw path、credential、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER detail、unsafe success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed 或进入 rejected/missing。

该 gate 只输出目录材料的脱敏状态和拒绝原因，不复制 raw filesystem path、credential、完整 artifact、traceback、checksum、raw ROS topic、`/cmd_vel`、串口/UART 细节或硬件参数。`ready_for_field_retest_material_pack_not_proven` 只表示 Docker/local software proof 足以把目录材料交给 result intake/reconciliation 继续复账，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest operator drill

`pc-tools/evidence/route_task_field_retest_operator_drill.py` 只读上一节 material pack artifact、summary 或 wrapper/nested JSON，把 `material_pack -> result_intake -> result_reconciliation` 的 PC 操作顺序整理成 operator drill artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_operator_drill.py \
  --material-pack-json /tmp/route_task_field_retest_material_pack_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_operator_drill.json \
  --summary-output /tmp/route_task_field_retest_operator_drill_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_operator_drill.v1`，summary 使用 `schema=trashbot.route_task_field_retest_operator_drill_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_operator_drill_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`material_pack_command`、`result_intake_command`、`result_reconciliation_command`、`required_outputs`、`missing_material_prompts`、`operator_callback_checklist`、`rerun_notes`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 drill 不读取材料目录或真实日志，只把 material pack summary 的 missing/rejected 状态转成现场同学可复跑的命令、必需输出和 callback checklist。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_operator_drill_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_operator_drill_gate` 已把复测材料链的操作顺序复账清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest drill console

`pc-tools/evidence/route_task_field_retest_drill_console.py` 只读上一节 operator drill artifact、summary 或 wrapper/nested JSON，把 `material_pack -> result_intake -> result_reconciliation` 的命令标签、安全 checklist、缺失材料提示和 operator callback checklist 汇总成 PC console artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_drill_console.py \
  --operator-drill-json /tmp/route_task_field_retest_operator_drill_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_drill_console.json \
  --summary-output /tmp/route_task_field_retest_drill_console_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_drill_console.v1`，summary 使用 `schema=trashbot.route_task_field_retest_drill_console_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_drill_console_gate`。核心字段包括 safe `evidence_ref`、`console_status`、`same_evidence_ref_required=true`、material pack / result intake / result reconciliation command labels、`safe_checklist`、`missing_material_prompts`、`operator_callback_checklist`、`rerun_notes`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 console 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、operator drill 未 ready、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_drill_console_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_drill_console_gate` 已把 operator drill 的复测演练控制台摘要整理清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest acceptance brief

`pc-tools/evidence/route_task_field_retest_acceptance_brief.py` 只读上一节 drill console artifact、summary 或 wrapper/nested JSON，把现场入口前置条件、执行 checklist、pass/fail criteria、必需证据包、owner handoff 和 rerun notes 整理成 PC acceptance brief artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_brief.py \
  --drill-console-json /tmp/route_task_field_retest_drill_console_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_brief.json \
  --summary-output /tmp/route_task_field_retest_acceptance_brief_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_brief.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_brief_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_brief_gate`。核心字段包括 safe `evidence_ref`、`acceptance_status`、`field_entry_prerequisites`、`execution_checklist`、`pass_fail_criteria`、`required_evidence_packet`、`owner_handoff`、`rerun_notes`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_brief` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 brief gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

必需证据包固定包含 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。该 brief 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、drill console 未 ready、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_acceptance_brief_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_brief_gate` 已把现场验收简报整理清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest acceptance review decision

`pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py` 只读上一节 acceptance brief artifact、summary 或 wrapper/nested JSON，把验收简报转成现场验收前的 metadata-only review decision：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_review_decision.py \
  --acceptance-brief-json /tmp/route_task_field_retest_acceptance_brief_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_review_decision.json \
  --summary-output /tmp/route_task_field_retest_acceptance_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_review_decision.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_review_decision_gate`。核心字段包括 `review_decision`、safe `evidence_ref`、`material_status`、`owner_handoff`、`next_required_evidence`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

Decision mapping 固定包含 `ready_for_controlled_field_retest_not_proven`、`needs_route_elevator_material_backfill_not_proven`、`needs_owner_handoff_not_proven`、`evidence_ref_mismatch_rerun_not_proven`、`blocked_acceptance_brief_not_ready`、`unsupported_acceptance_brief_schema_not_proven` 和 `rejected_unsafe_acceptance_brief_claim_not_proven`。该 gate 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser；ready 只表示 Docker/local software proof 已把受控现场复跑前的 review decision 口径整理清楚，不是真实现场通过、真实 delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest acceptance execution pack

`pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py` 只读上一节 acceptance review decision artifact、summary、wrapper/nested JSON，或 `file:<path>` / `env:<VAR>` source，把 review decision 转成现场复跑执行包：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_pack.py \
  --acceptance-review-decision-json /tmp/route_task_field_retest_acceptance_review_decision_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_pack.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_pack_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_pack.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_pack_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate`。核心字段包括 `execution_pack_status`、`review_decision_source`、`owner_checklist`、`rerun_commands`、`safe_evidence_bundle`、`required_route_elevator_materials`、`handoff_owner`、`next_required_evidence`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_pack` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 execution-pack gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

required route/elevator materials 固定包含 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。该 execution pack 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、review decision 未 ready、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_acceptance_execution_pack_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_pack_gate` 已把现场复跑 checklist、rerun commands 和 safe evidence bundle 整理清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest acceptance execution callback intake

`pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py` 只读上一节 acceptance execution pack artifact、summary、wrapper/nested JSON，或 `file:<path>` / `env:<VAR>` source，再读取 safe callback packet，把现场回执整理成 metadata-only callback intake artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_intake.py \
  --acceptance-execution-pack-json /tmp/route_task_field_retest_acceptance_execution_pack_summary.json \
  --callback-json /tmp/safe_callback_packet.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_callback_intake.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_callback_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_callback_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_callback_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate`。核心字段包括 `callback_intake_status`、`source_execution_pack`、`safe_callback_packet`、`evidence_ref_status`、`required_route_elevator_materials`、`received_materials`、`missing_materials`、`rejected_materials`、`owner_next_steps`、`next_required_evidence`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_intake` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 callback-intake gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

required route/elevator materials 固定覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion、delivery_result 和 diagnostics/mobile safe summary。该 callback intake 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported source/callback schema 或 boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、execution pack 未 ready、safe callback packet 字段弱类型、missing/rejected materials、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、checksum、完整 raw artifact、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_acceptance_execution_callback_intake_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_callback_intake_gate` 已把 safe callback packet 复账为只读摘要，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest acceptance execution callback review decision

`pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py` 只读上一轮 `route_task_field_retest_acceptance_execution_callback_intake` artifact、summary 或 wrapper/nested JSON，把 received/missing/rejected 材料状态转成 metadata-only review decision：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_decision.py \
  --callback-intake-json /tmp/route_task_field_retest_acceptance_execution_callback_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_callback_review_decision.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_callback_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_decision.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate`。核心字段包括 `review_decision`、`status_reasons`、safe `evidence_ref`、`source_callback_intake`、`field_rerun_readiness`、`owner_handoff`、`next_required_evidence`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_decision` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 callback-review-decision gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Decision mapping 固定包含 `ready_for_controlled_field_rerun`、`needs_material_backfill`、`evidence_ref_mismatch_rerun` 和 fail-closed unsafe/unsupported 状态。该 gate 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、callback intake 未 ready、missing/rejected/empty materials、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、checksum、完整 raw artifact、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_controlled_field_rerun` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_decision_gate` 已把回执材料复核为受控现场复跑前的只读决策，不是真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。

## route/task field retest acceptance execution callback review handoff

`pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py` 只读上一节 `route_task_field_retest_acceptance_execution_callback_review_decision` artifact、summary 或 wrapper/nested JSON，把复核决策转成 metadata-only handoff artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_callback_review_handoff.py \
  --callback-review-decision-json /tmp/route_task_field_retest_acceptance_execution_callback_review_decision_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_callback_review_handoff.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_callback_review_handoff_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_callback_review_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate`。核心字段包括 `handoff_status`、safe `evidence_ref`、source review decision/status、`owner_handoff`、`handoff_package`、`safe_rerun_hint`、`next_required_evidence`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_callback_review_handoff` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 callback-review-handoff gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Handoff mapping 固定包含 `ready_for_acceptance_execution_callback_review_handoff`、`needs_owner_follow_up`、`needs_acceptance_execution_callback_rerun`、`evidence_ref_mismatch_rerun` 和 `blocked_unsafe_review_handoff`。该 handoff gate 不读取真实材料目录、不触发现场复跑、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、unsupported review decision、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、checksum、完整 raw artifact、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_acceptance_execution_callback_review_handoff` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_callback_review_handoff_gate` 已把上一轮 review decision 交接成只读 handoff package，不是真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。

## route/task field retest acceptance execution handoff intake

`pc-tools/evidence/route_task_field_retest_acceptance_execution_handoff_intake.py` 只读上一节 `route_task_field_retest_acceptance_execution_callback_review_handoff` artifact、summary 或 wrapper/nested JSON，并可选读取 owner callback/intake JSON，把现场交接回执整理成 metadata-only handoff intake artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_handoff_intake.py \
  --handoff-json /tmp/route_task_field_retest_acceptance_execution_callback_review_handoff_summary.json \
  --owner-intake-json /tmp/owner_handoff_intake.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_handoff_intake.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_handoff_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_handoff_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_handoff_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate`。核心字段包括 `handoff_intake_status`、safe `evidence_ref`、source handoff status、owner acknowledgement state、`owner_handoff`、`next_required_evidence`、`safe_rerun_hint`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_handoff_intake` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 handoff-intake gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Handoff intake mapping 固定包含 `ready_for_controlled_field_rerun_queue`、`needs_owner_ack`、`needs_acceptance_execution_handoff_backfill`、`evidence_ref_mismatch_rerun` 和 `blocked_unsafe_handoff_intake`。该 handoff intake gate 不读取真实材料目录、不触发现场复跑、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、source handoff 未 ready、owner ack 缺失或证据号不一致、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、checksum、完整 raw artifact、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_controlled_field_rerun_queue` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_handoff_intake_gate` 已把 owner handoff intake 交接成只读排队状态，不是真实 route/elevator field pass、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。

## route/task field retest acceptance execution rerun queue

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py` 只读上一节 `route_task_field_retest_acceptance_execution_handoff_intake` artifact、summary 或 wrapper/nested JSON，并可选读取 owner-safe queue request JSON，把现场交接回执转换成 metadata-only 受控复跑队列 artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_queue.py \
  --handoff-intake-json /tmp/route_task_field_retest_acceptance_execution_handoff_intake_summary.json \
  --queue-request-json /tmp/owner_rerun_queue_request.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_rerun_queue.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_rerun_queue_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_queue.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_queue_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate`。核心字段包括 `rerun_queue_status`、safe `evidence_ref`、source handoff intake status、owner acknowledgement state、owner-safe queue request、`owner_handoff`、`next_required_evidence`、`safe_rerun_hint`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_queue` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 rerun-queue gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Rerun queue mapping 固定包含 `queued_for_controlled_field_rerun_not_proven`、`needs_owner_ack_before_queue`、`needs_acceptance_execution_rerun_queue_backfill`、`evidence_ref_mismatch_rerun_queue`、`blocked_unsafe_rerun_queue` 和 `blocked_unsupported_handoff_intake`。该 queue gate 不读取真实材料目录、不触发现场复跑、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、source handoff intake 未 ready、owner ack 缺失、queue request evidence_ref mismatch、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、checksum、完整 raw artifact、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`queued_for_controlled_field_rerun_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_queue_gate` 已把 owner-safe handoff intake 转成受控复跑队列候选，不是真实 route/elevator field pass、真实现场复跑、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。

## route/task field retest acceptance execution rerun result intake

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py` 只读上一节 `route_task_field_retest_acceptance_execution_rerun_queue` artifact、summary 或 wrapper/nested JSON，并可选读取 owner-safe rerun result packet，把受控复跑队列和结果回填转换成 metadata-only result review intake artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_intake.py \
  --rerun-queue-json /tmp/route_task_field_retest_acceptance_execution_rerun_queue_summary.json \
  --rerun-result-json /tmp/safe_rerun_result_packet.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_rerun_result_intake.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_rerun_result_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate`。核心字段包括 `rerun_result_intake_status`、safe `evidence_ref`、source rerun queue status、owner-safe rerun result packet、`owner_handoff`、`next_required_evidence`、`safe_review_hint`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_intake` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 rerun-result-intake gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Rerun result intake mapping 固定包含 `ready_for_acceptance_execution_rerun_result_review_not_proven`、`needs_acceptance_execution_rerun_result_backfill`、`evidence_ref_mismatch_rerun_result`、`blocked_unsafe_rerun_result` 和 `blocked_unsupported_rerun_queue`。该 result intake gate 不读取真实材料目录、不触发现场复跑、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。缺 safe rerun result packet、bad JSON、unsupported queue schema/boundary、缺 safe `evidence_ref`、证据号不一致、source rerun queue 未 queued、result packet 未 ready、缺 result material category、unsafe copy、raw path/credential/DB/queue URL/ROS topic/`/cmd_vel`/serial/UART/WAVE ROVER low-level controls、checksum、完整 raw artifact、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_acceptance_execution_rerun_result_review_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_intake_gate` 已把受控复跑队列和 safe result packet 转成可复核入口，不是真实 route/elevator field pass、真实现场复跑、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 O5 external proof。

## route/task field retest acceptance execution rerun result review decision

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py` 只读上一节 `route_task_field_retest_acceptance_execution_rerun_result_intake` artifact、summary 或 wrapper/nested JSON，把受控复跑结果 intake 转换成 metadata-only review decision artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_decision.py \
  --rerun-result-intake-json /tmp/route_task_field_retest_acceptance_execution_rerun_result_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_rerun_result_review_decision.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate`。核心字段包括 `decision_status`、safe `evidence_ref`、source rerun result intake status、provided/missing material categories、`review_decision_package`、`owner_handoff`、`next_required_evidence`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_decision` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 rerun-result-review-decision gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Rerun result review decision mapping 固定包含 `ready_for_acceptance_execution_rerun_result_handoff`、`needs_acceptance_execution_rerun_result_backfill`、`evidence_ref_mismatch_rerun_result`、`blocked_unsafe_rerun_result` 和 `blocked_unsupported_rerun_result_intake`。该 review decision gate 不读取真实材料目录、不触发现场复跑、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。缺 route completion signal、task record、Nav2/fixed-route runtime log、dropoff/cancel completion、delivery result、elevator door state、target floor confirmation 或 human assistance record 会进入 `needs_acceptance_execution_rerun_result_backfill`。unsupported intake schema/boundary、缺 safe `evidence_ref`、证据号不一致、unsafe copy、raw path/credential/DB/queue URL/ROS topic/`/cmd_vel`/serial/UART/WAVE ROVER low-level controls、checksum、完整 raw artifact、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_acceptance_execution_rerun_result_handoff` 只表示 Docker/local `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_decision_gate` 已把 safe intake 转成可交接复核决策，不是真实 route/elevator field pass、真实现场复跑、Nav2/fixed-route proof、task record/completion signal、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

### route/task field retest acceptance execution rerun result review handoff

`pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py` 只读上一节 `route_task_field_retest_acceptance_execution_rerun_result_review_decision` artifact、summary 或 wrapper/nested JSON，把 safe review decision 转换成 PR #4 真实 route/elevator 现场回填准备层的 metadata-only owner handoff artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.py \
  --rerun-result-review-decision-json /tmp/route_task_field_retest_acceptance_execution_rerun_result_review_decision_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_acceptance_execution_rerun_result_review_handoff.json \
  --summary-output /tmp/route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff.v1`，summary 使用 `schema=trashbot.route_task_field_retest_acceptance_execution_rerun_result_review_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_acceptance_execution_rerun_result_review_handoff_gate`。核心字段包括 `handoff_status`、safe `evidence_ref`、`owner_role`、`owner_handoff`、`next_required_evidence`、`rerun_summary`、`safe_copy`、`source=software_proof`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_route_task_field_retest_acceptance_execution_rerun_result_review_handoff` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 rerun-result-review-handoff gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Rerun result review handoff mapping 固定包含 `ready_for_acceptance_execution_rerun_result_owner_handoff`、`needs_acceptance_execution_rerun_result_material_backfill`、`evidence_ref_mismatch_rerun_result_handoff_blocked`、`blocked_unsafe_rerun_result_handoff_copy` 和 `blocked_unsupported_rerun_result_review_decision`。上一轮 `ready_for_acceptance_execution_rerun_result_handoff` 且 safe `evidence_ref` 匹配、`review_decision_package.ready=true`、材料类别齐全时映射为 `ready_for_acceptance_execution_rerun_result_owner_handoff`。缺真实门状态、楼层确认、人工协助记录、Nav2/fixed-route runtime log、task record/completion signal、dropoff/cancel completion 或 delivery result 会进入 `needs_acceptance_execution_rerun_result_material_backfill`。证据号不一致、缺 safe `evidence_ref` 或 `same_evidence_ref_required` 不是布尔 true 会进入 `evidence_ref_mismatch_rerun_result_handoff_blocked`。unsafe copy、raw artifact、本机路径、checksum、credential、DB/queue URL、ROS topic、`/cmd_vel`、serial/UART/WAVE ROVER low-level controls、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会进入 `blocked_unsafe_rerun_result_handoff_copy`。unsupported review decision schema/boundary、bad JSON 或 missing JSON 会进入 `blocked_unsupported_rerun_result_review_decision`。该 gate 不读取真实材料目录、不解析 raw artifact、不访问本地 path/checksum/credentials/DB/queue URL/ROS topic/serial/UART、不执行任何机器人动作；`ready_for_acceptance_execution_rerun_result_owner_handoff` 只表示 PR #4 owner handoff package 已由 safe decision 准备好，不是真实现场通过、O5/O1 proof、HIL、真实手机/browser 或 delivery success。

### field evidence rerun material dispatch

`pc-tools/evidence/field_evidence_rerun_material_dispatch.py` 只读 route/elevator rerun review handoff、`real_material_followup_escalation_status`、`real_material_evidence_intake`、`real_material_manifest_template` 或兼容 wrapper/nested summary，把真实现场复跑所需材料聚合为 owner 可执行派发包：

```bash
python3 pc-tools/evidence/field_evidence_rerun_material_dispatch.py \
  --source-json /tmp/supported_review_handoff_or_real_material_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/field_evidence_rerun_material_dispatch.json \
  --summary-output /tmp/field_evidence_rerun_material_dispatch_summary.json
```

输出 artifact 使用 `schema=trashbot.field_evidence_rerun_material_dispatch.v1`，summary 使用 `schema=trashbot.field_evidence_rerun_material_dispatch_summary.v1`，证据边界固定为 `software_proof_docker_field_evidence_rerun_material_dispatch_gate`。核心字段包括 `dispatch_status`、safe `evidence_ref`、required material groups（`real route completion signal`、`real field task record`、`real Nav2/fixed-route runtime log`、`real elevator door summary`、`real target floor / floor arrival summary`、`real human-assistance summary`、`real dropoff completion`、`real cancel completion`、`real delivery result`、`real phone/browser evidence`）、`owner_work_orders`、`rerun_commands`、`callback_packet_requirements`、`safe_copy`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false` 和 `primary_actions_enabled=false`。

顶层 acceptance command 可用 `python3 -m unittest tests.test_field_evidence_rerun_material_dispatch` 复用 `pc-tools/evidence` 下的离线围栏测试；该入口只证明本地 `field_evidence_rerun_material_dispatch` gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Mapping 固定包含 `ready_for_field_evidence_rerun_material_dispatch_not_proven`、`evidence_ref_mismatch_field_evidence_rerun_material_dispatch_blocked`、`blocked_unsafe_field_evidence_rerun_material_dispatch_copy` 和 `blocked_unsupported_field_evidence_rerun_material_dispatch_source`。缺输入、bad JSON、unsupported schema/boundary、source 不是 `source=software_proof` 或缺 `not_proven`、证据号不一致、unsafe copy、raw path、credential、DB/queue URL、ROS topic、serial/UART/WAVE ROVER detail、checksum、完整 artifact、success/control claim、`safe_to_control=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_evidence_rerun_material_dispatch_not_proven` 只表示同一 safe `evidence_ref` 的现场复跑材料派发包已准备好，不是真实 route/elevator field pass、真实 Nav2/fixed-route proof、dropoff/cancel completion、delivery success、HIL、O5 external proof、PR #5 resolved 或真实 phone/browser 证据。

### field evidence rerun callback intake

`pc-tools/evidence/field_evidence_rerun_callback_intake.py` 只读上一节 `field_evidence_rerun_material_dispatch` artifact/summary，以及现场 owner 回传的 safe callback packet，把十类真实材料回执归类为 `accepted`、`missing`、`rejected` 或 `blocked`：

```bash
python3 pc-tools/evidence/field_evidence_rerun_callback_intake.py \
  --dispatch-json /tmp/field_evidence_rerun_material_dispatch_summary.json \
  --callback-json /tmp/field_evidence_rerun_callback_packet.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/field_evidence_rerun_callback_intake.json \
  --summary-output /tmp/field_evidence_rerun_callback_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.field_evidence_rerun_callback_intake.v1`，summary 使用 `schema=trashbot.field_evidence_rerun_callback_intake_summary.v1`，证据边界固定为 `software_proof_docker_field_evidence_rerun_callback_intake_gate`。核心字段包括 `callback_intake_status`、safe `evidence_ref`、same-evidence-ref status、`accepted_materials`、`missing_materials`、`rejected_materials`、`blocked_materials`、`material_counts`、`next_required_evidence`、`safe_copy`、`source=software_proof`、`not_proven`、`safe_to_control=false`、`delivery_success=false` 和 `primary_actions_enabled=false`。

required material classes 固定覆盖 `real route completion signal`、`real field task record`、`real Nav2/fixed-route runtime log`、`real elevator door summary`、`real target floor / floor arrival summary`、`real human-assistance summary`、`real dropoff completion`、`real cancel completion`、`real delivery result` 和 `real phone/browser evidence`。顶层验收可用 `python3 -m unittest tests.test_field_evidence_rerun_callback_intake` 复用离线围栏测试；该入口只证明本地 callback-intake gate 的 fail-closed contract 可复跑，仍属于 Docker/local software proof。

Mapping 固定包含 `ready_for_field_evidence_rerun_callback_intake_not_proven`、`blocked_field_evidence_rerun_callback_materials_not_ready`、`evidence_ref_mismatch_field_evidence_rerun_callback_intake_blocked`、`blocked_unsafe_field_evidence_rerun_callback_intake_copy` 和 `blocked_unsupported_field_evidence_rerun_callback_intake_source`。缺 dispatch 输入、缺 callback packet、bad JSON、unsupported schema/boundary、source 不是 `source=software_proof` 或缺 `not_proven`、证据号不一致、弱类型 `same_evidence_ref_required`、unknown material class、非法 classification、unsafe copy、raw path、credential、DB/queue URL、ROS topic、serial/UART/WAVE ROVER detail、checksum、完整 artifact、traceback、success/control claim、`safe_to_control=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_evidence_rerun_callback_intake_not_proven` 只表示同一 safe `evidence_ref` 的现场 owner 回执已被复账成只读摘要，不是真实 route/elevator field pass、真实 Nav2/fixed-route proof、dropoff/cancel completion、delivery success、HIL、O5 external proof、PR #5 resolved 或真实 phone/browser 证据。

## route/task field retest evidence dispatch

`pc-tools/evidence/route_task_field_retest_evidence_dispatch.py` 只读上一节 acceptance brief artifact、summary 或 wrapper/nested JSON，把必需证据包派发成 material owners、recommended filenames、same-evidence-ref rule、backfill order、callback checklist 和 fail-closed rerun notes：

```bash
python3 pc-tools/evidence/route_task_field_retest_evidence_dispatch.py \
  --acceptance-brief-json /tmp/route_task_field_retest_acceptance_brief_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_evidence_dispatch.json \
  --summary-output /tmp/route_task_field_retest_evidence_dispatch_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_evidence_dispatch.v1`，summary 使用 `schema=trashbot.route_task_field_retest_evidence_dispatch_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_evidence_dispatch_gate`。核心字段包括 dispatch status、safe `evidence_ref`、material owners、recommended filenames、same-evidence-ref rule、backfill order、callback checklist、fail-closed rerun notes、required evidence packet、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

required evidence packet 固定包含 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。该 dispatch gate 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、acceptance brief 未 ready、必需证据包漏项、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_evidence_dispatch_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_evidence_dispatch_gate` 已把现场证据包派发口径整理清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest callback review decision

`pc-tools/evidence/route_task_field_retest_callback_review_decision.py` 只读上一轮 `route_task_field_retest_callback_intake` artifact、summary 或 wrapper/nested JSON，把 received/missing/same-evidence-ref/next-backfill 状态转成 metadata-only review decision：

```bash
python3 pc-tools/evidence/route_task_field_retest_callback_review_decision.py \
  --callback-intake-json /tmp/route_task_field_retest_callback_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_callback_review_decision.json \
  --summary-output /tmp/route_task_field_retest_callback_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_callback_review_decision.v1`，summary 使用 `schema=trashbot.route_task_field_retest_callback_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_callback_review_decision_gate`。核心字段包括 `review_decision`、safe `evidence_ref`、source intake status、received filenames summary、missing materials、same-evidence-ref verdict、next required evidence、result-intake readiness、owner handoff、rerun commands、fail-closed notes、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

Decision mapping 固定包含 `ready_for_result_intake`、`needs_material_backfill`、`evidence_ref_mismatch_rerun`、`unsupported_callback_schema`、`blocked_unsafe_callback` 和 `blocked_success_claim`。required evidence packet 固定覆盖 Nav2/fixed-route runtime log、route completion signal、task record、door_state、target_floor_confirmation、human_assistance_note、dropoff_or_cancel_completion 和 delivery_result。

该 review decision gate 不读取真实材料目录，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser。缺输入、坏 JSON、unsupported schema/boundary、same `evidence_ref` mismatch、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_result_intake` 只表示 Docker/local software proof 足以把 sanitized callback metadata 交给后续 result intake 复账，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest review result handoff

`pc-tools/evidence/route_task_field_retest_review_result_handoff.py` 只读上一节 `route_task_field_retest_callback_review_decision` artifact、summary 或 wrapper/nested JSON，把 review decision 转成 result-intake 前的 metadata-only handoff artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_review_result_handoff.py \
  --callback-review-json /tmp/route_task_field_retest_callback_review_decision_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_review_result_handoff.json \
  --summary-output /tmp/route_task_field_retest_review_result_handoff_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_review_result_handoff.v1`，summary 使用 `schema=trashbot.route_task_field_retest_review_result_handoff_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_review_result_handoff_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`handoff_status`、`source_review_decision`、`result_intake_readiness`、`owner_handoff`、`rerun_commands`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

Decision mapping 固定为：`ready_for_result_intake` -> `ready_for_result_intake_handoff` / `ready_for_result_material_intake`；`needs_material_backfill` -> `blocked_until_material_backfill` / `not_ready`；`evidence_ref_mismatch_rerun` -> `blocked_until_same_evidence_ref_rerun` / `not_ready`；`unsupported_callback_schema` -> `blocked_unsupported_source_schema` / `not_ready`；`blocked_unsafe_callback` 或 `blocked_success_claim` -> `blocked_unsafe_source_review` / `not_ready`。

该 handoff gate 不读取真实材料目录、不触发 result intake、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，也不执行任何机器人动作。缺输入、坏 JSON、unsupported schema/boundary、same `evidence_ref` mismatch、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_result_intake_handoff` 只表示 Docker/local `software_proof_docker_route_task_field_retest_review_result_handoff_gate` 已把上一轮 review decision 交接给 result-intake 前置面，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest callback intake

`pc-tools/evidence/route_task_field_retest_callback_intake.py` 只读上一节 evidence dispatch artifact、summary 或 wrapper/nested JSON，以及现场同学回传的 sanitized callback JSON，把推荐文件名收到状态、缺项、same-`evidence_ref` 对齐结果和下一步回填动作整理成 metadata-only callback intake artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_callback_intake.py \
  --dispatch-json /tmp/route_task_field_retest_evidence_dispatch_summary.json \
  --callback-json /tmp/route_task_field_retest_sanitized_callback.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_callback_intake.json \
  --summary-output /tmp/route_task_field_retest_callback_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_callback_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_callback_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_callback_intake_gate`。核心字段包括 intake status、safe `evidence_ref`、received filenames summary、missing materials、same-evidence-ref match result、next backfill action、callback checklist result、owner handoff、fail-closed rerun notes、required evidence packet、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

callback JSON 只允许现场同学已经脱敏的元数据字段：recommended filename received status、safe `evidence_ref`、missing material ids、next backfill action、owner callback note 和 callback checklist result。该 gate 故意不读取真实材料目录、不打开推荐文件名、不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue、4G 或真实手机/browser，因为它的职责只是确认回执元数据是否可继续交给 result intake。缺输入、坏 JSON、unsupported schema/boundary、证据号不一致、弱类型 callback 字段、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_callback_intake_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_callback_intake_gate` 已把现场回执元数据复账清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest result intake

`pc-tools/evidence/route_task_field_retest_result_intake.py` 只读现场复测回填后的 result artifact、summary、session handoff artifact/summary、review-result handoff artifact/summary 或 wrapper/nested JSON，把同一 `evidence_ref` 下的结果材料元数据整理成 fail-closed result intake artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_intake.py \
  --result-json /tmp/route_task_field_retest_session_handoff_summary_with_results.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_intake.json \
  --summary-output /tmp/route_task_field_retest_result_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_result_intake.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_intake_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_intake_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`result_materials`、`material_completeness`、`missing_materials`、`operator_next_steps`、`field_callback_checklist`、`rerun_summary`、`safe_copy`、`fail_closed_phone_safe_summary`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 intake 检查八类结果材料摘要：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion` 和 `delivery_result`。review-result handoff 只把上游 review decision 交给 result-intake 前置面，不能裁剪这八类固定 result materials；任何缺项仍按 `blocked_missing_result_materials` 处理。它只处理 JSON 元数据，不读取 ROS graph、Nav2 runtime、真实日志文件内容、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue 或 4G。

缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、缺任一结果材料、placeholder-only materials、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_result_intake_not_proven` 只表示 Docker/local software proof 足以接收同一证据号下的八类现场复测结果材料摘要，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest result reconciliation

`pc-tools/evidence/route_task_field_retest_result_reconciliation.py` 只读上一轮 result intake、session handoff、execution pack、result artifact/summary 或 wrapper/nested JSON，把同一 `evidence_ref` 下的八类现场结果材料复账成 PC-side reconciliation artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_reconciliation.py \
  --result-json /tmp/route_task_field_retest_result_intake.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_reconciliation.json \
  --summary-output /tmp/route_task_field_retest_result_reconciliation_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_result_reconciliation.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_reconciliation_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_reconciliation_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、`same_evidence_ref_status`、`result_materials`、`missing_materials`、`mismatch_reasons`、`operator_next_steps`、`rerun_summary`、`field_callback_checklist`、`fail_closed_phone_safe_summary`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。当输入是 result-intake artifact / summary，且其中 `source_result.schema` 指向 `trashbot.route_task_field_retest_review_result_handoff.v1` 或 `trashbot.route_task_field_retest_review_result_handoff_summary.v1` 时，artifact、summary 和 phone-safe summary 会保留 `source_result_intake_schema`、`source_result_intake_status`、`source_review_result_handoff_schema`、`source_review_result_handoff_status` 这四个 lineage 字段；gate 不读取 raw handoff artifact，也不改变八类 required result materials。

reconciliation 固定复账八类结果材料：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion` 和 `delivery_result`。它不读取 ROS graph、Nav2 runtime、真实日志文件内容、硬件、真实手机/browser、外部云、OSS/CDN、DB/queue、4G 或任何真实现场文件内容。

缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、缺任一结果材料、placeholder-only materials、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_result_reconciliation_not_proven` 只表示 Docker/local software proof 足以复账八类结果材料摘要，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest result acceptance packet

`pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py` 只读上一轮 `route_task_field_retest_result_reconciliation` artifact、summary 或 wrapper/nested JSON，把 safe lineage、八类 required result materials、缺口、owner handoff、rerun commands 和 pass/fail criteria 汇总成 PC acceptance packet artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_acceptance_packet.py \
  --reconciliation-json /tmp/route_task_field_retest_result_reconciliation.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_acceptance_packet.json \
  --summary-output /tmp/route_task_field_retest_result_acceptance_packet_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_result_acceptance_packet.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_acceptance_packet_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate`。核心字段包括 safe `evidence_ref`、`same_evidence_ref_required=true`、safe lineage、`required_result_materials`、`result_material_statuses`、`missing_materials`、`mismatch_reasons`、`acceptance_gap_summary`、`owner_handoff`、`rerun_commands`、`pass_fail_criteria`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

acceptance packet 固定汇总八类结果材料：`nav2_or_fixed_route_runtime_log`、`route_completion_signal`、`task_record`、`door_state`、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion` 和 `delivery_result`。它只消费 reconciliation 已白名单化的 material status、safe lineage 和 summary 字段，不读取 raw handoff artifact、ROS graph、Nav2 runtime、真实日志内容、serial/UART、WAVE ROVER、真实手机/browser、外部云、OSS/CDN、DB/queue 或 4G。

缺输入、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、reconciliation 未 ready、缺任一 result material、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success phrasing、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_result_acceptance_packet_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_result_acceptance_packet_gate` 已把结果验收包整理清楚；pass/fail criteria 是下一次现场复测的判断口径，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## route/task field retest result acceptance backfill

`pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py` 只读上一轮 `route_task_field_retest_result_acceptance_packet` artifact、summary 或 wrapper/nested JSON，并读取 `--material-dir` 中的八类回填材料，把 packet status 与 material completeness、same-`evidence_ref` alignment、missing/rejected material categories、owner handoff、rerun commands 和 pass/fail decision inputs 汇总成 PC acceptance backfill artifact / summary：

```bash
python3 pc-tools/evidence/route_task_field_retest_result_acceptance_backfill.py \
  --acceptance-packet-json /tmp/route_task_field_retest_result_acceptance_packet_summary.json \
  --material-dir /tmp/route_task_field_retest_materials \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_retest_result_acceptance_backfill.json \
  --summary-output /tmp/route_task_field_retest_result_acceptance_backfill_summary.json
```

输出 artifact 使用 `schema=trashbot.route_task_field_retest_result_acceptance_backfill.v1`，summary 使用 `schema=trashbot.route_task_field_retest_result_acceptance_backfill_summary.v1`，证据边界固定为 `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate`。核心字段包括 safe `evidence_ref`、`source_acceptance_packet`、safe lineage、`material_states`、`material_completeness`、`same_evidence_ref_alignment`、`acceptance_backfill_gap_summary`、`owner_handoff`、`rerun_commands`、`pass_fail_decision_inputs`、`safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

acceptance backfill 固定检查八类回填材料：`nav2_or_fixed_route_runtime_log`（Nav2/fixed-route runtime log）、`route_completion_signal`、`task_record`、`door_state`（door state）、`target_floor_confirmation`、`human_assistance_note`、`dropoff_or_cancel_completion` 和 `delivery_result`（delivery result）。它只读取 acceptance packet 已白名单化的 summary 字段和 material-dir 中的脱敏元数据，不读取 raw upstream artifact，不访问真实 Nav2/fixed-route runtime、serial/UART、WAVE ROVER、真实手机/browser、外部云、OSS/CDN、DB/queue 或 4G。

缺 source、坏 JSON、unsupported schema/boundary、缺 safe `evidence_ref`、证据号不一致、弱类型 `same_evidence_ref_required`、acceptance packet 未 ready、缺任一回填材料、placeholder-only materials、unsafe copy、raw path/credential/ROS topic/serial/UART/WAVE ROVER detail、success/control claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_field_retest_result_acceptance_backfill_not_proven` 只表示 Docker/local `software_proof_docker_route_task_field_retest_result_acceptance_backfill_gate` 已把 packet 后的八类材料回填入口复账清楚，不是真实 field pass、真实 Nav2/fixed-route、真实电梯、dropoff/cancel completion、delivery success、HIL、真实手机/browser 或 Objective 5 external proof。

## mobile route/elevator field-device precheck

`pc-tools/evidence/mobile_route_elevator_field_device_precheck.py` 只读 route/elevator field-session handoff，生成或校验真实设备/现场前检查 summary：

```bash
python3 pc-tools/evidence/mobile_route_elevator_field_device_precheck.py \
  --route-elevator-handoff-json /tmp/route_elevator_field_session_handoff.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/mobile_route_elevator_field_device_precheck.json \
  --summary-output /tmp/mobile_route_elevator_field_device_precheck_summary.json
```

校验已有 summary 时使用：

```bash
python3 pc-tools/evidence/mobile_route_elevator_field_device_precheck.py \
  --precheck-json /tmp/mobile_route_elevator_field_device_precheck_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.mobile_route_elevator_field_device_precheck.v1`，summary 使用 `schema=trashbot.mobile_route_elevator_field_device_precheck_summary.v1`，copy/export 白名单使用 `schema=trashbot.mobile_route_elevator_field_device_precheck_copy.v1`；证据边界固定为 `software_proof_docker_mobile_route_elevator_field_device_precheck_gate`。核心字段包括 `same_evidence_ref_required=true`、`route_elevator_handoff_summary`、`required_route_elevator_field_materials`、`device_pwa_observation_checklist`、`mobile_copy_summary`、`not_proven`、`real_device_observed=false`、`pwa_install_prompt_observed=false`、`route_elevator_field_pass=false`、`dropoff_completion=false`、`cancel_completion=false`、`delivery_success=false` 和 `primary_actions_enabled=false`。

`required_route_elevator_field_materials` 是 route/elevator 现场材料清单，要求同一 `evidence_ref` 回填 Nav2/fixed-route runtime log、route status、route completion signal、task record、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、delivery result 和 diagnostics mobile-safe summary。`device_pwa_observation_checklist` 是真实设备/PWA 观察清单，要求记录真实设备浏览器加载、viewport/touch target、PWA install prompt/user choice、precheck panel 可见、copy/export 白名单和主操作仍 disabled。

该 helper/gate 只输出 `software_proof` / `not_proven`；不访问 ROS graph、Nav2 runtime、serial/UART、真实电梯、真实手机、外部云、OSS/CDN、DB/queue 或 4G。缺 handoff、坏 JSON、unsupported schema/boundary/source、same-evidence-ref mismatch、unsafe copy、`real_device_observed=true`、`pwa_install_prompt_observed=true`、`route_elevator_field_pass=true`、`dropoff_completion=true`、`cancel_completion=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 blocked。该 precheck 用于现场前检查，不证明真实设备、真实 PWA prompt/user choice、真实 route/elevator field pass、真实 dropoff/cancel completion、真实 delivery success、HIL 或 Objective 5 external proof。

## mobile_field_material_intake

`pc-tools/evidence/mobile_field_material_intake.py` 接在 `mobile_route_elevator_field_device_precheck` 之后，用同一 safe `evidence_ref` 摄取现场前/现场后材料，并生成 `mobile_field_material_intake` summary：

```bash
python3 pc-tools/evidence/mobile_field_material_intake.py \
  --precheck-json /tmp/mobile_route_elevator_field_device_precheck_summary.json \
  --device-pwa-observation-json /tmp/device_pwa_observation.json \
  --route-elevator-field-materials-json /tmp/route_elevator_field_materials.json \
  --nav2-fixed-route-runtime-log-json /tmp/nav2_fixed_route_runtime_log.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_completion_signal.json \
  --dropoff-cancel-material-status-json /tmp/dropoff_cancel_material_status.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/mobile_field_material_intake.json \
  --summary-output /tmp/mobile_field_material_intake_summary.json
```

校验已有 summary 时使用：

```bash
python3 pc-tools/evidence/mobile_field_material_intake.py \
  --intake-json /tmp/mobile_field_material_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.mobile_field_material_intake.v1`，summary 使用 `schema=trashbot.mobile_field_material_intake_summary.v1`，copy/export 白名单使用 `schema=trashbot.mobile_field_material_intake_copy.v1`；证据边界固定为 `software_proof_docker_mobile_field_material_intake_gate`。核心字段包括 `same_evidence_ref_required=true`、`material_statuses`、`required_route_elevator_field_material_names`、`device_pwa_observation_checklist_names`、`mobile_copy_summary`、`not_proven`、`route_elevator_field_pass=false`、`nav2_fixed_route_completed=false`、`dropoff_completion=false`、`cancel_completion=false`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 intake gate 要求同一 `evidence_ref` 下至少提供真实设备/PWA observation checklist、route/elevator field materials、Nav2/fixed-route runtime log、task record、completion signal、dropoff/cancel material status。缺失、坏 JSON、非 object、placeholder、same-evidence-ref mismatch、unsafe copy、成功文案、`real_device_observed=true`、`route_elevator_field_pass=true`、`nav2_fixed_route_completed=true`、`dropoff_completion=true`、`cancel_completion=true`、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。

`mobile_field_material_intake` 只输出 `software_proof` / `not_proven`，用于现场材料回填前/回填后检查。它不访问 ROS graph、Nav2 runtime、serial/UART、真实手机、真实 route/elevator field pass、真实 dropoff/cancel completion、真实 delivery success、HIL、外部云、OSS/CDN、DB/queue 或 4G；也不证明 Objective 5 external proof。

## mobile_field_material_review_decision

`pc-tools/evidence/mobile_field_material_review_decision.py` 只读上一轮 `mobile_field_material_intake` artifact 或 summary，把 intake 材料状态转换成 owner handoff、next-required-evidence 和 review decision：

```bash
python3 pc-tools/evidence/mobile_field_material_review_decision.py \
  --intake-json /tmp/mobile_field_material_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/mobile_field_material_review_decision.json \
  --summary-output /tmp/mobile_field_material_review_decision_summary.json
```

需要直接给 Robot diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/mobile_field_material_review_decision.py \
  --intake-json /tmp/mobile_field_material_intake_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.mobile_field_material_review_decision.v1`，summary 使用 `schema=trashbot.mobile_field_material_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_mobile_field_material_review_decision_gate`。核心字段包括 `review_decision`、`owner handoff`、`owner_handoff`、`next-required-evidence`、`next_required_evidence`、`blocked_materials`、`same_evidence_ref_required=true`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

## mobile_field_material_retest_request

`pc-tools/evidence/mobile_field_material_retest_request.py` 只读上一轮 `mobile_field_material_review_decision` artifact 或 summary，把 Product/owner handoff 和 `next_required_evidence` 转成下一次 route/elevator field retest request：

```bash
python3 pc-tools/evidence/mobile_field_material_retest_request.py \
  --review-json /tmp/mobile_field_material_review_decision.json \
  --output /tmp/mobile_field_material_retest_request.json \
  --summary-output /tmp/mobile_field_material_retest_request_summary.json
```

需要直接给 Robot diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/mobile_field_material_retest_request.py \
  --review-json /tmp/mobile_field_material_review_decision_summary.json \
  --once-json
```

输出 artifact 使用 `schema=trashbot.mobile_field_material_retest_request.v1`，summary 使用 `schema=trashbot.mobile_field_material_retest_request_summary.v1`，证据边界固定为 `software_proof_docker_mobile_field_material_retest_request_gate`。核心字段包括 `request_verdict`、`route/elevator material checklist`、`route_elevator_material_checklist`、`next_required_evidence`、`next-required-evidence`、`retest_commands`、`source_review`、`same_evidence_ref_required=true`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

`ready_for_route_elevator_field_retest_request_not_proven` 只表示上一轮 review decision 可转成下一次现场复测材料请求；它不是真实 route/elevator、Nav2/fixed-route、dropoff/cancel、delivery success、HIL、WAVE ROVER/UART 或 Objective 5 external proof。缺 review、坏 JSON、unsupported schema/boundary、弱类型 `same_evidence_ref_required`、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或 success wording 时，CLI 会 fail closed，并继续输出 `not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

review decision 的枚举至少覆盖 `blocked_missing_real_phone_or_pwa_observation`、`blocked_missing_route_elevator_field_materials`、`blocked_missing_nav2_or_fixed_route_runtime_log`、`blocked_missing_same_evidence_ref_task_record_or_completion_signal`、`blocked_missing_dropoff_or_cancel_completion` 和 `ready_for_owner_handoff_not_proven`；unsupported schema/boundary、missing JSON、placeholder、unsafe copy、same-evidence-ref mismatch 或 success wording 会 fail closed 为 `blocked_invalid_intake`。owner handoff 只映射到 `Full-stack`、`Robot`、`Autonomy` 或 `Product closeout`。

该 review decision 仍只是 `software_proof` / `not_proven`：它不访问 ROS graph、Nav2 runtime、serial/UART、真实手机、真实 route/elevator field pass、真实 Nav2/fixed-route、真实 dropoff/cancel completion、真实 delivery success、HIL、WAVE ROVER/UART、外部云、OSS/CDN、DB/queue 或 4G；也不证明 Objective 5 external proof。

## hardware_baseline_review

`pc-tools/evidence/hardware_baseline_review_gate.py` 只读 `docs/product/production_hardware_boundary.md`，把 Navigation/Sensing Baseline 转成 Autonomy 可消费的 sensor responsibility summary：

```bash
python3 pc-tools/evidence/hardware_baseline_review_gate.py \
  --output /tmp/hardware_baseline_review.json \
  --summary-output /tmp/hardware_baseline_review_summary.json
```

需要直接给 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/hardware_baseline_review_gate.py --once-json
```

输出 artifact 使用 `schema=trashbot.hardware_baseline_review_gate.v1`，summary 使用 Robot diagnostics 可直接接收的 `schema=trashbot.hardware_baseline_review_summary.v1`，证据边界固定为 `software_proof_docker_hardware_baseline_review_gate`。核心字段包括 `hardware_baseline_review`、`sensor_responsibility_summary`、`2D LiDAR`、`monocular`、`ToF`、`hardware_material_pending`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 gate 明确责任边界：`2D LiDAR` 是 SLAM/Nav2 主链 product baseline / pending material；`monocular` 只承接电梯门/目标楼层语义证据；`ToF` 是 near-field safety gate，不是主建图输入。缺 production boundary、缺任一责任短语、`delivery_success=true`、`primary_actions_enabled=true`、`LiDAR field pass`、`ToF field pass` 或 HIL 成功断言都会 fail closed。该结果只证明 PC/local/Docker 能把产品硬件基线转成 autonomy responsibility summary，不证明真实 LiDAR/ToF field pass、真实 monocular 语义通过、真实 SLAM/Nav2 field run、HIL 或 delivery_success。

## hardware_baseline_source_alignment

`pc-tools/evidence/hardware_baseline_source_alignment_gate.py` 只读 `docs/product/production_hardware_boundary.md` 和 `docs/vendor/VENDOR_INDEX.md`，把默认硬件集、Navigation/Sensing target baseline、vendor/source coverage 和 LiDAR/ToF 缺口转成可重复 PC evidence gate：

```bash
python3 pc-tools/evidence/hardware_baseline_source_alignment_gate.py \
  --output /tmp/hardware_baseline_source_alignment.json \
  --summary-output /tmp/hardware_baseline_source_alignment_summary.json
```

需要直接给 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/hardware_baseline_source_alignment_gate.py --once-json
```

输出 artifact 使用 `schema=trashbot.hardware_baseline_source_alignment.v1`，summary 使用 `schema=trashbot.hardware_baseline_source_alignment_summary.v1`，证据边界固定为 `software_proof_docker_hardware_baseline_source_alignment_gate`。核心字段包括 `default_hardware_set_summary`、`target_sensor_baseline_summary`、`vendor_source_boundary`、`missing_alignment_items`、`hardware_material_pending`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 gate 明确采用 `docs/vendor/VENDOR_INDEX.md` 及其本地 vendor coverage：Orange Pi Zero 3、WAVE ROVER、UART newline-delimited JSON、WAVE ROVER ESP32 firmware/vendor app，以及 camera/tutorial material。这个 coverage 只说明当前资料边界，不证明项目 2D LiDAR 或 ToF SKU/source、采购、安装、接线、标定、HIL entry、Nav2/SLAM field pass、near-field safety pass 或 delivery success。缺 product boundary、缺 vendor index、缺关键 source alignment 语义、`delivery_success=true`、`primary_actions_enabled=true`、HIL 成功断言或 field-pass 成功断言都会 fail closed。

## hardware_sensor_procurement_intake

`pc-tools/evidence/hardware_sensor_procurement_intake_gate.py` 是硬件采购/安装/标定材料进入 Autonomy 主链前的只读 intake gate。它接收 Hardware worker 维护的 sensor procurement artifact，并生成 Autonomy、Robot diagnostics 和 sprint 复核可消费的 summary：

```bash
python3 pc-tools/evidence/hardware_sensor_procurement_intake_gate.py \
  --intake-json /tmp/hardware_sensor_procurement_intake.json \
  --summary-output /tmp/hardware_sensor_procurement_intake_summary.json
```

输出 artifact 使用 `schema=trashbot.hardware_sensor_procurement_intake_gate.v1`，summary 使用 `schema=trashbot.hardware_sensor_procurement_intake_summary.v1`，证据边界固定为 `software_proof_docker_hardware_sensor_procurement_intake_gate`。summary 只说明采购/安装/标定材料是否足够进入下一轮 Autonomy 计划复核，必须继续显示 `software_proof`、`not_proven`、`primary_actions_enabled=false` 和 safe `evidence_ref`。

Autonomy 责任边界如下：

- `2D LiDAR`: 只在完成采购、安装、标定和后续现场复核后，才是 SLAM/Nav2 主建图与定位链路的 target；intake summary 本身不把 LiDAR 加入当前 fixed-route 或 SLAM/Nav2 运行证据。
- `ToF`: 只作为近场 safety gate target，用于保守进入/退出、避障或停车前检查；它不是主 SLAM 输入，也不能替代 2D LiDAR 的地图/定位责任。
- `monocular`: 保留 elevator door / target-floor semantic evidence role，用于门状态、目标楼层和人工协助材料链；它不承担主定位、主建图或 fixed-route 完成判定。

该 gate 不访问 ROS graph、Nav2 runtime、SLAM map、serial/UART、WAVE ROVER、真实电梯、真实手机、外部云、OSS/CDN、DB/queue 或 4G。缺 procurement artifact、坏 JSON、unsupported schema/boundary、unsafe copy、控制放行字段或成功断言时，都必须保持 blocked/not_proven，并把下一步留给 Hardware procurement、Autonomy 标定计划或 Product closeout 复核。

## hardware_sensor_hil_entry_config_precheck

`pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py` 是 future HIL-entry sensor config 的 dependency-free PC gate。它只验证 config 是否把 sensor count、ToF channel count、thresholds、frame IDs、safety policy 和 evidence refs 参数化成可审查结构，不读取真实硬件、串口、ROS graph、sensor driver 或网络：

```bash
python3 pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py \
  --config-json /tmp/hardware_sensor_hil_entry_config.json \
  --summary-output /tmp/hardware_sensor_hil_entry_config_precheck_summary.json
```

没有 `--config-json` 时，CLI 会使用内置 default sample 证明 gate 可在 Docker-only/PC 环境运行；该 sample 仍是 `not_proven`，不是采购、安装、标定或 HIL 证据。需要把缺 config 作为 blocked case 验证时使用：

```bash
python3 pc-tools/evidence/hardware_sensor_hil_entry_config_precheck_gate.py --no-default-sample
```

输出 artifact 使用 `schema=trashbot.hardware_sensor_hil_entry_config_precheck.v1`，summary 使用 `schema=trashbot.hardware_sensor_hil_entry_config_precheck_summary.v1`，证据边界固定为 `software_proof_docker_hardware_sensor_hil_entry_config_precheck_gate`。summary 只暴露 precheck status、safe evidence refs、sensor count summary、thresholds summary、frame IDs summary、safety policy summary、`next_required_evidence`、`owner_handoff`、sanitized `safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 gate 明确采用 `docs/vendor/VENDOR_INDEX.md` 作为资料边界：Orange Pi Zero 3、WAVE ROVER、UART/JSON、firmware/vendor app 与 camera/tutorial coverage 只说明本地资料存在，不证明项目 2D LiDAR / ToF 已采购、安装、接线、供电、标定或通过 HIL-entry。缺 config、坏 JSON、unsupported schema、缺 sensor count / ToF channel count、缺 thresholds、缺 frame IDs、缺 safety policy、缺 evidence refs、unsafe copy、success claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。

## hardware_sensor_hil_entry_readiness_review

`pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py` 是 HIL-entry 前的 dependency-free PC review gate。它只消费上一轮 `hardware_sensor_procurement_receipt_intake` artifact/summary 与 `hardware_sensor_hil_entry_config_precheck` artifact/summary 的白名单字段，把 receipt/source/vendor/SKU 材料和 future sensor config 参数化结果合成为人工 HIL-entry readiness review：

```bash
python3 pc-tools/evidence/hardware_sensor_hil_entry_readiness_review_gate.py \
  --receipt-intake-json /tmp/hardware_sensor_procurement_receipt_intake_summary.json \
  --config-precheck-json /tmp/hardware_sensor_hil_entry_config_precheck_summary.json \
  --summary-output /tmp/hardware_sensor_hil_entry_readiness_review_summary.json
```

输出 artifact 使用 `schema=trashbot.hardware_sensor_hil_entry_readiness_review.v1`，summary 使用 `schema=trashbot.hardware_sensor_hil_entry_readiness_review_summary.v1`，证据边界固定为 `software_proof_docker_hardware_sensor_hil_entry_readiness_review_gate`。summary 只暴露 source statuses、same safe `evidence_ref`、`next_required_evidence`、`owner_handoff`、vendor/source boundary、sanitized `safe_copy`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 review gate 明确采用 `docs/vendor/VENDOR_INDEX.md` 及其本地 Orange Pi / WAVE ROVER / UART JSON / firmware/vendor app coverage 作为资料边界；这些资料不证明项目 2D LiDAR 或 ToF SKU/source、采购、安装、接线、供电、标定、HIL-entry、Nav2/SLAM field pass、near-field safety pass 或 delivery success。缺任一上游 summary、unsupported schema/boundary、上游未 ready、`evidence_ref` 不一致、weak boolean、unsafe copy、HIL/field/delivery success claim、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_hardware_sensor_hil_entry_readiness_review_not_proven` 只表示材料可进入人工评审，仍是 `software_proof` / `not_proven`。

## hardware_sensor_hil_entry_execution_pack

`pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py` 是 HIL-entry readiness review 后的 dependency-free PC evidence gate。它只消费上一轮 `hardware_sensor_hil_entry_readiness_review` artifact、summary 或 wrapper 内嵌 summary 的白名单字段，把 readiness review 转成 HIL-entry execution pack 的材料模板、owner handoff、rerun commands、next required evidence 和 fail-closed phone-safe summary：

```bash
python3 pc-tools/evidence/hardware_sensor_hil_entry_execution_pack_gate.py \
  --readiness-review-json /tmp/hardware_sensor_hil_entry_readiness_review_summary.json \
  --summary-output /tmp/hardware_sensor_hil_entry_execution_pack_summary.json
```

输出 artifact 使用 `schema=trashbot.hardware_sensor_hil_entry_execution_pack.v1`，summary 使用 `schema=trashbot.hardware_sensor_hil_entry_execution_pack_summary.v1`，证据边界固定为 `software_proof_docker_hardware_sensor_hil_entry_execution_pack_gate`。execution pack 模板列出 2D LiDAR SKU/source/receipt、ToF SKU/source/receipt、mounting plan、wiring/power plan、calibration plan、HIL-entry operator checklist、safe `evidence_ref`、rerun commands、owner handoff 和 next required evidence。summary 必须继续输出 `software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。

该 execution pack 明确采用 `docs/vendor/VENDOR_INDEX.md`、`docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`、`docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`、`docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h` 和 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h` 作为 vendor/source boundary；这些资料只证明本地 WAVE ROVER / UART JSON / firmware/vendor app 参考存在，不证明真实 2D LiDAR 或 ToF SKU/source、采购、收货、安装、接线、供电、标定、HIL-entry、Nav2/SLAM field pass、near-field safety pass 或 delivery success。缺 readiness review、坏 JSON、unsupported schema/boundary、readiness 未 ready、missing unsafe `evidence_ref`、weak boolean、unsafe copy、raw credentials、完整本机路径、raw serial/UART path、raw JSON artifact copy、OSS/DB/queue/token、HIL passed/field pass/采购完成/接线完成等成功断言、`delivery_success=true` 或 `primary_actions_enabled=true` 都会 fail closed。`ready_for_hardware_sensor_hil_entry_execution_pack_not_proven` 只表示 PC gate 生成了待人工履约材料模板，仍是 `software_proof` / `hardware_material_pending` / `not_proven`。

## hardware_sensor_procurement_review_decision

`pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py` 读取上一轮 `hardware_sensor_procurement_intake` artifact 或 summary，把 2D LiDAR / ToF 的缺 SKU、缺 source、缺采购、缺 mounting/wiring/power/calibration/HIL entry 转成采购评审决策、blocker、`next_required_evidence`、`owner_handoff` 和 `rerun_commands`：

```bash
python3 pc-tools/evidence/hardware_sensor_procurement_review_decision_gate.py \
  --intake-json /tmp/hardware_sensor_procurement_intake.json \
  --summary-output /tmp/hardware_sensor_procurement_review_decision_summary.json
```

输出 artifact 使用 `schema=trashbot.hardware_sensor_procurement_review_decision.v1`，summary 使用 `schema=trashbot.hardware_sensor_procurement_review_decision_summary.v1`，证据边界固定为 `software_proof_docker_hardware_sensor_procurement_review_decision_gate`。该 gate 只证明 PC/local/Docker 能把上一轮 intake 缺口转成 review decision；`docs/vendor/VENDOR_INDEX.md` 仍只证明当前 Orange Pi / WAVE ROVER / UART / camera vendor coverage，不证明真实 2D LiDAR 或 ToF source/procurement。

summary 必须继续输出 `software_proof`、`hardware_material_pending`、`not_proven`、`delivery_success=false` 和 `primary_actions_enabled=false`。缺 intake、坏 JSON、unsupported schema/boundary、`delivery_success=true`、`primary_actions_enabled=true`、HIL pass 或 LiDAR/ToF field pass 成功断言时，review decision 必须 fail closed。

## route/task rehearsal artifact

`pc-tools/evidence/evidence_crosscheck.py` 可在原有只读复账基础上额外写出 route/task rehearsal artifact：

```bash
python3 pc-tools/evidence/evidence_crosscheck.py \
  /tmp/trashbot_fixed_route_status.json \
  --evidence-ref /tmp/route_replay_evidence.json \
  --task-record-dir ~/.ros/trashbot_tasks \
  --rehearsal-artifact /tmp/route_task_rehearsal_artifact.json
```

artifact 使用 `schema=trashbot.route_task_rehearsal_artifact`、`schema_version=1`，证据边界固定为 `evidence_boundary=software_proof_docker_route_task_rehearsal_artifact_gate`。内容包括 `evidence_ref`、route status summary、task record summary、crosscheck status、HIL alignment status、`diagnostics_summary` 和 `not_proven`。当 fixed-route status、software proof replay 与 task record 对账通过时，`crosscheck_status.status=pass` 只表示本地/Docker 软件排练一致，不表示真实 Nav2/fixed-route 实跑、WAVE ROVER 运动、真实串口反馈、真实 HIL 或 delivery success。

可选 `--hil-gate-output` 只用于记录 HIL gate 对齐状态。未提供、文件缺失、`status=software_proof` 或 `status=blocked` 时 artifact 仍会保存，但 `hil_alignment_status.alignment_status=not_proven`，`not_proven` 继续包含 `real_hil_pass`。summary/artifact 输出会过滤 bearer token、Authorization header、OSS secret、AK/SK、root password、DB URL、queue URL、串口设备、波特率和 raw traceback。

`diagnostics_summary` 是给 `/api/diagnostics` 或支持面消费的 phone-safe 摘要，schema 为 `trashbot.route_task_rehearsal_diagnostics_summary`，证据边界固定为 `software_proof_docker_route_task_rehearsal_diagnostics_gate`。该 summary 只暴露脱敏后的 `status`、`evidence_boundary`、`evidence_ref`、`crosscheck_status`、`hil_alignment_status`、`not_proven` 和 `next_step`；diagnostics 可以把它作为 `route_task_rehearsal` 展示，但不能据此放行控制动作、声明真实 fixed-route/Nav2、HIL、delivery success 或云/4G/OSS/CDN/DB/queue proof。

## route/task rehearsal execution bundle

`pc-tools/evidence/route_task_rehearsal_bundle.py` 在 `evidence_crosscheck.py` 之上生成可传递 execution bundle manifest：

```bash
python3 pc-tools/evidence/route_task_rehearsal_bundle.py \
  /tmp/trashbot_fixed_route_status.json \
  --task-record /tmp/task_record.json \
  --output-dir /tmp/route_task_rehearsal_bundle
```

该命令会先写出 `route_task_rehearsal_artifact.json`，再写出 `route_task_rehearsal_execution_bundle.json`。manifest 使用 `schema=trashbot.route_task_rehearsal_execution_bundle`、`schema_version=1`，证据边界固定为 `software_proof_docker_route_task_rehearsal_execution_bundle_gate`。manifest 顶层直接提供 diagnostics 只读消费字段：`route_task_rehearsal_artifact_ref`、`crosscheck_status`、`hil_alignment_status` 和 `diagnostics_summary`；同时保留脱敏后的 route status、task record、task record dir、HIL gate output 和 artifact 路径引用，以及 `not_proven` 和 `next_step`。

`status=available_software_proof` 和顶层 `crosscheck_status.status=pass` 只代表 status/replay/task_record 软件对账通过，适合交给 diagnostics 或 sprint closeout 做同一 `evidence_ref` 的材料传递。顶层 `hil_alignment_status.alignment_status=not_proven` 时必须继续显示缺真实 HIL。该 manifest 不证明真实 Nav2/fixed-route 实跑、真实路线采集、WAVE ROVER 运动、真实串口/UART feedback、真实 HIL、dropoff/cancel completion 或 delivery success。

## route/task rehearsal operator review

`pc-tools/evidence/route_task_rehearsal_operator_review.py` 只读取上一节生成的 execution bundle JSON，并生成操作员复盘/下一轮重跑决策包：

```bash
python3 pc-tools/evidence/route_task_rehearsal_operator_review.py \
  --execution-bundle /tmp/route_task_rehearsal_bundle/route_task_rehearsal_execution_bundle.json \
  --output-dir /tmp/route_task_rehearsal_review
```

默认输出文件名为 `route_task_rehearsal_operator_review.json`；也可以用 `--output` 指定完整输出路径。review package 使用 `schema=trashbot.route_task_rehearsal_operator_review.v1`、`schema_version=1`，证据边界固定为 `software_proof_docker_route_task_rehearsal_operator_review_gate`。该工具只读 JSON，不访问硬件、serial/UART、ROS graph、Nav2 或网络；missing、read_error、unsupported schema 也会写出 `overall_status=blocked_*` 的 review package，避免复盘时只有异常没有材料。

`next_rehearsal_decision` 是给操作员看的下一步分支：crosscheck pass 但 HIL not_proven 时，准备真实路线/任务材料或同 `evidence_ref` 的真实 HIL 复账；crosscheck fail 时，先修 route status/task record mismatch 后重跑 execution bundle；missing/read_error/unsupported schema 时，重建 execution bundle；safe copy whitelist 失败时，先修 whitelist-only 摘要。`safe_copy` 只包含固定白名单摘要，不复制 artifact/raw path、本机绝对路径、凭证、ROS topic、serial/UART、baudrate、WAVE ROVER、traceback、checksum 或 complete artifact。`primary_actions_enabled=false`、`delivery_success=false` 是固定防误读字段，review 不能放行控制动作或声明 delivery success。

## route/task field-run readiness handoff

`pc-tools/evidence/route_task_field_run_readiness.py` 把 PC route debug console summary、route_task operator review 和 execution bundle 聚合为下一次真实路线-任务联跑前的 handoff：

```bash
python3 pc-tools/evidence/route_task_field_run_readiness.py \
  --pc-route-debug /tmp/pc_route_debug_console.json \
  --operator-review /tmp/route_task_rehearsal_operator_review.json \
  --execution-bundle /tmp/route_task_rehearsal_execution_bundle.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_readiness.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_readiness_gate`、`same_evidence_ref_required=true`、`required_field_run_materials`、`missing_materials`、`commands_to_run`、`phone_support_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`overall_status=ready_for_field_run_materials` 只表示三份 Docker/local 软件 handoff 材料可读、schema 可支持、同一 `evidence_ref` 可对齐且摘要可安全分享；它不是 HIL、真实 fixed-route/Nav2 实跑、真实路线采集、dropoff/cancel completion、delivery success 或 Objective 5 外部 proof。

`required_field_run_materials` 会列出下一次现场联跑必须收集的同一 `evidence_ref` 材料：route status、task record、PC route debug summary、operator review、execution bundle、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary。CLI 不读取 serial/UART、ROS graph、WAVE ROVER、DB/queue、OSS/CDN 或 raw robot response；缺文件、unsupported schema、不同 `evidence_ref` 或 unsafe copy 时会保守输出 blocked/not_proven。

## route/task field-run intake crosscheck

`pc-tools/evidence/route_task_field_run_intake.py` 是 readiness handoff 之后的现场材料入口。它只读接收五份 JSON object：route status、task record、Nav2/fixed-route runtime log、robot-side task evidence 和 support-safe mobile summary，并用同一个 `evidence_ref` 做交叉校验：

```bash
python3 pc-tools/evidence/route_task_field_run_intake.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --runtime-log-json /tmp/runtime_log.json \
  --robot-side-task-evidence-json /tmp/robot_evidence.json \
  --support-safe-mobile-summary-json /tmp/mobile_summary.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_intake_crosscheck.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_intake_crosscheck_gate`、`same_evidence_ref_required=true`、`missing_materials`、`mismatch_reasons`、`commands_to_rerun`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`overall_status=ready_for_review` 只表示五份 Docker/local 软件材料都可读、schema 支持、同一 `evidence_ref` 对齐且手机/售后摘要可安全展示；它不是 HIL、真实 Nav2/fixed-route 实跑、真实路线采集、dropoff/cancel completion、delivery success 或 Objective 5 外部 proof。

缺文件、坏 JSON、非 JSON object、unsupported schema、任一材料缺 `evidence_ref`、同 run 不一致或 support-safe mobile summary 含敏感材料时，CLI 会保守输出 blocked 状态，不抛未处理异常。`phone_safe_summary` 只包含 status、safe evidence ref、材料 present/missing/mismatch、`commands_to_rerun`、`not_proven` 和 accepted/processing support metadata only 语义；不得包含 raw artifact、完整本机路径、ROS 控制 topic、serial/UART、baudrate、WAVE ROVER 参数、token、Authorization、OSS AK/SK、DB/queue URL、traceback、checksum、complete artifact 或 raw robot response。

## route/task field-run review console

`pc-tools/evidence/route_task_field_run_review.py` 只读上一节生成的 intake/crosscheck JSON，把机器字段整理成 operator/support 可读的 review report：

```bash
python3 pc-tools/evidence/route_task_field_run_review.py \
  --intake-json /tmp/route_task_field_run_intake.json \
  --output /tmp/route_task_field_run_review.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_review.py \
  --intake-json /tmp/route_task_field_run_intake.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_review_console.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_review_console_gate`、`review_decision`、`operator_next_steps`、整理后的 `commands_to_rerun`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。review console 的新增价值是把 intake 的 missing/mismatch/unsafe/unsupported 状态转成现场下一步：补采缺失材料、统一 `evidence_ref` 后重跑、修复 support-safe 摘要，或进入人工复核但继续禁止 delivery claim。

该 report 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G；`ready_for_operator_review` 只表示 intake 材料足够进入 operator/support 复核，不表示真实 Nav2/fixed-route、真实路线采集、HIL、dropoff/cancel completion、delivery success 或 O5 external proof。缺 intake、坏 JSON、unsupported schema、unsafe phone/support copy、missing materials 或 mismatch 时，CLI 会输出 blocked review report，而不是抛未处理异常或猜测现场成功。

## route/task field-run execution pack

`pc-tools/evidence/route_task_field_run_execution_pack.py` 只读上一节 review console JSON，把 operator/support 下一步整理为现场联跑执行包：

```bash
python3 pc-tools/evidence/route_task_field_run_execution_pack.py \
  --review-json /tmp/route_task_field_run_review.json \
  --output /tmp/route_task_field_run_execution_pack.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_execution_pack.py \
  --review-json /tmp/route_task_field_run_review.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_execution_pack.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_execution_pack_gate`、`field_run_manifest`、`required_material_templates`、`first_run_commands`、`rerun_commands`、`same_evidence_ref_required=true`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`field_run_manifest` 是现场执行总目录，材料模板覆盖 route status、task record、Nav2/fixed-route runtime log、robot-side task evidence、support-safe mobile summary 和 PC review console；`first_run_commands` 与 `rerun_commands` 要求所有材料沿用同一 `evidence_ref`。

该 execution pack 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；`ready_for_field_run_execution_pack` 只表示 review console 足以生成现场联跑材料清单，不表示真实 Nav2/fixed-route、真实路线采集、HIL、dropoff/cancel completion、delivery success 或 O5 external proof。缺 review、坏 JSON、unsupported schema、unsafe copy、review blocked、`primary_actions_enabled=true` 或 `delivery_success=true` 时，CLI 会保守输出 blocked execution pack，并继续保留 `not_proven` 与 `delivery_success=false`。

## route/task field-run reconciliation

`pc-tools/evidence/route_task_field_run_reconciliation.py` 只读 execution pack JSON 与 intake/review JSON，做同一 `evidence_ref` 的现场材料复账：

```bash
python3 pc-tools/evidence/route_task_field_run_reconciliation.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --intake-json /tmp/route_task_field_run_intake.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_run_reconciliation.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_reconciliation.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --intake-json /tmp/route_task_field_run_review.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_reconciliation.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_reconciliation_gate`、`same_evidence_ref_required=true`、`reconciliation_verdict`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`--intake-json` 支持 intake crosscheck 或 review console，两者都只按白名单字段进入复账报告。

该 reconciliation gate 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；`ready_for_route_task_field_run_reconciliation` 只表示 execution pack 与 intake/review 材料可读、schema/boundary 支持、同一 safe `evidence_ref` 对齐且 phone-safe 摘要可展示。它不是真实 fixed-route/Nav2、真实路线采集、HIL、dropoff/cancel completion、delivery success 或 O5 external proof。缺 execution pack、缺 intake/review、坏 JSON、unsupported schema、unsupported boundary、缺 `evidence_ref`、`evidence_ref` mismatch、unsafe summary 或 missing materials 时，CLI 会输出 blocked reconciliation artifact，并继续保留 `not_proven` 与 `delivery_success=false`。

## route/task completion signal

`pc-tools/evidence/route_task_completion_signal.py` 只读 fixed-route status/replay、task record、上一轮 reconciliation/review/intake summary，以及可选 dropoff/cancel completion material，生成给 diagnostics/mobile 只读消费的 completion signal：

```bash
python3 pc-tools/evidence/route_task_completion_signal.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-summary-json /tmp/route_task_field_run_reconciliation.json \
  --dropoff-completion-json /tmp/dropoff_completion.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_completion_signal.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_completion_signal.py \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-summary-json /tmp/route_task_field_run_review.json \
  --cancel-completion-json /tmp/cancel_completion.json \
  --once-json
```

输出 `schema=trashbot.route_task_completion_signal.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_completion_signal_gate`、`same_evidence_ref_required=true`、`completion_verdict`、`fixed_route_summary`、`task_record_summary`、`state_transition_summary`、`dropoff_completion`、`cancel_completion`、`failure_reason`、`recovery_reason`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`completed_not_proven` 只表示 Docker/local completion signal 材料形状足够进入人工复核，不表示真实送达成功。

该 completion signal gate 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；它不是真实 delivery、真实 dropoff/cancel completion、真实 fixed-route/Nav2、真实路线采集、HIL、真实手机设备或 O5 external proof。缺 route/task/summary 必需材料、坏 JSON、unsupported schema、`evidence_ref` mismatch、unsafe phone summary、输入含 `delivery_success=true`，或状态机进入 dropoff/cancel 但缺对应 completion material 时，CLI 会 fail closed，保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## route/task field-run console

`pc-tools/evidence/route_task_field_run_console.py` 只读上一轮 execution pack、fixed-route status/replay、task record 和 completion signal，把它们整理成 PC/operator-facing 的现场运行准备 console：

```bash
python3 pc-tools/evidence/route_task_field_run_console.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_task_completion_signal.json \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_run_console.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_console.py \
  --execution-pack-json /tmp/route_task_field_run_execution_pack.json \
  --route-status-json /tmp/route_status.json \
  --task-record-json /tmp/task_record.json \
  --completion-signal-json /tmp/route_task_completion_signal.json \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_console.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_console_gate`、`same_evidence_ref_required=true`、`console_verdict`、`field_run_plan`、`capture_checklist`、`execution_pack_summary`、`route_status_summary`、`task_record_summary`、`completion_signal_summary`、`dropoff_completion`、`cancel_completion`、`operator_next_steps`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`field_run_plan` 是操作员准备顺序，`capture_checklist` 是下一次真实现场材料采集模板；两者都只要求沿用同一 `evidence_ref`，不会访问运行时系统。

该 field-run console 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；`field_run_materials_prepared_not_proven` 只表示本地材料可读、schema/boundary 支持、same `evidence_ref` 对齐且摘要安全。它不是真实 Nav2/fixed-route、真实路线采集、真实 dropoff/cancel completion、HIL、delivery success、真实手机设备或 Objective 5 external proof。缺 execution pack、route status、task record 或 completion signal、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true` 或输入含 `delivery_success=true` 时，CLI 会 fail closed，保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## route/task field-run evidence kit

`pc-tools/evidence/route_task_field_run_evidence_kit.py` 只读上一轮 `route_task_field_run_console` artifact，并可选检查 PC 侧材料目录，把现场执行说明、回填模板和只读摘要整理成可交给现场同学的 evidence kit：

```bash
python3 pc-tools/evidence/route_task_field_run_evidence_kit.py \
  --console-json /tmp/route_task_field_run_console.json \
  --material-dir /tmp/route_task_field_run_materials \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_run_evidence_kit.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_evidence_kit.py \
  --console-json /tmp/route_task_field_run_console.json \
  --material-dir /tmp/route_task_field_run_materials \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_evidence_kit.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_evidence_kit_gate`、`same_evidence_ref_required=true`、`evidence_kit_verdict`、`material_directory_manifest`、`capture_templates`、`commands_to_run`、`commands_to_rerun`、`missing_materials`、`operator_handoff`、`robot_diagnostics_summary`、`mobile_readonly_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`material_directory_manifest` 只检查/描述 PC 目录里是否有 `route_task_field_run_console.json`、`route_status.json`、`task_record.json`、`completion_signal.json`、`operator_notes.md`、`robot_diagnostics_summary.json` 和 `mobile_readonly_summary.json`；这些文件即使齐全，也只是现场执行和回填材料，不是 delivery success。

该 evidence kit 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、硬件、外部云、OSS/CDN、DB/queue 或 4G；`field_run_evidence_kit_ready_not_proven` 只表示上一轮 console 与材料目录可形成现场 handoff。缺 console、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、缺材料目录文件、unsafe summary、`primary_actions_enabled=true` 或输入含 `delivery_success=true` 时，CLI 会 fail closed，保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## route/task field-run material bundle

`pc-tools/evidence/route_task_field_run_material_bundle.py` 只读上一轮 `route_task_field_run_evidence_kit` artifact，输出现场材料包 summary；指定 `--material-dir` 时，会实际创建 route/task/completion/operator notes/diagnostics/mobile summary 的模板或占位文件：

```bash
python3 pc-tools/evidence/route_task_field_run_material_bundle.py \
  --evidence-kit-json /tmp/route_task_field_run_evidence_kit.json \
  --material-dir /tmp/route_task_field_run_material_bundle \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_run_material_bundle.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_material_bundle.py \
  --evidence-kit-json /tmp/route_task_field_run_evidence_kit.json \
  --material-dir /tmp/route_task_field_run_material_bundle \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_material_bundle.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_material_bundle_gate`、`same_evidence_ref_required=true`、`material_bundle_verdict`、`source_evidence_kit`、`material_directory_scaffold`、`material_bundle_summary`、`operator_next_steps`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`material_bundle_summary` 使用 `schema=trashbot.route_task_field_run_material_bundle_summary.v1`，供 Robot diagnostics 和 mobile 只读展示。

指定 `--material-dir` 后，工具会保留已有文件并补齐缺失模板：`route_status_template.json`、`task_record_template.json`、`completion_material_template.json`、`operator_notes.md`、`robot_diagnostics_summary_template.json` 和 `mobile_readonly_summary_template.json`。这些模板全部继承同一 safe `evidence_ref`，并固定 `delivery_success=false`、`primary_actions_enabled=false`、`same_evidence_ref_required=true`。

该 material bundle 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G；`field_run_material_bundle_ready_not_proven` 只表示 PC 侧可以从 evidence kit 生成现场材料包和模板。它不是真实 Nav2/fixed-route、真实路线采集、HIL、真实 dropoff/cancel completion、delivery success、真实手机设备或 Objective 5 external proof。缺 evidence kit、坏 JSON、unsupported schema/boundary、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true`、输入含 `delivery_success=true` 或目录不可写时，CLI 会 fail closed，保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## route/task field-run material validation

`pc-tools/evidence/route_task_field_run_material_validation.py` 只读上一轮 `route_task_field_run_material_bundle` artifact 和 `--material-dir`，把现场材料目录从“已生成模板”推进到“可校验状态”。它会检查 route、task、completion、operator notes、diagnostics、mobile summary 六类材料是否存在、是否仍是模板、是否坏 JSON、是否同一 `evidence_ref`、是否含 unsafe copy，以及是否越界声明 `primary_actions_enabled=true` 或 `delivery_success=true`：

```bash
python3 pc-tools/evidence/route_task_field_run_material_validation.py \
  --material-bundle-json /tmp/route_task_field_run_material_bundle.json \
  --material-dir /tmp/route_task_field_run_material_bundle \
  --evidence-ref /tmp/same_evidence_ref.json \
  --output /tmp/route_task_field_run_material_validation.json
```

需要直接给 diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/route_task_field_run_material_validation.py \
  --material-bundle-json /tmp/route_task_field_run_material_bundle.json \
  --material-dir /tmp/route_task_field_run_material_bundle \
  --once-json
```

输出 `schema=trashbot.route_task_field_run_material_validation.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_route_task_field_run_material_validation_gate`、`same_evidence_ref_required=true`、`material_validation_verdict`、`source_material_bundle`、`material_directory_status`、`material_validation_summary`、`operator_next_steps`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`material_validation_summary` 使用 `schema=trashbot.route_task_field_run_material_validation_summary.v1`，供 Robot diagnostics 和 mobile 只读展示。

该 material validation 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、硬件、外部云、OSS/CDN、DB/queue 或 4G；`field_run_material_validation_ready_not_proven` 只表示材料目录的文件形状、same `evidence_ref` 和 safe summary 条件可进入下一步 intake/review。它不是真实 Nav2/fixed-route、真实路线采集、HIL、真实 dropoff/cancel completion、delivery success、真实手机设备或 Objective 5 external proof。缺 material bundle、坏 JSON、unsupported schema/boundary、缺材料、模板未替换、`evidence_ref` mismatch、unsafe summary、`primary_actions_enabled=true` 或输入含 `delivery_success=true` 时，CLI 会 fail closed，保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## elevator assisted delivery field-run material validation

`pc-tools/evidence/elevator_field_run_material_validation.py` 是电梯 assisted delivery 的现场材料校验 gate。它只读 `--material-dir`，检查同一 `evidence_ref` 下的门状态、目标楼层确认、人工协助/operator note、Nav2/fixed-route runtime log、task record、completion signal、diagnostics/mobile safe summary 七类材料：

```bash
python3 pc-tools/evidence/elevator_field_run_material_validation.py \
  --material-dir /tmp/elevator_field_run_materials \
  --evidence-ref elevator-run-001 \
  --output /tmp/elevator_field_run_material_validation.json
```

需要直接给 Robot diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/elevator_field_run_material_validation.py \
  --material-dir /tmp/elevator_field_run_materials \
  --evidence-ref elevator-run-001 \
  --once-json
```

输出 `schema=trashbot.elevator_field_run_material_validation.v1`、`schema_version=1`、`evidence_boundary=software_proof_docker_elevator_field_material_validation_gate`、`same_evidence_ref_required=true`、`material_validation_verdict`、`material_directory_status`、`material_validation_summary`、`operator_next_steps`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。summary 使用 `schema=trashbot.elevator_field_run_material_validation_summary.v1`，只供 Robot diagnostics 和 mobile 只读展示。

该 elevator material validation 仍只是 Docker/local software proof。`elevator_field_material_validation_ready_not_proven` 只表示七类材料的文件形状、same `evidence_ref` 和 phone-safe 摘要条件可进入人工复核；它不是真实电梯门状态、真实目标楼层确认、真实人工协助现场记录、真实 Nav2/fixed-route 实跑、WAVE ROVER/UART/HIL、dropoff/cancel completion、delivery success、真实手机设备或 Objective 5 external proof。缺目录、缺文件、模板未替换、坏 JSON、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true` 或 `delivery_success=true` 都会 fail closed，并保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## elevator assisted delivery field-run review decision

`pc-tools/evidence/elevator_field_run_review.py` 只读上一轮 `elevator_field_run_material_validation` artifact 或 summary，把 missing/template/mismatch/unsafe/success-claim 状态整理成 operator 可执行的复核决策、复跑命令和采集清单：

```bash
python3 pc-tools/evidence/elevator_field_run_review.py \
  --validation-json /tmp/elevator_field_run_material_validation.json \
  --output /tmp/elevator_field_run_review.json
```

需要直接给 Robot diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/elevator_field_run_review.py \
  --validation-json /tmp/elevator_field_run_material_validation.json \
  --once-json
```

输出 `schema=trashbot.elevator_field_run_review.v1`、summary `schema=trashbot.elevator_field_run_review_summary.v1`、`evidence_boundary=software_proof_docker_elevator_field_review_decision_gate`、`review_decision`、`blocked_categories`、`operator_next_steps`、`commands_to_rerun`、`capture_checklist`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

review decision 的枚举固定为 `ready_for_controlled_elevator_field_rehearsal_not_proven`、`blocked_missing_materials`、`blocked_template_materials`、`blocked_evidence_ref_mismatch`、`blocked_unsafe_copy`、`blocked_success_claim` 和 `blocked_invalid_validation`。该 review gate 仍只是 Docker/local software proof：它不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G；`ready_for_controlled_elevator_field_rehearsal_not_proven` 只表示七类 validation 材料可进入人工复核/受控演练准备，不证明真实电梯、真实门状态、真实目标楼层、真实 Nav2/fixed-route、HIL、真实投放、真实取消完成、真实手机设备或 delivery success。

## elevator assisted delivery field-run execution pack

`pc-tools/evidence/elevator_field_run_execution_pack.py` 只读上一轮 `elevator_field_run_review` artifact 或 summary，把复核决策整理成受控电梯现场演练 execution pack：

```bash
python3 pc-tools/evidence/elevator_field_run_execution_pack.py \
  --review-json /tmp/elevator_field_run_review.json \
  --output /tmp/elevator_field_run_execution_pack.json
```

需要直接给 Robot diagnostics、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/elevator_field_run_execution_pack.py \
  --review-json /tmp/elevator_field_run_review.json \
  --once-json
```

输出 `schema=trashbot.elevator_field_run_execution_pack.v1`、summary `schema=trashbot.elevator_field_run_execution_pack_summary.v1`、`evidence_boundary=software_proof_docker_elevator_field_rehearsal_execution_pack_gate`、`execution_pack_verdict`、`controlled_rehearsal_manifest`、`required_material_templates`、`first_run_commands`、`rerun_commands`、`operator_handoff`、`same_evidence_ref_required=true`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

`controlled_rehearsal_manifest` 固定要求 human observer、stop path 和同一 `evidence_ref`；`required_material_templates` 覆盖 `door_state.json`、`target_floor_confirmation.json`、`human_assistance_operator_note.md`、`nav2_fixed_route_runtime_log.json`、`task_record.json`、`completion_signal.json` 和 `diagnostics_mobile_safe_summary.json`。该 execution pack 不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G；`ready_for_controlled_elevator_field_rehearsal_execution_pack_not_proven` 只表示 review 材料足以生成受控演练材料清单，不表示真实电梯门状态、真实目标楼层确认、真实 Nav2/fixed-route、HIL、真实投放、真实取消完成、真实手机设备或 delivery success。缺 review、坏 JSON、unsupported schema/boundary、unsafe copy、review blocked、`primary_actions_enabled=true` 或 `delivery_success=true` 时，CLI 会 fail closed，并继续保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## elevator assist rehearsal evidence

`pc-tools/evidence/elevator_assist_rehearsal_evidence.py` 生成 Robot dry-run 主链路只读消费的 rehearsal evidence artifact。它不读取上一轮现场材料，也不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G：

```bash
python3 pc-tools/evidence/elevator_assist_rehearsal_evidence.py \
  --evidence-ref elevator-rehearsal-001 \
  --target-floor 1F \
  --output /tmp/elevator_assist_rehearsal_evidence.json
```

需要直接给 Robot dry-run、mobile fixture 或 sprint 验收读取时，可使用：

```bash
python3 pc-tools/evidence/elevator_assist_rehearsal_evidence.py \
  --evidence-ref elevator-rehearsal-001 \
  --target-floor 1F \
  --once-json
```

输出 `schema=trashbot.elevator_assist_rehearsal_evidence.v1`、`schema_version=1`、`source=software_proof`、`evidence_boundary=software_proof_docker_elevator_evidence_driven_mainline_gate`、`same_evidence_ref_required=true`、`phase_evidence`、可选 `failure`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。`phone_safe_summary` 同样保留 `source=software_proof`，供 Robot dry-run 和 mobile 只读摘要对齐。`phase_evidence` 固定覆盖 `waiting_elevator_open`、`entering_elevator`、`requesting_floor_help`、`waiting_target_floor` 和 `exiting_elevator`。

`--failure-phase` 会把 artifact verdict 置为 `blocked_rehearsal_failure_injected_not_proven`，用于 Robot dry-run 验证失败分支和人工接管原因；未传 failure 时，verdict 为 `ready_for_robot_dry_run_readonly_rehearsal_evidence_not_proven`。该 gate 仍只是 Docker/local software proof：它只证明本机可以生成同一 `evidence_ref` 的电梯主链路 rehearsal evidence，供 Robot 只读复现状态转移。它不是真实电梯门状态、真实目标楼层确认、真实人工协助、真实 Nav2/fixed-route、HIL、真实投放、真实取消完成、真实手机设备或 delivery success。非法 `evidence_ref`、非法 `target_floor`、unsafe copy、成功文案或控制放行声明都必须 fail closed，并继续保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## elevator route evidence reconciliation

`pc-tools/evidence/elevator_route_evidence_reconciliation.py` 把 elevator rehearsal evidence 与 route/task completion signal 按同一 `evidence_ref` 复账，给 Robot diagnostics 与 mobile/web 后续只读消费提供安全 summary。它只读取本机 JSON artifact 或 phone-safe summary，不访问 ROS graph、Nav2 runtime、serial/UART、WAVE ROVER、真实电梯、外部云、OSS/CDN、DB/queue 或 4G：

```bash
python3 pc-tools/evidence/elevator_route_evidence_reconciliation.py \
  --elevator-json /tmp/elevator_assist_rehearsal_evidence.json \
  --route-completion-json /tmp/route_task_completion_signal.json \
  --evidence-ref elevator-rehearsal-001 \
  --output /tmp/elevator_route_evidence_reconciliation.json
```

需要直接给 sprint 验收、diagnostics fixture 或 mobile fixture 读取时，可使用：

```bash
python3 pc-tools/evidence/elevator_route_evidence_reconciliation.py \
  --elevator-json /tmp/elevator_assist_rehearsal_evidence.json \
  --route-completion-json /tmp/route_task_completion_signal.json \
  --once-json
```

输出 `schema=trashbot.elevator_route_evidence_reconciliation.v1`、summary `schema=trashbot.elevator_route_evidence_reconciliation_summary.v1`、`source=software_proof`、`evidence_boundary=software_proof_docker_elevator_route_evidence_reconciliation_gate`、`same_evidence_ref_required=true`、`same_evidence_ref_status`、`reconciliation_verdict`、`source_states`、`elevator_rehearsal_summary`、`route_completion_summary`、`materials_status`、`operator_next_steps`、`phone_safe_summary`、`not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

该 reconciliation gate 仍只是 Docker/local software proof。`reconciled_not_proven` 只表示电梯 rehearsal evidence 与 route completion signal 都可读、schema/boundary/source 支持、同一 safe `evidence_ref` 对齐且摘要可安全展示；它不是真实电梯门状态、真实目标楼层确认、真实人工协助、真实 Nav2/fixed-route、WAVE ROVER/UART/HIL、真实投放、真实取消完成、真实手机设备、Objective 5 external proof 或 delivery success。缺任一 JSON、坏 JSON、unsupported schema/boundary、`source!=software_proof`、缺 `evidence_ref`、`evidence_ref` mismatch、unsafe copy、`primary_actions_enabled=true`、`delivery_success=true` 或成功文案都会 fail closed，并继续保留 `not_proven`、`primary_actions_enabled=false` 和 `delivery_success=false`。

## Agent 工作纪律

- 修改本目录前必读 `AGENTS.md`、`OKR.md`、对应 sprint 文档。
- 涉及视觉样本 schema / 标注格式时，必读 `pc-tools/labeling/CONTRACT.md` 和 `onboard/src/ros2_trashbot_vision/` 对应接口定义，不发明字段。
- 中文注释比例 >20%，注释解释"为什么"而非"做什么"。
- 测试覆盖核心场景：CSV → YAML 转换、debug web 渲染、evidence crosscheck 一致性、phone gate 报告生成。
- 不允许 pc-tools/* 直接 import 任何 `ros2_trashbot_*` ROS2 包；这些工具应能在没有 ROS2 安装的 PC 上独立运行（如必须依赖 rclpy，必须明确写在子目录 README 顶部 + 测试可绕过）。

## 路线图（Roadmap）

| 阶段 | 工作 |
| --- | --- |
| 本 sprint P1（当前） | README 脚手架 + labeling CONTRACT 占位 |
| 本 sprint P4 | route / evidence 工具搬迁 |
| 后续 sprint | labeling GUI 实现、training pipeline 集成、数据集版本管理 |

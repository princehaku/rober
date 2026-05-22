# PR #5 Mandatory Sensor Material Follow-Up Escalation Status Side2Side Check

Run time: 2026-05-23 04:48 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 验收对照

| 验收项 | 结果 | 证据 |
| --- | --- | --- |
| PC gate 输出 `pr5_mandatory_sensor_material_followup_escalation_status` | pass | Hardware 新增 PC gate 与 7 个 focused tests。 |
| 三端统一边界 `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate` | pass | PC summary、Robot diagnostics alias、mobile fixture/docs 均包含该 boundary。 |
| Robot 只暴露 safe alias | pass | `robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary` 已新增并测试。 |
| mobile/web 只读展示 | pass | “PR #5 强制传感器材料跟进升级状态” panel 已新增；Start Delivery / Confirm Dropoff / Cancel 在 fixture 下保持 disabled。 |
| 禁止真实证明扩大 | pass | 文档和 summary 保留 `source=software_proof`、`not_proven`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`。 |
| OKR 保守收口 | pass | Objective 5 约 68%、Objective 1 约 81%、Objective 2/3/4 约 99%；no OKR percentage lift。 |

## 用户价值和产品北极星

本轮支持北极星的方式是减少“材料状态不清”的现场验收风险：support、owner、reviewer 能看到 PR #5 强制传感器材料是 pending、overdue、escalated、blocked，还是 ready_for_reviewer_followup_not_proven。它不把本地材料跟进状态包装成真实交付能力。

## OKR 映射和 KR 检查

- Objective 1：PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`；Q/U resolved 不能关闭 X。缺真实 2D LiDAR/ToF、WAVE ROVER/UART/HIL 和 reviewer resolution，所以保持约 81%。
- Objective 2：没有 route/elevator field pass、dropoff/cancel completion、delivery result 或 delivery_success=true；保持约 99%。
- Objective 3：没有 Nav2/fixed-route runtime pass、route completion signal 或真实路线采集；保持约 99%。
- Objective 4：mobile/web 是 read-only panel，不是 true phone/browser proof；保持约 99%。
- Objective 5：没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result；保持约 68%。

## 整合验证

- closeout file existence check：pass。
- `python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`：pass。
- `python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_followup_escalation_status.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py mobile/web/test_mobile_web_entrypoint.py`：pass，`Ran 590 tests in 5.330s OK`。
- `node --check mobile/web/app.js`：pass。
- `python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status.json`：pass。
- required `rg` for `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`、Objective 5、Objective 1、Objective 2、Objective 3、Objective 4、`PRRT_kwDOSWB9286CJ3tX`、`delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false`、`not_proven`、`no OKR percentage lift`：pass。
- scoped `git diff --check`：pass。

## 非证明范围

本轮 accepted only as `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`。它不是 true phone/browser proof、route/elevator field pass、Nav2/fixed-route runtime pass、verified terminal result、dropoff/cancel completion、delivery result、delivery success、Objective 5 external proof、Objective 1 HIL、WAVE ROVER/UART proof、LiDAR/ToF installed proof 或 PR #5 resolution。

## 剩余风险

真实材料仍是下一步：2D LiDAR / ToF SKU/source/receipt/procurement、安装、接线、电源、标定、HIL-entry、operator HIL report、真实 WAVE ROVER/UART/HIL logs、真实 route/elevator/mobile/browser 材料和 Objective 5 外部材料。

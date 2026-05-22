# PR #5 Mandatory Sensor Material Follow-Up Escalation Status Tech Done

Run time: 2026-05-23 04:48 Asia/Shanghai

## Sprint Type

sprint_type: epic

## 用户价值和产品北极星

北极星仍是让普通手机用户把垃圾交给小车后，小车可验证地完成固定路线/电梯 assisted delivery 送达。本轮用户价值不是证明送达，而是把 PR #5 强制传感器材料缺口变成 PC、Robot diagnostics、mobile/web 三端一致的安全跟进升级状态，让 owner/reviewer 知道真实 2D LiDAR / ToF、安装、接线、电源、标定、HIL-entry 与 reviewer resolution 仍需补齐。

## OKR 映射

- Objective 5：约 68%，仍是最低 Objective；本轮没有真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser 或 verified terminal result，所以 no OKR percentage lift。
- Objective 1：约 81%；本轮针对 PR #5 `PRRT_kwDOSWB9286CJ3tX` 的 hardware_material_pending follow-up 状态，但没有真实 WAVE ROVER/UART/HIL、真实 2D LiDAR/ToF material 或 reviewer resolution，所以 no OKR percentage lift。
- Objective 2：约 99%；本轮没有 route/elevator field pass、dropoff/cancel completion、delivery result 或 delivery_success=false 以外的真实送达证据。
- Objective 3：约 99%；本轮没有 Nav2/fixed-route runtime pass、route completion signal、真实路线采集或同一 safe `evidence_ref` 上车实机复账。
- Objective 4：约 99%；本轮 mobile/web 是 read-only panel，不是 true phone/browser proof，也不是 production app 或真实 iPhone/Android device behavior。

## KR 拆解或更新

本轮不更新 OKR/KR 文案，不提高百分比。实际 KR-level 抓手为：

- Hardware：把 `pr5_mandatory_sensor_source_alignment` 后续材料状态转成 `pr5_mandatory_sensor_material_followup_escalation_status` PC gate。
- Robot：把安全 summary 暴露为 `robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary`，保持 `safe_to_control=false`。
- Full-Stack：把 PR #5 强制传感器材料跟进升级状态做成 mobile/web read-only panel，保持 `primary_actions_enabled=false`。
- Product：把本轮验收收口为 `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`，并把 no OKR percentage lift 写入 OKR/progress log。

## 实际改动

### Task A Hardware

- 新增 `pc-tools/evidence/pr5_mandatory_sensor_material_followup_escalation_status.py`。
- 新增 `pc-tools/evidence/test_pr5_mandatory_sensor_material_followup_escalation_status.py`。
- 更新 `pc-tools/README.md`。
- 更新 `docs/interfaces/pr5_mandatory_sensor_source_alignment.md`。
- 更新 `docs/product/production_hardware_boundary.md`。
- Vendor 来源已复核：`docs/vendor/VENDOR_INDEX.md`、Orange Pi Zero 3 manual/schematic PDFs、WAVE ROVER `ugv_rpi/README.md`、`base_ctrl.py`、`config.yaml`、`WAVE_ROVER_V0.9/json_cmd.h`、`uart_ctrl.h`、`movtion_module.h`。这些来源只支持 source boundary，不证明真实 2D LiDAR/ToF、HIL、UART 或安装完成。

### Task B Robot

- 更新 `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`。
- 更新 `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`。
- 更新 `docs/interfaces/ros_runtime_contracts.md`。
- 新增 alias `robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status_summary`。
- 首轮失败定位：unsafe blocked summary text 仍提到 `/cmd_vel`，已改成 generic wording 后通过。

### Task C Full-Stack

- 更新 `mobile/web/app.js`。
- 新增 `mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_followup_escalation_status.json`。
- 更新 `mobile/web/test_mobile_web_entrypoint.py`。
- 更新 `docs/product/mobile_user_flow.md`。
- 新增 read-only panel “PR #5 强制传感器材料跟进升级状态”。

### Task D Product

- 新增本文件。
- 新增 `side2side_check.md`。
- 新增 `final.md`。
- 更新 `OKR.md`。
- 更新 `docs/process/okr_progress_log.md`。

## 验证结果

三路 Engineer 报告：

- Hardware：`py_compile` pass；unittest `Ran 7 tests in 0.399s OK`；CLI `--help` pass；required `rg` pass；scoped diff check pass。
- Robot：`py_compile` pass；diagnostics unittest `Ran 299 tests in 2.385s OK`；required `rg` pass；scoped diff check pass。
- Full-Stack：`node --check` pass；fixture `json.tool` pass；mobile unittest `Ran 284 tests in 2.532s OK`；required `rg` pass；scoped diff check pass。

Product closeout 运行整合围栏：

- closeout file existence check：pass。
- combined `py_compile`：pass。
- combined unittest：pass，`Ran 590 tests in 5.330s OK`。
- `node --check mobile/web/app.js`：pass。
- fixture `json.tool`：pass。
- required `rg`：pass。
- scoped `git diff --check`：pass。

## 证据边界

本轮 accepted only as `software_proof_docker_pr5_mandatory_sensor_material_followup_escalation_status_gate`。

必须保留：

- `source=software_proof`
- `software_proof`
- `hardware_material_pending`
- `not_proven`
- `delivery_success=false`
- `primary_actions_enabled=false`
- `safe_to_control=false`

Live PR #5 `PRRT_kwDOSWB9286CJ3tX` 仍 unresolved / `is_resolved=false` / `hardware_material_pending`。`PRRT_kwDOSWB9286CJ3tQ` 与 `PRRT_kwDOSWB9286CJ3tU` resolved 不能关闭 X。

## 非证明范围

本轮不是 true phone/browser proof、route/elevator field pass、Nav2/fixed-route runtime pass、verified terminal result、dropoff/cancel completion、delivery result、delivery success、Objective 5 external proof、Objective 1 HIL、WAVE ROVER/UART proof、LiDAR/ToF installed proof 或 PR #5 resolution。

## 剩余风险和证据链缺口

- O1 仍缺真实 2D LiDAR / ToF SKU/source/receipt/procurement、安装、接线、电源、标定、HIL-entry、operator HIL report、WAVE ROVER powered bench/UART/HIL logs 和 PR #5 reviewer resolution。
- O5 仍缺真实 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue、worker/cutover、真实手机/browser、verified terminal result 和 delivery success。
- O2/O3/O4 仍缺真实 task record、Nav2/fixed-route runtime log、route completion signal、电梯门状态、目标楼层确认、人工协助记录、dropoff/cancel completion、真实 route/elevator field pass 和真实 iPhone/Android/browser evidence。

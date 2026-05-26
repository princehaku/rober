# Tech Done - PR5 mandatory sensor material owner-response reviewer ACK intake

- sprint_type: epic
- sprint: `2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake`
- closeout time: 2026-05-24 12:26 Asia/Shanghai
- target capability: `pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake`
- proof boundary: `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate`
- Product closeout owner: `product-okr-owner`
- implementation owners: `robot-hardware-engineer`, `robot-software-engineer`, `full-stack-software-engineer`
- OKR decision: no OKR percentage lift

## 用户价值和产品北极星

本轮用户价值是把 PR #5 mandatory sensor material owner-response review handoff 之后的 reviewer ACK 状态接入 PC gate、Robot diagnostics safe alias 和 `mobile/web` 只读 panel。普通手机用户、support reviewer 和 hardware owner 能看到同一个 `PRRT_kwDOSWB9286CJ3tX`、同一个 `hardware_material_pending`、同一个 next evidence list，以及同一组 fail-closed flags，而不会把软件证据误读成真实 2D LiDAR / ToF、WAVE ROVER/UART/HIL、GitHub resolution 或 delivery success。

产品北极星保持不变：真实材料缺失时，用户触点只展示安全、可解释、不可误操作的状态；主操作必须 fail closed。

## OKR 映射和 KR 收口

| Objective | 本轮关系 | 收口判断 |
| --- | --- | --- |
| Objective 1：硬件协议可信底盘 | PR #5 mandatory sensor material evidence chain 的 reviewer ACK intake rung。 | 保持约 81%，因为没有真实 LiDAR/ToF procurement/install/calibration/HIL 或 reviewer resolution。 |
| Objective 4：手机用户体验与低成本量产边界 | `mobile/web` 新增 first-screen read-only panel。 | 保持约 99%，因为本轮不是 true phone/browser proof。 |
| Objective 5：云中转 + OSS/CDN 数据通路产品化 | Robot/API 只暴露 read-only safe alias。 | 保持约 68%，因为没有 public HTTPS/TLS、4G/SIM、OSS/CDN live traffic、production DB/queue 或 verified terminal result。 |

KR-A Hardware reviewer ACK intake gate、KR-B Robot diagnostics safe alias、KR-C Full-Stack read-only panel 已由对应 worker 完成并通过 focused validation。KR-D Product closeout 本文件记录 combined fenced validation，并同步 `side2side_check.md`、`final.md`、`OKR.md`、`docs/process/okr_progress_log.md`。

## 实际改动文件

Hardware worker:

- `pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py`
- `pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py`
- `pc-tools/README.md`
- `docs/interfaces/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.md`
- `docs/product/production_hardware_boundary.md`

Robot worker:

- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py`
- `onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py`
- `onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py`
- `docs/interfaces/ros_runtime_contracts.md`
- `docs/product/remote_4g_mvp.md`

Full-Stack worker:

- `mobile/web/app.js`
- `mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json`
- `mobile/web/test_mobile_web_entrypoint.py`
- `docs/product/mobile_user_flow.md`

Product closeout:

- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/tech-done.md`
- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/side2side_check.md`
- `sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake/final.md`
- `OKR.md`
- `docs/process/okr_progress_log.md`

## Worker 结果核对

- Hardware：新增 PC-only reviewer ACK intake gate、focused tests、README、interface doc 和 production hardware boundary 更新。Hardware worker 已读取 `docs/vendor/VENDOR_INDEX.md`，并把 WAVE ROVER `base_ctrl.py`、`config.yaml`、`json_cmd.h`、`uart_ctrl.h`、`movtion_module.h` 作为 source-boundary evidence；Orange Pi PDFs 存在但未解析，因为 `pdftotext` 不可用。Python comment ratio reported 20.56%。本轮仍不是真实 LiDAR/ToF proof、不是 WAVE ROVER/UART/HIL。
- Robot：新增 `robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary` safe alias，并接入 operator diagnostics / remote relay read-only surfaces。首轮 operator test 因 raw sibling priority 失败，Robot worker 已修复为优先消费 robot safe alias，最终 focused checks 通过。
- Full-Stack：新增 `mobile/web` first-screen read-only PR5 reviewer ACK intake panel、fixture、focused tests 和 mobile flow docs。Start Delivery、Confirm Dropoff、Cancel 继续 disabled；无 material upload、GitHub mutation、ACK/cursor route、replay/resubmit 或 robot command path。

## Combined fenced validation

Product closeout 重新运行用户指定 combined fenced validation，结果如下：

```text
$ python3 -m py_compile pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py
passed

$ python3 -m unittest pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py
Ran 7 tests in 0.287s
OK

$ python3 -m py_compile onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py
passed

$ python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py -k pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
Ran 1 test in 0.028s
OK

$ python3 -m unittest onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py -k pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
Ran 1 test in 35.544s
OK

$ node --check mobile/web/app.js
passed

$ python3 -m json.tool mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json >/tmp/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_fixture_closeout.json
passed

$ python3 -m unittest mobile/web/test_mobile_web_entrypoint.py -k pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake
Ran 2 tests in 0.050s
OK

$ rg -n "pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake|robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_summary|software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate|PRRT_kwDOSWB9286CJ3tX|hardware_material_pending|source=software_proof|delivery_success=false|primary_actions_enabled=false|safe_to_control=false" pc-tools/evidence onboard/src/ros2_trashbot_behavior mobile/web docs sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake OKR.md
passed; representative hits include sprint PRD/tech-plan, OKR snapshot, pc-tools gate/test, Robot diagnostics safe alias, mobile fixture/panel, interface docs, product docs, and fail-closed flags.

$ git diff --check -- pc-tools/evidence/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py pc-tools/evidence/test_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.py pc-tools/README.md docs/interfaces/pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.md docs/product/production_hardware_boundary.md onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/ros2_trashbot_behavior/remote_cloud_relay.py onboard/src/ros2_trashbot_behavior/test/test_operator_gateway_diagnostics.py onboard/src/ros2_trashbot_behavior/test/test_remote_cloud_relay.py docs/interfaces/ros_runtime_contracts.md docs/product/remote_4g_mvp.md mobile/web/app.js mobile/web/fixtures/robot_diagnostics_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake.json mobile/web/test_mobile_web_entrypoint.py docs/product/mobile_user_flow.md sprints/2026.05.24_12-13_pr5-mandatory-sensor-material-owner-response-reviewer-ack-intake OKR.md docs/process/okr_progress_log.md
passed
```

GitHub read-only thread check:

```text
PR #5 review threads:
- PRRT_kwDOSWB9286CJ3tQ is_resolved=true
- PRRT_kwDOSWB9286CJ3tU is_resolved=true
- PRRT_kwDOSWB9286CJ3tX is_resolved=false, resolved_by=null

PR #7 review threads:
- []
```

No GitHub mutation, PR thread resolution, label mutation, comment mutation, or reviewer action was performed.

## 失败定位

Product closeout rerun found no new validation failure. Known worker-phase failure already fixed by Robot worker: operator diagnostics initially preferred a raw sibling summary over the robot safe alias; fix was to prefer the robot safe alias so only sanitized reviewer ACK intake fields reach Robot/mobile consumers.

## 剩余风险和证据缺口

- PR #5 `PRRT_kwDOSWB9286CJ3tX` remains unresolved / `hardware_material_pending`; PR #7 open/no review threads does not resolve it.
- This is `source=software_proof` and `software_proof_docker_pr5_mandatory_sensor_material_owner_response_reviewer_ack_intake_gate` only.
- Not real LiDAR/ToF proof, not WAVE ROVER/UART/HIL, not true phone/browser proof, not GitHub mutation/resolution, not Objective 5 external proof, not route/elevator field pass, not Nav2/fixed-route runtime pass, not verified terminal result, not delivery success.
- `delivery_success=false`、`primary_actions_enabled=false`、`safe_to_control=false` remain mandatory.
- Objective 5 remains about 68%；Objective 1 remains about 81%；Objective 4 remains about 99%；no OKR percentage lift.

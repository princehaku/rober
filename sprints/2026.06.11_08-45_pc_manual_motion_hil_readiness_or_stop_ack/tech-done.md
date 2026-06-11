# PC Manual Motion HIL Readiness Or Stop ACK

## sprint_type

micro

## 已读 vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`

采用的硬件事实：

- WAVE ROVER 上下位机链路是 UART、UTF-8、newline-delimited JSON。
- vendor Raspberry Pi 示例使用 `/dev/ttyAMA0`、`115200`；本项目 Orange Pi 上车串口不能凭此硬编码，必须以真实目标机 readback/配置为准。
- vendor 固件中 `T=1` 是左右轮速度控制，`T=13` 是 ROS 线速度/角速度控制，`T=130/131/142/143` 分别用于底盘反馈请求、反馈流、反馈间隔和 UART echo。
- 本轮不直接写串口、不直接调用远端 `/api/base/manual` 发送非零运动；PC 手动运动尝试只走 workstation proxy 固定接口。

## 已证实的硬件/门禁结论

- 真实上位机 Robot API `http://192.168.1.11:8787` 当前可读：
  - `GET /api/operator/report`：HTTP 200，`operator_report_status=ready_for_execution`，`field_hil_material=false`。
  - `GET /api/base/status`：HTTP 200，`robot_control_executed=false`，`safe_to_control=false`，`sends_motion_commands=false`。
  - `GET /api/base/feedback-samples/latest`：HTTP 200，`robot_control_executed=false`，`sends_motion_commands=false`。
- 当前 operator report 只确认了 `operator_present=true`、`physical_clearance_confirmed=true`、`emergency_stop_ready=true`；仍缺少真实 HIL 必需材料：
  - `external_video_recorded=false`
  - `visible_content_proven=false`
  - `wheel_feedback_lr_nonzero_proven=false`
  - `physical_motion_lidar_delta_proven=false`
- PC proxy stop safety smoke 通过：`POST /api/robot-control/base/stop?baseUrl=http://192.168.1.11:8787` 返回 HTTP 200，`remote_http_status=200`，`proxy_status=command_forwarded`，`operator_report_preflight.status=not_required_for_stop`，证明 stop 通道可达且不依赖 operator report。
- PC proxy 低速 non-stop manual 请求被本地安全门禁拦截：
  - 请求：`direction=forward`、`speed=0.05`、`duration_ms=400`、`confirm_hil_checklist=true`
  - 响应：HTTP 400，`proxy_status=command_rejected`，`failure_reason=operator_report_preflight_required`，`operator_report_preflight.status=blocked`
  - 关键安全字段：`remote_http_status=null`、`robot_control_executed=false`
- 是否发生真实非零运动：no。门禁阻止原因是 operator report 缺少外部视频、可见相机材料、左右轮非零反馈材料和 LiDAR delta 材料；因此没有远端 `/api/base/manual` 非零调用，没有 `/cmd_vel` 或 UART 命令证据。

## 实际改动

- 新增本 sprint 留档：
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/tech-done.md`
- 新增真实 smoke artifacts：
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/before_operator_report.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/before_base_status.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/before_feedback_latest.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/pc_summary_before.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/pc_stop_before_manual.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/pc_manual_attempt.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/after_operator_report.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/after_base_status.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/after_feedback_latest.json`
  - `sprints/2026.06.11_08-45_pc_manual_motion_hil_readiness_or_stop_ack/artifacts/real_pc_manual_motion_gate_capture.json`

未改 PC 普通首屏 UI、PC proxy 产品代码、onboard Python API、launch 参数、串口配置或 vendor 文件。

## 验证结果

- `git diff --check`：通过，无 whitespace 错误。
- `GET http://192.168.1.11:8787/api/operator/report`：HTTP 200，`operator_report_status=ready_for_execution`，`field_hil_material=false`，缺少真实 HIL 四项材料。
- `GET http://192.168.1.11:8787/api/base/status`：HTTP 200，`robot_control_executed=false`，`safe_to_control=false`，`sends_motion_commands=false`。
- `GET http://192.168.1.11:8787/api/base/feedback-samples/latest`：HTTP 200，`robot_control_executed=false`，`sends_motion_commands=false`。
- `GET http://127.0.0.1:8787/api/robot-control/summary?baseUrl=http://192.168.1.11:8787`：HTTP 200，`robot_api_connection.status=blocked`，`loaded_count=10`，`blocked_count=3`。
- PC proxy stop smoke：
  - HTTP 200
  - `proxy_status=command_forwarded`
  - `remote_http_status=200`
  - `robot_control_executed=false`
  - `operator_report_preflight.status=not_required_for_stop`
- PC proxy non-stop manual smoke：
  - HTTP 400
  - `proxy_status=command_rejected`
  - `failure_reason=operator_report_preflight_required`
  - `operator_report_preflight.status=blocked`
  - `operator_report_preflight.http_status=200`
  - `operator_report_preflight.missing_fields=[external_video_recorded, visible_content_proven, wheel_feedback_lr_nonzero_proven, physical_motion_lidar_delta_proven]`
  - `remote_http_status=null`
  - `robot_control_executed=false`
- Cleanup：
  - SSH `root@192.168.1.11 -p 37878` 可达。
  - 上位机 API 进程仍在：`python3 /root/rober/onboard/scripts/upper_robot_api.py --host 0.0.0.0 --port 8787 --camera-base-url http://127.0.0.1:8088 --base-port /dev/ttyS5 --base-baudrate 115200 --max-speed 0.12`
  - `0.0.0.0:8787` 由该 `python3` 进程监听。
  - `lsof /dev/ttyS5` / `fuser /dev/ttyS5` 未返回占用。
  - 未发现 `base/manual`、`base/stop`、`robot-control`、`pc-tools` helper 残留进程。
- PC test/docs 未改，未运行 `cd pc-tools/workstation && npm run test -- --run`。
- Python API 未改，未运行 `python3 -m unittest onboard.tests.test_upper_robot_api`。

## 剩余风险和下一步履约动作

- 本轮没有真实非零运动，结论是 HIL readiness blocked by missing field materials，而不是 HIL pass。
- operator report 里的 `operator_present`、clearance 和 E-stop 为现场人工上报材料；PC proxy 只消费结构化字段，不验证外部视频/相机/轮速/LiDAR 文件真实性。
- 下一步需要现场补齐并上传真实外部视频 ref、可见相机材料 ref、左右轮非零反馈 ref、LiDAR delta ref。只有 readback 明确这些材料真实存在且当前安全条件满足时，才允许 exactly one 低速短点动，且点动后必须立即 stop 并保存 before/after readbacks。
- OKR 软提醒：本 micro sprint 针对 O1 真实 WAVE ROVER 上车 HIL 准入，也支撑 O7 PC 手动控制门禁证据。

## 当前运行时间

2026-06-11 08:44:17 CST

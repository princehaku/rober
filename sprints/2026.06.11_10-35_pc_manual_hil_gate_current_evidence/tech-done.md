# PC Manual HIL Gate Current Evidence

## sprint_type

micro

## 本轮目标

本轮继续推进真实上车 evidence capture，但只聚焦 PC workstation `手动移动/运动`
链路的真实 HIL 准入判断。真实上位机为 `root@192.168.1.11:37878`，
Robot API 为 `http://192.168.1.11:8787`，PC proxy 本地为
`http://127.0.0.1:8796`。

## 已读 vendor 来源

- `AGENTS.md`
- `OKR.md`
- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/base_ctrl.py`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/config.yaml`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/uart_ctrl.h`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/movtion_module.h`

采用的硬件事实边界：WAVE ROVER 上下位机链路是 UART UTF-8 JSON 按行发送；
vendor Raspberry Pi 参考默认 `/dev/ttyAMA0 @ 115200`，项目 Orange Pi 真实路径
必须以现场 readback 为准；速度/反馈命令包括 `T=1`、`T=13`、`T=130`、
`T=131`，其中 `T=13` 仍不能写成当前底盘已实机确认。本轮没有改 vendor、
firmware、串口默认值或 launch 硬件默认。

## 当前 gate 判断

本轮先读取以下当前端点，并保存 raw JSON：

- `/api/operator/report`
- `/api/base/status`
- `/api/base/feedback-samples/latest`
- `/api/radar/status`
- `/api/radar/scan-proof/latest`

五个端点均返回 HTTP 200。当前 PC manual 非 stop HIL gate 为 `blocked`，缺项：

- `external_video_recorded=false`
- `visible_content_proven=false`
- `wheel_feedback_lr_nonzero_proven=false`
- `physical_motion_lidar_delta_proven=false`

同时 `operator_present=true`、`physical_clearance_confirmed=true`、
`emergency_stop_ready=true` 已满足。上一轮摄像头结论仍成立：
`visible_content_proven=false` 是阻止真实手动运动的合理 gate 缺口。

## 是否执行真实非零运动

未执行真实非零运动。

原因：PC gate 当前不满足。按安全边界，本轮没有绕过 PC proxy 调远端
`/api/base/manual`，没有发布 `/cmd_vel`，没有调用 Nav2 start/NavigateToPose，
没有写 `/dev/ttyS5`。

## 实际改动

- 新增本轮 artifact：
  `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/artifacts/**`
- 新增本轮留档：
  `sprints/2026.06.11_10-35_pc_manual_hil_gate_current_evidence/tech-done.md`
- 更新硬件 smoke 文档：
  `docs/hardware/board_sensor_stack_smoke.md`
- 更新 PC workstation 产品边界：
  `docs/product/pc_tools_workstation.md`
- 更新 PC tools README：
  `pc-tools/README.md`

未修改 PC 代码、onboard Python、vendor 资料、WAVE ROVER firmware/factory binary、
底盘串口默认值、launch 硬件默认、Nav2 start/fixed route execution、camera/radar
参数或 PC 普通用户首屏结构/风格。

## Artifact 路径和关键字段

- `artifacts/pc_proxy/gate_decision_before.json`
  - `operator_gate.status=blocked`
  - `missing_fields=["external_video_recorded","visible_content_proven","wheel_feedback_lr_nonzero_proven","physical_motion_lidar_delta_proven"]`
  - `visible_content_proven_blocks_motion=true`
  - `manual_nonzero_policy=do_not_send_nonzero_expect_pc_local_reject`
- `artifacts/pc_proxy/stop_safety_smoke.json`
  - `http_status=200`
  - `proxy_status=command_forwarded`
  - `remote_endpoint=/api/base/stop`
  - `remote_http_status=200`
  - `robot_control_executed=false`
  - `evidence_capture_status=captured`
- `artifacts/pc_proxy/manual_forward_expected_reject.json`
  - request body: `direction=forward`、`speed=0.12`、`duration_ms=800`、
    `confirm_hil_checklist=true`
  - `http_status=400`
  - `proxy_status=command_rejected`
  - `failure_reason=operator_report_preflight_required`
  - `remote_endpoint=/api/base/manual`
  - `remote_http_status=null`
  - `operator_report_preflight.status=blocked`
  - `robot_control_executed=false`
  - `evidence_capture_status=captured`
- `artifacts/pc_proxy/proxy_smoke_result.json`
  - `remote_base_manual_not_called_by_local_reject=true`
- `artifacts/remote_readback/*.json`
  - before/after operator、base、feedback、radar、scan proof readbacks。
- `artifacts/ssh_cleanup/remote_cleanup_readback.log`
  - `trashbot-upper-robot-api.service active`
  - `trashbot-local-webrtc-camera.service active`
  - `8088/8787` 正常监听
  - `/dev/ttyS5`、`/dev/ttyACM0` 的 `lsof`/`fuser` 无占用输出
  - helper grep 只看到常驻 `upper_robot_api.py` 和 `local_webrtc_camera_smoke.py`
- `artifacts/logs/git_diff_check.log`
  - `git diff --check` 输出为空，通过。

## 验证结果

- 真实 PC proxy smoke：通过。
  - stop safety smoke 只通过 PC proxy 调用固定 `/api/base/stop`。
  - non-stop manual request 被 PC 本地拒绝，未调用远端 `/api/base/manual`。
- SSH cleanup/readback：通过。
  - 上位机服务保持 active，目标设备无本轮 helper 残留占用。
- `git diff --check`：通过，输出为空，记录在 `artifacts/logs/git_diff_check.log`。

未运行 `cd pc-tools/workstation && npm run build && npm run test -- --run && npm run lint`，
因为本轮没有修改 PC 代码。未运行 onboard Python `py_compile` 或 unittest，因为本轮
没有修改 onboard Python。

## 剩余风险和下一步现场动作

- 现场补外部视频，并把真实可复核路径写入 `external_video_ref`。
- 处理 DV20 USB 摄像头近黑问题；把摄像头对准明亮场景或更换 UVC 摄像头，重跑可见内容 proof，
  直到 `visible_content_proven=true` 且 `camera_artifacts_ref` 有效。
- 在 PC gate 允许前，不做非 stop manual jog；补齐可见画面后，仍需补
  `wheel_feedback_lr_nonzero_proven` 和 `physical_motion_lidar_delta_proven` 的真实引用。
- 后续若 gate 全部通过，只允许通过 PC workstation proxy 执行 exactly one 低速短时
  `forward` jog，并立即 stop，保存 before/after base feedback、wheel feedback、
  LiDAR scan proof/delta、operator report 和 cleanup。

## 完成前反思

- 本轮没有误把材料 readback 或 stop smoke 写成 HIL pass。
- 本轮没有绕过 PC proxy，未触碰 `/cmd_vel`、Nav2 start、底盘串口写入或 vendor 文件。
- 当前缺口是现场材料和可见相机内容，不是 PC proxy gate 行为缺失。

## 当前运行时间

2026-06-11 10:34:32 CST

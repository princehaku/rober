# PC Robot API 端口漂移诊断

sprint_type: micro

## 实际改动

- 在 `pc-tools/workstation/src/server/robotControlSummary.ts` 增加 `192.168.1.11:7071` 端口漂移识别：当显式传入 7071 且只读端点全失败时，`robot_api_connection.blocked_reasons` 与 `blocked_reasons` 首位返回 `robot_api_port_7071_mismatch_use_8787`。
- 同步把 `current_fact_plain` 前置为普通用户文案：PC 页面端口是 `0.0.0.0:7001`，小车上位机 Robot API 是 `192.168.1.11:8787`，不要把 Robot API 填成 7071。
- 在 `pc-tools/workstation/test/catalog.test.ts` 增加 7071 全 fetch failed 回归测试，避免以后再把端口误填泛化成摄像头、雷达或 Nav2 故障。
- 更新 `pc-tools/README.md` 和 `docs/product/pc_tools_workstation.md`，明确 7001/8787/7071 的边界。

## 验证结果

- `npm --prefix pc-tools/workstation test -- catalog.test.ts -t "7071|default robot api|workstation node"` 通过：`1 passed | 162 skipped`。
- `npm --prefix pc-tools/workstation test` 通过：`2 files / 378 tests passed`。
- `npm --prefix pc-tools/workstation run build` 通过；仅保留既有 Vite chunk-size warning。
- 本机 PC API 已重启到 `0.0.0.0:7001`，监听 PID 为 `35798`。
- 远端只读复核：`ssh root@192.168.1.11 -p 37878` 下 `ss -ltnp` 显示 `0.0.0.0:8787` 和 `0.0.0.0:8088` 监听，没有 `7071` 监听。
- `GET http://127.0.0.1:7001/api/robot-control/summary` 默认返回 `source_base_url=http://192.168.1.11:8787`、`normalized_base_url=http://192.168.1.11:8787`，真实读数显示 `camera.status=source_first_frame_failed`、`camera.source_diagnosis_status=uvc_no_frame_not_exclusive`、`nav2.status=goal_succeeded_wheel_feedback_not_proven`、`nav2.path_preview_point_count=18`、`safe_command_boundary.nav2_goal_ready=true`、`free_roam_motion_start_ready=true`、`keyboard_control_start_ready=true`。
- `GET http://127.0.0.1:7001/api/robot-control/summary?baseUrl=http%3A%2F%2F192.168.1.11%3A7071` 返回 `robot_api_connection.blocked_reasons[0]=robot_api_port_7071_mismatch_use_8787`，`current_fact_plain` 首句明确提示 PC 页面是 `0.0.0.0:7001`、小车 Robot API 是 `192.168.1.11:8787`、不要填 7071。
- `GET http://127.0.0.1:7001/api/robot-control/camera/mjpeg/status` 默认走 `192.168.1.11:8787`，返回 `source_diagnosis_status=uvc_no_frame_not_exclusive`、`shared_preview_exclusive_camera_claim=false`、`last_failure_reason=camera_source_first_frame_failed`。

## 剩余风险

- 本轮只修正 PC 端只读诊断和默认端口误用提示，不会自动启动或修复远端 `upper_robot_api.py`。
- 自动驾驶真实运动仍需要现场显式安全确认后执行 Nav2/键盘/自由移动动作；本轮没有调用任何会发车的接口。
- live 状态显示摄像头不是页面独占，而是 UVC 首帧失败；Nav2 路线已可执行但上次执行的同窗口轮速 L/R 仍未非零，需要现场安全确认后按 ROS 模式重跑复验。

# Camera First Frame Motion Gate

sprint_type: micro

## 实际改动

- `onboard/scripts/local_webrtc_camera_smoke.py`
  - `/health` 新增 `last_successful_frame`，只有 WebRTC offer 或 MJPEG stream 真实读到 frame 后才把 `source_readiness` 升级为 `first_frame_observed`。
  - 保留 `source_selected_not_probed` 表示“已选中相机但还没读到帧”，避免把设备路径存在误当成画面 ready。
- `onboard/scripts/upper_robot_api.py`
  - `camera_motion_readiness()` 改为要求 `source_readiness=first_frame_observed` 且 `last_successful_frame` 存在。
  - 自动扫图 start 在相机未出首帧时返回 `camera_first_frame_not_observed`，不写 `enable_cmd_vel_publish`、`motion_hil_unlocked` 或 `cmd_vel_topic`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`
  - 普通首屏把“共享预览可尝试”和“自动扫图/建图可放行”分开。
  - 自动扫图/建图 motion gate 只接受浏览器像素可见、MJPEG 已绘制、first-frame probe 可见或上车 `first_frame_observed` 作为相机 ready 证据。
- `onboard/tests/test_local_webrtc_camera_smoke.py`、`onboard/tests/test_upper_robot_api.py`、`pc-tools/workstation/test/App.test.ts`
  - 覆盖首帧未观察时阻止自动扫图、首帧已观察时放行门禁，以及 PC ready fixture 的首帧证明口径。
- `docs/vision/board_camera_publisher.md`、`docs/product/pc_tools_workstation.md`
  - 同步记录：`source_selected_not_probed` 只说明设备已选中，不再代表可建图/可自助移动。

本轮未调用 subagent；原因是 CEO 明确要求去掉 subagent 调用，并且当前运行时此前反复失败在 child model service tier validation。

## 验证结果

- `python3 -m unittest onboard.tests.test_local_webrtc_camera_smoke onboard.tests.test_upper_robot_api`
  - 66 tests passed。
- `npm test -- App.test.ts`
  - 135 tests passed。
- `npm test -- catalog.test.ts`
  - 102 tests passed。
- `npm test`
  - 237 tests passed。
- `npm run build`
  - TypeScript 与 Vite build passed；保留 Vite chunk size warning。
- 部署验证：
  - 已复制 `local_webrtc_camera_smoke.py` 与 `upper_robot_api.py` 到 `root@192.168.1.11:37878`。
  - 上车进程已重启：8088 camera service PID 136161，8787 upper API PID 136162。
  - PC Node 已重启到 `0.0.0.0:7001`，监听 PID 37052。
- Live readback：
  - `GET http://192.168.1.11:8088/health` 返回 `status=ready`、`video_source=/dev/video1`、`source_usage.status=not_in_use`、`source_readiness=source_selected_not_probed`、`last_successful_frame=null`。
  - `GET http://127.0.0.1:7001/api/robot-control/summary?refresh=1` 返回 camera 同步为 `source_selected_not_probed`，`free_roam_autonomy_start_ready=true` 但 runtime 仍是 artifact-only/stopping。
  - `POST http://127.0.0.1:7001/api/robot-control/free-roam/autonomy/start?baseUrl=http://192.168.1.11:8787` 返回 `status=blocked`、`failure_reason=free_roam_motion_sensors_not_ready`、`blocked_reasons=["camera_first_frame_not_observed"]`、`sets_state_machine_parameters=false`、`motion_unlock_requested=false`。

## 剩余风险

- 当前相机没有被其它进程独占，但 DV20 `/dev/video1` 仍未证明能读到真实首帧；需要复位/更换摄像头、检查 USB 供电和视频输入源，或接入 known-good UVC 复测。
- 雷达已从自由低速自移动硬门禁降级为监看项，但 Nav2 完整路线执行仍受定位闭环影响；最新 live readback 仍显示 localization proof 有 `amcl_pose_observed=false` 的失败记录，不能宣称自动驾驶已修好。
- wheel raw L/R 仍是 `0/0`，不等于底盘物理运动已证明；键盘连续手控仍应保留现有轮速/HIL gate。

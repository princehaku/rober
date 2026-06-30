# onboard sensor current diagnostics

sprint_type: micro

## 实际改动

- 修正 `onboard/scripts/local_webrtc_camera_smoke.py` 的 `/health` 当前状态优先级：同一个视频源当前首帧失败时，历史 `last_successful_frame` 不再把 `source_observed` 置为 true，避免 PC 看到“当前失败但已观察首帧”的矛盾材料。
- 新增 `onboard/scripts/test_local_webrtc_camera_smoke_health.py`，覆盖 DV20 UVC 当前 `first_frame_total_timeout` 且无其他占用时，health 必须返回 `source_first_frame_failed` / `uvc_no_frame_not_exclusive`。
- 扩展 `onboard/scripts/test_upper_robot_api_free_roam.py`，验证 LiDAR driver 诊断 JSON 的 nested `diagnosis.status` 会展平成 PC 可消费的 `diagnosis_status`，例如 `serial_open_but_no_bytes`。
- 更新 `docs/product/pc_tools_workstation.md`，同步本轮现场只读诊断结论：PC 地图普通用户用本页大地图和 `?view=map`，ROS2 配套建议 RViz2 / Foxglove；相机当前问题按 USB/UVC 无首帧处理，雷达按 WAVE ROVER/STC vendor 资料和 driver diagnostics 排查。

## 验证结果

- `python3 -m unittest onboard.scripts.test_local_webrtc_camera_smoke_health onboard.scripts.test_upper_robot_api_free_roam`：通过，6 tests。
- `python3 -m py_compile onboard/scripts/local_webrtc_camera_smoke.py onboard/scripts/test_local_webrtc_camera_smoke_health.py onboard/scripts/test_upper_robot_api_free_roam.py`：通过。
- `python3 -m unittest onboard.src.ros2_trashbot_hardware.test.test_lidar_driver_stubs`：通过，16 tests。
- `npm test -- --run App.test.ts`（`pc-tools/workstation`）：通过，1 file / 225 tests。
- `git diff --check`：通过。

## 剩余风险

- 本轮没有发送任何 live 运动/control POST；SSH 只读诊断已确认相机更像 USB/UVC 层错误，不是页面独占，但未更换摄像头、线缆或供电做 HIL 复验。
- 现场雷达 lifecycle 运行但 `/scan`、`/lidar/raw_packet` 仍无消息；本地代码已有 driver diagnostics 文件合同，仍需在上车端部署/重启后读取 `/tmp/rober_lidar_lifecycle/lidar_driver_diagnostics.json` 才能区分无字节、无 packet 或无 scan。

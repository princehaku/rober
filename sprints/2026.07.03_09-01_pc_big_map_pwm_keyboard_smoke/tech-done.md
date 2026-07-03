# Tech Done

sprint_type: micro

## 实际改动

- PC 大地图链路继续以 `/api/robot-control/map/preview` 作为普通用户主入口；上位机 `/api/map/preview` 同包返回地图图片、Nav2 path preview、目标点、小车地图位姿和雷达贴图。
- 上位机地图预览新增目标点兜底：优先使用 `path_preview_points` 终点；如果路线点暂缺但最近 NavigateToPose artifact 有 `goal_request`，则以 `source=latest_goal_request` 返回目标点。
- PC summary/map preview 合同新增 `route_target_visible`、`route_target_source`、`route_target_state`，`/api/robot-control/live-summary` 同步暴露这些字段，脚本可直接判断图上目标是否可见。
- PC 前端地图目标 overlay 在没有直接 Nav2 execution 值时，会使用 `/api/map/preview.target`，避免地图有目标但页面不画 marker。
- PC 键盘连续手控和屏幕方向键默认改为 `command_mode=pwm`，固定代理 `/api/robot-control/base/manual` 转发到上位机 `/api/base/manual` 后走 WAVE ROVER `T=11` PWM 快速短脉冲。
- 文档更新 `docs/navigation/fixed_route_workflow.md` 和 `docs/product/pc_free_roam_mapping_design.md`，说明 PC `/map` 大屏、RViz2/Foxglove 工程观察边界、地图目标来源和 PWM 手控协议来源。

## Vendor 来源

- `docs/vendor/VENDOR_INDEX.md`
- `docs/vendor/waveshare_wave_rover/WAVE_ROVER/WAVE_ROVER_V0.9/json_cmd.h`
- `docs/vendor/waveshare_wave_rover/ugv_rpi/tutorial_cn/08 下位机 JSON 指令集.ipynb`

本轮采用的硬件协议事实：WAVE ROVER `T=11` 是左右轮 PWM 输入，`L/R` 为 `-255..255`；PC 键盘手控使用该路径只影响手控短脉冲，不改变 Nav2 自动路线的 ROS/Nav2 gate。

## 验证结果

- `python3 -m unittest onboard.src.ros2_trashbot_nav.test.test_upper_robot_api_map_preview_target_static`：通过，2 tests。
- `npm test -- App.test.ts robotControlSummary.test.ts catalog.test.ts`：通过，3 files / 435 tests。
- `npm run build`：通过；Vite 仍提示单 chunk 超 500 kB，为既有体积警告。
- 本机 PC 服务已重启在 `0.0.0.0:7001`，当前监听 PID 为 `31117`。
- `curl http://127.0.0.1:7001/map`：HTTP 200，`time_total=0.007652`。
- `GET /api/robot-control/map/preview?baseUrl=http://192.168.1.11:8787`：`proxy_status=preview_forwarded`，`path_preview_point_count=18`，`route_target_visible=true`，`route_target_source=path_preview_points`，`robot_pose_status=map_pose_observed`，`radar_overlay_status=loaded`，`radar_overlay_point_count=7`。
- `GET /api/robot-control/live-summary?baseUrl=http://192.168.1.11:8787`：`keyboard_manual_command_mode=pwm`，`path_preview_point_count=18`，`route_target_visible=true`，`radar_overlay_status=loaded`。
- `POST /api/robot-control/base/manual?baseUrl=http://192.168.1.11:8787`，body 为 `direction=right/speed_mps=0.04/duration_ms=180`：HTTP 200，`time_total=0.206903`，`proxy_status=command_forwarded`，`manual_command_executed=true`，`auto_stop_executed=true`。
- 上位机 `/root/rober/onboard/runtime/wave_rover_command_debug.jsonl` 尾部确认最近手控为 `command_mode=pwm`、`command_transport=http`、`vendor_command={"T":11,"L":255,"R":-255}`，随后 stop 为 `{"T":11,"L":0,"R":0}`。

## 剩余风险

- 相机仍未出实时画面。本轮 PC status 显示 `source_usage_scope=free`、`source_usage_not_exclusive=true`，不是独占占用；诊断为 `uvc_full_speed_usb_not_exclusive` / `first_frame_total_timeout`，需要换高速 USB 口/线/供电后复测。
- wheel raw L/R 非零仍未由本轮 180ms 手控回包证明，`wheel_feedback_lr_nonzero_proven=false`；当前已证明 PC 到上位机到底盘命令链写入成功，但轮速反馈闭环还需要更长反馈窗口或底盘反馈链路复测。
- 本轮没有做完整 Nav2 真实路线执行；只验证了地图路线/目标/雷达可见和手控快路径。自动驾驶路线执行仍需单独 HIL 验收。

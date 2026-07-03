# PC base feedback motion signal

## sprint_type

micro

## 实际改动

- `pc-tools/workstation/src/shared/contracts.ts`：`RobotControlBaseFeedbackSamplesProxyResponse` 新增 `imu_attitude_delta_observed`、`motion_signal_observed`、`motion_signal_source`、`motion_signal_plain_hint`、`motion_signal_next_action`，并在 `sample_key_values` 中保留同源字段。
- `pc-tools/workstation/src/server/index.ts`：`GET/POST /api/robot-control/base/feedback-samples` 从上车 `base_feedback_samples_latest` / sample payload 透传 IMU motion signal；当 wheel raw L/R 仍为 0/0 但 IMU 姿态变化已观察到时，顶层 `next_action_plain` 直接说明“已观察到 IMU 动作信号，但 wheel L/R 非零仍未证明”。
- `pc-tools/workstation/test/catalog.test.ts`：覆盖 POST 采样 motion=false 和 GET latest motion=true 两类读回，确保只读 feedback endpoint 不触发 manual/Nav2。
- `docs/product/pc_tools_workstation.md`、`docs/process/okr_progress_log.md`：同步记录 WASD/低速试动动作信号读回边界。

## 验证结果

- `npm test -- test/catalog.test.ts -t "base feedback samples" --run`：通过，2 tests OK / 186 skipped。
- `npm test -- test/App.test.ts -t "keyboard|WASD|feedback|wheel|motion signal|map display|camera" --run`：通过，87 tests OK / 153 skipped。
- `npm run build`：通过，仅 Vite chunk size warning。
- live 7001 验证：`GET /api/robot-control/base/feedback-samples` 返回 `wheel_raw_left=0`、`wheel_raw_right=0`、`wheel_feedback_lr_nonzero_proven=false`，同时返回 `imu_attitude_delta_observed=true`、`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`。
- live 地图复核：`path_preview_point_count=18`、`robot_pose_status=map_pose_observed`、`radar_overlay_current_point_count=98`、`route_target={x:0.8,y:0.05,frame_id:map,source:path_preview_points,source_index:17}`。
- 7001 已重启到 `HOST=0.0.0.0 PORT=7001 DEFAULT_ROBOT_API_BASE_URL=http://192.168.1.11:8787 npm run api`，新 PID `14126` 监听 `TCP *:7001`。

## 剩余风险

- 本轮增强 WASD/低速试动动作迹象读回，不等于 wheel raw L/R 非零已完成；当前 vendor `T=1001 L/R` 仍为 `0/0`。
- 摄像头仍为 `/dev/video1` DV20 无首帧；实时图传最终验收仍需摄像头输入、线/接口/供电或 known-good UVC 复测。

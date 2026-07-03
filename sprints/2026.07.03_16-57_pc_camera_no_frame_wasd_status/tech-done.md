# PC 相机无帧与 WASD 状态收口

## Sprint 类型

sprint_type: micro

## 实际改动

- `pc-tools/workstation/src/server/robotControlSummary.ts`：把 `source_first_frame_failed + uvc_no_frame_not_exclusive` 且非页面独占的相机无首帧状态提升为用户可理解的相机处理动作，输出 `camera_hardware_action_required=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`；同时保持 `camera_blocks_free_move=false` 和 `free_move_without_camera_allowed=true`。
- `pc-tools/workstation/src/components/RobotControlConsolePanel.vue`：普通 PC 首屏继续保持简单用户风格，把“硬件/速度/时长”等工程词改成“设备/画面处理、速率、持续”等口径；建图下一步文案在相机缺口存在时仍明确“自由移动不受影响”。
- `pc-tools/workstation/test/App.test.ts`、`pc-tools/workstation/test/robotControlSummary.test.ts`：同步更新 DOM 和 summary 回归，覆盖相机非独占无帧应提示检查摄像头输入/供电、且不阻塞自由移动。
- `docs/product/pc_tools_workstation.md`、`docs/product/pc_free_roam_mapping_design.md`：同步当前产品口径，说明普通用户用 PC 大地图，ROS2 工程观察可用 RViz2/Foxglove；相机当前为 480M 非独占但仍无帧。

## 资料来源

- 已按硬件纪律读取 `docs/vendor/VENDOR_INDEX.md`。
- WAVE ROVER 命令事实来自 `docs/vendor/waveshare_wave_rover/WAVE_ROVER_V0.9/json_cmd.h`：`T=11` 是 PWM 输入，`T=13` 是 ROS 速度输入且标注不适用于无编码器产品，`T=1001` 是底盘反馈。现场验证仍以同窗口 `T=1001 L/R` 是否非零作为 wheel raw L/R 证据边界。

## 验证结果

- `npx vitest run test/App.test.ts`：通过，239 tests。
- `npm test`：通过，3 个测试文件共 439 tests。
- `npm run lint`：通过。
- `npm run build`：通过；仅保留既有 Vite chunk size warning。
- PC Node 已重启并绑定 `0.0.0.0:7001`，health 读回 `host=0.0.0.0`、`port=7001`、robot base URL 为 `http://192.168.1.11:8787`。
- 真实 PC 首帧短探针：`probe_total_timeout`、remote HTTP 503；随后 summary 读回 `camera_status=source_first_frame_failed`、`camera_source_diagnosis_status=uvc_no_frame_not_exclusive`、`camera_source_diagnosis_not_exclusive=true`、`camera_hardware_action_required=true`、`camera_hardware_action_label=检查摄像头输入/供电后复测`、`camera_blocks_free_move=false`、`free_move_without_camera_allowed=true`。
- 真实 WASD/手控代理短脉冲：3 次 `POST /api/robot-control/base/manual` 均 `proxy_status=command_forwarded`、HTTP 200，stop 也 HTTP 200；远端 debug log 读到 `/cmd_vel -> esp32_bridge -> HTTP` 写出 vendor `T=11 L/R=255`，停止写出 `T=11 L/R=0`。
- 同窗口运动信号：`motion_signal_observed=true`、`motion_signal_source=imu_attitude_delta`；但 `wheel_nonzero=false`，`T=1001 L/R` 仍为 `0/0`。

## 剩余风险

- 实时相机画面仍未恢复：当前 DV20 是 USB `480M` 且无页面独占，但 kernel/capture 仍没有输出首帧；下一步应检查摄像头输入、供电、线缆或更换 known-good UVC 后复测。
- wheel raw L/R 非零尚未证明：已有 PWM 发车命令和 IMU 运动迹象，但 vendor `T=1001 L/R` 仍为 `0/0`，不能当作轮速反馈完成。
- 完整 Nav2 路线执行与 `delivery_success` 仍未收口；本轮只把相机无帧处理口径、普通 PC 文案和 WASD 命令链路状态收敛清楚。

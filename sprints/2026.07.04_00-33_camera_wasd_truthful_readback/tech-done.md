# 相机矩阵复测与 WASD 真实读回修正

sprint_type: micro

## 实际改动

- 修正 PC summary 顶层 `keyboard_wheel_lr_nonzero` 语义：它现在只代表真实 `wheel_feedback_lr_nonzero_proven=true`，不再把 `command_raw_lr_nonzero_proven`、`motion_evidence_complete` 或 IMU 姿态变化混入 wheel raw L/R 非零验收。
- 补充回归测试：即使 summary query 提供 command raw 非零和 motion complete，`keyboard_wheel_lr_nonzero` 仍必须在 wheel feedback 未证明时保持 `false`，同时 `keyboard_command_raw_lr_nonzero` 与 `keyboard_motion_evidence_complete` 可以单独为 `true`。
- 现场复测 DV20 相机完整格式矩阵，并同步 `pc-tools/README.md`、`docs/product/pc_tools_workstation.md`、`docs/vision/board_camera_publisher.md`。
- 硬件协议边界采用 `docs/vendor/VENDOR_INDEX.md`：本轮涉及 WAVE ROVER 运动读回时继续区分 vendor wheel feedback 与 IMU/命令运动信号；不把 IMU 姿态变化伪装成 wheel raw L/R。

## 验证结果

- `npm test -- --run test/catalog.test.ts -t "workstation summary reuses recent manual and stop evidence without keyboard query"`
  - 结果：通过，目标用例 1 passed。
- `npm test -- --run test/App.test.ts test/robotControlSummary.test.ts test/catalog.test.ts`
  - 结果：通过，`Test Files 3 passed`，`Tests 447 passed`。
- `npm run build`
  - 结果：通过，`tsc -p tsconfig.app.json && vite build && tsc -p tsconfig.server.json` 成功。
- 上位机状态
  - SSH：`root@192.168.1.11 -p 7878` 可连接。
  - `trashbot-upper-robot-api.service=active`，`trashbot-local-webrtc-camera.service=active`。
  - 8787 与 8088 均监听 `0.0.0.0`。
- 相机直接矩阵复测
  - 停止 `trashbot-local-webrtc-camera.service` 后 `/dev/video1` 无占用，DV20 位于 `480M` 高速 USB。
  - `MJPG@1920x1080@30`、`MJPG@1280x720@30`、`MJPG@640x480@30`、`MJPG@480x320@30`、`YUYV@640x480@22`、`YUYV@320x240@25`、`YUYV@320x240@20` 经 v4l2/ffmpeg 均为 0 字节。
  - 恢复相机服务后为 active，PC 共享 MJPEG 返回 `first_frame_total_timeout`。
- WASD/低速手控 live 复验
  - PC `forward` / `back` 短脉冲均 `proxy_status=command_forwarded`、`base_command_mode=ros`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`。
  - PC stop 代理 `proxy_status=command_forwarded`、`status=stopped`。
  - 修复后 live summary 读回 `keyboard_continuous_motion_verified=true`、`keyboard_stop_after_release=true`、`keyboard_command_raw_lr_nonzero=true`、`keyboard_motion_evidence_complete=true`，但 `keyboard_wheel_lr_nonzero=false` 且 `wheel_feedback_latest_raw_left/right=0/0`。

## 剩余风险

- 实时图传仍未达成：当前证据指向 DV20/摄像头输入信号、线材/接口、供电或上游视频源没有输出真实帧；PC 页面、共享预览独占、USB 低速和未覆盖格式已被排除。
- WASD 可通过 PC 固定代理产生同窗口命令与 IMU/车体运动信号，但 vendor `T1001 L/R` 仍为 `0/0`，不能宣称 wheel raw L/R 非零。
- 本轮未执行完整 Nav2 路线、delivery complete 或自由移动启动。

# PC Nav2 O11 防 OOM 与后退别名

sprint_type: micro

## 实际改动

- `onboard/scripts/o11_nav2_goal_execution_proof.py`：复用现场已有 Nav2/`esp32_bridge` runtime 时，从进程参数提取 `feedback_debug_log_path`、`command_debug_log_path` 和 `command_mode`，避免不抢串口的同时丢失底盘命令/反馈证据。
- `onboard/scripts/o11_nav2_goal_execution_proof.py`：`summarize_feedback_debug_log()` 与 `summarize_command_debug_log()` 改为只读 debug 日志尾部 2MiB 窗口；现场 `wave_rover_feedback_debug.jsonl` 已达 448 万行、约 1.19GB，全量 `read_text()` 会拖垮 2GB 上位机并触发 OOM。
- `pc-tools/workstation/src/server/index.ts`：PC manual 代理新增 `backward`/`reverse` 方向别名，统一归一为上位机标准 `back`；最终仍只转发固定白名单方向，不开放任意运动字符串。
- `onboard/tests/test_o11_nav2_goal_execution_proof.py` 与 `pc-tools/workstation/test/catalog.test.ts`：补 O11 debug 路径提取、大日志尾部窗口、防旧非零样本误证明，以及 `backward -> back` 代理回归。

硬件协议依据：`docs/vendor/VENDOR_INDEX.md` 指向的 Waveshare WAVE ROVER 本地资料，底盘控制为 UART 换行 JSON；本轮涉及的命令口径包括 `T=13` ROS 速度、`T=11` PWM 和 `T=1001` 底盘反馈。

## 验证结果

- `python3 -m unittest onboard.tests.test_o11_nav2_goal_execution_proof -v`：13 tests OK。
- `npm test -- test/catalog.test.ts -t "base manual proxy" --run`：4 tests OK / 184 skipped。
- `npm test -- test/App.test.ts -t "keyboard|WASD|map display|camera|Nav2|manual" --run`：93 tests OK / 146 skipped。
- `npm test -- test/robotControlSummary.test.ts --run`：15 tests OK。
- `npm run build`：通过，仅保留 Vite chunk size warning。
- 上位机部署验证：`/root/rober/onboard/scripts/o11_nav2_goal_execution_proof.py` 已同步并 `py_compile` 通过；真实 1.19GB `wave_rover_feedback_debug.jsonl` 摘要从全量卡死/OOM 风险降为 0.52 秒返回，`tail_truncated=true`。
- PC 7001 live：`GET /api/health` 返回 `workstation_host=0.0.0.0`、`workstation_port=7001`；`/api/robot-control/map/preview` 返回雷达当前点 143、路线点 18、机器人 `map` 位姿和目标点 `(0.8,0.05)`。
- PC 7001 live WASD/后退：`POST /api/robot-control/base/manual` 传 `direction=backward` 后实际转发 `back`，返回 `command_forwarded`、`command_result_ok=true`、`stop_result_ok=true`、`motion_signal_observed=true`。
- PC 7001 live Nav2：`POST /api/robot-control/nav2/goal/execute` 返回 `execution_forwarded`、`goal_accepted=true`、`cancel_accepted=true`、`uses_base_uart=true`、`base_command_nonzero_observed=true`、`base_command_nonzero_count=733`、`base_feedback_sample_count=5941`、`base_feedback_lr_nonzero_proven=false`、`base_feedback_imu_attitude_delta_observed=true`。

## 剩余风险

- 自动驾驶仍未完成验收：本轮证明 Nav2/bridge 已发非零底盘命令并观察到 IMU 运动迹象，但同窗口 WAVE ROVER `T=1001 L/R` 仍为 `0/0`，8 秒结果窗口为 `goal_timeout_cancel_requested`，不能宣称完整路线执行或 delivery success。
- 图传仍未完成验收：DV20 UVC 当前 480M、无人占用、不是 PC 页面独占，但 MJPG/YUYV 多格式首帧仍为 `first_frame_total_timeout`；需要检查摄像头输入、USB 线/接口/供电或换 known-good UVC。
